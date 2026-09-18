from uuid import uuid4

import httpx


API_URL = "http://127.0.0.1:9000"


def run_duplicate_record():
    run_id = uuid4().hex[:8]

    location = f"Duplicate Test Site {run_id}"
    finding = f"Duplicate integrity test {run_id}"

    payload = {
        "location": location,
        "inspector": "FlexGuard",
        "finding": finding,
        "notes": "Intentional duplicate detection test",
        "risk_level": "High",
        "idempotency_key": str(uuid4()),
    }

    try:
        with httpx.Client(timeout=10.0) as client:

            create_response = client.post(
                f"{API_URL}/inspections",
                json=payload,
            )

            if create_response.status_code != 200:
                return {
                    "scenario": "Duplicate Record",
                    "status": "FAIL",
                    "reason": (
                        f"Original record creation returned HTTP "
                        f"{create_response.status_code}"
                    ),
                }

            original = create_response.json()
            inspection_id = original["id"]

            duplicate_response = client.post(
                f"{API_URL}/test/duplicate/{inspection_id}"
            )

            if duplicate_response.status_code != 200:
                return {
                    "scenario": "Duplicate Record",
                    "status": "FAIL",
                    "reason": (
                        f"Duplicate creation returned HTTP "
                        f"{duplicate_response.status_code}"
                    ),
                }

            list_response = client.get(
                f"{API_URL}/inspections"
            )

            if list_response.status_code != 200:
                return {
                    "scenario": "Duplicate Record",
                    "status": "FAIL",
                    "reason": (
                        f"Inspection list returned HTTP "
                        f"{list_response.status_code}"
                    ),
                }

            inspections = list_response.json()

            matching_records = [
                inspection
                for inspection in inspections
                if (
                    inspection.get("location") == location
                    and inspection.get("finding") == finding
                )
            ]

            match_count = len(matching_records)

            if match_count == 2:
                return {
                    "scenario": "Duplicate Record",
                    "status": "PASS",
                    "reason": (
                        "Exactly 2 matching records detected"
                    ),
                }

            return {
                "scenario": "Duplicate Record",
                "status": "FAIL",
                "reason": (
                    f"Expected 2 matching records, "
                    f"found {match_count}"
                ),
            }

    except Exception as error:
        return {
            "scenario": "Duplicate Record",
            "status": "FAIL",
            "reason": str(error),
        }