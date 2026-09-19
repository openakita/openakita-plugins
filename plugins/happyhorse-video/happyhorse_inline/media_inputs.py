"""Convert plugin-local media inputs into URLs consumable by DashScope."""

from __future__ import annotations

import asyncio
from pathlib import Path
from urllib.parse import unquote, urlsplit
from uuid import uuid4


def normalize_first_frame(mode: str, params: dict) -> None:
    """Canonical fields take precedence over legacy image aliases."""
    if mode not in {"i2v", "i2v_end"}:
        return
    params["first_frame_url"] = (
        params.get("first_frame_url")
        or params.get("first_frame_path")
        or params.get("image_url")
        or params.get("image_path")
        or ""
    )
    # These are aliases in i2v, not additional inputs for the vendor.
    params["image_url"] = ""
    params.pop("image_path", None)


async def prepare_media_inputs(params: dict, *, uploader, uploads_root: Path) -> None:
    """Keep HTTP URLs intact; upload existing local files once per request.

    Only relative preview URLs owned by this plugin map to its upload folder.
    No IM-specific paths, credentials, or APIs are involved.
    """
    fields = (
        "first_frame_url",
        "last_frame_url",
        "source_video_url",
        "video_url",
        "image_url",
        "audio_url",
        "driving_audio_url",
        "reference_urls",
        "image_urls",
        "ref_images_url",
    )
    cache: dict[Path, str] = {}
    pending: list[tuple[str, list[tuple[str, Path | None]], bool]] = []
    preview_prefix = "/api/plugins/happyhorse-video/uploads/"
    root = uploads_root.resolve()
    # Validate every input before uploading anything.
    for field in fields:
        raw = params.get(field)
        if not raw:
            continue
        is_list = isinstance(raw, list)
        resolved = []
        for value in raw if is_list else [raw]:
            value = str(value).strip()
            parsed = urlsplit(value)
            if parsed.scheme.lower() in {"http", "https"}:
                if not parsed.netloc:
                    raise ValueError(f"Invalid media URL for {field}")
                resolved.append((value, None))
                continue
            if value.startswith(preview_prefix):
                relative = unquote(parsed.path[len(preview_prefix) :])
                path = (root / relative).resolve()
                if not path.is_relative_to(root):
                    raise ValueError(f"Media preview path escapes upload directory: {field}")
            elif value.startswith("/api/") and params.get(field.removesuffix("_url") + "_path"):
                # Asset Bus entries may pair a host preview URL with a local source.
                path = Path(params[field.removesuffix("_url") + "_path"]).expanduser().resolve()
            else:
                # Windows drive letters are paths, not URL schemes.
                if parsed.scheme and not (len(parsed.scheme) == 1 and value[1:2] == ":"):
                    raise ValueError(f"Unsupported media URL scheme for {field}: {parsed.scheme}")
                path = Path(value).expanduser().resolve()
            if not path.is_file():
                raise ValueError(f"Local media file not found for {field}: {path}")
            resolved.append((value, path))
        pending.append((field, resolved, is_list))

    for field, resolved, is_list in pending:
        urls = []
        for value, path in resolved:
            if path is not None:
                if path not in cache:
                    key = uploader.build_object_key(
                        scope=f"inputs/{uuid4().hex}", filename=path.name
                    )
                    cache[path] = await asyncio.to_thread(uploader.upload_file, path, key=key)
                value = cache[path]
                if not is_list:
                    params[field.removesuffix("_url") + "_path"] = str(path)
            urls.append(value)
        params[field] = urls if is_list else urls[0]
