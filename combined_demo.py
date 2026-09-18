import threading
import time

import gradio as gr
import uvicorn

try:
    import spaces

    @spaces.GPU(duration=1)
    def _zerogpu_probe():
        return None

except ImportError:
    pass

from fieldsync.main import app as fieldsync_api
from fieldsync.frontend import app as fieldsync_ui
from guard_engine.chaos.proxy import app as proxy_api
from guard_engine.dashboard import app as flexguard_ui


# ============================================================
# BACKEND SERVICES
# ============================================================

def start_server(application, port):
    uvicorn.run(
        application,
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )


def start_services():
    backend_thread = threading.Thread(
        target=start_server,
        args=(fieldsync_api, 8000),
        daemon=True,
    )

    proxy_thread = threading.Thread(
        target=start_server,
        args=(proxy_api, 9000),
        daemon=True,
    )

    backend_thread.start()
    proxy_thread.start()

    time.sleep(2)


# ============================================================
# THEME
# ============================================================

theme = gr.themes.Base(
    primary_hue="blue",
    neutral_hue="slate",
    radius_size="lg",
    spacing_size="md",
)


# ============================================================
# CUSTOM CSS
# ============================================================

CUSTOM_CSS = """
/* ------------------------------------------------------------
   GLOBAL
------------------------------------------------------------- */

:root {
    --lab-bg: #070b14;
    --lab-bg-secondary: #0b1120;
    --lab-card: rgba(15, 23, 42, 0.78);
    --lab-card-hover: rgba(20, 30, 52, 0.92);

    --lab-border: rgba(148, 163, 184, 0.14);
    --lab-border-bright: rgba(96, 165, 250, 0.32);

    --lab-text: #f8fafc;
    --lab-muted: #94a3b8;

    --lab-blue: #3b82f6;
    --lab-cyan: #22d3ee;
    --lab-purple: #8b5cf6;
    --lab-green: #34d399;

    --lab-radius: 18px;
}


html,
body {
    background: var(--lab-bg) !important;
}


.gradio-container {
    max-width: none !important;
    min-height: 100vh !important;
    background:
        radial-gradient(
            circle at 15% 0%,
            rgba(59, 130, 246, 0.12),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 5%,
            rgba(139, 92, 246, 0.10),
            transparent 28%
        ),
        linear-gradient(
            180deg,
            #070b14 0%,
            #090e19 45%,
            #070b14 100%
        ) !important;

    color: var(--lab-text);
}


/* ------------------------------------------------------------
   MAIN SHELL
------------------------------------------------------------- */

#lab-shell {
    width: min(1500px, calc(100% - 48px));
    margin: 0 auto;
    padding: 30px 0 50px 0;
}


/* ------------------------------------------------------------
   HERO
------------------------------------------------------------- */

#lab-header {
    position: relative;
    overflow: hidden;

    border: 1px solid var(--lab-border);
    border-radius: 24px;

    background:
        linear-gradient(
            120deg,
            rgba(15, 23, 42, 0.96),
            rgba(15, 23, 42, 0.78)
        );

    box-shadow:
        0 30px 70px rgba(0, 0, 0, 0.28),
        inset 0 1px 0 rgba(255, 255, 255, 0.025);

    margin-bottom: 22px;
}


/* glow behind header */

#lab-header::before {
    content: "";
    position: absolute;
    width: 350px;
    height: 350px;

    top: -200px;
    right: -60px;

    background: var(--lab-blue);
    filter: blur(120px);
    opacity: 0.16;

    pointer-events: none;
}


.lab-header-inner {
    position: relative;
    z-index: 2;

    display: flex;
    align-items: center;
    justify-content: space-between;

    gap: 30px;

    padding: 30px 34px;
}


/* ------------------------------------------------------------
   BRAND
------------------------------------------------------------- */

.lab-brand {
    display: flex;
    align-items: center;
    gap: 18px;
}


.lab-logo {
    width: 54px;
    height: 54px;

    display: flex;
    align-items: center;
    justify-content: center;

    flex-shrink: 0;

    border-radius: 16px;

    background:
        linear-gradient(
            135deg,
            rgba(59, 130, 246, 0.22),
            rgba(139, 92, 246, 0.20)
        );

    border: 1px solid rgba(96, 165, 250, 0.25);

    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.08),
        0 12px 35px rgba(59, 130, 246, 0.12);
}


.lab-logo-mark {
    font-size: 24px;
    font-weight: 800;

    background:
        linear-gradient(
            135deg,
            #60a5fa,
            #22d3ee,
            #a78bfa
        );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}


.lab-eyebrow {
    margin-bottom: 4px;

    font-size: 11px;
    font-weight: 700;

    text-transform: uppercase;
    letter-spacing: 0.16em;

    color: #60a5fa;
}


.lab-title {
    margin: 0;

    font-size: clamp(25px, 3vw, 34px);
    line-height: 1.12;

    font-weight: 720;
    letter-spacing: -0.035em;

    color: #f8fafc;
}


.lab-description {
    margin-top: 7px;

    color: var(--lab-muted);

    font-size: 14px;
    line-height: 1.5;
}


/* ------------------------------------------------------------
   HEADER BADGES
------------------------------------------------------------- */

.lab-meta {
    display: flex;
    align-items: center;

    flex-wrap: wrap;
    justify-content: flex-end;

    gap: 9px;
}


.lab-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;

    padding: 8px 12px;

    border-radius: 999px;

    background: rgba(15, 23, 42, 0.65);

    border: 1px solid rgba(148, 163, 184, 0.15);

    color: #cbd5e1;

    font-size: 12px;
    font-weight: 600;

    white-space: nowrap;
}


.lab-status-dot {
    width: 7px;
    height: 7px;

    border-radius: 50%;

    background: var(--lab-green);

    box-shadow:
        0 0 0 3px rgba(52, 211, 153, 0.08),
        0 0 12px rgba(52, 211, 153, 0.45);
}


.lab-port-dot {
    width: 6px;
    height: 6px;

    border-radius: 50%;

    background: #60a5fa;
}


/* ------------------------------------------------------------
   TAB AREA
------------------------------------------------------------- */

#workspace-tabs {
    border: none !important;
    background: transparent !important;
}


/*
   We only target tabs inside our own #workspace-tabs,
   so this won't accidentally modify everything in Gradio.
*/

#workspace-tabs button[role="tab"] {
    min-width: 150px;

    padding: 11px 20px !important;

    margin-right: 8px;

    border-radius: 12px !important;
    border: 1px solid transparent !important;

    font-size: 14px !important;
    font-weight: 650 !important;

    color: #94a3b8 !important;

    background: transparent !important;

    transition:
        background 0.18s ease,
        color 0.18s ease,
        border-color 0.18s ease,
        transform 0.18s ease !important;
}


#workspace-tabs button[role="tab"]:hover {
    color: #e2e8f0 !important;

    background:
        rgba(30, 41, 59, 0.7) !important;
}


#workspace-tabs button[role="tab"][aria-selected="true"] {
    color: #f8fafc !important;

    background:
        linear-gradient(
            135deg,
            rgba(37, 99, 235, 0.22),
            rgba(79, 70, 229, 0.14)
        ) !important;

    border-color:
        rgba(96, 165, 250, 0.28) !important;

    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.04),
        0 5px 20px rgba(37, 99, 235, 0.08);
}


/* ------------------------------------------------------------
   APPLICATION PANEL
------------------------------------------------------------- */

.workspace-card {
    margin-top: 15px;

    padding: 22px !important;

    border-radius: 22px !important;

    border:
        1px solid var(--lab-border) !important;

    background:
        linear-gradient(
            145deg,
            rgba(15, 23, 42, 0.80),
            rgba(10, 16, 29, 0.88)
        ) !important;

    box-shadow:
        0 20px 50px rgba(0, 0, 0, 0.20),
        inset 0 1px 0 rgba(255, 255, 255, 0.02);
}


/* ------------------------------------------------------------
   INNER GRADIO COMPONENTS
------------------------------------------------------------- */

.workspace-card .block {
    border-radius: 14px !important;
}


/* inputs */

.workspace-card input,
.workspace-card textarea {
    border-radius: 11px !important;

    border-color:
        rgba(148, 163, 184, 0.18) !important;

    transition:
        border-color 0.18s ease,
        box-shadow 0.18s ease !important;
}


.workspace-card input:focus,
.workspace-card textarea:focus {
    border-color:
        rgba(96, 165, 250, 0.55) !important;

    box-shadow:
        0 0 0 3px rgba(59, 130, 246, 0.09) !important;
}


/* Buttons */

.workspace-card button.primary {
    border: 1px solid rgba(96, 165, 250, 0.20) !important;

    border-radius: 11px !important;

    font-weight: 650 !important;

    background:
        linear-gradient(
            135deg,
            #2563eb,
            #4f46e5
        ) !important;

    box-shadow:
        0 7px 18px rgba(37, 99, 235, 0.18);

    transition:
        transform 0.15s ease,
        box-shadow 0.15s ease !important;
}


.workspace-card button.primary:hover {
    transform: translateY(-1px);

    box-shadow:
        0 10px 25px rgba(37, 99, 235, 0.27);
}


/* tables */

.workspace-card table {
    border-radius: 12px !important;
    overflow: hidden;
}


/* ------------------------------------------------------------
   FOOTER
------------------------------------------------------------- */

.lab-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;

    gap: 15px;

    padding: 18px 5px 0;

    font-size: 11px;

    color: #64748b;
}


.lab-footer-name {
    color: #94a3b8;
    font-weight: 600;
}


/* ------------------------------------------------------------
   RESPONSIVE
------------------------------------------------------------- */

@media (max-width: 850px) {

    #lab-shell {
        width: calc(100% - 24px);
        padding-top: 16px;
    }

    .lab-header-inner {
        flex-direction: column;
        align-items: flex-start;

        padding: 24px;
    }

    .lab-meta {
        justify-content: flex-start;
    }

    .workspace-card {
        padding: 14px !important;
    }

}


@media (max-width: 520px) {

    .lab-logo {
        width: 46px;
        height: 46px;
    }

    .lab-title {
        font-size: 24px;
    }

    .lab-description {
        font-size: 13px;
    }

    #workspace-tabs button[role="tab"] {
        min-width: auto;
        padding: 9px 14px !important;
    }

}


/* Hide standard Gradio footer */
footer {
    display: none !important;
}
"""


