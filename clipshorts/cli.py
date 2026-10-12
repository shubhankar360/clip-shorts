"""`cs` command line. Every command prints JSON on stdout so Claude (or you) can read it."""
import argparse
import json
import sys

LAYOUTS = ["blur", "zoom", "crop", "face"]


def _out(obj):
    print(json.dumps(obj, indent=2))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cs", description="Clip long videos into scored, captioned Shorts.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("clip", help="make Shorts from a URL or file")
    p.add_argument("src", nargs="+")
    p.add_argument("--n", type=int, default=8)
    p.add_argument("--min-score", type=float, default=60)
    p.add_argument("--layout", choices=LAYOUTS, default="blur",
                   help="blur (default) | zoom (podcasts) | crop (centered) | face (follows the speaker)")
    p.add_argument("--model", default="small", help="whisper size: tiny/base/small/medium")
    p.add_argument("--min-len", type=int, default=20)
    p.add_argument("--max-len", type=int, default=58)

    p = sub.add_parser("rerender", help="re-render one clip with a hook banner / new layout")
    p.add_argument("folder")
    p.add_argument("clip_id", type=int)
    p.add_argument("--hook", default="")
    p.add_argument("--layout", choices=LAYOUTS)

    sub.add_parser("reports", help="list all clip reports")

    p = sub.add_parser("upload", help="upload/schedule a Short to YouTube")
    p.add_argument("path")
    p.add_argument("--title", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--tags", default="")
    p.add_argument("--publish-at")
    p.add_argument("--campaign", default="")

    p = sub.add_parser("log", help="record views for a posted clip")
    p.add_argument("url")
    p.add_argument("views", type=int)
    p.add_argument("--campaign", default="")
    p.add_argument("--note", default="")

    sub.add_parser("stats", help="views and estimated earnings per campaign")
    p = sub.add_parser("slots", help="next posting times (UTC, for --publish-at)")
    p.add_argument("--n", type=int, default=4)
    sub.add_parser("doctor", help="check setup")
    sub.add_parser("mcp", help="run the MCP server (stdio)")

    a = ap.parse_args(argv)
    log = lambda msg: print(msg, file=sys.stderr, flush=True)  # noqa: E731

    if a.cmd == "clip":
        from .pipeline import make_clips
        _out([make_clips(s, a.n, a.min_score, a.layout, a.model, a.min_len, a.max_len, log=log) for s in a.src])
    elif a.cmd == "rerender":
        from .pipeline import rerender
        _out(rerender(a.folder, a.clip_id, a.hook, a.layout))
    elif a.cmd == "reports":
        from .pipeline import list_reports
        _out(list_reports())
    elif a.cmd == "upload":
        from . import tracker, youtube
        url = youtube.upload(a.path, a.title, a.description,
                             [t.strip() for t in a.tags.split(",") if t.strip()], a.publish_at)
        tracker.log(url, 0, a.campaign, clip=a.path, note="uploaded")
        _out({"url": url, "scheduled_for": a.publish_at})
    elif a.cmd == "log":
        from .tracker import log as track
        _out(track(a.url, a.views, a.campaign, note=a.note))
    elif a.cmd == "stats":
        from .tracker import stats
        _out(stats())
    elif a.cmd == "slots":
        from .youtube import next_slots
        _out(next_slots(a.n))
    elif a.cmd == "doctor":
        from .doctor import doctor
        _out(doctor())
    elif a.cmd == "mcp":
        from .server import mcp
        mcp.run()
