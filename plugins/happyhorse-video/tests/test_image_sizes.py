"""Model-specific canvas presets and request parameter regressions."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from _plugin_loader import load_happyhorse_plugin
from happyhorse_image_models import IMAGE_MODELS, image_size_presets

_HH = load_happyhorse_plugin()


def image_plugin():
    plugin = _HH.Plugin.__new__(_HH.Plugin)
    plugin._client = SimpleNamespace(has_api_key=lambda: True)
    plugin._read_settings = lambda: {"default_aspect_ratio": "16:9"}
    plugin._tm = SimpleNamespace(
        create_task=AsyncMock(return_value="image"),
        update_task_safe=AsyncMock(),
        get_task=AsyncMock(return_value={"id": "image"}),
    )
    plugin._broadcast = lambda *args: None
    plugin._run_image_task = AsyncMock()
    return plugin


PRESETS = [
    (model.model_id, preset)
    for model in IMAGE_MODELS
    for preset in image_size_presets(model.model_id, model.sizes)
]


@pytest.mark.asyncio
@pytest.mark.parametrize("model_id,preset", PRESETS)
async def test_catalog_canvas_is_preserved_through_submission(model_id, preset):
    plugin = image_plugin()
    await plugin._create_image_task_internal(
        _HH.ImageCreateTaskBody(
            prompt="rainy street",
            model_id=model_id,
            size=preset["size"],
            output_ratio=preset["ratio"],
            wait_for_completion=True,
            mode="image_edit" if model_id == "wan2.6-image" else "image_text2img",
            images=["https://example.com/a.png"] if model_id == "wan2.6-image" else [],
        )
    )
    params = plugin._run_image_task.call_args.args[1]
    assert params["size"] == preset["size"]
    assert params["output_ratio"] == preset["ratio"]
    width, height = map(int, preset["size"].split("*"))
    assert params["expected_media"]["width"] == width
    assert params["expected_media"]["height"] == height
    plugin._client.submit_image_multimodal = AsyncMock(return_value={"async": False})
    plugin._image_urls_from_result = AsyncMock(return_value=["https://example.com/result.png"])
    await plugin._submit_image_request(params)
    sent = plugin._client.submit_image_multimodal.call_args.kwargs
    assert sent["size"] == preset["size"]
    assert sent["model"] == model_id
    if model_id.startswith("wan2.7-") or model_id == "wan2.6-image":
        edge = {"1K": 1024, "2K": 2048, "4K": 4096}[preset["tier"]]
        if model_id == "wan2.6-image" and preset["tier"] == "1K":
            edge = 1280
        assert 768**2 <= width * height <= edge**2
        assert width * height >= edge**2 * 0.75


@pytest.mark.asyncio
async def test_explicit_portrait_without_ratio_ignores_default_landscape():
    plugin = image_plugin()
    await plugin._create_image_task_internal(
        _HH.ImageCreateTaskBody(
            prompt="portrait",
            model_id="qwen-pro",
            size="1024*1536",
            wait_for_completion=True,
        )
    )
    params = plugin._run_image_task.call_args.args[1]
    assert params["size"] == "1024*1536"
    assert params["expected_media"]["height"] == 1536


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extra",
    [
        {"size": "1024*1536", "output_ratio": "16:9"},
        {"size": "512*512"},
        {"size": "8192*8192"},
        {"size": "4096*4096", "mode": "image_edit", "images": ["https://example.com/a.png"]},
        {"size": "4096*4096", "enable_sequential": True},
        {"size": "4096*4096", "model_id": "wan27"},
        {"size": "1280*1280", "model_id": "wan26"},
        {
            "size": "4096*4096",
            "model_id": "wan26",
            "mode": "image_edit",
            "images": ["https://example.com/a.png"],
        },
    ],
)
async def test_invalid_canvas_is_rejected_before_creating_task(extra):
    plugin = image_plugin()
    body = {"prompt": "portrait", "model_id": "wan27-pro", **extra}
    with pytest.raises(_HH.HTTPException) as exc:
        await plugin._create_image_task_internal(_HH.ImageCreateTaskBody(**body))
    assert exc.value.status_code == 422
    plugin._tm.create_task.assert_not_called()
