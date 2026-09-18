import threading
import time
import webbrowser

import uvicorn

from fieldsync.main import app as fieldsync_api
from fieldsync.frontend import app as fieldsync_ui
from guard_engine.chaos.proxy import app as proxy_api
from guard_engine.dashboard import (
    app as flexguard_ui,
    custom_css,
    dashboard_theme,
)


def start_api(application, port):
    uvicorn.run(
        application,
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )


def start_services():
    fieldsync_api_thread = threading.Thread(
        target=start_api,
        args=(fieldsync_api, 8000),
        daemon=True,
    )

    proxy_thread = threading.Thread(
        target=start_api,
        args=(proxy_api, 9000),
        daemon=True,
    )

    fieldsync_api_thread.start()
    proxy_thread.start()

    time.sleep(2)


def start_fieldsync_ui():
    fieldsync_ui.launch(
        server_name="127.0.0.1",
        server_port=7861,
        prevent_thread_lock=True,
    )


def open_browser_tabs():
    time.sleep(3)

    webbrowser.open(
        "http://127.0.0.1:7861"
    )

    webbrowser.open(
        "http://127.0.0.1:7860"
    )


if __name__ == "__main__":

    print()
    print("Starting FlexGuard Reliability Lab")
    print("==================================")
    print("FieldSync API:     http://127.0.0.1:8000")
    print("API Documentation: http://127.0.0.1:8000/docs")
    print("Chaos Proxy:       http://127.0.0.1:9000")
    print("FieldSync App:     http://127.0.0.1:7861")
    print("FlexGuard:         http://127.0.0.1:7860")
    print()

    start_services()

    start_fieldsync_ui()

    browser_thread = threading.Thread(
        target=open_browser_tabs,
        daemon=True,
    )

    browser_thread.start()

    flexguard_ui.launch(
        server_name="127.0.0.1",
        server_port=7860,
        theme=dashboard_theme,
        css=custom_css,
    )