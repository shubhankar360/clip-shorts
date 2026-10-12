"""Karaoke-style ASS captions (current word highlighted) plus an optional hook banner on top."""

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Arial Black,86,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,7,3,2,70,70,500,1
Style: Hook,Arial Black,64,&H00000000,&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,1,0,0,0,100,100,0,0,3,18,0,8,90,90,230,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
HIGHLIGHT = r"{\c&H00FFFF&}"  # yellow (ASS is BGR)
RESET = r"{\c&HFFFFFF&}"


def ass_time(t: float) -> str:
    t = max(t, 0.0)
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def clean(text: str) -> str:
    return text.replace("{", "").replace("}", "").replace("\\", "").upper()


def chunk_words(words, size=3):
    """Groups of <= size words, breaking early after punctuation or long pauses."""
    chunk = []
    for i, w in enumerate(words):
        chunk.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        pause = nxt is not None and nxt["start"] - w["end"] > 0.6
        if len(chunk) == size or w["text"].endswith((".", "!", "?", ",")) or pause or nxt is None:
            yield chunk
            chunk = []


def build_ass(words, offset: float, duration: float, hook: str = "") -> str:
    lines = []
    if hook:
        lines.append(f"Dialogue: 1,{ass_time(0)},{ass_time(duration)},Hook,,0,0,0,,{clean(hook)}")
    for chunk in chunk_words(words):
        texts = [clean(w["text"]) for w in chunk]
        for k, w in enumerate(chunk):
            start = w["start"] - offset
            end = (chunk[k + 1]["start"] if k + 1 < len(chunk) else w["end"]) - offset
            line = " ".join(f"{HIGHLIGHT}{t}{RESET}" if j == k else t for j, t in enumerate(texts))
            lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(max(end, start + 0.05))},Cap,,0,0,0,,{line}")
    return HEADER + "\n".join(lines) + "\n"
