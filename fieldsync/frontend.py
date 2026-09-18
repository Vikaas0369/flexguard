from pathlib import Path
import mimetypes
from uuid import uuid4

import gradio as gr
import httpx

from fieldsync.offline_queue import add_to_queue



API_URL = "http://127.0.0.1:8000"


def check_api_status():
    try:
        response = httpx.get(
            f"{API_URL}/health",
            timeout=3
        )

        if response.status_code == 200:
            return """
            <div class="system-status online">
                <span class="status-light"></span>
                API CONNECTED
            </div>
            """

    except Exception:
        pass

    return """
    <div class="system-status offline">
        <span class="status-light"></span>
        API OFFLINE
    </div>
    """


def create_inspection(
    location,
    inspector,
    finding,
    notes,
    risk_level,
    evidence_file
):

    if not location:
        return (
            "LOCATION REQUIRED",
            "Waiting",
            "-",
            None,
            "NOT READY"
        )

    if not inspector:
        return (
            "INSPECTOR REQUIRED",
            "Waiting",
            "-",
            None,
            "NOT READY"
        )

    if not finding:
        return (
            "FINDING REQUIRED",
            "Waiting",
            "-",
            None,
            "NOT READY"
        )

    if not risk_level:
        return (
            "RISK LEVEL REQUIRED",
            "Waiting",
            "-",
            None,
            "NOT READY"
        )

    request_key = str(uuid4())

    data = {
        "idempotency_key": request_key,
        "location": location,
        "inspector": inspector,
        "finding": finding,
        "notes": notes,
        "risk_level": risk_level,
    }

    try:
        response = httpx.post(
            f"{API_URL}/inspections",
            json=data,
            timeout=10
        )

        if response.status_code != 200:
            return (
                f"INSPECTION CREATION FAILED\n\n{response.text}",
                "Failed",
                "-",
                None,
                "NOT READY"
            )

        inspection = response.json()

        inspection_id = inspection["id"]

        inspection_code = (
            f"INS-{inspection_id:04d}"
        )

        evidence_status = "No evidence attached"

        if evidence_file:
            file_path = Path(evidence_file)

            mime_type, _ = mimetypes.guess_type(
                file_path.name
            )

            if mime_type is None:
                mime_type = "application/octet-stream"

            with open(file_path, "rb") as image_file:
                files = {
                    "file": (
                        file_path.name,
                        image_file,
                        mime_type
                    )
                }

                upload_response = httpx.post(
                    (
                        f"{API_URL}/inspections/"
                        f"{inspection_id}/evidence"
                    ),
                    files=files,
                    timeout=20
                )

            if upload_response.status_code == 200:
                evidence_status = "Evidence uploaded"

            else:
                evidence_status = "Evidence upload failed"

        message = (
            "INSPECTION CREATED\n\n"
            f"Reference      {inspection_code}\n"
            f"Location       {inspection['location']}\n"
            f"Inspector      {inspection['inspector']}\n"
            f"Risk           {inspection['risk_level']}\n"
            f"Status         {inspection['status'].upper()}\n"
            f"Evidence       {evidence_status}"
        )

        return (
            message,
            inspection["status"].upper(),
            inspection_code,
            inspection_id,
            "NOT READY"
        )

    except Exception:
        queue_id = add_to_queue(
            location=location,
            inspector=inspector,
            finding=finding,
            notes=notes,
            risk_level=risk_level,
            evidence_path=evidence_file,
            idempotency_key=request_key
        )

        return (
            (
                "SAVED LOCALLY\n\n"
                f"Local Reference  LOCAL-{queue_id:04d}\n"
                f"Location         {location}\n"
                f"Inspector        {inspector}\n"
                f"Risk             {risk_level}\n"
                "Status           PENDING\n\n"
                "Backend unavailable.\n"
                "Inspection is waiting for synchronisation."
            ),
            "PENDING",
            f"LOCAL-{queue_id:04d}",
            None,
            "PENDING"
        )


