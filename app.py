import threading
import time

import uvicorn

from fieldsync.main import app as fieldsync_app
from guard_engine.chaos.proxy import app as proxy_app
from guard_engine.dashboard import (
    app as dashboard_app,
    custom_css,
    dashboard_theme,
)


# Hugging Face ZeroGPU requires at least one
# function registered with @spaces.GPU.
# FlexGuard itself does not need GPU processing.

try:
    import spaces

    @spaces.GPU(duration=1)
    def _zerogpu_probe():
        return None

except ImportError:
    pass


def start_server(application, port):
    uvicorn.run(
        application,
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )


def start_flexguard_services():
    fieldsync_thread = threading.Thread(
        target=start_server,
        args=(fieldsync_app, 8000),
        daemon=True,
    )

    proxy_thread = threading.Thread(
        target=start_server,
        args=(proxy_app, 9000),
        daemon=True,
    )

    fieldsync_thread.start()
    proxy_thread.start()

    time.sleep(2)


if __name__ == "__main__":
    start_flexguard_services()

    dashboard_app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=dashboard_theme,
        css=custom_css,
    )