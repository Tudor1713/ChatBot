import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from PySide6.QtWidgets import QApplication
from desk.controller import Controller
from desk.session_profiles import SessionProfiles
from core import style as style_module
from core.client import ProviderError

APP = QApplication.instance() or QApplication([])


class SessionProfileTests(unittest.TestCase):
    def test_goal_context_and_auto_flag_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            profiles = SessionProfiles(Path(temp))
            profiles.update("wxid_a", "合成甲", goal="约周六吃饭", context="上次她说想吃火锅")
            profiles.update("wxid_b", "合成乙", auto_analyze=True)
            reloaded = SessionProfiles(Path(temp))
            self.assertEqual(reloaded.get("wxid_a")["goal"], "约周六吃饭")
            self.assertEqual(reloaded.auto_sessions(), {"wxid_b"})
            text = reloaded.context_text("wxid_a")
            self.assertIn("约周六吃饭", text)
            self.assertIn("火锅", text)
            self.assertEqual(reloaded.context_text("wxid_none"), "")
            reloaded.update("wxid_b", auto_analyze=False)   # 全空的设定不留记录
            self.assertNotIn("wxid_b", SessionProfiles(Path(temp)).sessions)


class StyleTests(unittest.TestCase):
    def samples(self, n=40):
        return [{"group": i % 3, "text": f"好嘞第{i}句"} for i in range(n)]

    def test_examples_must_be_verbatim_and_profile_bounded(self):
        body = {"profile": ["句子很短", "爱用好嘞"], "examples": ["好嘞第1句", "模型自己编的", "好嘞第2句"]}
        response = {"choices": [{"message": {"content": json.dumps(body, ensure_ascii=False)}, "finish_reason": "stop"}]}
        route = SimpleNamespace(model="m", url="http://127.0.0.1/v1/chat/completions", key="k", kind="chat")
        with patch.object(style_module, "resolve_reply", return_value=route), \
             patch.object(style_module, "resolve_decision", return_value=None), \
             patch.object(style_module, "structured_options", side_effect=lambda r, p: p), \
             patch.object(style_module, "post_json", return_value=response) as post:
            result = style_module.learn_style(self.samples(), {})
        self.assertEqual(result["examples"], ["好嘞第1句", "好嘞第2句"])
        self.assertIn("- 爱用好嘞", result["profile"])
        sent = post.call_args[0][1]["messages"][1]["content"]
        self.assertIn("【会话1】", sent)

    def test_too_few_samples_is_explained(self):
        with self.assertRaisesRegex(ProviderError, "太少"):
            style_module.learn_style(self.samples(5), {})

    def test_style_prompt_respects_switch(self):
        record = {"profile": "- 很短", "examples": ["好嘞"], "enabled": True}
        self.assertIn("好嘞", style_module.style_prompt(record))
        self.assertEqual(style_module.style_prompt({**record, "enabled": False}), "")
        self.assertEqual(style_module.style_prompt({}), "")


class ScheduleTests(unittest.TestCase):
    def fake(self, auto_ids=()):
        return SimpleNamespace(analysis_due={}, profiles=SimpleNamespace(auto_sessions=lambda: set(auto_ids)))

    def session(self, sides):
        return {"messages": [{"side": s} for s in sides]}

    def test_wait_counts_from_first_unanswered_message(self):
        fake, cfg = self.fake(), {"debounce_ms": 1200, "auto_analyze_wait": 300, "auto_analyze_count": 0}
        Controller._schedule_auto_analysis(fake, "a", self.session(["me", "other"]), cfg)
        first = fake.analysis_due["a"]
        self.assertAlmostEqual(first - time.time(), 300, delta=2)
        Controller._schedule_auto_analysis(fake, "a", self.session(["me", "other", "other"]), cfg)
        self.assertEqual(fake.analysis_due["a"], first)   # 后续消息不顺延

    def test_enough_messages_skip_the_wait(self):
        fake, cfg = self.fake(), {"debounce_ms": 1200, "auto_analyze_wait": 600, "auto_analyze_count": 3}
        Controller._schedule_auto_analysis(fake, "a", self.session(["other", "me", "other", "other"]), cfg)
        self.assertGreater(fake.analysis_due["a"] - time.time(), 500)
        Controller._schedule_auto_analysis(fake, "a", self.session(["other", "me", "other", "other", "other"]), cfg)
        self.assertLess(fake.analysis_due["a"] - time.time(), 2)

    def test_scope_selected_only_allows_chosen_sessions(self):
        fake = self.fake({"b"})
        self.assertFalse(Controller._auto_analyze_allowed(fake, "a", {"auto_analyze": False}))
        self.assertTrue(Controller._auto_analyze_allowed(fake, "a", {"auto_analyze": True, "auto_analyze_scope": "all"}))
        self.assertFalse(Controller._auto_analyze_allowed(fake, "a", {"auto_analyze": True, "auto_analyze_scope": "selected"}))
        self.assertTrue(Controller._auto_analyze_allowed(fake, "b", {"auto_analyze": True, "auto_analyze_scope": "selected"}))


class AutoResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        native = patch('desk.capture_service.CaptureService')
        native.start()
        self.addCleanup(native.stop)

    def test_resume_is_stored_only_while_running_with_consent(self):
        data = Path(self.temp.name) / 'data'
        ctrl = Controller(data)
        ctrl.auto_resume = True
        ctrl.auto_policy['enabled'] = True
        ctrl._save_auto_state()
        stored = json.loads((data / 'auto-reply.json').read_text(encoding='utf-8'))['policy']
        self.assertFalse(stored['enabled'])          # 发送器本身从不以已开启状态落盘
        self.assertTrue(stored['resume'])
        ctrl.auto_paused = True
        ctrl._save_auto_state()
        self.assertFalse(json.loads((data / 'auto-reply.json').read_text(encoding='utf-8'))['policy']['resume'])
        ctrl.close()

    def test_launch_with_resume_runs_the_normal_start_checks(self):
        data = Path(self.temp.name) / 'data'
        data.mkdir(parents=True)
        (data / 'auto-reply.json').write_text(json.dumps({'version': 1, 'policy': {'resume': True, 'wait_me_seconds': 30},
                                                          'allowlist': [], 'guard': {'version': 1, 'seen': [], 'sent': [], 'pending': {}}}),
                                              encoding='utf-8')
        ctrl = Controller(data)
        self.assertTrue(ctrl.auto_resume_on_launch)
        self.assertEqual(ctrl.auto_policy['wait_me_seconds'], 30)
        self.assertFalse(ctrl.auto_policy['enabled'])
        ctrl._resume_auto_after_launch()             # 名单为空：正常检查拒绝，不会武装
        self.assertFalse(ctrl.auto_policy['enabled'])
        self.assertIn('没能自动恢复', ctrl.auto_detail)
        self.assertTrue((data / 'auto-events.jsonl').exists())
        ctrl.close()


class SafeClickTests(unittest.TestCase):
    def test_click_refused_when_point_is_covered(self):
        from app import fill

        class U:
            def __init__(self): self.clicks = []
            def GetCursorPos(self, p): return True
            def SetCursorPos(self, x, y): return True
            def mouse_event(self, *a): self.clicks.append(a)

        class X:
            def __init__(self, root): self.root, self.z = root, []
            def SetWindowPos(self, hwnd, after, *a): self.z.append(after.value)
            def WindowFromPoint(self, p): return 999
            def GetAncestor(self, h, flag): return self.root

        u = U()
        for root, ok in ((555, False), (123, True)):
            x = X(root)
            with patch.object(fill, "libraries", return_value=(u, None, None)), patch.object(fill, "_user32", return_value=x), \
                 patch.object(fill.time, "sleep"):
                if ok:
                    fill.safe_click(123, 10, 10)
                else:
                    with self.assertRaisesRegex(RuntimeError, "挡住"):
                        fill.safe_click(123, 10, 10)
            import ctypes
            self.assertEqual(x.z, [ctypes.c_void_p(-1).value, ctypes.c_void_p(-2).value])  # 置顶后一定取消置顶
        self.assertEqual(len(u.clicks), 2)           # 只有落点属于微信时才按下/抬起一次

    def test_focus_reports_lock_screen(self):
        from app import fill
        u = SimpleNamespace(GetForegroundWindow=lambda: 1)
        with patch.object(fill, "libraries", return_value=(u, None, None)), patch.object(fill, "session_locked", return_value=True):
            with self.assertRaisesRegex(RuntimeError, "锁屏"):
                fill.focus_window(123)


if __name__ == "__main__":
    unittest.main()
