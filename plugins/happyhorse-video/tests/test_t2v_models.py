"""Current T2V catalog, vendor payloads, prices and output contracts."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from _plugin_loader import load_happyhorse_plugin
from happyhorse_dashscope_client import HappyhorseDashScopeClient
from happyhorse_inline.asset_probe import MediaTarget, video_target_for
from happyhorse_model_registry import lookup, models_for
from happyhorse_models import estimate_cost

_HH = load_happyhorse_plugin()
NEW_MODELS = (
    "wan3.0-video",
    "wan3.0-video-prime",
    "happyhorse-1.1-t2v",
    "wan2.7-t2v",
    "wan2.7-t2v-2026-06-12",
    "wan2.7-t2v-2026-04-25",
)


def test_catalog_exposes_all_new_t2v_models_and_keeps_previous_choices():
    ids = {entry.model_id for entry in models_for("t2v")}
    assert ids == {*NEW_MODELS, "happyhorse-1.0-t2v", "wan2.6-t2v"}


def test_agent_tool_exposes_new_models_and_480p():
    plugin = _HH.Plugin.__new__(_HH.Plugin)
    tool = next(t for t in plugin._tool_definitions() if t["name"] == "hh_t2v")
    props = tool["input_schema"]["properties"]
    assert set(NEW_MODELS) <= set(props["model_id"]["enum"])
    assert "480P" in props["resolution"]["enum"]


@pytest.mark.asyncio
@pytest.mark.parametrize("model_id", NEW_MODELS)
async def test_new_t2v_vendor_body_uses_resolution_and_ratio(model_id):
    client = HappyhorseDashScopeClient(lambda: {"api_key": "test"})
    client._submit_async = AsyncMock(return_value="vendor-task")
    entry = lookup("t2v", model_id)
    await client.submit_video_synth(
        mode="t2v",
        model_id=model_id,
        prompt="a cat in the rain",
        aspect="9:16",
        resolution="1080P",
        duration=entry.duration_range[1],
        negative_prompt="blur",
        watermark=False,
        prompt_extend=True,
        shot_type="multi",
        audio=False,
        driving_audio_url="https://example.com/audio.mp3" if entry.supports_audio_url else None,
    )
    body = client._submit_async.call_args.args[1]
    params = body["parameters"]
    assert params["ratio"] == "9:16"
    assert params["resolution"] == "1080P"
    assert params["duration"] == entry.duration_range[1]
    assert params["watermark"] is False
    assert "size" not in params
    assert "shot_type" not in params
    assert "negative_prompt" not in params
    if model_id.startswith("wan2.7-"):
        assert body["input"]["negative_prompt"] == "blur"
        assert body["input"]["audio_url"] == "https://example.com/audio.mp3"
        assert "audio" not in params
    elif model_id.startswith("wan3."):
        assert params["audio"] is False
        assert "negative_prompt" not in body["input"]
    else:
        assert "audio" not in params
        assert "prompt_extend" not in params


@pytest.mark.parametrize(
    "model_id,prices",
    [
        ("wan3.0-video", {"480P": 0.30, "720P": 0.60, "1080P": 1.20}),
        ("wan3.0-video-prime", {"480P": 0.45, "720P": 0.90, "1080P": 1.80}),
        ("happyhorse-1.1-t2v", {"480P": 0.45, "720P": 0.90, "1080P": 1.20}),
        *[(model, {"720P": 0.60, "1080P": 1.00}) for model in NEW_MODELS[3:]],
    ],
)
def test_new_t2v_costs_use_model_prices(model_id, prices):
    for resolution, price in prices.items():
        for audio in (True, False):
            preview = estimate_cost(
                "t2v",
                {
                    "model": model_id,
                    "resolution": resolution,
                    "duration": 5,
                    "audio": audio,
                },
            )
            assert preview["items"][0]["unit_price"] == price
            assert preview["items"][0]["subtotal"] == round(price * 5, 4)


def test_wan27_output_dimensions_follow_vendor_table():
    assert video_target_for("1:1", "720P", dimension_policy="wan27") == MediaTarget("1:1", 960, 960)
    assert video_target_for("9:16", "1080P", dimension_policy="wan27") == MediaTarget(
        "9:16", 1080, 1920
    )
    assert video_target_for("4:3", "1080P", dimension_policy="wan27") == MediaTarget(
        "4:3", 1648, 1248
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("model_id", NEW_MODELS)
async def test_new_t2v_creation_accepts_duration_and_sets_output_contract(model_id):
    plugin = _HH.Plugin.__new__(_HH.Plugin)
    plugin._client = SimpleNamespace(has_api_key=lambda: True)
    plugin._settings_cache = {}
    plugin._data_dir = Path(".")
    plugin._oss = Mock()
    plugin._tm = SimpleNamespace(
        create_task=AsyncMock(return_value="task"), get_task=AsyncMock(return_value={"id": "task"})
    )
    plugin._preflight_asset_specs = AsyncMock()
    plugin._spawn_pipeline = Mock()
    entry = lookup("t2v", model_id)
    await plugin._create_task_internal(
        _HH.CreateTaskBody(
            mode="t2v",
            model_id=model_id,
            prompt="a cat",
            resolution="1080P",
            aspect_ratio="1:1",
            duration=entry.duration_range[1],
        )
    )
    expected = plugin._tm.create_task.call_args.kwargs["params"]["expected_media"]
    if model_id.startswith("wan2.7-"):
        assert expected == {"aspect_ratio": "1:1", "width": 1440, "height": 1440}
    else:
        assert expected == {"aspect_ratio": "1:1", "resolution": "1080P", "validation": "aspect"}
