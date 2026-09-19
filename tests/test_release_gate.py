from guard_engine.risk_engine import get_release_decision


def test_clean_results_approve_release():
    results = [
        {
            "scenario": "Normal Request",
            "status": "PASS",
            "outcome": "SAFE",
            "risk": "Critical",
        }
    ]

    decision = get_release_decision(
        results,
        100.0,
    )

    assert decision == "RELEASE APPROVED"


def test_critical_unsafe_blocks_release():
    results = [
        {
            "scenario": "Offline Recovery",
            "status": "FAIL",
            "outcome": "UNSAFE",
            "risk": "Critical",
        }
    ]

    decision = get_release_decision(
        results,
        80.0,
    )

    assert decision == "BLOCK RELEASE"