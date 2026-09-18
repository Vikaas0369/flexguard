import httpx


API_URL = "http://127.0.0.1:8000"


def run_http_500():

    try:
        response = httpx.get(
            f"{API_URL}/test/error",
            timeout=5
        )

        if response.status_code == 500:
            return {
                "scenario": "HTTP 500",
                "status": "PASS",
                "reason": "Server error detected correctly"
            }

        return {
            "scenario": "HTTP 500",
            "status": "FAIL",
            "reason": f"Expected 500, got {response.status_code}"
        }

    except Exception as error:
        return {
            "scenario": "HTTP 500",
            "status": "FAIL",
            "reason": str(error)
        }