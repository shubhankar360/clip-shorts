"""Render a 1080x1920 Short with burned-in captions."""
from pathlib import Path

from .captions import build_ass
from .media import ffmpeg
from .reframe import x_expr

# {x} is the crop's left edge: centered, or an expression that follows the face track
LAYOUTS = {
    # full frame over a blurred fill: safest for any source
    "blur": ("[0:v]split[a][b];"
             "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];"
             "[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"),
    # tighter crop over blur, following the face when one is found: bigger faces for podcasts/interviews
    "zoom": ("[0:v]split[a][b];"
             "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];"
             "[b]scale=1440:-2,crop=1080:ih:{x}:0[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"),
    # full-bleed center crop: single speaker centered in frame
    "crop": "[0:v]scale=-2:1920,crop=1080:1920",
    # full-bleed crop that follows the speaker's face (centered if none is found)
    "face": "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:{x}:(ih-oh)/2",
}
FACE_LAYOUTS = {"face", "zoom"}


def render(video: Path, words, start: float, end: float, out: Path, layout: str = "blur", hook: str = "",
           keys=None) -> Path:
    """keys: face keyframes [(t, center_x)] from reframe.track() for face/zoom; None crops the center."""
    if layout not in LAYOUTS:
        raise ValueError(f"layout must be one of {sorted(LAYOUTS)}")
    ass = out.with_suffix(".ass")
    ass.write_text(build_ass(words, start, end - start, hook), encoding="utf-8")
    x = f"'{x_expr(keys)}'" if keys else "(iw-ow)/2"
    graph = f"{LAYOUTS[layout].format(x=x)},subtitles={ass.name}[v]"
    # cwd + relative .ass name sidesteps ffmpeg filter escaping of paths with spaces
    ffmpeg("-ss", f"{start:.2f}", "-to", f"{end:.2f}", "-i", Path(video).resolve(),
           "-filter_complex", graph, "-map", "[v]", "-map", "0:a?",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", 20, "-r", 30,
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out.name,
           cwd=out.parent)
    return out
