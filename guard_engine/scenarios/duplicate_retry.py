import uuid

import httpx


API_URL = "http://127.0.0.1:8000"


def run_duplicate_retry():

    request_key = str(uuid.uuid4())

    data = {
        "idempotency_key": request_key,
        "location": "Duplicate Retry Test",
        "inspector": "FlexGuard",
        "finding": "Duplicate retry scenario",
        "notes": "Same request sent twice",
        "risk_level": "Medium",
    }

    try:
        first_response = httpx.post(
            f"{API_URL}/inspections",
            json=data,
            timeout=10
        )

        second_response = httpx.post(
            f"{API_URL}/inspections",
            json=data,
            timeout=10
        )

        if (
            first_response.status_code != 200
            or second_response.status_code != 200
        ):
            return {
                "scenario": "Duplicate Retry",
                "status": "FAIL",
                "reason": "One of the requests failed"
            }

        first_id = first_response.json()["id"]
        second_id = second_response.json()["id"]

        if first_id == second_id:
            return {
                "scenario": "Duplicate Retry",
                "status": "PASS",
                "reason": (
                    f"Both requests returned inspection {first_id}"
                )
            }

        return {
            "scenario": "Duplicate Retry",
            "status": "FAIL",
            "reason": (
                f"Duplicate created: {first_id} and {second_id}"
            )
        }

    except Exception as error:
        return {
            "scenario": "Duplicate Retry",
            "status": "FAIL",
            "reason": str(error)
        }