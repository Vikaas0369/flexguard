import uuid

import httpx


API_URL = "http://127.0.0.1:9000"


def run_missing_record():

    request_key = str(uuid.uuid4())

    data = {
        "idempotency_key": request_key,
        "location": "Integrity Test Site",
        "inspector": "FlexGuard",
        "finding": "Missing record test",
        "notes": "Created for integrity testing",
        "risk_level": "Low",
    }

    try:
        create_response = httpx.post(
            f"{API_URL}/inspections",
            json=data,
            timeout=10
        )

        if create_response.status_code != 200:
            return {
                "scenario": "Missing Record",
                "status": "FAIL",
                "reason": "Could not create test inspection"
            }

        inspection_id = create_response.json()["id"]

        delete_response = httpx.delete(
            f"{API_URL}/test/inspections/{inspection_id}",
            timeout=10
        )

        if delete_response.status_code != 200:
            return {
                "scenario": "Missing Record",
                "status": "FAIL",
                "reason": "Could not simulate missing record"
            }

        check_response = httpx.get(
            f"{API_URL}/inspections/{inspection_id}",
            timeout=10
        )

        if check_response.status_code == 404:
            return {
                "scenario": "Missing Record",
                "status": "PASS",
                "reason": "Missing record detected correctly"
            }

        return {
            "scenario": "Missing Record",
            "status": "FAIL",
            "reason": "Missing record was not detected"
        }

    except Exception as error:
        return {
            "scenario": "Missing Record",
            "status": "FAIL",
            "reason": str(error)
        }