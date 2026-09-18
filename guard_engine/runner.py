from guard_engine.risk_engine import (
    calculate_reliability_score,
    get_overall_risk,
    get_risk_level,
)

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
from guard_engine.scenarios.missing_record import (
    run_missing_record,
)
from guard_engine.scenarios.duplicate_record import (
    run_duplicate_record,
)
from guard_engine.scenarios.changed_data import (
    run_changed_data,
)
from guard_engine.scenarios.missing_attachment import (
    run_missing_attachment,
)
from guard_engine.scenarios.checksum_validation import (
    run_checksum_validation,
)
from guard_engine.scenarios.failure_replay import (
    run_failure_replay,
)


def run_tests():

    print()
    print("FLEXGUARD TEST ENGINE")
    print("=====================")
    print()

    tests = [
        run_normal_request,
        run_timeout_request,
        run_http_500,
        run_slow_response,
        run_connection_drop,
        run_duplicate_retry,
        run_interrupted_upload,
        run_missing_record,
        run_duplicate_record,
        run_changed_data,
        run_missing_attachment,
        run_checksum_validation,
        run_failure_replay,
    ]

    results = []

    for test in tests:
        result = test()

        risk = get_risk_level(
            result["scenario"]
        )

        result["risk"] = risk

        results.append(result)

        print(
            f"Scenario: {result['scenario']}"
        )

        print(
            f"Status:   {result['status']}"
        )

        print(
            f"Risk:     {risk}"
        )

        if "reason" in result:
            print(
                f"Reason:   {result['reason']}"
            )

        if "inspection_id" in result:
            print(
                f"Inspection ID: "
                f"{result['inspection_id']}"
            )

        print()

    score = calculate_reliability_score(
        results
    )

    overall_risk = get_overall_risk(
    score
)

    print("=====================")
    print("FLEXGUARD SUMMARY")
    print("=====================")

    print(
        f"Total Tests:        {len(results)}"
    )

    passed = sum(
        1
        for result in results
        if result["status"] == "PASS"
    )

    failed = len(results) - passed

    print(
        f"Passed:             {passed}"
    )

    print(
        f"Failed:             {failed}"
    )

    print(
        f"Reliability Score:  {score}%"
    )

    print(
        f"Overall Risk:       {overall_risk}"
    )

    print()

    return {
        "results": results,
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "score": score,
        "overall_risk": overall_risk,
    }


if __name__ == "__main__":
    run_tests()