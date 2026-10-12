"""End-to-end check: synthetic talk video -> `python -m clipshorts clip` -> 1080x1920 Shorts, plus
face tracking on a drawn face and an MCP stdio handshake. Needs requirements.txt installed and
espeak-ng (Linux) or `say` (macOS). Downloads the whisper model on first run.

    python tests/e2e.py [--model tiny] [--keep DIR] [--screenshot docs/screenshot.png]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from clipshorts.media import ffmpeg, ffmpeg_exe, video_size  # noqa: E402

SCRIPT = [
    "Why does nobody talk about this? I lost a million dollars in one single day. "
    "It was the most insane mistake of my entire life.",
    "Here is the secret that nobody tells you. Most people quit right before it works. "
    "They get scared, they panic, and they sell everything.",
    "Imagine waking up broke after building something for ten years. That was me. "
    "I was terrified, and honestly, I hated myself.",
    "Then I learned the one rule that changed everything. Never risk money you cannot afford to lose. "
    "Write that down.",
    "Three years later, I had made it all back, and more. So stop waiting for the perfect moment. Start today.",
    "Here is the crazy part. The biggest wins of my career came from the worst failures. "
    "Every single one of them. Remember that the next time you fail.",
]
HOOK = "I LOST A MILLION IN 1 DAY"


def say(text: str, out: Path) -> None:
    if shutil.which("espeak-ng"):
        subprocess.run(["espeak-ng", "-s", "160", "-w", str(out), text], check=True)
    elif shutil.which("say"):
        subprocess.run(["say", "-r", "165", "--data-format=LEI16@22050", "-o", str(out), text], check=True)
    else:
        sys.exit("need espeak-ng (apt-get install espeak-ng) or macOS `say` to synthesize speech")


def speech(out: Path, pause: float = 1.2) -> None:
    """One wav of all paragraphs with a pause between them (a topic shift for the scorer)."""
    params, frames = None, b""
    for i, text in enumerate(SCRIPT):
        part = out.with_name(f"part{i}.wav")
        say(text, part)
        with wave.open(str(part)) as w:
            params = params or w.getparams()
            frames += w.readframes(w.getnframes()) + b"\0" * int(pause * w.getframerate()) * w.getsampwidth()
    with wave.open(str(out), "wb") as w:
        w.setparams(params)
        w.writeframes(frames)


def face_video(out: Path, seconds: int = 6) -> None:
    """A drawn face on the left for the first half, then on the right (a camera cut)."""
    import cv2
    import numpy as np

    def frame(cx):
        img = np.full((720, 1280, 3), 110, np.uint8)
        s, cy = 480, 360
        cv2.ellipse(img, (cx, cy), (int(s * .42), int(s * .55)), 0, 0, 360, (200, 200, 200), -1)
        for d in (-1, 1):
            cv2.ellipse(img, (cx + d * int(s * .17), cy - int(s * .12)), (int(s * .09), int(s * .05)),
                        0, 0, 360, (40, 40, 40), -1)
            cv2.line(img, (cx + d * int(s * .08), cy - int(s * .24)), (cx + d * int(s * .27), cy - int(s * .25)),
                     (60, 60, 60), 16)
        cv2.line(img, (cx, cy - int(s * .08)), (cx, cy + int(s * .12)), (150, 150, 150), 12)
        cv2.ellipse(img, (cx, cy + int(s * .27)), (int(s * .16), int(s * .05)), 0, 0, 360, (70, 70, 70), -1)
        return img.tobytes()

    left, right = frame(320), frame(960)
    proc = subprocess.Popen([ffmpeg_exe(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                             "-s", "1280x720", "-r", "30", "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                             str(out)], stdin=subprocess.PIPE)
    for i in range(seconds * 30):
        proc.stdin.write(left if i < seconds * 15 else right)
    proc.stdin.close()
    assert proc.wait() == 0, "ffmpeg failed to encode the face video"


def mcp_tools(env) -> list:
    """initialize -> notifications/initialized -> tools/list over stdio; returns tool names."""
    proc = subprocess.Popen([sys.executable, "-m", "clipshorts", "mcp"], cwd=ROOT, env=env, text=True,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    timer = threading.Timer(120, proc.kill)
    timer.start()

    def send(msg):
        proc.stdin.write(json.dumps(dict(jsonrpc="2.0", **msg)) + "\n")
        proc.stdin.flush()

    def reply(rid):
        for line in proc.stdout:
            msg = json.loads(line)
            if msg.get("id") == rid:
                assert "result" in msg, msg
                return msg["result"]
        raise AssertionError("MCP server exited before replying")

    try:
        send(dict(id=1, method="initialize", params=dict(
            protocolVersion="2025-06-18", capabilities={}, clientInfo=dict(name="e2e", version="0"))))
        info = reply(1)
        send(dict(method="notifications/initialized"))
        send(dict(id=2, method="tools/list"))
        tools = [t["name"] for t in reply(2)["tools"]]
        print(f"   mcp server {info['serverInfo']['name']} (protocol {info['protocolVersion']}): {tools}")
        return tools
    finally:
        timer.cancel()
        proc.kill()
        proc.wait()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model", default="tiny")
    ap.add_argument("--keep", help="work in this folder and keep it (default: a temp folder, deleted)")
    ap.add_argument("--screenshot", help="also save a 540px-wide frame of clip 1 with a hook banner here")
    a = ap.parse_args()
    tmp = Path(a.keep or tempfile.mkdtemp(prefix="clipshorts-e2e-")).resolve()
    tmp.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, CLIP_SHORTS_HOME=str(tmp / "home"), PYTHONPATH=str(ROOT))
    cs = [sys.executable, "-m", "clipshorts"]
    try:
        print("1/5 doctor")
        checks = json.loads(subprocess.run(cs + ["doctor"], cwd=ROOT, env=env, check=True,
                                           capture_output=True, text=True).stdout)
        print("   ", checks["checks"])
        assert checks["ready_to_clip"], "doctor says not ready to clip"

        print("2/5 synthesizing a ~60s talk video")
        wav, video = tmp / "speech.wav", tmp / "talk.mp4"
        speech(wav)
        ffmpeg("-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30", "-i", wav, "-shortest",
               "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", video)
        print(f"    {video} {video_size(video)}")

        print(f"3/5 clipping with whisper-{a.model}")
        run = subprocess.run(cs + ["clip", str(video), "--model", a.model, "--n", "2", "--min-score", "0"],
                             cwd=ROOT, env=env, check=True, stdout=subprocess.PIPE, text=True)
        report = json.loads(run.stdout)[0]
        clips = report["clips"]
        assert clips, f"no clips in report ({report['candidates_considered']} candidates)"
        for c in clips:
            size = video_size(c["file"])
            print(f"    clip {c['id']}: {c['duration']}s score {c['virality_score']} {size} {c['opening_line']!r}")
            assert Path(c["file"]).exists() and size == (1080, 1920), c["file"]

        print("4/5 face tracking + face layout")
        from clipshorts.reframe import track
        from clipshorts.render import render
        faces = tmp / "face.mp4"
        face_video(faces)
        keys = track(faces, 0, 6)
        print(f"    keyframes {keys}")
        assert keys and abs(keys[0][1] - 0.25) < 0.05 and abs(keys[-1][1] - 0.75) < 0.05, keys
        out = render(faces, [], 0, 6, tmp / "face_clip.mp4", "face", keys=keys)
        assert video_size(out) == (1080, 1920)

        print("5/5 MCP stdio handshake")
        assert "make_clips" in mcp_tools(env)

        if a.screenshot:
            subprocess.run(cs + ["rerender", report["folder"], "1", "--hook", HOOK],
                           cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL)
            # grab a frame mid-word (~3s in) so a caption is on screen with one word highlighted
            words = json.loads((Path(report["path"]) / f"transcript-{a.model}.json").read_text())["words"]
            w = next(w for w in words if w["start"] >= clips[0]["start"] + 3)
            shot = Path(a.screenshot).resolve()
            ffmpeg("-ss", f"{(w['start'] + w['end']) / 2 - clips[0]['start']:.2f}", "-i", clips[0]["file"],
                   "-frames:v", 1, "-vf",
                   "scale=540:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse",
                   "-update", 1, shot)
            print(f"    screenshot -> {shot} ({shot.stat().st_size // 1024} KB)")
        print("e2e OK")
    finally:
        if not a.keep:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
