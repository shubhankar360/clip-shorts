"""View tracking + earnings estimate per campaign (tracker.csv in the data folder)."""
import csv
import datetime as dt

from . import config

FIELDS = ["timestamp", "url", "platform", "campaign", "views", "clip", "note"]


def log(url: str, views: int = 0, campaign: str = "", platform: str = "", clip: str = "", note: str = "") -> dict:
    config.ensure()
    new = not config.TRACKER.exists()
    row = dict(timestamp=dt.datetime.now().isoformat(timespec="minutes"), url=url,
               platform=platform or _platform(url), campaign=campaign, views=int(views), clip=clip, note=note)
    with config.TRACKER.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    return row


def _platform(url: str) -> str:
    for key in ("youtube", "tiktok", "instagram"):
        if key in url:
            return key
    return ""


def stats() -> dict:
    """Latest views per post, grouped by campaign, with estimated earnings (views/1000 * CPM)."""
    if not config.TRACKER.exists():
        return {"posts": 0, "views": 0, "est_earnings_usd": 0, "campaigns": {}, "top_posts": []}
    latest = {}
    with config.TRACKER.open() as f:
        for row in csv.DictReader(f):
            prev = latest.get(row["url"], {})
            row["campaign"] = row["campaign"] or prev.get("campaign", "")
            row["views"] = max(int(row["views"] or 0), int(prev.get("views", 0)))
            latest[row["url"]] = row
    cpms = config.campaign_cpms()
    campaigns = {}
    for r in latest.values():
        name = r["campaign"] or "(none)"
        c = campaigns.setdefault(name, {"posts": 0, "views": 0, "cpm": cpms.get(name, config.DEFAULT_CPM)})
        c["posts"] += 1
        c["views"] += r["views"]
    for c in campaigns.values():
        c["est_earnings_usd"] = round(c["views"] / 1000 * c["cpm"], 2)
        c["avg_views"] = round(c["views"] / c["posts"])
    top = sorted(latest.values(), key=lambda r: r["views"], reverse=True)[:5]
    return {"posts": len(latest), "views": sum(c["views"] for c in campaigns.values()),
            "est_earnings_usd": round(sum(c["est_earnings_usd"] for c in campaigns.values()), 2),
            "campaigns": campaigns,
            "top_posts": [{k: r[k] for k in ("url", "views", "campaign", "clip")} for r in top]}