def submit_inspection(inspection_id):

    if inspection_id is None:
        return (
            "CREATE AN INSPECTION FIRST",
            "Waiting",
            "NOT READY"
        )

    try:
        response = httpx.post(
            (
                f"{API_URL}/inspections/"
                f"{inspection_id}/submit"
            ),
            timeout=10
        )

        if response.status_code == 200:
            return (
                (
                    "INSPECTION SUBMITTED\n\n"
                    f"Reference      INS-{inspection_id:04d}\n"
                    "Status         SUBMITTED\n"
                    "Sync           PENDING SYNC"
                ),
                "SUBMITTED",
                "PENDING SYNC"
            )

        return (
            f"SUBMISSION FAILED\n\n{response.text}",
            "Failed",
            "NOT READY"
        )

    except Exception as error:
        return (
            f"API CONNECTION FAILED\n\n{error}",
            "Offline",
            "NOT READY"
        )


custom_css = """

body {
    background: #f4f6f8;
}

.gradio-container {
    max-width: 1320px !important;
    margin: auto !important;
    padding-top: 24px !important;
}


/* HEADER */

#topbar {
    background: #111827;
    border-radius: 18px;
    padding: 30px 34px;
    margin-bottom: 18px;
    position: relative;
    overflow: hidden;
}

#topbar::after {
    content: "";
    position: absolute;
    width: 300px;
    height: 300px;
    right: -80px;
    top: -170px;
    background: #2563eb;
    opacity: 0.15;
    border-radius: 50%;
}

.brand-small {
    color: #60a5fa;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
}

.brand-title {
    color: white;
    font-size: 40px;
    font-weight: 800;
    margin-top: 5px;
    margin-bottom: 4px;
}

.brand-description {
    color: #9ca3af;
    font-size: 14px;
}


/* API STATUS */

.system-status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-top: 5px;
    margin-bottom: 18px;
    border-radius: 30px;
    padding: 7px 13px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
}

.system-status.online {
    color: #15803d;
    background: #dcfce7;
    border: 1px solid #bbf7d0;
}

.system-status.offline {
    color: #b91c1c;
    background: #fee2e2;
    border: 1px solid #fecaca;
}

.status-light {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
}


/* MAIN PANELS */

.panel {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 26px;
    box-shadow: 0 5px 18px rgba(15, 23, 42, 0.04);
}

.panel-number {
    color: #2563eb;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.5px;
}

.panel-title {
    color: #111827;
    font-size: 23px;
    font-weight: 750;
    margin-top: 5px;
}

.panel-description {
    color: #6b7280;
    font-size: 13px;
    margin-bottom: 16px;
}


/* BUTTONS */

#create-button {
    min-height: 50px;
    margin-top: 12px;
    border-radius: 11px !important;
    border: none !important;
    background: #2563eb !important;
    color: white !important;
    font-size: 14px !important;
    font-weight: 750 !important;
}

#create-button:hover {
    background: #1d4ed8 !important;
}

#submit-button {
    min-height: 50px;
    margin-top: 10px;
    border-radius: 11px !important;
    border: 1px solid #111827 !important;
    background: #111827 !important;
    color: white !important;
    font-size: 14px !important;
    font-weight: 750 !important;
}

#submit-button:hover {
    background: #1f2937 !important;
}


/* RESULT */

#activity-output textarea {
    background: #111827 !important;
    color: #d1fae5 !important;
    border-radius: 12px !important;

    font-family:
        Consolas,
        Monaco,
        monospace !important;

    font-size: 13px !important;
    line-height: 1.9 !important;
    padding: 18px !important;
}


/* FLOW */

.flow-box {
    padding: 15px;
    border-radius: 12px;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    margin-top: 14px;
}

.flow-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 7px 2px;
    font-size: 13px;
    color: #4b5563;
}

.flow-number {
    width: 23px;
    height: 23px;
    border-radius: 7px;
    background: #e5e7eb;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: 800;
    color: #374151;
}


/* FOOTER */

#footer {
    text-align: center;
    font-size: 11px;
    color: #9ca3af;
    margin-top: 22px;
    padding-bottom: 15px;
    letter-spacing: 0.5px;
}

"""


