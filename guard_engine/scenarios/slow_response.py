import time

import httpx


API_URL = "http://127.0.0.1:8000"


def run_slow_response():

    try:
        start_time = time.perf_counter()

        response = httpx.get(
            f"{API_URL}/test/delay/2",
            timeout=5
        )

        elapsed = time.perf_counter() - start_time

        if (
            response.status_code == 200
            and elapsed >= 2
        ):
            return {
                "scenario": "Slow Response",
                "status": "PASS",
                "reason": f"Response took {elapsed:.2f} seconds"
            }

        return {
            "scenario": "Slow Response",
            "status": "FAIL",
            "reason": f"Unexpected response time: {elapsed:.2f}"
        }

    except Exception as error:
        return {
            "scenario": "Slow Response",
            "status": "FAIL",
            "reason": str(error)
        }