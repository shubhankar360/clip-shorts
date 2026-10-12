"""Virality score (0-100) for candidate clip windows. Pure stdlib so it is easy to test and tune."""
import re
from bisect import bisect_left

HOOK_WORDS = {
    "why", "how", "nobody", "never", "secret", "truth", "stop", "wrong", "biggest",
    "worst", "best", "crazy", "insane", "actually", "imagine", "listen", "here's",
    "everyone", "mistake", "million", "billion", "what", "if", "you", "no",
}
INTENSE_WORDS = {
    "crazy", "insane", "money", "fired", "love", "hate", "died", "rich", "broke",
    "scared", "shocked", "lied", "cheated", "fight", "war", "illegal", "million",
    "billion", "destroyed", "genius", "stupid", "unbelievable", "honestly", "literally",
    "terrifying", "amazing", "never", "worst", "best", "dangerous", "quit", "lost",
    "won", "secret", "wild", "obsessed", "regret", "pain", "dream", "failed",
}
WEAK_STARTS = {"and", "but", "so", "because", "or", "um", "uh", "like", "yeah", "which"}

VERDICTS = ((85, "POST FIRST"), (70, "POST"), (60, "MAYBE"), (0, "SKIP"))


def tokens(text: str) -> list:
    return re.findall(r"[a-z']+|\d+", text.lower())


def verdict(score: float) -> str:
    return next(label for floor, label in VERDICTS if score >= floor)


def score_window(ws, rms, start, end, last_text, mean_rms):
    dur = end - start
    opening = " ".join(w["text"] for w in ws if w["start"] < start + 3)
    first3, all_toks = tokens(opening), tokens(" ".join(w["text"] for w in ws))

    hook = 15 if any(t in HOOK_WORDS for t in first3) else 0
    hook += 5 if any(t.isdigit() for t in first3) else 0
    hook += 5 if any(w["text"].endswith("?") for w in ws if w["start"] < start + 5) else 0
    if first3 and first3[0] in WEAK_STARTS:
        hook -= 8  # starts mid-thought

    density = sum(t in INTENSE_WORDS for t in all_toks) / max(len(all_toks), 1)
    emotion = min(20, density * 400)

    wps = len(ws) / max(dur, 1)
    pace = 15 if 2.3 <= wps <= 3.6 else max(0, 15 - abs(wps - 2.95) * 10)

    seg = rms[int(start):int(end) + 1] or [0]
    energy = min(15, max(0, (max(seg) / (mean_rms or 1) - 1) * 7.5))

    payoff = 10 if last_text.rstrip().endswith((".", "!", "?")) else 3

    length = 15 if 25 <= dur <= 45 else max(0, 15 - min(abs(dur - 25), abs(dur - 45)) * 1.5)

    parts = dict(hook=max(hook, 0), emotion=emotion, pace=pace, energy=energy,
                 payoff=payoff, length=length)
    return round(sum(parts.values()), 1), {k: round(v, 1) for k, v in parts.items()}


def candidates(words, sents, rms, min_len=20, max_len=58):
    """Every sentence-aligned window between min_len and max_len seconds, best first."""
    starts = [w["start"] for w in words]
    mean_rms = sum(rms) / len(rms) if rms else 1
    out = []
    for i, s in enumerate(sents):
        start = s["start"]
        for j in range(i, len(sents)):
            end = sents[j]["end"]
            if end - start > max_len:
                break
            if end - start < min_len:
                continue
            ws = words[bisect_left(starts, start):bisect_left(starts, end)]
            if not ws:
                continue
            score, parts = score_window(ws, rms, start, end, sents[j]["text"], mean_rms)
            out.append(dict(start=start, end=end, score=score, parts=parts, words=ws,
                            text=" ".join(x["text"] for x in sents[i:j + 1])))
    out.sort(key=lambda c: c["score"], reverse=True)
    return out


def pick(cands, n):
    """Top n non-overlapping windows."""
    chosen = []
    for c in cands:
        if all(c["end"] <= p["start"] or c["start"] >= p["end"] for p in chosen):
            chosen.append(c)
            if len(chosen) == n:
                break
    return chosen


def words_between(words, start, end):
    starts = [w["start"] for w in words]
    return words[bisect_left(starts, start):bisect_left(starts, end)]
