import gradio as gr

from guard_engine.runner import run_tests
from guard_engine.risk_engine import (
    get_release_decision,
)


def run_dashboard_tests():
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

    resilience_safe = [
        result
        for result in resilience_results
        if result.get("outcome") == "SAFE"
    ]

    resilience_failures = [
        result
        for result in resilience_results
        if result.get("outcome") == "UNSAFE"
    ]

    detector_passed = [
        result
        for result in detector_results
        if result.get("status") == "PASS"
    ]

    release_decision = get_release_decision(
        summary["results"]
    )

    if resilience_failures:
        failure_text = "\n".join(
            (
                f"{result['scenario']}: "
                f"{result.get('reason', '')}"
            )
            for result in resilience_failures
        )
    else:
        failure_text = (
            "No application resilience "
            "failures detected."
        )

    resilience_table = []

    for result in resilience_results:
        resilience_table.append(
            [
                result["scenario"],
                result["status"],
                result["outcome"],
                result["risk"],
                result.get("reason", ""),
            ]
        )

    detector_table = []

    for result in detector_results:
        detector_table.append(
            [
                result["scenario"],
                result["status"],
                result["outcome"],
                result["risk"],
                result.get("reason", ""),
            ]
        )

    resilience_summary = (
        f"{len(resilience_safe)} / "
        f"{len(resilience_results)} SAFE"
    )

    detector_summary = (
        f"{len(detector_passed)} / "
        f"{len(detector_results)} PASS"
    )

    decision_html = f"""
    <div class="decision-box">

        <div class="decision-label">
            RELEASE DECISION
        </div>

        <div class="decision-value">
            {release_decision}
        </div>

        <div class="decision-note">
            Based on application resilience
            scenarios and critical data invariants.
        </div>

    </div>
    """

    return (
        summary["total"],
        resilience_summary,
        detector_summary,
        summary["failed"],
        f"{summary['score']}%",
        summary["overall_risk"],
        failure_text,
        resilience_table,
        detector_table,
        decision_html,
    )


custom_css = """

.gradio-container {
    max-width: 1400px !important;
    margin: auto !important;
}


/* Header */

#dashboard-header {
    background: #111827;
    border-radius: 18px;
    padding: 32px;
    margin-bottom: 20px;
}

.header-label {
    color: #60a5fa;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
}

.header-title {
    color: white;
    font-size: 38px;
    font-weight: 800;
    margin-top: 4px;
}

.header-subtitle {
    color: #9ca3af;
    margin-top: 5px;
}


/* Run Button */

#run-button {
    min-height: 52px;
    background: #2563eb !important;
    color: white !important;
    border: none !important;
    border-radius: 11px !important;
    font-weight: 700 !important;
}


/* Summary */

.metric-box {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 18px;
}


/* Section Headers */

.section-title {
    margin-top: 28px;
    margin-bottom: 8px;
}

.section-description {
    color: #6b7280;
    font-size: 13px;
}


/* Failure Section */

#critical-box textarea {
    background: #111827 !important;
    color: #fca5a5 !important;
    font-family: Consolas, monospace !important;
}


/* Decision */

.decision-box {
    background: #111827;
    border-radius: 16px;
    padding: 28px;
    text-align: center;
    margin-top: 24px;
}

.decision-label {
    color: #9ca3af;
    font-size: 11px;
    letter-spacing: 2px;
    font-weight: 700;
}

.decision-value {
    color: white;
    font-size: 30px;
    font-weight: 800;
    margin-top: 8px;
}

.decision-note {
    color: #9ca3af;
    font-size: 12px;
    margin-top: 8px;
}


/* Footer */

#footer {
    text-align: center;
    margin-top: 24px;
    color: #9ca3af;
    font-size: 11px;
}

"""


dashboard_theme = gr.themes.Base()


with gr.Blocks(
    title="FlexGuard Dashboard"
) as app:

    gr.HTML(
        """
        <div id="dashboard-header">

            <div class="header-label">
                RELEASE ASSURANCE CONTROL
            </div>

            <div class="header-title">
                FlexGuard
            </div>

            <div class="header-subtitle">
                Failure injection and resilience
                validation for offline field
                applications.
            </div>

        </div>
        """
    )

    run_button = gr.Button(
        "RUN FLEXGUARD TEST SUITE",
        elem_id="run-button",
    )

    with gr.Row():

        total_tests = gr.Textbox(
            label="Total Checks",
            interactive=False,
        )

        resilience_score = gr.Textbox(
            label="Application Resilience",
            interactive=False,
        )

        detector_score = gr.Textbox(
            label="Detector Checks",
            interactive=False,
        )

        failed_tests = gr.Textbox(
            label="Failed Checks",
            interactive=False,
        )

        assurance_score = gr.Textbox(
            label="Test Assurance Score",
            interactive=False,
        )

        overall_risk = gr.Textbox(
            label="Overall Risk",
            interactive=False,
        )

    gr.Markdown(
        """
## Application Resilience

These scenarios verify whether FieldSync
preserves and recovers real inspection data
under failure conditions.
        """
    )

    resilience_table = gr.Dataframe(
        headers=[
            "Scenario",
            "Test Status",
            "System Outcome",
            "Risk",
            "Reason",
        ],
        datatype=[
            "str",
            "str",
            "str",
            "str",
            "str",
        ],
        interactive=False,
    )

    gr.Markdown(
        """
## FlexGuard Detector Checks

These checks verify that FlexGuard can detect
injected faults and data-integrity problems.
A DETECTED result does not mean the application
itself experienced an unresolved production failure.
        """
    )

    detector_table = gr.Dataframe(
        headers=[
            "Scenario",
            "Test Status",
            "Detection Outcome",
            "Risk",
            "Reason",
        ],
        datatype=[
            "str",
            "str",
            "str",
            "str",
            "str",
        ],
        interactive=False,
    )

    gr.Markdown(
        "## Application Resilience Failures"
    )

    resilience_failures = gr.Textbox(
        label="",
        lines=4,
        interactive=False,
        elem_id="critical-box",
    )

    release_decision = gr.HTML()

    run_button.click(
        fn=run_dashboard_tests,
        outputs=[
            total_tests,
            resilience_score,
            detector_score,
            failed_tests,
            assurance_score,
            overall_risk,
            resilience_failures,
            resilience_table,
            detector_table,
            release_decision,
        ],
    )

    gr.HTML(
        """
        <div id="footer">
            FLEXGUARD RELIABILITY LAB
        </div>
        """
    )


if __name__ == "__main__":
    app.launch(
        theme=dashboard_theme,
        css=custom_css,
    )