from unittest.mock import Mock

import pytest
from happyhorse_inline.media_inputs import normalize_first_frame, prepare_media_inputs
from happyhorse_inline.oss_uploader import OssNotConfigured, OssUploadError


@pytest.mark.parametrize("alias", ["image_url", "image_path", "first_frame_path"])
def test_first_frame_alias_and_precedence(alias):
    params = {alias: "photo.png"}
    normalize_first_frame("i2v", params)
    assert params["first_frame_url"] == "photo.png"
    params = {alias: "ignored.png", "first_frame_url": "https://example.com/frame.png"}
    normalize_first_frame("i2v_end", params)
    assert params["first_frame_url"] == "https://example.com/frame.png"


def test_digital_human_image_is_not_a_first_frame_alias():
    params = {"image_url": "portrait.png"}
    normalize_first_frame("photo_speak", params)
    assert params == {"image_url": "portrait.png"}


@pytest.mark.asyncio
async def test_signed_remote_url_is_preserved_without_oss(tmp_path):
    url = "https://example.com/frame.png?Signature=a%2Bb&Expires=123"
    params = {"first_frame_url": url}
    uploader = Mock()
    await prepare_media_inputs(params, uploader=uploader, uploads_root=tmp_path)
    assert params["first_frame_url"] == url
    assert uploader.mock_calls == []


@pytest.mark.asyncio
async def test_local_inputs_and_reference_lists_upload_once(tmp_path):
    photo = tmp_path / "photo.png"
    photo.write_bytes(b"photo")
    remote = "https://example.com/remote.png"
    params = {"first_frame_url": str(photo), "reference_urls": [str(photo), remote]}
    uploader = Mock()
    uploader.upload_file.return_value = "https://oss.example.com/signed.png?signature=abc"
    await prepare_media_inputs(params, uploader=uploader, uploads_root=tmp_path)
    uploader.upload_file.assert_called_once()
    assert params["first_frame_url"] == uploader.upload_file.return_value
    assert params["first_frame_path"] == str(photo.resolve())
    assert params["reference_urls"] == [uploader.upload_file.return_value, remote]


@pytest.mark.asyncio
async def test_plugin_preview_maps_to_uploaded_file(tmp_path):
    photo = tmp_path / "images" / "my photo.png"
    photo.parent.mkdir()
    photo.write_bytes(b"photo")
    uploader = Mock()
    uploader.upload_file.return_value = "https://oss.example.com/photo"
    params = {"image_url": "/api/plugins/happyhorse-video/uploads/images/my%20photo.png"}
    await prepare_media_inputs(params, uploader=uploader, uploads_root=tmp_path)
    assert uploader.upload_file.call_args.args[0] == photo.resolve()


@pytest.mark.asyncio
async def test_relative_local_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    photo = tmp_path / "frame.png"
    photo.write_bytes(b"image")
    uploader = Mock()
    uploader.upload_file.return_value = "https://oss.example.com/frame"
    params = {"first_frame_url": "frame.png"}
    await prepare_media_inputs(params, uploader=uploader, uploads_root=tmp_path)
    assert uploader.upload_file.call_args.args[0] == photo


@pytest.mark.asyncio
async def test_asset_bus_preview_uses_local_source(tmp_path):
    photo = tmp_path / "frame.png"
    photo.write_bytes(b"image")
    uploader = Mock()
    uploader.upload_file.return_value = "https://oss.example.com/frame"
    params = {"first_frame_url": "/api/files?path=frame.png", "first_frame_path": str(photo)}
    await prepare_media_inputs(params, uploader=uploader, uploads_root=tmp_path)
    assert params["first_frame_url"] == uploader.upload_file.return_value


@pytest.mark.asyncio
async def test_same_filename_inputs_use_distinct_oss_keys(tmp_path):
    files = []
    for folder in ("a", "b"):
        photo = tmp_path / folder / "frame.png"
        photo.parent.mkdir()
        photo.write_bytes(folder.encode())
        files.append(str(photo))
    uploader = Mock()
    uploader.build_object_key.side_effect = lambda scope, filename: f"{scope}/{filename}"
    uploader.upload_file.side_effect = lambda path, key: f"https://oss.example.com/{key}"
    params = {"reference_urls": files}
    await prepare_media_inputs(params, uploader=uploader, uploads_root=tmp_path)
    assert len(set(params["reference_urls"])) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "value",
    [
        "missing.png",
        "/api/plugins/happyhorse-video/uploads/../outside.png",
        "ftp://example.com/file",
    ],
)
async def test_invalid_local_inputs_fail_before_upload(tmp_path, value):
    uploader = Mock()
    with pytest.raises(ValueError):
        await prepare_media_inputs(
            {"first_frame_url": value}, uploader=uploader, uploads_root=tmp_path
        )
    assert uploader.mock_calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error", [OssNotConfigured("missing credentials"), OssUploadError("permission denied")]
)
async def test_upload_failure_is_not_reported_as_missing_first_frame(tmp_path, error):
    photo = tmp_path / "photo.png"
    photo.write_bytes(b"photo")
    uploader = Mock()
    uploader.upload_file.side_effect = error
    with pytest.raises(type(error), match=str(error)):
        await prepare_media_inputs(
            {"first_frame_url": str(photo)}, uploader=uploader, uploads_root=tmp_path
        )
