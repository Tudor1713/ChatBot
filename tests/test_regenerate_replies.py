import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from PySide6.QtWidgets import QApplication
from core import engine
from desk.controller import Controller

APP = QApplication.instance() or QApplication([])
ANSWERS = {"true_intent": {"type": "choice", "choice": "request_action", "confidence": .9},
           "should_reply_now": {"type": "binary", "noul": .8}}


class EngineReuseTests(unittest.TestCase):
    def test_previous_answers_skip_the_judgment_call(self):
        calls = []

        def ask(route, state, questions, timeout):
            calls.append(sorted(questions))
            return {"best_reply": {"choice": "reply_b", "probabilities": {}}}, {}, []

        messages = [{"side": "other", "text": "今晚有空吗"}]
        with patch.object(engine, "resolve_decision", return_value=object()), \
             patch.object(engine, "resolve_reply", return_value=object()), \
             patch.object(engine, "_ask", side_effect=ask), \
             patch.object(engine, "draft_bundle", return_value=(["好呀", "可以"], {}, {}, [])):
            result = engine.analyze(messages, {"context_limit": 10}, previous={"answers": ANSWERS})
        self.assertEqual(calls, [["best_reply"]])          # 只有排序，没有重新判断
        self.assertEqual(result["best_index"], 1)
        self.assertEqual(result["answers"], ANSWERS)


class ControllerRegenerateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        native = patch("desk.capture_service.CaptureService")
        native.start()
        self.addCleanup(native.stop)
        self.ctrl = Controller(Path(self.temp.name) / "data")
        self.addCleanup(self.ctrl.close)
        self.ctrl.store.secrets["api_key"] = "synthetic"
        self.ctrl.store.config["context_days"] = 0
        self.ctrl.sessions["s"] = {"id": "s", "title": "合成联系人", "source": "manual",
                                   "messages": [{"id": "1", "side": "other", "text": "今晚有空吗"}]}
        self.ctrl.current_id = "s"

    def submitted(self, params):
        captured = {}

        class Future:
            def add_done_callback(self, fn):
                pass

        def submit(kind, payload):
            captured.update(kind=kind, payload=payload)
            return Future()

        with patch.object(self.ctrl.models, "submit", side_effect=submit):
            self.ctrl.handle("regenerate_replies", params)
        self.ctrl.inflight = None
        return captured

    def test_unchanged_conversation_reuses_judgment_and_avoids_last_batch(self):
        self.ctrl.results["s"] = {"answers": ANSWERS, "candidates": [{"text": "好呀"}, {"text": "可以"}]}
        self.ctrl.result_fingerprints["s"] = self.ctrl.fingerprint(self.ctrl.sessions["s"])
        captured = self.submitted({"session_id": "s", "instruction": "更短一点"})
        payload = captured["payload"]
        self.assertEqual(payload["previous"], {"answers": ANSWERS})
        self.assertIn("更短一点", payload["config"]["style"])
        self.assertIn(json.dumps(["好呀", "可以"], ensure_ascii=False), payload["config"]["style"])
        self.assertNotIn("s", self.ctrl.regen_requests)

    def test_changed_conversation_runs_full_analysis(self):
        self.ctrl.results["s"] = {"answers": ANSWERS, "candidates": [{"text": "好呀"}]}
        self.ctrl.result_fingerprints["s"] = "stale"
        payload = self.submitted({"session_id": "s"})["payload"]
        self.assertNotIn("previous", payload)
        self.assertIn("不满意", payload["config"]["style"])


if __name__ == "__main__":
    unittest.main()
