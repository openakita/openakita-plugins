"""Public inspiration metadata caching and upstream failure handling."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from _plugin_loader import load_happyhorse_plugin
from fastapi import APIRouter, HTTPException

_HH = load_happyhorse_plugin()


def endpoint():
    router = APIRouter()
    _HH.Plugin.__new__(_HH.Plugin)._register_routes(router)
    return next(route.endpoint for route in router.routes if route.path == "/inspiration")


def upstream(payload):
    return httpx.Response(200, json=payload, request=httpx.Request("GET", "https://example.test"))


@pytest.mark.asyncio
async def test_manifest_cache_and_stale_fallback():
    handler = endpoint()
    client = AsyncMock()
    client.get.return_value = upstream({"items": [{"id": "image-01"}]})
    clock = [100.0]
    with patch("httpx.AsyncClient") as factory, patch.object(
        _HH.time, "monotonic", side_effect=lambda: clock[0]
    ):
        factory.return_value.__aenter__.return_value = client
        first = await handler()
        assert await handler() == first
        assert client.get.call_count == 1
        assert client.get.call_args.args[0].endswith("/happyhorse-video/metadata.json")
        clock[0] += 301
        client.get.side_effect = httpx.ConnectError("offline")
        assert await handler() == first
        assert client.get.call_count == 2
        assert await handler() == first
        assert client.get.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [{"items": None}, [], {"items": "bad"}])
async def test_invalid_initial_manifest_returns_502(payload):
    client = AsyncMock()
    client.get.return_value = upstream(payload)
    with patch("httpx.AsyncClient") as factory:
        factory.return_value.__aenter__.return_value = client
        with pytest.raises(HTTPException) as error:
            await endpoint()()
    assert error.value.status_code == 502
