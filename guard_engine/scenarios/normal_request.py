import uuid

import httpx


API_URL = "http://127.0.0.1:9000"


def run_normal_request():
    request_key = str(uuid.uuid4())

    data = {
        "idempotency_key": request_key,
        "location": "FlexGuard Test Site",
        "inspector": "FlexGuard",
        "finding": "Normal request test",
        "notes": "Generated automatically by FlexGuard",
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
                "scenario": "Normal Request",
                "status": "FAIL",
                "reason": (
                    f"Create returned HTTP "
                    f"{create_response.status_code}"
                )
            }

        inspection = create_response.json()

        inspection_id = inspection["id"]

        get_response = httpx.get(
            f"{API_URL}/inspections/{inspection_id}",
            timeout=10
        )

        if get_response.status_code != 200:
            return {
                "scenario": "Normal Request",
                "status": "FAIL",
                "reason": "Created inspection could not be retrieved"
            }

        saved_inspection = get_response.json()

        if saved_inspection["idempotency_key"] != request_key:
            return {
                "scenario": "Normal Request",
                "status": "FAIL",
                "reason": "Idempotency key does not match"
            }

        return {
            "scenario": "Normal Request",
            "status": "PASS",
            "inspection_id": inspection_id,
            "idempotency_key": request_key
        }

    except Exception as error:
        return {
            "scenario": "Normal Request",
            "status": "FAIL",
            "reason": str(error)
        }