import httpx


API_URL = "http://127.0.0.1:9000"


def run_interrupted_upload():

    try:
        response = httpx.post(
            f"{API_URL}/test/interrupted-upload",
            timeout=5
        )

        if response.status_code == 500:
            return {
                "scenario": "Interrupted Upload",
                "status": "PASS",
                "reason": "Upload interruption detected correctly"
            }

        return {
            "scenario": "Interrupted Upload",
            "status": "FAIL",
            "reason": (
                f"Expected HTTP 500, got "
                f"{response.status_code}"
            )
        }

    except Exception as error:
        return {
            "scenario": "Interrupted Upload",
            "status": "FAIL",
            "reason": str(error)
        }