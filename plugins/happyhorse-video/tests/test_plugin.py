"""Plugin entry — verifies tool registration + workbench schema."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from _plugin_loader import load_happyhorse_plugin
from fastapi import APIRouter, Depends, FastAPI

_HH = load_happyhorse_plugin()
HappyhorsePlugin = _HH.Plugin


EXPECTED_TOOLS = {
    "hh_t2v",
    "hh_image_create",
    "hh_image_edit",
    "hh_image_style_repaint",
    "hh_image_background",
    "hh_image_outpaint",
    "hh_image_sketch",
    "hh_image_ecommerce",
    "hh_i2v",
    "hh_r2v",
    "hh_video_edit",
    "hh_photo_speak",
    "hh_video_relip",
    "hh_video_reface",
    "hh_pose_drive",
    "hh_avatar_compose",
    "hh_status",
    "hh_list",
    "hh_cost_preview",
    "hh_long_video_create",
    "hh_storyboard_decompose",
    "hh_video_concat",
}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field", ["first_frame_url", "first_frame_path", "image_url", "image_path"]
)
async def test_i2v_create_uploads_local_first_frame_before_pipeline(tmp_path, field):
    photo = tmp_path / "input.png"
    photo.write_bytes(b"test image")
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    plugin._client = SimpleNamespace(has_api_key=lambda: True)
    plugin._settings_cache = {}
    plugin._data_dir = tmp_path
    plugin._oss = Mock()
    plugin._oss.upload_file.return_value = "https://oss.example.com/frame?signature=test"
    plugin._tm = SimpleNamespace(
        create_task=AsyncMock(return_value="task"), get_task=AsyncMock(return_value={"id": "task"})
    )
    plugin._preflight_asset_specs = AsyncMock()
    plugin._spawn_pipeline = Mock()
    body = _HH.CreateTaskBody(
        mode="i2v", prompt="owl catches mouse", duration=5, **{field: str(photo)}
    )
    await plugin._create_task_internal(body)
    params = plugin._tm.create_task.call_args.kwargs["params"]
    assert params["first_frame_url"] == plugin._oss.upload_file.return_value
    assert params["first_frame_path"] == str(photo.resolve())
    assert plugin._spawn_pipeline.call_args.args[2]["first_frame_url"] == params["first_frame_url"]
    plugin._oss.upload_file.assert_called_once()


@pytest.mark.asyncio
async def test_i2v_oss_failure_does_not_create_task(tmp_path):
    photo = tmp_path / "input.png"
    photo.write_bytes(b"test image")
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    plugin._client = SimpleNamespace(has_api_key=lambda: True)
    plugin._settings_cache = {}
    plugin._data_dir = tmp_path
    plugin._oss = Mock()
    plugin._oss.upload_file.side_effect = _HH.OssUploadError("access denied")
    plugin._tm = SimpleNamespace(create_task=AsyncMock())
    plugin._preflight_asset_specs = AsyncMock()
    body = _HH.CreateTaskBody(mode="i2v", prompt="owl", image_path=str(photo))
    with pytest.raises(_HH.HTTPException) as exc:
        await plugin._create_task_internal(body)
    assert exc.value.status_code == 502
    assert "access denied" in exc.value.detail
    plugin._tm.create_task.assert_not_called()


def _plugin_with_lifecycle_state(*, ready: bool, error: str | None = None):
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    plugin._ready_event = asyncio.Event()
    if ready:
        plugin._ready_event.set()
    plugin._init_error = error
    plugin._stopping = False
    return plugin


@pytest.mark.asyncio
async def test_settings_route_returns_503_until_plugin_is_ready():
    plugin = _plugin_with_lifecycle_state(ready=False)
    plugin._tm = SimpleNamespace(
        get_all_config=lambda: pytest.fail("route ran before readiness dependency")
    )
    router = APIRouter(dependencies=[Depends(plugin._require_ready)])
    plugin._register_routes(router)
    app = FastAPI()
    app.include_router(router)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/settings")

    assert response.status_code == 503
    assert response.headers["retry-after"] == "1"
    assert "initializing" in response.json()["detail"]


@pytest.mark.asyncio
async def test_initialization_failure_is_retained_for_routes_and_tools():
    plugin = _plugin_with_lifecycle_state(ready=False)

    async def fail_init():
        raise RuntimeError("database unavailable")

    plugin._async_init = fail_init
    await plugin._run_initialization()

    assert plugin._lifecycle_status() == (
        "failed",
        "RuntimeError: database unavailable",
    )
    with pytest.raises(_HH.HTTPException) as exc_info:
        await plugin._require_ready()
    assert exc_info.value.status_code == 503
    assert "database unavailable" in str(exc_info.value.detail)

    payload = json.loads(await plugin._handle_tool("hh_status", {}))
    assert payload["error_kind"] == "plugin_not_ready"
    assert "database unavailable" in payload["error_message"]


def test_plugin_registers_video_and_image_tools():
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    tools = plugin._tool_definitions()
    names = {t["name"] for t in tools}
    assert names == EXPECTED_TOOLS


def test_video_tools_advertise_from_asset_ids_in_schema():
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    tools = plugin._tool_definitions()
    by_name = {t["name"]: t for t in tools}
    for tool_name in (
        "hh_t2v",
        "hh_i2v",
        "hh_r2v",
        "hh_video_edit",
        "hh_photo_speak",
        "hh_avatar_compose",
    ):
        schema = by_name[tool_name]["input_schema"]
        assert "from_asset_ids" in schema["properties"], (
            f"{tool_name} must accept from_asset_ids for workbench chaining"
        )


def test_video_tools_declare_model_catalog_and_idempotency_contract():
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    tools = plugin._tool_definitions()
    by_name = {t["name"]: t for t in tools}
    for tool_name in ("hh_t2v", "hh_i2v", "hh_r2v", "hh_video_edit"):
        tool = by_name[tool_name]
        assert tool["x-openakita-idempotency-param"] == "client_request_id"
        contract = tool["x-openakita-media-contract"]
        assert contract["kind"] == "video"
        assert contract["default_model"] in contract["models"]
        assert all(
            len(model_contract["duration_range"]) == 2
            for model_contract in contract["models"].values()
        )
        model_ids = tool["input_schema"]["properties"]["model_id"]["enum"]
        assert model_ids
        assert all(isinstance(model_id, str) and model_id for model_id in model_ids)


@pytest.mark.asyncio
async def test_video_task_rejects_model_outside_mode_catalog_before_submission():
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    plugin._client = SimpleNamespace(has_api_key=lambda: True)
    body = _HH.CreateTaskBody(mode="t2v", prompt="test", model_id="kling-v2")

    with pytest.raises(_HH.HTTPException) as exc_info:
        await plugin._create_task_internal(body)

    assert exc_info.value.status_code == 422
    assert "可用目录" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_video_task_rejects_unsupported_duration_before_submission():
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    plugin._client = SimpleNamespace(has_api_key=lambda: True)
    body = _HH.CreateTaskBody(
        mode="i2v",
        prompt="test",
        model_id="happyhorse-1.0-i2v",
        duration=2,
        resolution="720P",
    )

    with pytest.raises(_HH.HTTPException) as exc_info:
        await plugin._create_task_internal(body)

    assert exc_info.value.status_code == 422
    assert "3-15s" in str(exc_info.value.detail)


def test_video_tools_accept_documented_alias_fields():
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    tools = plugin._tool_definitions()
    by_name = {t["name"]: t for t in tools}
    props = by_name["hh_video_edit"]["input_schema"]["properties"]
    assert "video_url" in props
    assert "source_video_url" in props
    assert "task_type" in props
    assert "mode_pro" in props
    assert "ref_images_url" in props


def test_status_tool_requires_task_id():
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    tools = plugin._tool_definitions()
    by_name = {t["name"]: t for t in tools}
    schema = by_name["hh_status"]["input_schema"]
    assert "task_id" in schema["required"]


def test_long_video_tool_requires_segments():
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    tools = plugin._tool_definitions()
    by_name = {t["name"]: t for t in tools}
    schema = by_name["hh_long_video_create"]["input_schema"]
    assert "segments" in schema["required"]


def test_storyboard_decompose_tool_schema():
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    tools = plugin._tool_definitions()
    by_name = {t["name"]: t for t in tools}
    schema = by_name["hh_storyboard_decompose"]["input_schema"]
    assert "story" in schema["required"]
    props = schema["properties"]
    for field in ("story", "total_duration", "segment_duration", "aspect_ratio", "style"):
        assert field in props, f"hh_storyboard_decompose missing field: {field}"


def test_video_concat_tool_schema():
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    tools = plugin._tool_definitions()
    by_name = {t["name"]: t for t in tools}
    schema = by_name["hh_video_concat"]["input_schema"]
    assert "task_ids" in schema["required"]
    props = schema["properties"]
    assert props["task_ids"]["type"] == "array"
    assert "transition" in props
    assert "fade_duration" in props
    assert "output_name" in props
    transition_enum = set(props["transition"]["enum"])
    assert {"none", "crossfade", "cut"}.issubset(transition_enum), (
        f"transition enum missing expected aliases: {transition_enum}"
    )


def test_module_exposes_pydantic_bodies():
    """plugin.py must export its request bodies so on_load can use them."""
    assert hasattr(_HH, "CreateTaskBody")
    assert hasattr(_HH, "ImageCreateTaskBody")
    assert hasattr(_HH, "LongVideoCreateBody")
    assert hasattr(_HH, "PromptOptimizeBody")


def test_image_tools_publish_asset_ids_contract():
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    tools = plugin._tool_definitions()
    by_name = {t["name"]: t for t in tools}
    schema = by_name["hh_image_create"]["input_schema"]
    assert "from_asset_ids" in schema["properties"]
    assert "model_id" in schema["properties"]
    assert "size" in schema["properties"]


# ─── Bug 6 regression — hh_image_ecommerce schema accepts product_name ─


def test_image_ecommerce_schema_accepts_either_prompt_or_product_name():
    """hh_image_ecommerce historically required ``prompt`` even though
    the backend builds prompts from ``product_name`` alone. The schema
    now exposes ``anyOf`` so LLMs can call the tool with whichever
    field they have.
    """
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    tools = plugin._tool_definitions()
    by_name = {t["name"]: t for t in tools}
    schema = by_name["hh_image_ecommerce"]["input_schema"]
    assert "required" not in schema or "prompt" not in schema.get("required", [])
    assert "anyOf" in schema
    required_groups = [grp.get("required", []) for grp in schema["anyOf"]]
    assert ["prompt"] in required_groups
    assert ["product_name"] in required_groups


def test_image_text2img_schema_still_requires_prompt():
    """The relaxation for hh_image_ecommerce must not leak into other
    image tools — text-to-image still needs a prompt."""
    plugin = HappyhorsePlugin.__new__(HappyhorsePlugin)
    tools = plugin._tool_definitions()
    by_name = {t["name"]: t for t in tools}
    schema = by_name["hh_image_create"]["input_schema"]
    assert schema.get("required") == ["prompt"]
