import asyncio

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
import random


TARGET_API = "http://127.0.0.1:8000"

CHAOS_MODE = "normal"
DELAY_SECONDS = 3


app = FastAPI(
    title="FlexGuard Chaos Proxy"
)


@app.api_route(
    "/{path:path}",
    methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE"
    ]
)
async def proxy_request(
    path: str,
    request: Request
):
    body = await request.body()

    target_url = (
        f"{TARGET_API}/{path}"
    )

    if CHAOS_MODE == "delay":
        await asyncio.sleep(
            DELAY_SECONDS
        )

    if CHAOS_MODE == "error":
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Simulated chaos proxy error"
            }
        )

    if CHAOS_MODE == "drop":
        raise httpx.ConnectError(
            "Simulated connection drop"
        )

    if CHAOS_MODE == "unstable":

        chance = random.random()

        if chance < 0.30:
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Simulated unstable network failure"
                }
            )

        if chance < 0.60:
            await asyncio.sleep(3)   

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers={
                "content-type": request.headers.get(
                    "content-type",
                    "application/json"
                )
            },
            timeout=30
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get(
            "content-type"
        )
    )