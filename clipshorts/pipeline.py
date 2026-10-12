"""clip: source -> transcript -> scored windows -> rendered Shorts + report.json."""
import json
from pathlib import Path

from . import config
from .media import fetch, loudness
from .render import render
from .score import candidates, pick, verdict, words_between
from .transcribe import transcribe


def make_clips(src: str, n: int = 8, min_score: float = 60, layout: str = "blur",
               model: str = "small", min_len: int = 20, max_len: int = 58, log=print) -> dict:
    config.ensure()
    log("1/4 fetching source…")
    video, workdir, meta = fetch(src, config.CLIPS)
    log(f"2/4 transcribing with whisper-{model} (cached after first run)…")
    words, sents = transcribe(video, workdir, model)
    if not words:
        raise RuntimeError("No speech detected; this tool needs talking-head/podcast style content.")
    log("3/4 scoring windows…")
    rms = loudness(video, workdir)
    ranked = candidates(words, sents, rms, min_len, max_len)
    chosen = [c for c in pick(ranked, n) if c["score"] >= min_score]

    clips = []
    for i, c in enumerate(chosen, 1):
        log(f"4/4 rendering clip {i}/{len(chosen)} (score {c['score']})…")
        out = render(video, c["words"], c["start"], c["end"], workdir / f"clip_{i:02d}.mp4", layout)
        clips.append(dict(id=i, file=str(out), start=c["start"], end=c["end"],
                          duration=round(c["end"] - c["start"], 1), virality_score=c["score"],
                          verdict=verdict(c["score"]), breakdown=c["parts"],
                          opening_line=c["words"] and " ".join(w["text"] for w in c["words"][:14]),
                          transcript=c["text"], hook=""))
    report = dict(meta, folder=workdir.name, path=str(workdir), source=str(video), model=model, layout=layout,
                  candidates_considered=len(ranked), clips=clips)
    (workdir / "report.json").write_text(json.dumps(report, indent=2))
    return report


def rerender(folder: str, clip_id: int, hook: str = "", layout: str | None = None) -> dict:
    """Re-render one clip, e.g. with a hook banner or a different layout. Reuses all caches."""
    workdir = config.CLIPS / folder
    report = json.loads((workdir / "report.json").read_text())
    clip = next(c for c in report["clips"] if c["id"] == clip_id)
    words = json.loads((workdir / f"transcript-{report['model']}.json").read_text())["words"]
    render(Path(report["source"]), words_between(words, clip["start"], clip["end"]),
           clip["start"], clip["end"], Path(clip["file"]), layout or report["layout"], hook)
    clip["hook"] = hook
    (workdir / "report.json").write_text(json.dumps(report, indent=2))
    return clip


def list_reports() -> list:
    return [json.loads(p.read_text()) for p in sorted(config.CLIPS.glob("*/report.json"))]
