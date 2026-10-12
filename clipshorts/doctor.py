"""Setup health check."""
import importlib.util
import subprocess
import sys

from . import config


def doctor() -> dict:
    checks = {"python>=3.10": sys.version_info >= (3, 10)}
    for mod in ("yt_dlp", "faster_whisper", "numpy", "imageio_ffmpeg", "mcp", "googleapiclient"):
        checks[mod] = importlib.util.find_spec(mod) is not None
    try:
        from .media import ffmpeg_exe
        filters = subprocess.run([ffmpeg_exe(), "-hide_banner", "-filters"], capture_output=True, text=True).stdout
        checks["ffmpeg+libass"] = " subtitles " in filters
    except Exception:
        checks["ffmpeg+libass"] = False
    try:  # face/zoom layouts need the Haar cascade bundled with opencv-python 4.x
        import cv2
        checks["opencv+haar"] = not cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml").empty()
    except Exception:
        checks["opencv+haar"] = False
    checks["youtube_client_secret"] = (config.SECRETS / "client_secret.json").exists()
    checks["youtube_signed_in"] = (config.SECRETS / "token.json").exists()
    required = [k for k in checks if not k.startswith("youtube")]
    return {"ready_to_clip": all(checks[k] for k in required),
            "ready_to_upload": checks["youtube_client_secret"],
            "data_folder": str(config.HOME), "checks": checks}
