import gradio as gr

from guard_engine.runner import run_tests


def run_dashboard_tests():
    summary = run_tests()

    critical_failures = [
        result
        for result in summary["results"]
        if (
            result["status"] == "FAIL"
            and result["risk"] == "Critical"
        )
    ]

    if critical_failures:
        release_decision = "BLOCK RELEASE"

    elif summary["score"] < 95:
        release_decision = "REVIEW REQUIRED"

    else:
        release_decision = "RELEASE APPROVED"

    if critical_failures:
        failure_text = "\n".join(
            f"{result['scenario']}: {result.get('reason', '')}"
            for result in critical_failures
        )
    else:
        failure_text = "No critical failures detected."

    table_data = []

    for result in summary["results"]:
        table_data.append(
            [
                result["scenario"],
                result["status"],
                result["risk"],
                result.get("reason", "")
            ]
        )

    decision_html = f"""
    <div class="decision-box">
        <div class="decision-label">
            RELEASE DECISION
        </div>

        <div class="decision-value">
            {release_decision}
        </div>
    </div>
    """

    return (
        summary["total"],
        summary["passed"],
        summary["failed"],
        f"{summary['score']}%",
        summary["overall_risk"],
        failure_text,
        table_data,
        decision_html
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


/* Summary Cards */

.metric-box {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 18px;
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
    margin-top: 18px;
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


/* Footer */

#footer {
    text-align: center;
    margin-top: 24px;
    color: #9ca3af;
    font-size: 11px;
}

"""


with gr.Blocks(
    title="FlexGuard Dashboard",
    theme=gr.themes.Base(),
    css=custom_css
) as app:

    gr.HTML(
        """
        <div id="dashboard-header">

            <div class="header-label">
                RELEASE RELIABILITY CONTROL
            </div>

            <div class="header-title">
                FlexGuard
            </div>

            <div class="header-subtitle">
                Automated reliability testing for
                offline field applications.
            </div>

        </div>
        """
    )

    run_button = gr.Button(
        "RUN FLEXGUARD TEST SUITE",
        elem_id="run-button"
    )

    with gr.Row():

        total_tests = gr.Textbox(
            label="Total Tests",
            interactive=False
        )

        passed_tests = gr.Textbox(
            label="Passed",
            interactive=False
        )

        failed_tests = gr.Textbox(
            label="Failed",
            interactive=False
        )

        reliability_score = gr.Textbox(
            label="Reliability Score",
            interactive=False
        )

        overall_risk = gr.Textbox(
            label="Overall Risk",
            interactive=False
        )

    gr.Markdown("## Critical Failures")

    critical_failures = gr.Textbox(
        label="",
        lines=4,
        interactive=False,
        elem_id="critical-box"
    )

    gr.Markdown("## Test Results")

    results_table = gr.Dataframe(
        headers=[
            "Scenario",
            "Status",
            "Risk",
            "Reason"
        ],
        datatype=[
            "str",
            "str",
            "str",
            "str"
        ],
        interactive=False
    )

    release_decision = gr.HTML()

    run_button.click(
        fn=run_dashboard_tests,
        outputs=[
            total_tests,
            passed_tests,
            failed_tests,
            reliability_score,
            overall_risk,
            critical_failures,
            results_table,
            release_decision
        ]
    )

    gr.HTML(
        """
        <div id="footer">
            FLEXGUARD RELIABILITY LAB
        </div>
        """
    )


if __name__ == "__main__":
    app.launch()