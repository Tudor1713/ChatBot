import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from desk.memory import MemoryStore, SELF
from desk.reply_history import ReplyHistory
from desk import stickers
from desk.stickers import StickerNotes, allowed_url, clean_description, parse_emoji
from desk.wechat_db_source import _kind
from core.draft import parse_memory
from core.media import _resolve_route

MD5 = "0123456789abcdef0123456789abcdef"
EMOJI_XML = ('wxid_synthetic:\n<msg><emoji fromusername="a" md5="%s" type="2" width="240" height="240" '
             'cdnurl="http://vweixinf.tc.qq.com/110/20401/stodownload?m=%s" '
             'thumburl="https://evil.example.com/x.gif" externurl="http://wxapp.tc.qq.com/262/x"/></msg>') % (MD5, MD5)


class MemoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.store = MemoryStore(Path(self.dir.name))

    def test_items_are_kept_per_stable_session_id(self):
        self.store.add("wxid_a", "不吃香菜", "合成甲")
        self.store.add("wxid_b", "下月去成都出差", "合成甲")  # 同名不同人
        self.assertEqual([i["text"] for i in self.store.items("wxid_a")], ["不吃香菜"])
        self.assertEqual(self.store.count("wxid_b"), 1)
        reloaded = MemoryStore(Path(self.dir.name))
        self.assertEqual(reloaded.count("wxid_a"), 1)

    def test_auto_merge_skips_duplicates_and_respects_switch(self):
        self.store.add("wxid_a", "不吃香菜", "合成甲")
        added = self.store.merge_auto("wxid_a", "合成甲", ["不吃香菜。", "养了一只猫叫团子", "嗯", 42])
        self.assertEqual([i["text"] for i in added], ["养了一只猫叫团子"])
        self.assertEqual(added[0]["source"], "auto")
        self.store.set_auto(False)
        self.assertEqual(self.store.merge_auto("wxid_a", "合成甲", ["周末要搬家"]), [])

    def test_context_includes_self_only_when_asked(self):
        self.store.add("wxid_a", "不吃香菜")
        self.store.add(SELF, "晚上八点后才有空")
        self.assertIn("晚上八点后才有空", self.store.context("wxid_a"))
        auto = self.store.context("wxid_a", include_self=False)
        self.assertIn("不吃香菜", auto)
        self.assertNotIn("八点", auto)
        self.assertEqual(self.store.context("wxid_none", include_self=False), "")

    def test_update_delete_and_overview(self):
        item = self.store.add("wxid_a", "喜欢徒步", "合成甲")
        self.store.update(item["id"], "喜欢周末徒步")
        overview = self.store.overview()
        self.assertEqual(overview["people"][0]["preview"], "喜欢周末徒步")
        self.store.delete(item["id"])
        self.assertEqual(self.store.overview()["people"], [])
        with self.assertRaises(ValueError):
            self.store.add("wxid_a", "   ")


class ReplyHistoryTests(unittest.TestCase):
    def test_records_dedupes_and_marks_sent(self):
        with tempfile.TemporaryDirectory() as temp:
            history = ReplyHistory(Path(temp))
            cands = [{"text": "好呀"}, {"text": "今晚可以"}]
            first = history.record("wxid_a", "合成甲", "今晚有空吗", cands, best_index=1)
            self.assertEqual(history.record("wxid_a", "合成甲", "今晚有空吗", cands, 1), first)
            history.record("wxid_a", "合成甲", "那几点", [{"text": "八点吧"}], 0, auto=True)
            history.mark_sent("wxid_a", "八点吧", "sent")
            items = ReplyHistory(Path(temp)).items("wxid_a")
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0]["sent"]["status"], "sent")      # 最新的在前
            self.assertTrue(items[0]["auto"])
            self.assertEqual(history.text("wxid_a", first, 1), "今晚可以")
            with self.assertRaises(ValueError):
                history.text("wxid_a", first, 5)
            history.clear("wxid_a")
            self.assertEqual(history.count("wxid_a"), 0)


class StickerTests(unittest.TestCase):
    def test_parse_keeps_only_tencent_urls(self):
        info = parse_emoji(EMOJI_XML)
        self.assertEqual(info["md5"], MD5)
        self.assertEqual(len(info["urls"]), 2)
        self.assertTrue(all("qq.com" in u for u in info["urls"]))
        self.assertIsNone(parse_emoji("<msg><emoji md5='bad'/></msg>"))
        self.assertIsNone(parse_emoji("not xml"))
        self.assertFalse(allowed_url("file:///C:/x.gif"))
        self.assertFalse(allowed_url("http://qq.com.evil.example/x"))

    def test_description_cleanup(self):
        self.assertEqual(clean_description("礼貌微笑，图上无文字。"), "礼貌微笑")
        self.assertEqual(clean_description("表情：开心比耶\n解释"), "开心比耶")

    def test_notes_persist_by_md5(self):
        with tempfile.TemporaryDirectory() as temp:
            notes = StickerNotes(Path(temp))
            self.assertEqual(notes.put(MD5, "无语翻白眼。"), "无语翻白眼")
            self.assertEqual(StickerNotes(Path(temp)).get(MD5.upper()), "无语翻白眼")
            self.assertEqual(notes.put("nope", "x"), "")

    def test_fetch_rejects_non_images(self):
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): return False

        from PIL import Image
        png = io.BytesIO(); Image.new("RGB", (8, 8), "red").save(png, "PNG")
        bodies = iter([Response(b"<html>not an image</html>"), Response(png.getvalue())])
        with patch.object(stickers.urllib.request.OpenerDirector, "open", side_effect=lambda *a, **k: next(bodies)):
            data, mime = stickers.fetch_sticker(parse_emoji(EMOJI_XML))
        self.assertEqual(mime, "image/png")
        with patch.object(stickers.urllib.request.OpenerDirector, "open", side_effect=OSError("offline")):
            with self.assertRaises(RuntimeError):
                stickers.fetch_sticker(parse_emoji(EMOJI_XML))

    def test_composite_message_types_use_low_32_bits(self):
        self.assertEqual(_kind((5 << 32) | 49, ""), ("app", "[链接或应用消息]"))
        self.assertEqual(_kind(47, ""), ("emoji", "[表情]"))


class ModelPlumbingTests(unittest.TestCase):
    def test_draft_memory_field_is_optional_and_bounded(self):
        body = {"candidates": ["好"], "memory": ["不吃香菜", "x", {"text": "下月搬家"}, "不吃香菜"]}
        response = {"choices": [{"message": {"content": json.dumps(body, ensure_ascii=False)}, "finish_reason": "stop"}]}
        self.assertEqual(parse_memory(response), ["不吃香菜", "下月搬家"])
        empty = {"choices": [{"message": {"content": '{"candidates":["好"]}'}, "finish_reason": "stop"}]}
        self.assertEqual(parse_memory(empty), [])

    def test_image_route_falls_back_to_main_model(self):
        route = _resolve_route({"base_url": "http://127.0.0.1:8788/v1", "model_name": "synthetic-vl", "api_key": "k"}, "image")
        self.assertEqual(route.model, "synthetic-vl")
        self.assertTrue(route.url.endswith("/chat/completions"))


if __name__ == "__main__":
    unittest.main()
