# Contributing to clip-shorts

Thanks for helping. Bug reports, scoring ideas, and small focused PRs are all welcome.

## Set up
```bash
git clone https://github.com/shubhankar360/clip-shorts.git && cd clip-shorts
./scripts/setup.sh                       # venv at ~/.clip-shorts/venv with every dependency
~/.clip-shorts/venv/bin/python -m clipshorts doctor
```
`scripts/cs` runs the CLI from your checkout, so your edits apply immediately.

## Test
```bash
python3 -m unittest discover -s tests -v          # unit tests: stdlib only, under a second
~/.clip-shorts/venv/bin/python tests/e2e.py        # end-to-end: a few minutes
```
The end-to-end test needs `espeak-ng` on Linux (`sudo apt-get install espeak-ng`) or macOS's built-in `say`. It downloads whisper-tiny on its first run. Add `--keep /tmp/e2e` to look at the clips it makes. CI runs both tests on every push and PR.

## House style
- **Free and offline by default.** Anything that calls a paid or online service (like `--rerank llm`) is opt-in and falls back gracefully when it isn't configured.
- **Compact, stdlib-first modules.** Import heavy dependencies (faster-whisper, OpenCV, numpy, anthropic) inside the function that needs them, so `cs --help`, the unit tests, and the MCP server start fast.
- **Pure functions for the logic you'd want to tune** (scoring, smoothing, captions), with unit tests that don't need media files.
- **JSON on stdout, progress on stderr** for every CLI command, so Claude and scripts can read the output.
- Python 3.10+, and both mcp 1.x and 2.x (see the import fallback in `clipshorts/server.py`).
- Keep the install working with `pip install --prefer-binary` on Intel Macs. Some of the newest wheels skip macOS x86_64.

## Pull requests
- One topic per PR, with tests for new logic. Add a line to `CHANGELOG.md` under the next version.
- Never commit media (clips, sources, `.wav`), OAuth secrets, tokens, or `tracker.csv`. `.gitignore` covers the usual paths. The one exception is a small docs image like `docs/screenshot.png`.
- Clip only content you have permission to use, including in test fixtures and screenshots. `tests/e2e.py` synthesizes its own video for this reason.

## Releases
The maintainer bumps the version in `clipshorts/__init__.py` and `.claude-plugin/plugin.json`, dates the `CHANGELOG.md` entry, and tags the release.
