import asyncio
import random

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel


TARGET_API = "http://127.0.0.1:8000"

CHAOS_MODE = "normal"
DELAY_SECONDS = 3

VALID_MODES = {
    "normal",
    "delay",
    "error",
    "drop",
    "unstable",
    "lost_ack",
}


app = FastAPI(
    title="FlexGuard Chaos Proxy"
)


class ChaosModeRequest(BaseModel):
    mode: str


@app.get("/__chaos/status")
def get_chaos_status():
    return {
        "mode": CHAOS_MODE,
        "delay_seconds": DELAY_SECONDS,
    }


@app.post("/__chaos/mode")
def set_chaos_mode(config: ChaosModeRequest):
    global CHAOS_MODE

    mode = config.mode.lower().strip()

    if mode not in VALID_MODES:
        return JSONResponse(
            status_code=400,
            content={
                "detail": (
                    f"Invalid chaos mode: {mode}"
                ),
                "valid_modes": sorted(
                    VALID_MODES
                ),
            },
        )

    CHAOS_MODE = mode

    return {
        "mode": CHAOS_MODE,
        "message": (
            f"Chaos mode changed to "
            f"{CHAOS_MODE}"
        ),
    }


@app.post("/__chaos/reset")
def reset_chaos_mode():
    global CHAOS_MODE

    CHAOS_MODE = "normal"

    return {
        "mode": CHAOS_MODE,
        "message": "Chaos mode reset",
    }


@app.api_route(
    "/{path:path}",
    methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    ],
)
async def proxy_request(
    path: str,
    request: Request,
):
    body = await request.body()

    target_url = (
        f"{TARGET_API}/{path}"
    )

    if request.url.query:
        target_url += (
            f"?{request.url.query}"
        )

    if CHAOS_MODE == "delay":
        await asyncio.sleep(
            DELAY_SECONDS
        )

    if CHAOS_MODE == "error":
        return JSONResponse(
            status_code=500,
            content={
                "detail": (
                    "Simulated chaos proxy error"
                )
            },
        )

    if CHAOS_MODE == "drop":
        return JSONResponse(
            status_code=503,
            content={
                "detail": (
                    "Simulated connection failure"
                )
            },
        )

    if CHAOS_MODE == "unstable":
        chance = random.random()

        if chance < 0.30:
            return JSONResponse(
                status_code=500,
                content={
                    "detail": (
                        "Simulated unstable "
                        "network failure"
                    )
                },
            )

        if chance < 0.60:
            await asyncio.sleep(
                DELAY_SECONDS
            )

    headers = {}

    content_type = request.headers.get(
        "content-type"
    )

    if content_type:
        headers["content-type"] = (
            content_type
        )

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers=headers,
            timeout=30,
        )

    # Important reliability scenario:
    # the backend successfully processes the
    # create request, but the client never receives
    # the successful acknowledgement.
    if (
        CHAOS_MODE == "lost_ack"
        and request.method == "POST"
        and path.rstrip("/") == "inspections"
        and 200 <= response.status_code < 300
    ):
        return JSONResponse(
            status_code=504,
            content={
                "detail": (
                    "Simulated lost acknowledgement "
                    "after server commit"
                )
            },
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get(
            "content-type"
        ),
    )