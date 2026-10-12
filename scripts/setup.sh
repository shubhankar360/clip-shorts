#!/usr/bin/env bash
# Creates ~/.clip-shorts/venv with all dependencies (ffmpeg is bundled — no Homebrew needed).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE="${CLIP_SHORTS_STATE:-$HOME/.clip-shorts}"
VENV="$STATE/venv"
log() { echo "[clip-shorts] $*" >&2; }

pick_python() {
  for c in python3.13 python3.12 python3.11 python3.10 python3 \
           /opt/homebrew/bin/python3 /usr/local/bin/python3 /opt/anaconda3/bin/python3 \
           "$HOME/anaconda3/bin/python3" "$HOME/miniconda3/bin/python3" \
           /Library/Frameworks/Python.framework/Versions/3.1[0-9]/bin/python3; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
      echo "$c"; return 0
    fi
  done
  return 1
}

PY="$(pick_python)" || { log "Python 3.10+ is required: https://www.python.org/downloads/"; exit 1; }
[ -x "$VENV/bin/python" ] || { log "creating virtualenv ($PY) at $VENV"; "$PY" -m venv "$VENV"; }
log "installing dependencies (first run downloads ~300MB, takes a few minutes)…"
"$VENV/bin/python" -m pip install -q --upgrade pip 1>&2
"$VENV/bin/python" -m pip install -q -r "$ROOT/requirements.txt" 1>&2
rm -f "$VENV"/.req-*
touch "$VENV/.req-$(cksum < "$ROOT/requirements.txt" | cut -d' ' -f1)"
mkdir -p "$STATE/bin"
ln -sfn "$ROOT/scripts/cs" "$STATE/bin/cs"
log "ready → CLI: $STATE/bin/cs   data: ${CLIP_SHORTS_HOME:-$HOME/ClipShorts}"
