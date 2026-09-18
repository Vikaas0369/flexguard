import json
import sys
from pathlib import Path

from guard_engine.runner import run_tests


REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)


def run_ci():

    summary = run_tests()

    critical_failures = [
        result
        for result in summary["results"]
        if (
            result["status"] == "FAIL"
            and result["risk"] == "Critical"
        )
    ]

    report = {
        "total_tests": summary["total"],
        "passed": summary["passed"],
        "failed": summary["failed"],
        "reliability_score": summary["score"],
        "overall_risk": summary["overall_risk"],
        "critical_failures": critical_failures,
        "results": summary["results"],
    }

    report_path = (
        REPORT_DIR
        / "flexguard_report.json"
    )

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=4
        )

    print()
    print("CI REPORT")
    print("=====================")
    print(
        f"Report: {report_path}"
    )
    print(
        f"Reliability: {summary['score']}%"
    )
    print(
        f"Critical Failures: "
        f"{len(critical_failures)}"
    )

    if critical_failures:
        print()
        print("PIPELINE RESULT: FAIL")
        sys.exit(1)

    print()
    print("PIPELINE RESULT: PASS")
    sys.exit(0)


if __name__ == "__main__":
    run_ci()