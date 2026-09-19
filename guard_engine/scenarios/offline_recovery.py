from pathlib import Path
from uuid import uuid4
import base64

import httpx

from fieldsync.offline_queue import (
    add_to_queue,
    get_queue_item,
    sync_queue_item,
)


PROXY_URL = "http://127.0.0.1:9000"


def run():
    run_id = uuid4().hex[:8]
    key = str(uuid4())

    evidence_dir = Path(
        "guard_engine/results"
    )
    evidence_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    evidence_file = (
        evidence_dir
        / f"offline_evidence_{run_id}.png"
    )

    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB"
        "CAQAAAC1HAwCAAAAC0lEQVR42mP8/x8A"
        "AusB9Y9Zk6YAAAAASUVORK5CYII="
    )

    evidence_file.write_bytes(
        png_data
    )

    queue_id = None

    try:
        # Simulate unavailable backend/network.
        mode_response = httpx.post(
            f"{PROXY_URL}/__chaos/mode",
            json={"mode": "error"},
            timeout=10,
        )

        if mode_response.status_code != 200:
            return {
                "scenario": "Offline Recovery",
                "status": "FAIL",
                "reason": (
                    "Could not enable failure mode"
                ),
            }

        payload = {
            "idempotency_key": key,
            "location": (
                f"Offline Recovery Site {run_id}"
            ),
            "inspector": "FlexGuard",
            "finding": (
                "Offline recovery validation"
            ),
            "notes": (
                "Inspection must survive "
                "temporary connectivity loss"
            ),
            "risk_level": "High",
        }

        # First attempt should fail through
        # the chaos proxy.
        first_response = httpx.post(
            f"{PROXY_URL}/inspections",
            json=payload,
            timeout=10,
        )

        if first_response.status_code != 500:
            return {
                "scenario": "Offline Recovery",
                "status": "FAIL",
                "reason": (
                    "Expected initial request "
                    "to fail"
                ),
            }

        # Application preserves the operation
        # locally instead of losing it.
        queue_id = add_to_queue(
            location=payload["location"],
            inspector=payload["inspector"],
            finding=payload["finding"],
            notes=payload["notes"],
            risk_level=payload["risk_level"],
            evidence_path=str(
                evidence_file
            ),
            idempotency_key=key,
        )

        queued = get_queue_item(
            queue_id
        )

        if (
            queued is None
            or queued["status"] != "PENDING"
        ):
            return {
                "scenario": "Offline Recovery",
                "status": "FAIL",
                "reason": (
                    "Inspection was not safely "
                    "stored as PENDING"
                ),
            }

        # Connectivity returns.
        reset_response = httpx.post(
            f"{PROXY_URL}/__chaos/reset",
            timeout=10,
        )

        if reset_response.status_code != 200:
            return {
                "scenario": "Offline Recovery",
                "status": "FAIL",
                "reason": (
                    "Could not restore "
                    "normal connectivity"
                ),
            }

        # Retry the exact queued operation.
        sync_result = sync_queue_item(
            queue_id
        )

        if (
            sync_result.get("status")
            != "SYNCED"
        ):
            return {
                "scenario": "Offline Recovery",
                "status": "FAIL",
                "reason": (
                    "Queued inspection did not "
                    "recover successfully: "
                    f"{sync_result.get('message')}"
                ),
            }

        queued_after = get_queue_item(
            queue_id
        )

        if (
            queued_after is None
            or queued_after["status"]
            != "SYNCED"
        ):
            return {
                "scenario": "Offline Recovery",
                "status": "FAIL",
                "reason": (
                    "Local queue was not marked "
                    "SYNCED"
                ),
            }

        # Verify server state.
        all_response = httpx.get(
            f"{PROXY_URL}/inspections",
            timeout=10,
        )

        all_response.raise_for_status()

        matches = [
            record
            for record in all_response.json()
            if (
                record.get(
                    "idempotency_key"
                )
                == key
            )
        ]

        if len(matches) != 1:
            return {
                "scenario": "Offline Recovery",
                "status": "FAIL",
                "reason": (
                    f"Expected exactly 1 "
                    f"server record, found "
                    f"{len(matches)}"
                ),
            }

        server_record = matches[0]

        if (
            server_record.get("status")
            != "submitted"
        ):
            return {
                "scenario": "Offline Recovery",
                "status": "FAIL",
                "reason": (
                    "Server inspection was not "
                    "submitted"
                ),
            }

        if not server_record.get(
            "evidence_path"
        ):
            return {
                "scenario": "Offline Recovery",
                "status": "FAIL",
                "reason": (
                    "Evidence was not uploaded "
                    "during recovery"
                ),
            }

        return {
            "scenario": "Offline Recovery",
            "status": "PASS",
            "reason": (
                "Inspection survived connectivity "
                "loss, synced after recovery, "
                "uploaded evidence and created "
                "exactly one server record"
            ),
            "inspection_id": (
                server_record["id"]
            ),
        }

    except Exception as error:
        return {
            "scenario": "Offline Recovery",
            "status": "FAIL",
            "reason": str(error),
        }

    finally:
        try:
            httpx.post(
                f"{PROXY_URL}/__chaos/reset",
                timeout=5,
            )
        except Exception:
            pass

        try:
            if evidence_file.exists():
                evidence_file.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    print(run())