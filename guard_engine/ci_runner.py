import json
import sys
from pathlib import Path

from guard_engine.runner import run_tests
from guard_engine.risk_engine import (
    get_release_decision,
)


REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)


def run_ci():
    summary = run_tests()

    resilience_results = [
        result
        for result in summary["results"]
        if result.get("type") == "RESILIENCE"
    ]

    detector_results = [
        result
        for result in summary["results"]
        if result.get("type") == "DETECTOR"
    ]

    unsafe_resilience = [
        result
        for result in resilience_results
        if result.get("outcome") != "SAFE"
    ]

    detector_failures = [
        result
        for result in detector_results
        if result.get("status") != "PASS"
    ]

    release_decision = get_release_decision(
        summary["results"]
    )

    report = {
        "total_checks": summary["total"],
        "passed_checks": summary["passed"],
        "failed_checks": summary["failed"],

        "application_resilience": {
            "total": len(resilience_results),
            "safe": (
                len(resilience_results)
                - len(unsafe_resilience)
            ),
            "unsafe": len(unsafe_resilience),
            "results": resilience_results,
        },

        "detector_checks": {
            "total": len(detector_results),
            "passed": (
                len(detector_results)
                - len(detector_failures)
            ),
            "failed": len(detector_failures),
            "results": detector_results,
        },

        "test_assurance_score": (
            summary["score"]
        ),

        "overall_risk": (
            summary["overall_risk"]
        ),

        "release_decision": (
            release_decision
        ),

        "results": summary["results"],
    }

    report_path = (
        REPORT_DIR
        / "flexguard_report.json"
    )

    with open(
        report_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=4,
        )

    print()
    print("FLEXGUARD CI REPORT")
    print("========================")

    print(
        f"Report: {report_path}"
    )

    print(
        "Application Resilience: "
        f"{len(resilience_results) - len(unsafe_resilience)}"
        f"/{len(resilience_results)} SAFE"
    )

    print(
        "Detector Checks: "
        f"{len(detector_results) - len(detector_failures)}"
        f"/{len(detector_results)} PASS"
    )

    print(
        f"Test Assurance Score: "
        f"{summary['score']}%"
    )

    print(
        f"Overall Risk: "
        f"{summary['overall_risk']}"
    )

    print(
        f"Release Decision: "
        f"{release_decision}"
    )

    # Application resilience controls
    # whether the release is approved.
    if release_decision != "RELEASE APPROVED":
        print()
        print(
            "PIPELINE RESULT: FAIL"
        )
        print(
            "Reason: Application resilience "
            "requirements were not satisfied."
        )
        sys.exit(1)

    # Detector failures mean the FlexGuard
    # test harness itself is not healthy.
    if detector_failures:
        print()
        print(
            "PIPELINE RESULT: FAIL"
        )
        print(
            "Reason: One or more FlexGuard "
            "detector checks failed."
        )
        sys.exit(1)

    print()
    print(
        "PIPELINE RESULT: PASS"
    )

    sys.exit(0)


if __name__ == "__main__":
    run_ci()