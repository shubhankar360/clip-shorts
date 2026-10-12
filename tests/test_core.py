import datetime as dt
import unittest

from clipshorts.captions import ass_time, build_ass, chunk_words
from clipshorts.score import candidates, pick, verdict
from clipshorts.youtube import next_slots


def fake(sents):
    words = []
    for s in sents:
        toks = s["text"].split()
        step = (s["end"] - s["start"]) / len(toks)
        words += [{"start": s["start"] + i * step, "end": s["start"] + (i + 1) * step, "text": t}
                  for i, t in enumerate(toks)]
    return words


SENTS = [
    {"start": 0, "end": 4, "text": "Why does nobody talk about this?"},
    {"start": 4, "end": 20, "text": "I lost a million dollars in one day and it was honestly the most insane thing that ever happened to me in my entire life and career so far."},
    {"start": 20, "end": 34, "text": "And honestly that was the worst mistake I ever made, I regret it every single day of my life."},
    {"start": 34, "end": 60, "text": "so um we kind of moved on after that and started working on the next thing which was fine I guess for the time being."},
]


class ScoreTests(unittest.TestCase):
    def test_hooky_window_beats_rambling(self):
        words = fake(SENTS)
        ranked = candidates(words, SENTS, [100] * 20 + [400] + [100] * 40)
        self.assertEqual(ranked[0]["start"], 0)
        self.assertGreaterEqual(ranked[0]["score"], 70)
        self.assertLess(min(c["score"] for c in ranked if c["start"] == 34), ranked[0]["score"])

    def test_pick_non_overlapping(self):
        chosen = pick(candidates(fake(SENTS), SENTS, [100] * 60), 5)
        for a in chosen:
            for b in chosen:
                if a is not b:
                    self.assertTrue(a["end"] <= b["start"] or a["start"] >= b["end"])

    def test_verdicts(self):
        self.assertEqual([verdict(s) for s in (90, 75, 65, 10)], ["POST FIRST", "POST", "MAYBE", "SKIP"])


class CaptionTests(unittest.TestCase):
    def test_time_format(self):
        self.assertEqual(ass_time(3725.456), "1:02:05.46")

    def test_chunks_break_on_punctuation(self):
        chunks = list(chunk_words(fake([{"start": 0, "end": 4, "text": "Hi. You are great"}])))
        self.assertEqual([len(c) for c in chunks], [1, 3])

    def test_karaoke_and_hook(self):
        ass = build_ass(fake(SENTS[:1]), 0, 4, hook="{bad} hook")
        self.assertIn("Hook,,0,0,0,,BAD HOOK", ass)
        self.assertIn(r"{\c&H00FFFF&}WHY{\c&HFFFFFF&}", ass)


class SlotTests(unittest.TestCase):
    def test_slots_future_and_ordered(self):
        now = dt.datetime(2026, 10, 12, 12, 0, tzinfo=dt.timezone.utc)
        slots = next_slots(4, now=now)
        self.assertEqual(slots[0], "2026-10-12T13:00:00Z")
        self.assertEqual(slots, sorted(slots))


if __name__ == "__main__":
    unittest.main()
