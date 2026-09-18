from uuid import uuid4

import httpx


API_URL = "http://127.0.0.1:9000"


def run_normal_request():
    idempotency_key = str(uuid4())

    payload = {
        "location": "FlexGuard Test Site",
        "inspector": "FlexGuard",
        "finding": "Normal request validation",
        "notes": "Standard request used for reliability validation",
        "risk_level": "Low",
        "idempotency_key": idempotency_key,
    }

    try:
        with httpx.Client(timeout=10.0) as client:

            create_response = client.post(
                f"{API_URL}/inspections",
                json=payload,
            )

            if create_response.status_code != 200:
                return {
                    "scenario": "Normal Request",
                    "status": "FAIL",
                    "reason": (
                        f"Create request returned HTTP "
                        f"{create_response.status_code}"
                    ),
                }

            created_inspection = create_response.json()

            inspection_id = created_inspection["id"]

            get_response = client.get(
                f"{API_URL}/inspections/{inspection_id}"
            )

            if get_response.status_code != 200:
                return {
                    "scenario": "Normal Request",
                    "status": "FAIL",
                    "reason": (
                        f"Inspection could not be retrieved. "
                        f"HTTP {get_response.status_code}"
                    ),
                    "inspection_id": inspection_id,
                }

            stored_inspection = get_response.json()

            if (
                stored_inspection.get("idempotency_key")
                != idempotency_key
            ):
                return {
                    "scenario": "Normal Request",
                    "status": "FAIL",
                    "reason": (
                        "Stored idempotency key does not "
                        "match the original request"
                    ),
                    "inspection_id": inspection_id,
                }

            return {
                "scenario": "Normal Request",
                "status": "PASS",
                "reason": (
                    "Inspection created and retrieved successfully"
                ),
                "inspection_id": inspection_id,
            }

    except Exception as error:
        return {
            "scenario": "Normal Request",
            "status": "FAIL",
            "reason": str(error),
        }