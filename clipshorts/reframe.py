"""Face-following reframe: OpenCV's bundled Haar cascade finds the speaker, ffmpeg's crop follows them.

Only detect() needs OpenCV; the smoothing and expression code is pure stdlib so it is easy to test and tune.
"""
import subprocess
from statistics import median_low

from .media import ffmpeg_exe, video_size

FPS = 3          # face samples per second
WINDOW = 5       # median filter width, in samples
MIN_HITS = 0.2   # need a face in this share of samples, else stay centered
DEAD = 0.05      # ignore moves smaller than this (fraction of the source width)
JUMP = 0.25      # bigger moves are camera cuts: jump instead of pan
PAN = 0.5        # seconds to pan for smaller moves
MAX_KEYS = 40    # keeps the ffmpeg expression small


def pick_face(faces, frame_w, prev=None):
    """Center x (0-1) of the largest face. A near-equal face close to prev wins, so two
    similar-sized faces don't make the crop ping-pong."""
    if not len(faces):
        return None
    found = [((x + w / 2) / frame_w, w * h) for x, y, w, h in faces]
    best = max(found, key=lambda f: f[1])
    if prev is not None:
        near = [f for f in found if abs(f[0] - prev) <= 2 * DEAD and f[1] >= 0.7 * best[1]]
        best = max(near, key=lambda f: f[1]) if near else best
    return best[0]


def detect(video, start: float, end: float, fps: int = FPS, width: int = 640) -> list:
    """[(t, center_x or None)] sampled at fps through the window; t is seconds from start."""
    import cv2
    import numpy as np

    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    sw, sh = video_size(video)
    w, h = width, max(2, round(sh * width / sw / 2) * 2)
    # same input seek as render(), so sample times line up with the crop filter's t
    proc = subprocess.Popen([ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
                             "-ss", f"{start:.2f}", "-to", f"{end:.2f}", "-i", str(video), "-an",
                             "-vf", f"fps={fps},scale={w}:{h}:flags=area,format=gray", "-f", "rawvideo", "-"],
                            stdout=subprocess.PIPE)
    out, prev = [], None
    while len(buf := proc.stdout.read(w * h)) == w * h:
        gray = cv2.equalizeHist(np.frombuffer(buf, np.uint8).reshape(h, w))
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(min(w, h) // 10,) * 2)
        c = pick_face([tuple(map(int, f)) for f in faces], w, prev)
        prev = prev if c is None else c
        out.append((round(len(out) / fps, 3), c))
    proc.stdout.close()
    proc.wait()
    return out


def smooth(samples, window: int = WINDOW, min_hits: float = MIN_HITS) -> list:
    """Hold the last face through gaps (back-filling the start), then median filter.
    Returns [] when faces are too rare to trust."""
    found = [c for _, c in samples if c is not None]
    if not found or len(found) < min_hits * len(samples):
        return []
    held, last = [], found[0]
    for _, c in samples:
        last = last if c is None else c
        held.append(last)
    half = window // 2
    return [(t, median_low(held[max(0, i - half):i + half + 1])) for i, (t, _) in enumerate(samples)]


def keyframes(track, dead: float = DEAD, jump: float = JUMP, pan: float = PAN, fps: int = FPS) -> list:
    """Collapse a smoothed track into [(t, x)] keyframes starting at t=0: hold inside the
    dead zone, pan over `pan` seconds for small moves, and cut (at the sample midpoint) for big ones."""
    if not track:
        return []
    cur = track[0][1]
    keys = [(0.0, round(cur, 4))]
    for t, c in track[1:]:
        move = abs(c - cur)
        if move <= dead:
            continue
        end = t - 0.5 / fps if move > jump else t
        begin = end - (0.04 if move > jump else pan)
        if begin > keys[-1][0]:
            keys.append((round(begin, 3), round(cur, 4)))
        keys.append((round(max(end, keys[-1][0] + 0.01), 3), round(c, 4)))
        cur = c
    return keys


def x_expr(keys) -> str:
    """ffmpeg crop x: the piecewise-linear center track times iw, minus half the crop, kept in frame."""
    expr = f"{keys[-1][1]:.4f}"
    for (t0, c0), (t1, c1) in reversed(list(zip(keys, keys[1:]))):
        seg = f"{c0:.4f}" if c0 == c1 else f"{c0:.4f}+({c1 - c0:.4f})*(t-{t0:.3f})/{t1 - t0:.3f}"
        expr = f"if(between(t,{t0:.3f},{t1:.3f}),{seg},{expr})"
    return f"clip(({expr})*iw-ow/2,0,iw-ow)"


def track(video, start: float, end: float):
    """Face keyframes for a clip window, or None (no face, or OpenCV missing) for a centered crop."""
    try:
        samples = detect(video, start, end)
    except ImportError:
        return None
    smoothed, dead = smooth(samples), DEAD
    keys = keyframes(smoothed, dead)
    while len(keys) > MAX_KEYS:
        dead *= 1.5
        keys = keyframes(smoothed, dead)
    return keys or None
