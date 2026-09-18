import uuid

import httpx


API_URL = "http://127.0.0.1:9000"


def run_duplicate_record():

    request_key = str(uuid.uuid4())

    data = {
        "idempotency_key": request_key,
        "location": "Integrity Duplicate Site",
        "inspector": "FlexGuard",
        "finding": "Duplicate record test",
        "notes": "Created for integrity testing",
        "risk_level": "Medium",
    }

    try:
        create_response = httpx.post(
            f"{API_URL}/inspections",
            json=data,
            timeout=10
        )

        if create_response.status_code != 200:
            return {
                "scenario": "Duplicate Record",
                "status": "FAIL",
                "reason": "Could not create test inspection"
            }

        inspection_id = create_response.json()["id"]

        duplicate_response = httpx.post(
            f"{API_URL}/test/duplicate/{inspection_id}",
            timeout=10
        )

        if duplicate_response.status_code != 200:
            return {
                "scenario": "Duplicate Record",
                "status": "FAIL",
                "reason": "Could not create duplicate"
            }

        all_response = httpx.get(
            f"{API_URL}/inspections",
            timeout=10
        )

        inspections = all_response.json()

        matches = [
            item
            for item in inspections
            if (
                item["location"] == "Integrity Duplicate Site"
                and item["finding"] == "Duplicate record test"
            )
        ]

        if len(matches) > 1:
            return {
                "scenario": "Duplicate Record",
                "status": "PASS",
                "reason": f"{len(matches)} matching records detected"
            }

        return {
            "scenario": "Duplicate Record",
            "status": "FAIL",
            "reason": "Duplicate was not detected"
        }

    except Exception as error:
        return {
            "scenario": "Duplicate Record",
            "status": "FAIL",
            "reason": str(error)
        }