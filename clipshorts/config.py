"""Paths and defaults. Everything user-facing lives in ~/ClipShorts (override with CLIP_SHORTS_HOME)."""
import json
import os
from pathlib import Path

HOME = Path(os.environ.get("CLIP_SHORTS_HOME", "~/ClipShorts")).expanduser()
CLIPS = HOME / "clips"
TRACKER = HOME / "tracker.csv"
SECRETS = HOME / "secrets"
CAMPAIGNS = HOME / "campaigns.json"  # {"campaign name": cpm_usd, ...}
DEFAULT_CPM = float(os.environ.get("CLIP_SHORTS_CPM", "1.0"))
POST_HOURS = (9, 13, 18, 21)


def ensure() -> None:
    for d in (CLIPS, SECRETS):
        d.mkdir(parents=True, exist_ok=True)


def campaign_cpms() -> dict:
    return json.loads(CAMPAIGNS.read_text()) if CAMPAIGNS.exists() else {}
