from guard_engine.scenarios.normal_request import (
    run_normal_request,
)

from guard_engine.scenarios.timeout_request import (
    run_timeout_request,
)

from guard_engine.scenarios.http_500 import (
    run_http_500,
)

from guard_engine.scenarios.slow_response import (
    run_slow_response,
)

from guard_engine.scenarios.connection_drop import (
    run_connection_drop,
)

from guard_engine.scenarios.duplicate_retry import (
    run_duplicate_retry,
)

from guard_engine.scenarios.interrupted_upload import (
    run_interrupted_upload,
)

def print_result(result):

    print(f"Scenario: {result['scenario']}")
    print(f"Status:   {result['status']}")

    if "reason" in result:
        print(f"Reason:   {result['reason']}")

    if "inspection_id" in result:
        print(
            f"Inspection ID: "
            f"{result['inspection_id']}"
        )

    print()


def run_tests():

    print("\nFLEXGUARD TEST ENGINE")
    print("=====================\n")

    tests = [
        run_normal_request,
        run_timeout_request,
        run_http_500,
        run_slow_response,
        run_connection_drop,
        run_duplicate_retry,
        run_interrupted_upload,
    ]

    for test in tests:
        result = test()
        print_result(result)


if __name__ == "__main__":
    run_tests()