# Changelog

This file follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [semantic versioning](https://semver.org/).

## [0.2.0] - Unreleased

### Added
- `face` layout: a full-bleed 1080x1920 crop that follows the speaker's face (OpenCV's bundled Haar cascade, no model download). Small moves pan smoothly, camera cuts jump, and clips with no face fall back to a centered crop.
- `zoom` now centers its foreground crop on the face when one is found.
- `face_track` per clip in `report.json`, reused when you re-render.
- End-to-end test (`tests/e2e.py`) and a CI job. The test synthesizes a talk video, clips it with whisper-tiny, checks the 1080x1920 output, tracks a drawn face, and runs an MCP stdio handshake.
- README badges and screenshot, `CONTRIBUTING.md`, and issue templates.
- `suggested_hook` (6 words or fewer) and `suggested_title` (60 characters or fewer, ending in `#shorts`) for every clip in `report.json`, taken from its opening line. The `/clip-shorts` skill starts its polish step from them.
- `--rerank llm` (CLI) and `rerank="llm"` (MCP `make_clips`), off by default. With `ANTHROPIC_API_KEY` set, Claude (`claude-sonnet-5-5`) picks the N most self-contained, viral clips from the top 3N candidates and writes their hooks and titles. It falls back to the heuristic order, recording `rerank_error`, when the key, the SDK, or the API isn't available. `anthropic` stays optional.

### Changed
- `cs doctor` checks that OpenCV's face cascade loads.
- Scoring adds a **standalone** signal (0-10). Starting after a pause of more than 0.8s (a topic shift) earns points, and opening on a dangling "he", "she", "they", "it", "that", or "this one" costs points. Emotion (20 to 15) and length (15 to 10) were rebalanced to make room, so totals stay 0-100. Scores from 0.1.0 reports aren't directly comparable.
- `cs rerender` remembers the layout you last re-rendered a clip with.
- `blur` and `zoom` render about 3x faster. Their background fill is now blurred at 270x480 and scaled up instead of blurred at 1080x1920, and it looks the same. A 34.6s clip re-renders in 17s instead of 55s on an Intel MacBook Air.
- Unit tests run on Python 3.10 and 3.12 in CI.

### Dependencies
- Added `opencv-python-headless>=4.8,<5`. OpenCV 5.0 removed `CascadeClassifier` and the bundled cascades.

## [0.1.0] - 2026-10-12

### Added
- First release: local auto-clipper (yt-dlp, faster-whisper, bundled ffmpeg) with a 0-100 virality score, karaoke captions, hook banners, and `blur`/`zoom`/`crop` layouts.
- YouTube Data API upload and scheduling, a view tracker with earnings estimates, the `cs` CLI, the `clipper` MCP server, the `/clip-shorts` and `/clip-stats` skills, and a Claude Code plugin manifest.
- Intel Mac install fixes (`pip --prefer-binary`), support for both mcp 1.x and 2.x, and caption placement fixes.

[0.2.0]: https://github.com/shubhankar360/clip-shorts/compare/6155195...main
[0.1.0]: https://github.com/shubhankar360/clip-shorts/commit/6155195