# ============================================================
# HEADER
# ============================================================

HEADER_HTML = """
<div id="lab-header">
    <div class="lab-header-inner">

        <div class="lab-brand">

            <div class="lab-logo">
                <div class="lab-logo-mark">FG</div>
            </div>

            <div>
                <div class="lab-eyebrow">
                    Reliability Engineering Platform
                </div>

                <h1 class="lab-title">
                    FlexGuard Reliability Lab
                </h1>

                <div class="lab-description">
                    Validate field workflows, simulate failure conditions,
                    and investigate system resilience from one workspace.
                </div>
            </div>

        </div>

        <div class="lab-meta">

            <div class="lab-pill">
                <span class="lab-status-dot"></span>
                Live Demo
            </div>

            <div class="lab-pill">
                <span class="lab-port-dot"></span>
                FieldSync API
            </div>

            <div class="lab-pill">
                <span class="lab-port-dot"></span>
                Chaos Proxy
            </div>

        </div>

    </div>
</div>
"""


# ============================================================
# MAIN APPLICATION
# ============================================================

with gr.Blocks(
    title="FlexGuard Reliability Lab",
    fill_width=True,
) as combined_app:

    with gr.Column(elem_id="lab-shell"):

        gr.HTML(HEADER_HTML)

        with gr.Tabs(elem_id="workspace-tabs"):

            # ------------------------------------------------
            # FIELDSYNC
            # ------------------------------------------------

            with gr.Tab("FieldSync"):

                with gr.Column(
                    elem_classes=["workspace-card"]
                ):
                    fieldsync_ui.render()

            # ------------------------------------------------
            # FLEXGUARD
            # ------------------------------------------------

            with gr.Tab("FlexGuard"):

                with gr.Column(
                    elem_classes=["workspace-card"]
                ):
                    flexguard_ui.render()

        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        gr.HTML(
            """
            <div class="lab-footer">
                <span class="lab-footer-name">
                    FlexGuard Reliability Lab
                </span>

                <span>
                    Field workflow validation · Failure injection ·
                    Reliability testing
                </span>
            </div>
            """
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    start_services()

    combined_app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=theme,
        css=CUSTOM_CSS,
    )