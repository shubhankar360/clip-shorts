import datetime as dt
import unittest

from clipshorts.captions import ass_time, build_ass, chunk_words
from clipshorts.reframe import keyframes, pick_face, smooth, x_expr
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


def crop_x(expr, t, iw=1000, ow=300):
    """Evaluate an ffmpeg crop expression in Python (both if() branches are plain arithmetic)."""
    env = dict(t=t, iw=iw, ow=ow, between=lambda x, a, b: a <= x <= b,
               clip=lambda x, lo, hi: min(max(x, lo), hi), if_=lambda c, a, b: a if c else b)
    return eval(expr.replace("if(", "if_("), {"__builtins__": {}}, env)


class ReframeTests(unittest.TestCase):
    def test_pick_largest_face_but_stay_on_a_near_equal_one(self):
        faces = [(0, 0, 12, 12), (80, 0, 13, 13)]  # x, y, w, h in a 100px-wide frame
        self.assertAlmostEqual(pick_face(faces, 100), 0.865)
        self.assertAlmostEqual(pick_face(faces, 100, prev=0.07), 0.06)
        self.assertIsNone(pick_face((), 100))

    def test_smooth_fills_gaps_and_drops_outliers(self):
        samples = [(0, None), (0.33, 0.3), (0.67, None), (1, 0.31), (1.33, 0.9), (1.67, 0.3), (2, 0.3)]
        self.assertEqual([c for _, c in smooth(samples)], [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3])
        self.assertEqual(smooth([(t, None) for t in range(9)] + [(9, 0.5)]), [])  # 1 face in 10 frames

    def test_keyframes_hold_pan_and_cut(self):
        track = [(i / 3, c) for i, c in enumerate([0.5, 0.52, 0.48, 0.5] * 2 + [0.6] * 6 + [0.1] * 3)]
        self.assertEqual(keyframes(track), [(0.0, 0.5), (2.167, 0.5), (2.667, 0.6),
                                            (4.46, 0.6), (4.5, 0.1)])
        self.assertEqual(keyframes([(0, 0.4), (1, 0.42)]), [(0.0, 0.4)])

    def test_crop_expression_follows_keys_and_stays_in_frame(self):
        expr = x_expr([(0.0, 0.2), (1.0, 0.2), (2.0, 0.8)])
        self.assertIn("if(between(t,", expr)
        for t, x in ((0.5, 50), (1.5, 350), (2.0, 650), (9.0, 650)):
            self.assertAlmostEqual(crop_x(expr, t), x)
        self.assertEqual(crop_x(x_expr([(0.0, 0.0)]), 3), 0)
        self.assertEqual(crop_x(x_expr([(0.0, 1.0)]), 3), 700)


class SlotTests(unittest.TestCase):
    def test_slots_future_and_ordered(self):
        now = dt.datetime(2026, 10, 12, 12, 0, tzinfo=dt.timezone.utc)
        slots = next_slots(4, now=now)
        self.assertEqual(slots[0], "2026-10-12T13:00:00Z")
        self.assertEqual(slots, sorted(slots))


if __name__ == "__main__":
    unittest.main()
