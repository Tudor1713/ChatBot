import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from desk.capture_service import CaptureService, sidebar_target_point
from desk.platforms import keep_responsive_in_background


def row(text, x, y, w=90, h=20, score=0.96):
    return [[[x, y], [x + w, y], [x + w, y + h], [x, y + h]], text, score]


NAMES = ["合成联系人甲", "文件传输助手", "合成群聊乙", "陈铄果"]


class SidebarTargetTests(unittest.TestCase):
    def test_exact_row_below_search_box_returns_its_center(self):
        rows = [row("合成联系人甲", 170, 140), row("11:20", 390, 142, w=40), row("文件传输助手", 170, 620)]
        self.assertEqual(sidebar_target_point(rows, "文件传输助手", NAMES), (215.0, 630.0))

    def test_search_box_text_is_never_clicked(self):
        rows = [row("文件传输助手", 150, 70)]
        self.assertIsNone(sidebar_target_point(rows, "文件传输助手", NAMES))
        # 125% 缩放时搜索框更低，仍按比例排除。
        self.assertIsNone(sidebar_target_point([row("文件传输助手", 150, 100)], "文件传输助手", NAMES, scale=1.25))

    def test_two_matching_rows_are_ambiguous(self):
        rows = [row("合成联系人甲", 170, 140), row("合成联系人甲", 170, 240)]
        self.assertIsNone(sidebar_target_point(rows, "合成联系人甲", NAMES))

    def test_truncated_name_needs_a_unique_prefix(self):
        rows = [row("合成联系…", 170, 140)]
        self.assertEqual(sidebar_target_point(rows, "合成联系人甲", NAMES), (215.0, 150.0))
        rival = NAMES + ["合成联系人丙"]
        self.assertIsNone(sidebar_target_point(rows, "合成联系人甲", rival))

    def test_one_missed_character_matches_only_without_a_better_rival(self):
        rows = [row("陈果", 170, 140)]
        self.assertIsNotNone(sidebar_target_point(rows, "陈铄果", NAMES))
        self.assertIsNone(sidebar_target_point(rows, "陈铄果", NAMES + ["陈果"]))

    def test_message_preview_containing_the_name_is_ignored(self):
        rows = [row("合成联系人甲：明天见", 170, 172), row("[图片]", 170, 272)]
        self.assertIsNone(sidebar_target_point(rows, "合成联系人甲", NAMES))

    def test_low_confidence_line_is_ignored(self):
        self.assertIsNone(sidebar_target_point([row("文件传输助手", 170, 620, score=0.5)], "文件传输助手", NAMES))


class SendFailureCodeTests(unittest.TestCase):
    def test_codes_name_the_failing_check_without_content(self):
        cases = {
            "输入框画面已过期，已取消发送": "composer_frame_stale",
            "输入框画面未更新，已取消发送": "composer_frame_not_new",
            "微信标题画面未更新，已拒绝发送": "frame_stale",
            "目标会话不在微信左侧列表的可见范围，已拒绝发送": "target_not_listed",
            "微信当前会话标题与数据库目标不一致": "target_unverified",
        }
        for message, code in cases.items():
            self.assertEqual(CaptureService._db_send_failure(RuntimeError(message))[0], code, message)


class ProcessPriorityTests(unittest.TestCase):
    def test_non_windows_is_a_no_op(self):
        self.assertEqual(keep_responsive_in_background("linux"), {})


if __name__ == "__main__":
    unittest.main()