with gr.Blocks(
    title="FieldSync",
    theme=gr.themes.Base(),
    css=custom_css
) as app:

    current_inspection_id = gr.State(
        value=None
    )

    gr.HTML(
        """
        <div id="topbar">

            <div class="brand-small">
                FIELD OPERATIONS CONTROL
            </div>

            <div class="brand-title">
                FieldSync
            </div>

            <div class="brand-description">
                Capture field inspections.
                Protect operational data.
                Prepare records for reliable synchronisation.
            </div>

        </div>
        """
    )

    api_status = gr.HTML()

    with gr.Row():

        inspection_status = gr.Textbox(
            value="Waiting",
            label="Inspection Status",
            interactive=False
        )

        inspection_reference = gr.Textbox(
            value="-",
            label="Inspection Reference",
            interactive=False
        )

        sync_status = gr.Textbox(
            value="NOT READY",
            label="Sync Status",
            interactive=False
        )

    with gr.Row(equal_height=False):

        with gr.Column(scale=3):

            with gr.Group(elem_classes="panel"):

                gr.HTML(
                    """
                    <div class="panel-number">
                        01 / INSPECTION CAPTURE
                    </div>

                    <div class="panel-title">
                        Record field observation
                    </div>

                    <div class="panel-description">
                        Create a safety inspection record
                        and attach supporting evidence.
                    </div>
                    """
                )

                location = gr.Textbox(
                    label="Site Location",
                    placeholder="Galway Site C"
                )

                inspector = gr.Textbox(
                    label="Inspector",
                    placeholder="Inspector name"
                )

                finding = gr.Textbox(
                    label="Safety Finding",
                    placeholder=(
                        "Describe the issue observed "
                        "during inspection"
                    ),
                    lines=4
                )

                notes = gr.Textbox(
                    label="Additional Notes",
                    placeholder=(
                        "Add actions taken, people informed, "
                        "or other useful information"
                    ),
                    lines=3
                )

                evidence_file = gr.File(
                    label="Photo Evidence",
                    file_types=["image"],
                    type="filepath"
                )

                risk_level = gr.Radio(
                    choices=[
                        "Low",
                        "Medium",
                        "High",
                        "Critical"
                    ],
                    value="Medium",
                    label="Risk Classification"
                )

                create_button = gr.Button(
                    "CREATE INSPECTION",
                    elem_id="create-button"
                )

                submit_button = gr.Button(
                    "SUBMIT INSPECTION",
                    elem_id="submit-button"
                )

        with gr.Column(scale=2):

            with gr.Group(elem_classes="panel"):

                gr.HTML(
                    """
                    <div class="panel-number">
                        02 / ACTIVITY
                    </div>

                    <div class="panel-title">
                        Record status
                    </div>

                    <div class="panel-description">
                        Current inspection activity
                        appears below.
                    </div>
                    """
                )

                result = gr.Textbox(
                    value=(
                        "WAITING FOR INSPECTION\n\n"
                        "No field record has been created."
                    ),
                    label="",
                    lines=13,
                    interactive=False,
                    elem_id="activity-output"
                )

                gr.HTML(
                    """
                    <div class="flow-box">

                        <div class="flow-row">
                            <div class="flow-number">1</div>
                            Capture inspection
                        </div>

                        <div class="flow-row">
                            <div class="flow-number">2</div>
                            Store field record
                        </div>

                        <div class="flow-row">
                            <div class="flow-number">3</div>
                            Attach evidence
                        </div>

                        <div class="flow-row">
                            <div class="flow-number">4</div>
                            Submit inspection
                        </div>

                        <div class="flow-row">
                            <div class="flow-number">5</div>
                            Synchronise record
                        </div>

                    </div>
                    """
                )

    create_button.click(
        fn=create_inspection,
        inputs=[
            location,
            inspector,
            finding,
            notes,
            risk_level,
            evidence_file
        ],
        outputs=[
            result,
            inspection_status,
            inspection_reference,
            current_inspection_id,
            sync_status
        ]
    )

    submit_button.click(
        fn=submit_inspection,
        inputs=[
            current_inspection_id
        ],
        outputs=[
            result,
            inspection_status,
            sync_status
        ]
    )

    app.load(
        fn=check_api_status,
        outputs=api_status
    )

    gr.HTML(
        """
        <div id="footer">
            FIELDSYNC / FLEXGUARD RELIABILITY LAB
        </div>
        """
    )


if __name__ == "__main__":
    app.launch()