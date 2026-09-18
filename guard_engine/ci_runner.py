import json
import sys
from pathlib import Path

from guard_engine.runner import run_tests


REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)


def run_ci():
    summary = run_tests()

    critical_unsafe = [
        result
        for result in summary["results"]
        if (
            result.get("outcome") == "UNSAFE"
            and result.get("risk") == "Critical"
        )
    ]

    if critical_unsafe:
        release_decision = "BLOCK RELEASE"
    elif summary["score"] < 95:
        release_decision = "REVIEW REQUIRED"
    else:
        release_decision = "RELEASE APPROVED"

    report = {
        "total_tests": summary["total"],
        "passed": summary["passed"],
        "failed": summary["failed"],
        "assurance_score": summary["score"],
        "overall_risk": summary["overall_risk"],
        "critical_unsafe_outcomes": critical_unsafe,
        "release_decision": release_decision,
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
    print("CI REPORT")
    print("=====================")
    print(
        f"Report: {report_path}"
    )
    print(
        f"Assurance Score: "
        f"{summary['score']}%"
    )
    print(
        f"Critical Unsafe Outcomes: "
        f"{len(critical_unsafe)}"
    )
    print(
        f"Release Decision: "
        f"{release_decision}"
    )

    if critical_unsafe:
        print()
        print("PIPELINE RESULT: FAIL")
        sys.exit(1)

    print()
    print("PIPELINE RESULT: PASS")
    sys.exit(0)


if __name__ == "__main__":
    run_ci()