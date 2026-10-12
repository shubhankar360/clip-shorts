"""clip: source -> transcript -> scored windows -> rendered Shorts + report.json."""
import json
from pathlib import Path

from . import config
from .media import fetch, loudness
from .reframe import track
from .render import FACE_LAYOUTS, render
from .rerank import choose
from .score import candidates, verdict, words_between
from .transcribe import transcribe


def make_clips(src: str, n: int = 8, min_score: float = 60, layout: str = "blur",
               model: str = "small", min_len: int = 20, max_len: int = 58, rerank: str = "off", log=print) -> dict:
    """rerank="llm" lets Claude pick the final clips and write hooks/titles (needs ANTHROPIC_API_KEY)."""
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
    chosen, reranked = choose(ranked, n, min_score, rerank, meta, log)

    clips = []
    for i, c in enumerate(chosen, 1):
        log(f"4/4 rendering clip {i}/{len(chosen)} (score {c['score']})…")
        out = workdir / f"clip_{i:02d}.mp4"
        clip = dict(id=i, file=str(out), start=c["start"], end=c["end"],
                    duration=round(c["end"] - c["start"], 1), virality_score=c["score"],
                    verdict=verdict(c["score"]), breakdown=c["parts"],
                    opening_line=c["words"] and " ".join(w["text"] for w in c["words"][:14]),
                    transcript=c["text"], hook="", suggested_hook=c["suggested_hook"],
                    suggested_title=c["suggested_title"])
        if "llm_why" in c:
            clip["llm_why"] = c["llm_why"]
        render(video, c["words"], c["start"], c["end"], out, layout, keys=_face_track(video, clip, layout, log))
        clips.append(clip)
    report = dict(meta, folder=workdir.name, path=str(workdir), source=str(video), model=model, layout=layout,
                  **reranked, candidates_considered=len(ranked), clips=clips)
    (workdir / "report.json").write_text(json.dumps(report, indent=2))
    return report


def rerender(folder: str, clip_id: int, hook: str = "", layout: str | None = None) -> dict:
    """Re-render one clip, e.g. with a hook banner or a different layout. Reuses all caches."""
    workdir = config.CLIPS / folder
    report = json.loads((workdir / "report.json").read_text())
    clip = next(c for c in report["clips"] if c["id"] == clip_id)
    words = json.loads((workdir / f"transcript-{report['model']}.json").read_text())["words"]
    layout = layout or clip.get("layout") or report["layout"]
    keys = _face_track(Path(report["source"]), clip, layout)
    render(Path(report["source"]), words_between(words, clip["start"], clip["end"]),
           clip["start"], clip["end"], Path(clip["file"]), layout, hook, keys=keys)
    clip.update(hook=hook, layout=layout)
    (workdir / "report.json").write_text(json.dumps(report, indent=2))
    return clip


def _face_track(video, clip: dict, layout: str, log=lambda *_: None):
    """Face keyframes for face-following layouts, cached on the clip entry as face_track."""
    if layout not in FACE_LAYOUTS:
        return None
    if "face_track" not in clip:
        clip["face_track"] = track(video, clip["start"], clip["end"])
        if not clip["face_track"]:
            log(f"    clip {clip['id']}: no face found, using a centered crop")
    return clip["face_track"]


def list_reports() -> list:
    return [json.loads(p.read_text()) for p in sorted(config.CLIPS.glob("*/report.json"))]
