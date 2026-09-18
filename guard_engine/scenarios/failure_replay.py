import httpx

from guard_engine.replay import ReplayRecorder


API_URL = "http://127.0.0.1:9000"

MAX_RETRIES = 3


def run_failure_replay():

    replay = ReplayRecorder(
        "HTTP 500 Failure"
    )

    replay.record(
        "Request started"
    )

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        replay.record(
            f"Retry attempt {attempt}"
        )

        try:
            response = httpx.get(
                f"{API_URL}/test/error",
                timeout=5
            )

            replay.record(
                f"Server returned HTTP {response.status_code}"
            )

            if response.status_code == 500:

                if attempt < MAX_RETRIES:
                    replay.record(
                        "Retry required"
                    )

                    continue

                replay.record(
                    "Maximum retries reached"
                )

                replay.record(
                    "Final state: FAILED"
                )

                replay.show()

                return {
                    "scenario": "Failure Replay",
                    "status": "PASS",
                    "reason": "Retries and final state recorded"
                }

        except Exception as error:

            replay.record(
                f"Connection error: {error}"
            )

    replay.record(
        "Final state: UNKNOWN"
    )

    replay.show()

    return {
        "scenario": "Failure Replay",
        "status": "FAIL",
        "reason": "Replay did not finish correctly"
    }