# Changelog · happyhorse-video / 快乐马工作室

All notable changes to this plugin are recorded here. The plugin follows
[SemVer](https://semver.org/) and the project's standard
"date-versioned changelog" convention.

## [1.2.0] — 2026-09-19

### Added

- Generate text-to-video with Wan 3.0, Wan 3.0 Prime, HappyHorse 1.1,
  and Wan 2.7, including its dated model variants.
- Browse image and video inspiration galleries, preview videos on hover,
  and reuse a sample's prompt and a supported aspect ratio in the creation form.
- Choose image dimensions and aspect ratios supported by the selected model.

### Fixed

- Local first-frame images are uploaded to OSS before video generation;
  upload failures are reported before a task is created.
- Image task progress now describes image generation instead of video generation.
- Video output checks and cost estimates respect the selected model's capabilities.

## [1.1.0] — 2026-05-17

### Added

- **`hh_storyboard_decompose` LLM tool** — wraps the existing
  `POST /storyboard/decompose` REST handler. Takes `story` /
  `total_duration` / `segment_duration` / `aspect_ratio` / `style`
  and synchronously returns `{ok, task_id, segments: [...], ...}` so
  an org agent can pipe its output straight into `hh_long_video_create`.
  Each segment carries `prompt` / `duration` / `key_frame_description` /
  `end_frame_description` / `transition_to_next` (`cut` / `crossfade` /
  `ai_extend`) / `camera_notes`. Shares the Brain serialisation lock
  with the REST route.
- **`hh_video_concat` LLM tool** — wraps `POST /long-video/concat`.
  Takes `task_ids` (≥2 already-downloaded video tasks), `transition`
  (`none` / `cut` / `crossfade` / `fade` / `xfade` / `dissolve` /
  `ai_extend` — all aliases normalise to `none` or `crossfade`),
  `fade_duration`, and optional `output_name`. Produces a real
  `long_video_concat` task row, publishes the merged MP4 as an
  Asset Bus entry, and returns `{ok, task_id, output_path,
  preview_url, asset_ids, transition, segments_used}`.
- Both new tools are declared in `plugin.json#provides.tools` and
  classified in `tool_classes` (`network_out` / `exec_low_risk`).

### Changed

- Updated the upstream default org template **`aigc-video-studio`**
  ([`src/openakita/orgs/templates.py`](../../src/openakita/orgs/templates.py))
  to a 7-node HappyHorse-only studio (producer + screenwriter +
  art-director + 4 workbench leaves: image / video / digital-human /
  long-video post). All four workbench nodes share
  `plugin_origin.plugin_id = "happyhorse-video"` but expose
  category-specific `external_tools` subsets.
  - **Hierarchy single-parent invariant**: `art-director` is the only
    hierarchy parent of all four workbench leaves. The producer
    delegates to screenwriter/art-director and the art-director
    handles workbench dispatch (including the long-video concat
    step) — this is enforced by
    `test_art_director_owns_all_workbench_nodes` and required so that
    `org_submit_deliverable`'s `get_parent` fallback always routes
    workbench results back to the art-director (the actual delegator)
    instead of bypassing them to producer.
- Plugin entry-point docstring bumped from "20 LLM tools" to **22**
  to account for the two new wrappers.
- `hh_storyboard_decompose` / `hh_video_concat` success payloads now
  carry the full workbench-protocol field set (`ok / task_id / status
  / mode / model_id / video_url / video_path / last_frame_url /
  last_frame_path / image_urls / local_paths / asset_ids`) in
  addition to their tool-specific fields (`segments`, `output_path`,
  `preview_url`, `transition`, ...) so `OrgRuntime
  ._record_plugin_asset_output` can pick up the merged MP4 by either
  `video_url` or `asset_ids` without bespoke handling.

### Removed

- The legacy companion org template **`happyhorse-video-studio`**
  ("百炼 AIGC 视频创作工作室", which paired `tongyi-image` with
  `happyhorse-video`) has been folded into the new default
  `aigc-video-studio`. Users with an existing
  `data/org_templates/happyhorse-video-studio.json` should delete
  that JSON manually — `ensure_builtin_templates` only seeds missing
  files and will not auto-remove orphaned templates.

### Migration

- Old environments may also have a stale
  `data/org_templates/aigc-video-studio.json` left over from the
  previous Seedance-based default. Delete both JSONs and restart the
  server to pick up the new defaults; in-flight orgs forked from
  either template keep working but their workbench nodes will show
  `deprecated_tools` warnings until you re-bind them.

## [1.0.0] — 2026-05-15

Initial release. Bailian-powered unified video studio merging the spirit
of [`plugins/seedance-video`](../seedance-video/) (storyboard long-video
pipeline, prompt optimizer, ffmpeg concat) and
[`plugins/avatar-studio`](../avatar-studio/) (digital-human modes, OSS
uploader, CosyVoice / Edge-TTS) on a single backend (Aliyun DashScope /
Bailian).

### Added

- **HappyHorse 1.0 family** as the default video engine across `t2v` /
  `i2v` / `r2v` / `video_edit` modes (native audio-video sync, 7-language
  lip-sync, 720P/1080P, 3-15s).
- **Wan 2.6 / 2.7 fallback** registered as alternative model picks per
  mode: `wan2.6-t2v`, `wan2.6-i2v` / `wan2.6-i2v-flash`,
  `wan2.6-r2v` / `wan2.6-r2v-flash`, and `wan2.7-i2v` (multimodal:
  first-frame / first-and-last-frame / video-continuation).
- **5 digital-human modes** ported from avatar-studio: `photo_speak`
  (`wan2.2-s2v`), `video_relip` (`videoretalk`), `video_reface`
  (`wan2.2-animate-mix`), `pose_drive` (`wan2.2-animate-move`),
  `avatar_compose` (`wan2.7-image` → s2v).
- **Long-video storyboard pipeline** ported from seedance-video:
  AI-driven shot decomposition, serial / parallel chain generation,
  ffmpeg concat with optional crossfade.
- **Unified TTS**: CosyVoice-v2 (12 system voices + custom clones) and
  Edge-TTS (free, 12 Chinese voices).
- **Per-mode model dropdown** in CreateTab + `default_model_<mode>` in
  Settings. Submitted task without explicit `model` falls back to the
  per-mode default.
- **OSS-backed input pipeline** (signed HTTPS URLs, 6h TTL).
- **OrgRuntime workbench protocol**: every `hh_*` tool returns
  `video_url` / `video_path` / `last_frame_url` / `local_paths` /
  `asset_ids`, and every input schema accepts `from_asset_ids` so the
  node can consume upstream image-workbench output without rehosting.
- **Black-themed React/Babel single-file UI** (7 tabs: Create / Tasks /
  Storyboard / Voices / Figures / Prompt / Settings) with Iconify SVG
  icons inlined into `_assets/icons.js`.
- **Org template** `happyhorse-video-studio` registered in
  [`src/openakita/orgs/templates.py`](../../src/openakita/orgs/templates.py)
  for end-to-end "Bailian AIGC video studio" orchestration. *(Removed
  in 1.1.0 — see the 1.1.0 entry above for the replacement.)*
- Companion test plan doc
  [`docs/happyhorse-video-test-plan.md`](../../docs/happyhorse-video-test-plan.md).

### Notes

- HappyHorse 1.0 rejects the legacy params `with_audio` / `size` /
  `quality` / `fps` / `audio`; the client validates and surfaces a
  clear `error_kind: client` instead of letting DashScope late-fail.
- Wan 2.6 uses the legacy protocol (`size: "1280*720"`); Wan 2.7-i2v
  and HappyHorse use the new async protocol (`resolution: "720P"`).
  Both routed through `happyhorse_dashscope_client.py` via the
  `endpoint_family` / `protocol_version` registry fields.
- DashScope async per-key concurrency cap = 1; submits are serialised
  by an internal `asyncio.Semaphore(1)`.
