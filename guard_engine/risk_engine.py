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
    "Offline Recovery": "Critical",
    "Lost Acknowledgement": "Critical",
    "Evidence Upload Recovery": "Critical",
    "Missing Record": "Critical",
    "Duplicate Record": "High",
    "Changed Data": "Critical",
    "Missing Attachment": "High",
    "Checksum Validation": "Critical",
    "Failure Replay": "Low",
}


SCENARIO_TYPE = {
    "Normal Request": "RESILIENCE",
    "Offline Recovery": "RESILIENCE",
    "Lost Acknowledgement": "RESILIENCE",
    "Evidence Upload Recovery": "RESILIENCE",

    "Timeout": "DETECTOR",
    "HTTP 500": "DETECTOR",
    "Slow Response": "DETECTOR",
    "Missing Record": "DETECTOR",
    "Duplicate Record": "DETECTOR",
    "Changed Data": "DETECTOR",
    "Missing Attachment": "DETECTOR",
    "Checksum Validation": "DETECTOR",
    "Failure Replay": "DETECTOR",
}


SAFE_SCENARIOS = {
    "Normal Request",
    "Offline Recovery",
    "Lost Acknowledgement",
    "Evidence Upload Recovery",
}


def get_risk_level(scenario_name):
    return SCENARIO_RISK.get(
        scenario_name,
        "Medium",
    )


def get_scenario_type(scenario_name):
    return SCENARIO_TYPE.get(
        scenario_name,
        "DETECTOR",
    )


def get_system_outcome(
    scenario_name,
    test_status,
):
    if test_status != "PASS":
        return "UNSAFE"

    scenario_type = get_scenario_type(
        scenario_name
    )

    if scenario_type == "RESILIENCE":
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

        if (
            result.get("outcome")
            == "UNSAFE"
        ):
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


def get_resilience_results(results):
    return [
        result
        for result in results
        if (
            get_scenario_type(
                result["scenario"]
            )
            == "RESILIENCE"
        )
    ]


def get_release_decision(
    results,
    score=None,
):
    resilience_results = (
        get_resilience_results(
            results
        )
    )

    if not resilience_results:
        return "REVIEW REQUIRED"

    unsafe_resilience = [
        result
        for result
        in resilience_results
        if (
            result.get("outcome")
            != "SAFE"
        )
    ]

    if unsafe_resilience:
        return "BLOCK RELEASE"

    return "RELEASE APPROVED"