"""Local, free speech-to-text with word timestamps (faster-whisper). Cached per model."""
import json
from pathlib import Path


def transcribe(video: Path, workdir: Path, model_size: str = "small"):
    cache = workdir / f"transcript-{model_size}.json"
    if cache.exists():
        data = json.loads(cache.read_text())
        return data["words"], data["sents"]

    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, _ = model.transcribe(str(video), word_timestamps=True, vad_filter=True)
    words, sents = [], []
    for seg in segments:
        sents.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()})
        for w in seg.words or []:
            text = w.word.strip()
            if text:
                words.append({"start": round(w.start, 2), "end": round(w.end, 2), "text": text})
    cache.write_text(json.dumps({"words": words, "sents": sents}))
    return words, sents
