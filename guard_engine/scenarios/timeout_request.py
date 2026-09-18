import httpx


API_URL = "http://127.0.0.1:8000"


def run_timeout_request():

    try:
        httpx.get(
            f"{API_URL}/test/delay/3",
            timeout=1
        )

        return {
            "scenario": "Timeout",
            "status": "FAIL",
            "reason": "Request did not time out"
        }

    except httpx.TimeoutException:

        return {
            "scenario": "Timeout",
            "status": "PASS",
            "reason": "Timeout detected correctly"
        }

    except Exception as error:

        return {
            "scenario": "Timeout",
            "status": "FAIL",
            "reason": str(error)
        }