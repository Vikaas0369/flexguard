RISK_WEIGHTS = {
    "Low": 1,
    "Medium": 3,
    "High": 7,
    "Critical": 10,
}


SCENARIO_RISK = {
    "Normal Request": "Critical",
    "Timeout": "Medium",
    "HTTP 500": "Medium",
    "Slow Response": "Low",
    "Connection Drop": "High",
    "Duplicate Retry": "High",
    "Interrupted Upload": "High",
    "Missing Record": "Critical",
    "Duplicate Record": "High",
    "Changed Data": "Critical",
    "Missing Attachment": "High",
    "Checksum Validation": "Critical",
    "Failure Replay": "Low",
}


SAFE_SCENARIOS = {
    "Normal Request",
    "Duplicate Retry",
    "Checksum Validation",
}


def get_risk_level(scenario_name):
    return SCENARIO_RISK.get(
        scenario_name,
        "Medium",
    )


def get_system_outcome(
    scenario_name,
    test_status,
):
    if test_status != "PASS":
        return "UNSAFE"

    if scenario_name in SAFE_SCENARIOS:
        return "SAFE"

    return "DETECTED"


def calculate_reliability_score(results):
    total_weight = 0
    unsafe_weight = 0

    for result in results:
        risk = get_risk_level(
            result["scenario"]
        )

        weight = RISK_WEIGHTS[risk]

        total_weight += weight

        if result.get("outcome") == "UNSAFE":
            unsafe_weight += weight

    if total_weight == 0:
        return 100.0

    score = (
        1
        - (
            unsafe_weight
            / total_weight
        )
    ) * 100

    return round(
        score,
        1,
    )


def get_overall_risk(score):
    if score >= 95:
        return "Low"

    if score >= 85:
        return "Medium"

    if score >= 70:
        return "High"

    return "Critical"

def get_release_decision(results, score):
    critical_unsafe = [
        result
        for result in results
        if (
            result.get("outcome") == "UNSAFE"
            and result.get("risk") == "Critical"
        )
    ]

    if critical_unsafe:
        return "BLOCK RELEASE"

    if score < 95:
        return "REVIEW REQUIRED"

    return "RELEASE APPROVED"