#!/usr/bin/env bash
# One-command install: deps + `cs` CLI + Claude Code skills + MCP server (user scope).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CS="${CLIP_SHORTS_STATE:-$HOME/.clip-shorts}/bin/cs"

chmod +x "$ROOT/scripts/cs" "$ROOT/scripts/setup.sh"
"$ROOT/scripts/setup.sh"

mkdir -p "$HOME/.claude/skills"
for dir in "$ROOT"/skills/*/; do
  dir="${dir%/}"; target="$HOME/.claude/skills/$(basename "$dir")"
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "[clip-shorts] skipped $target (a non-link folder already exists)"; continue
  fi
  ln -sfn "$dir" "$target" && echo "[clip-shorts] skill linked: /$(basename "$dir")"
done

if command -v claude >/dev/null 2>&1; then
  claude mcp remove clipper -s user >/dev/null 2>&1 || true
  claude mcp add -s user clipper -- "$CS" mcp && echo "[clip-shorts] MCP server 'clipper' registered"
else
  echo "[clip-shorts] add this MCP server to your client: command=$CS args=[\"mcp\"]"
fi

"$CS" doctor
echo
echo "Done. Restart Claude Code, then try:  /clip-shorts <youtube-url>"
