import hashlib
import os
import tempfile
import uuid

import httpx


API_URL = "http://127.0.0.1:9000"


def calculate_checksum(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(4096)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def run_checksum_validation():

    request_key = str(uuid.uuid4())

    data = {
        "idempotency_key": request_key,
        "location": "Checksum Test Site",
        "inspector": "FlexGuard",
        "finding": "Checksum validation test",
        "notes": "Testing file integrity",
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
                "scenario": "Checksum Validation",
                "status": "FAIL",
                "reason": "Could not create inspection"
            }

        inspection_id = create_response.json()["id"]

        with tempfile.NamedTemporaryFile(
            suffix=".jpg",
            delete=False
        ) as temp_file:
            temp_file.write(
                b"FlexGuard checksum test image"
            )

            original_path = temp_file.name

        original_checksum = calculate_checksum(
            original_path
        )

        with open(original_path, "rb") as image_file:
            upload_response = httpx.post(
                f"{API_URL}/inspections/{inspection_id}/evidence",
                files={
                    "file": (
                        "checksum_test.jpg",
                        image_file,
                        "image/jpeg"
                    )
                },
                timeout=10
            )

        os.remove(original_path)

        if upload_response.status_code != 200:
            return {
                "scenario": "Checksum Validation",
                "status": "FAIL",
                "reason": "Could not upload file"
            }

        uploaded_path = upload_response.json()[
            "evidence_path"
        ]

        if not os.path.exists(uploaded_path):
            return {
                "scenario": "Checksum Validation",
                "status": "FAIL",
                "reason": "Uploaded file is missing"
            }

        uploaded_checksum = calculate_checksum(
            uploaded_path
        )

        if original_checksum == uploaded_checksum:
            return {
                "scenario": "Checksum Validation",
                "status": "PASS",
                "reason": "File checksum matches"
            }

        return {
            "scenario": "Checksum Validation",
            "status": "FAIL",
            "reason": "File checksum mismatch"
        }

    except Exception as error:
        return {
            "scenario": "Checksum Validation",
            "status": "FAIL",
            "reason": str(error)
        }