import uuid

import httpx


API_URL = "http://127.0.0.1:9000"


def run_changed_data():

    request_key = str(uuid.uuid4())

    expected_risk = "High"

    data = {
        "idempotency_key": request_key,
        "location": "Integrity Change Site",
        "inspector": "FlexGuard",
        "finding": "Changed data test",
        "notes": "Checking data integrity",
        "risk_level": expected_risk,
    }

    try:
        create_response = httpx.post(
            f"{API_URL}/inspections",
            json=data,
            timeout=10
        )

        if create_response.status_code != 200:
            return {
                "scenario": "Changed Data",
                "status": "FAIL",
                "reason": "Could not create test inspection"
            }

        inspection_id = create_response.json()["id"]

        change_response = httpx.patch(
            f"{API_URL}/test/change/{inspection_id}",
            timeout=10
        )

        if change_response.status_code != 200:
            return {
                "scenario": "Changed Data",
                "status": "FAIL",
                "reason": "Could not simulate changed data"
            }

        check_response = httpx.get(
            f"{API_URL}/inspections/{inspection_id}",
            timeout=10
        )

        saved = check_response.json()

        actual_risk = saved["risk_level"]

        if actual_risk != expected_risk:
            return {
                "scenario": "Changed Data",
                "status": "PASS",
                "reason": (
                    f"Expected {expected_risk}, "
                    f"found {actual_risk}"
                )
            }

        return {
            "scenario": "Changed Data",
            "status": "FAIL",
            "reason": "Data change was not detected"
        }

    except Exception as error:
        return {
            "scenario": "Changed Data",
            "status": "FAIL",
            "reason": str(error)
        }