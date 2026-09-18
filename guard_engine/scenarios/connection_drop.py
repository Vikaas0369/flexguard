import httpx


def run_connection_drop():

    try:
        httpx.get(
            "http://127.0.0.1:9999",
            timeout=3
        )

        return {
            "scenario": "Connection Drop",
            "status": "FAIL",
            "reason": "Connection unexpectedly succeeded"
        }

    except httpx.ConnectError:
        return {
            "scenario": "Connection Drop",
            "status": "PASS",
            "reason": "Connection failure detected correctly"
        }

    except Exception as error:
        return {
            "scenario": "Connection Drop",
            "status": "FAIL",
            "reason": str(error)
        }