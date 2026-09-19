import hashlib
from uuid import uuid4

import httpx


PROXY_URL = "http://127.0.0.1:9000"


def run_interrupted_upload():
    run_id = uuid4().hex[:8]
    key = str(uuid4())

    evidence_bytes = (
        b"FlexGuard evidence recovery "
        b"validation "
        + run_id.encode()
    )

    local_checksum = hashlib.sha256(
        evidence_bytes
    ).hexdigest()

    try:
        # Always start from a normal proxy state.
        httpx.post(
            f"{PROXY_URL}/__chaos/reset",
            timeout=5,
        )

        payload = {
            "idempotency_key": key,
            "location": (
                f"Evidence Recovery Site "
                f"{run_id}"
            ),
            "inspector": "FlexGuard",
            "finding": (
                "Evidence upload recovery "
                "validation"
            ),
            "notes": (
                "Evidence must survive "
                "temporary upload failure"
            ),
            "risk_level": "High",
        }

        # Create the inspection normally.
        create_response = httpx.post(
            f"{PROXY_URL}/inspections",
            json=payload,
            timeout=10,
        )

        if create_response.status_code != 200:
            return {
                "scenario": (
                    "Evidence Upload Recovery"
                ),
                "status": "FAIL",
                "reason": (
                    "Could not create inspection"
                ),
            }

        inspection_id = (
            create_response.json()["id"]
        )

        # Make the network/API path fail.
        mode_response = httpx.post(
            f"{PROXY_URL}/__chaos/mode",
            json={"mode": "error"},
            timeout=10,
        )

        if mode_response.status_code != 200:
            return {
                "scenario": (
                    "Evidence Upload Recovery"
                ),
                "status": "FAIL",
                "reason": (
                    "Could not enable failure mode"
                ),
            }

        files = {
            "file": (
                "evidence.png",
                evidence_bytes,
                "image/png",
            )
        }

        # First evidence attempt must fail.
        failed_upload = httpx.post(
            (
                f"{PROXY_URL}/inspections/"
                f"{inspection_id}/evidence"
            ),
            files=files,
            timeout=10,
        )

        if failed_upload.status_code != 500:
            return {
                "scenario": (
                    "Evidence Upload Recovery"
                ),
                "status": "FAIL",
                "reason": (
                    "Expected first evidence "
                    "upload to fail"
                ),
            }

        # Restore connectivity.
        reset_response = httpx.post(
            f"{PROXY_URL}/__chaos/reset",
            timeout=10,
        )

        if reset_response.status_code != 200:
            return {
                "scenario": (
                    "Evidence Upload Recovery"
                ),
                "status": "FAIL",
                "reason": (
                    "Could not restore "
                    "connectivity"
                ),
            }

        # Verify the failed upload did not
        # falsely mark evidence as present.
        before_retry = httpx.get(
            (
                f"{PROXY_URL}/inspections/"
                f"{inspection_id}"
            ),
            timeout=10,
        )

        if before_retry.status_code != 200:
            return {
                "scenario": (
                    "Evidence Upload Recovery"
                ),
                "status": "FAIL",
                "reason": (
                    "Could not verify inspection "
                    "after failed upload"
                ),
            }

        if before_retry.json().get(
            "evidence_path"
        ):
            return {
                "scenario": (
                    "Evidence Upload Recovery"
                ),
                "status": "FAIL",
                "reason": (
                    "Failed upload was incorrectly "
                    "recorded as evidence"
                ),
            }

        # Retry the same evidence normally.
        retry_files = {
            "file": (
                "evidence.png",
                evidence_bytes,
                "image/png",
            )
        }

        retry_response = httpx.post(
            (
                f"{PROXY_URL}/inspections/"
                f"{inspection_id}/evidence"
            ),
            files=retry_files,
            timeout=20,
        )

        if retry_response.status_code != 200:
            return {
                "scenario": (
                    "Evidence Upload Recovery"
                ),
                "status": "FAIL",
                "reason": (
                    "Evidence retry failed"
                ),
            }

        # Verify evidence integrity through
        # the API, not direct filesystem access.
        checksum_response = httpx.get(
            (
                f"{PROXY_URL}/inspections/"
                f"{inspection_id}/"
                "evidence/checksum"
            ),
            timeout=10,
        )

        if checksum_response.status_code != 200:
            return {
                "scenario": (
                    "Evidence Upload Recovery"
                ),
                "status": "FAIL",
                "reason": (
                    "Could not verify evidence "
                    "checksum"
                ),
            }

        server_checksum = (
            checksum_response.json()[
                "sha256"
            ]
        )

        if (
            server_checksum
            != local_checksum
        ):
            return {
                "scenario": (
                    "Evidence Upload Recovery"
                ),
                "status": "FAIL",
                "reason": (
                    "Evidence checksum mismatch"
                ),
            }

        # Submit only after evidence recovery.
        submit_response = httpx.post(
            (
                f"{PROXY_URL}/inspections/"
                f"{inspection_id}/submit"
            ),
            timeout=10,
        )

        if submit_response.status_code != 200:
            return {
                "scenario": (
                    "Evidence Upload Recovery"
                ),
                "status": "FAIL",
                "reason": (
                    "Inspection could not be "
                    "submitted after recovery"
                ),
            }

        final_response = httpx.get(
            (
                f"{PROXY_URL}/inspections/"
                f"{inspection_id}"
            ),
            timeout=10,
        )

        if final_response.status_code != 200:
            return {
                "scenario": (
                    "Evidence Upload Recovery"
                ),
                "status": "FAIL",
                "reason": (
                    "Could not verify final state"
                ),
            }

        final_record = (
            final_response.json()
        )

        if (
            final_record.get("status")
            != "submitted"
        ):
            return {
                "scenario": (
                    "Evidence Upload Recovery"
                ),
                "status": "FAIL",
                "reason": (
                    "Final inspection was not "
                    "submitted"
                ),
            }

        if not final_record.get(
            "evidence_path"
        ):
            return {
                "scenario": (
                    "Evidence Upload Recovery"
                ),
                "status": "FAIL",
                "reason": (
                    "Recovered evidence is missing"
                ),
            }

        return {
            "scenario": (
                "Evidence Upload Recovery"
            ),
            "status": "PASS",
            "reason": (
                "Failed evidence upload recovered "
                "on retry; checksum matched and "
                "inspection submitted"
            ),
            "inspection_id": inspection_id,
        }

    except Exception as error:
        return {
            "scenario": (
                "Evidence Upload Recovery"
            ),
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


if __name__ == "__main__":
    print(
        run_interrupted_upload()
    )