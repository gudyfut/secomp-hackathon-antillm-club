"""One explicit live Jev call with secret-safe request and response logging."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import httpx2
from dotenv import load_dotenv
from typesafe_sdk import AsyncTypeSafeClient

from decision.examples.common import make_example_world_state, print_json
from decision.jev import JevDecisionEngine


def _decode_json(raw: bytes) -> Any:
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


async def _log_request(request: httpx2.Request) -> None:
    body = await request.aread()
    print_json(
        "HTTP REQUEST - JSON REALMENTE ENVIADO (HEADERS OMITIDOS)",
        {"method": request.method, "url": str(request.url), "body": _decode_json(body)},
    )


async def _log_response(response: httpx2.Response) -> None:
    body = await response.aread()
    print_json(
        "HTTP RESPONSE - JSON BRUTO RECEBIDO",
        {"status": response.status_code, "body": _decode_json(body)},
    )


async def main() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    load_dotenv(repository_root / ".env")
    if not os.getenv("TYPESAFE_API_KEY", "").strip():
        raise RuntimeError("TYPESAFE_API_KEY ausente no .env da raiz do repositorio")

    world_state = make_example_world_state()
    print_json("WORLDSTATE ANTES DO ADAPTER", world_state)

    async with httpx2.AsyncClient(
        event_hooks={"request": [_log_request], "response": [_log_response]}
    ) as http_client:
        client = AsyncTypeSafeClient(http_client=http_client)
        evaluator = JevDecisionEngine(client)
        result = await evaluator.evaluate(world_state)

    print_json("OUTPUT MAPEADO PELO ADAPTER PYTHON", result)


if __name__ == "__main__":
    asyncio.run(main())
