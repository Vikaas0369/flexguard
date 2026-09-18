import os
import tempfile
import uuid

import httpx


API_URL = "http://127.0.0.1:9000"


def run_missing_attachment():

    request_key = str(uuid.uuid4())

    data = {
        "idempotency_key": request_key,
        "location": "Attachment Test Site",
        "inspector": "FlexGuard",
        "finding": "Missing attachment test",
        "notes": "Testing evidence integrity",
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
                "scenario": "Missing Attachment",
                "status": "FAIL",
                "reason": "Could not create inspection"
            }

        inspection_id = create_response.json()["id"]

        with tempfile.NamedTemporaryFile(
            suffix=".jpg",
            delete=False
        ) as temp_file:
            temp_file.write(b"FlexGuard test image")
            temp_path = temp_file.name

        with open(temp_path, "rb") as image_file:
            upload_response = httpx.post(
                f"{API_URL}/inspections/{inspection_id}/evidence",
                files={
                    "file": (
                        "test.jpg",
                        image_file,
                        "image/jpeg"
                    )
                },
                timeout=10
            )

        os.remove(temp_path)

        if upload_response.status_code != 200:
            return {
                "scenario": "Missing Attachment",
                "status": "FAIL",
                "reason": "Could not upload attachment"
            }

        evidence_path = upload_response.json()["evidence_path"]

        if os.path.exists(evidence_path):
            os.remove(evidence_path)

        check_response = httpx.get(
            f"{API_URL}/inspections/{inspection_id}",
            timeout=10
        )

        inspection = check_response.json()

        stored_path = inspection["evidence_path"]

        if stored_path and not os.path.exists(stored_path):
            return {
                "scenario": "Missing Attachment",
                "status": "PASS",
                "reason": "Missing attachment detected correctly"
            }

        return {
            "scenario": "Missing Attachment",
            "status": "FAIL",
            "reason": "Missing attachment was not detected"
        }

    except Exception as error:
        return {
            "scenario": "Missing Attachment",
            "status": "FAIL",
            "reason": str(error)
        }