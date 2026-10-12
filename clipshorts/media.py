"""Download sources and run ffmpeg (bundled via imageio-ffmpeg, so no Homebrew needed)."""
import json
import re
import shutil
import subprocess
import wave
from functools import lru_cache
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}


@lru_cache(maxsize=1)
def ffmpeg_exe() -> str:
    # Prefer the bundled build: it ships libass, which caption burning needs.
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        found = shutil.which("ffmpeg")
        if not found:
            raise RuntimeError("ffmpeg not found. Run scripts/setup.sh to install dependencies.")
        return found


def ffmpeg(*args, cwd=None) -> None:
    subprocess.run([ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error", *map(str, args)],
                   check=True, cwd=cwd)


def slugify(text: str, limit: int = 60) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-")[:limit].strip("-") or "video"


def fetch(src: str, root: Path):
    """Return (video_path, workdir, meta). Downloads are cached per video id."""
    local = Path(src).expanduser()
    if local.exists():
        workdir = root / slugify(local.stem)
        workdir.mkdir(parents=True, exist_ok=True)
        meta = {"title": local.stem, "uploader": "", "url": ""}
        (workdir / "meta.json").write_text(json.dumps(meta, indent=2))
        return local.resolve(), workdir, meta

    import yt_dlp

    base = {"quiet": True, "no_warnings": True, "noprogress": True, "noplaylist": True,
            "ffmpeg_location": ffmpeg_exe()}
    with yt_dlp.YoutubeDL(base) as ydl:
        info = ydl.extract_info(src, download=False)
    workdir = root / slugify(f"{info.get('id', '')}-{info.get('title', '')}")
    workdir.mkdir(parents=True, exist_ok=True)
    meta = {"title": info.get("title", ""),
            "uploader": info.get("uploader") or info.get("channel") or "",
            "url": info.get("webpage_url", src)}
    (workdir / "meta.json").write_text(json.dumps(meta, indent=2))

    if not _source(workdir):
        opts = {**base, "format": "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height<=1080]+ba/b",
                "merge_output_format": "mp4", "outtmpl": str(workdir / "source.%(ext)s")}
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([src])
    video = _source(workdir)
    if not video:
        raise RuntimeError(f"Download finished but no video file found in {workdir}")
    return video, workdir, meta


def _source(workdir: Path):
    return next((f for f in workdir.glob("source.*") if f.suffix in VIDEO_EXTS), None)


def loudness(video: Path, workdir: Path) -> list:
    """RMS loudness per second (cached)."""
    cache = workdir / "loudness.json"
    if cache.exists():
        return json.loads(cache.read_text())
    import numpy as np

    wav = workdir / "audio.wav"
    ffmpeg("-i", video, "-vn", "-ac", 1, "-ar", 8000, "-f", "wav", wav)
    with wave.open(str(wav)) as f:
        data = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32)
    wav.unlink()
    n = len(data) // 8000
    rms = np.sqrt((data[:n * 8000].reshape(n, 8000) ** 2).mean(axis=1)).round(1).tolist() if n else []
    cache.write_text(json.dumps(rms))
    return rms
