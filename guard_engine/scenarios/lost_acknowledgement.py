from uuid import uuid4

import httpx


PROXY_URL = "http://127.0.0.1:9000"


def run():
    key = str(uuid4())

    payload = {
        "idempotency_key": key,
        "location": "Galway Reliability Test",
        "inspector": "FlexGuard",
        "finding": "Lost acknowledgement validation",
        "notes": (
            "Server commit should survive "
            "a lost acknowledgement"
        ),
        "risk_level": "High",
    }

    try:
        # Enable lost acknowledgement mode
        mode_response = httpx.post(
            f"{PROXY_URL}/__chaos/mode",
            json={"mode": "lost_ack"},
            timeout=10,
        )

        if mode_response.status_code != 200:
            return {
                "scenario": "Lost Acknowledgement",
                "status": "FAIL",
                "reason": "Could not enable lost_ack mode",
            }

        # First request reaches backend,
        # but acknowledgement is deliberately lost
        first_response = httpx.post(
            f"{PROXY_URL}/inspections",
            json=payload,
            timeout=10,
        )

        if first_response.status_code != 504:
            return {
                "scenario": "Lost Acknowledgement",
                "status": "FAIL",
                "reason": (
                    "Expected lost acknowledgement "
                    "HTTP 504"
                ),
            }

        # Restore normal connectivity
        httpx.post(
            f"{PROXY_URL}/__chaos/reset",
            timeout=10,
        )

        # Retry exact same operation
        retry_response = httpx.post(
            f"{PROXY_URL}/inspections",
            json=payload,
            timeout=10,
        )

        if retry_response.status_code != 200:
            return {
                "scenario": "Lost Acknowledgement",
                "status": "FAIL",
                "reason": "Retry did not succeed",
            }

        retry_record = retry_response.json()

        # Verify exactly one record exists
        all_response = httpx.get(
            f"{PROXY_URL}/inspections",
            timeout=10,
        )

        all_response.raise_for_status()

        matches = [
            record
            for record in all_response.json()
            if record.get("idempotency_key") == key
        ]

        if len(matches) != 1:
            return {
                "scenario": "Lost Acknowledgement",
                "status": "FAIL",
                "reason": (
                    f"Expected 1 record, "
                    f"found {len(matches)}"
                ),
            }

        if matches[0]["id"] != retry_record["id"]:
            return {
                "scenario": "Lost Acknowledgement",
                "status": "FAIL",
                "reason": (
                    "Retry returned a different "
                    "inspection"
                ),
            }

        return {
            "scenario": "Lost Acknowledgement",
            "status": "PASS",
            "reason": (
                "Server commit survived lost "
                "acknowledgement; retry returned "
                "the same inspection with no duplicate"
            ),
            "inspection_id": retry_record["id"],
        }

    except Exception as error:
        return {
            "scenario": "Lost Acknowledgement",
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
    print(run())