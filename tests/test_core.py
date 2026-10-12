import datetime as dt
import json
import os
import unittest
from types import SimpleNamespace
from unittest import mock

from clipshorts.captions import ass_time, build_ass, chunk_words
from clipshorts.reframe import keyframes, pick_face, smooth, x_expr
from clipshorts.rerank import choose, llm_rerank, suggest
from clipshorts.score import candidates, dangling, pick, tokens, verdict
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

    def test_dangling_openers(self):
        for text, expected in (("He said no", True), ("So they're broke", True), ("It's insane", True),
                               ("This one time I quit", True), ("That was it", True),
                               ("This is crazy", False), ("Elon said no", False), ("Why does it fail", False)):
            self.assertEqual(dangling(tokens(text)), expected, text)

    def test_standalone_rewards_topic_shift_and_penalizes_dangling(self):
        sents = [{"start": 0, "end": 22, "text": "This is the intro to the show and today we have a great guest on."},
                 {"start": 22, "end": 46, "text": "He said it was the worst mistake of his life and he regrets it daily."},
                 {"start": 47.5, "end": 72, "text": "Why do most people quit right before it works? Nobody tells you."}]
        by_start = {c["start"]: c["parts"]["standalone"]
                    for c in candidates(fake(sents), sents, [100] * 72, min_len=20, max_len=26)}
        self.assertEqual(by_start, {0: 10, 22: 0, 47.5: 10})  # video start, dangling "he", 1.5s pause

    def test_score_stays_within_100(self):
        sents = [{"start": 0, "end": 30, "text": "Why did 1 million people quit? " + "insane crazy money " * 27 + "done."}]
        top = candidates(fake(sents), sents, [100] * 10 + [900] + [100] * 20)[0]
        self.assertEqual(set(top["parts"]), {"hook", "emotion", "pace", "energy", "payoff", "length", "standalone"})
        self.assertEqual(top["score"], 100)

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


class FakeClient:
    """Stands in for anthropic.Anthropic(): records the request, returns a canned JSON reply."""

    def __init__(self, reply, stop_reason="end_turn"):
        self.reply, self.stop_reason, self.request = reply, stop_reason, None
        self.messages = self

    def create(self, **request):
        self.request = request
        text = SimpleNamespace(type="text", text=json.dumps(self.reply))
        return SimpleNamespace(stop_reason=self.stop_reason, content=[SimpleNamespace(type="thinking"), text])


def cand(start, score, text):
    return dict(start=start, end=start + 30, score=score, text=text)


class RerankTests(unittest.TestCase):
    CANDS = [cand(0, 80, "So um I lost a million dollars in one single day and it was insane. Then I quit."),
             cand(40, 75, "Why does nobody talk about this?"),
             cand(80, 70, "He said that was fine.")]

    def test_heuristic_hook_and_title_from_opening_line(self):
        s = suggest(self.CANDS[0])
        self.assertEqual(s["suggested_hook"], "I LOST A MILLION DOLLARS")
        self.assertEqual(s["suggested_title"], "I lost a million dollars in one single day #shorts")
        self.assertEqual(suggest(self.CANDS[1], "Some Pod")["suggested_title"],
                         "Why does nobody talk about this? | Some Pod #shorts")
        self.assertLessEqual(len(suggest(cand(0, 1, "word " * 40))["suggested_title"]), 60)
        run_on = suggest(cand(0, 1, "Why does nobody talk about this, I lost a million dollars in one day, it was"))
        self.assertEqual(run_on, dict(suggested_hook="WHY DOES NOBODY TALK ABOUT THIS",
                                      suggested_title="Why does nobody talk about this #shorts"))

    def test_choose_off_keeps_heuristic_order(self):
        chosen, info = choose([dict(c) for c in self.CANDS], 2, 72)
        self.assertEqual((info, [c["start"] for c in chosen]), ({"rerank": "off"}, [0, 40]))
        self.assertTrue(all(c["suggested_title"].endswith("#shorts") for c in chosen))

    def test_llm_rerank_validates_and_clamps(self):
        fake = FakeClient({"picks": [
            {"id": 2, "suggested_hook": "the one rule nobody ever tells you", "why": "w",
             "suggested_title": "A very long title that keeps going well past the sixty character limit"},
            {"id": 2, "suggested_hook": "dup", "suggested_title": "dup", "why": ""},
            {"id": 9, "suggested_hook": "bad id", "suggested_title": "bad", "why": ""}]})
        chosen, info = choose([dict(c) for c in self.CANDS], 2, 0, "llm", {"title": "Pod"}, log=lambda *_: None,
                              client=fake)
        self.assertEqual((info, [c["start"] for c in chosen]), ({"rerank": "llm"}, [80, 0]))  # topped up
        top = chosen[0]
        self.assertEqual(top["suggested_hook"], "THE ONE RULE NOBODY EVER TELLS")
        self.assertTrue(top["suggested_title"].endswith(" #shorts") and len(top["suggested_title"]) <= 60)
        self.assertEqual(chosen[1]["suggested_hook"], "I LOST A MILLION DOLLARS")
        req = fake.request
        self.assertEqual(req["model"], "claude-sonnet-5-5")
        self.assertEqual(req["output_config"]["format"]["type"], "json_schema")
        self.assertIn("Why does nobody talk about this?", req["messages"][0]["content"])

    def test_llm_failure_falls_back_to_heuristics(self):
        logs = []
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
            chosen, info = choose([dict(c) for c in self.CANDS], 2, 0, "llm", log=logs.append)
        self.assertEqual((info["rerank"], len(chosen)), ("off", 2))
        self.assertIn("ANTHROPIC_API_KEY", info["rerank_error"])
        self.assertIn("ANTHROPIC_API_KEY", logs[0])
        with self.assertRaises(RuntimeError):
            llm_rerank(self.CANDS, 2, {}, client=FakeClient({}, stop_reason="refusal"))


class SlotTests(unittest.TestCase):
    def test_slots_future_and_ordered(self):
        now = dt.datetime(2026, 10, 12, 12, 0, tzinfo=dt.timezone.utc)
        slots = next_slots(4, now=now)
        self.assertEqual(slots[0], "2026-10-12T13:00:00Z")
        self.assertEqual(slots, sorted(slots))


if __name__ == "__main__":
    unittest.main()
