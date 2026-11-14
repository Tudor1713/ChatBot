"""微信表情（type 47）：解析消息自带的 CDN 地址、下载表情图、按 md5 缓存识别结果。

只访问腾讯自己的表情 CDN 域名，不跟随跳转到其他域名；下载内容必须能被解码为
GIF/PNG/JPEG/WebP。识别结果（一句短描述）按表情 md5 存在数据目录，同一表情只识别一次。
微信 4.x 的聊天照片是加密存放的（V2 .dat），需要微信进程里的图片密钥，这里不处理。
"""
from __future__ import annotations

import io
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

_ALLOWED_SUFFIXES = ('.qq.com', '.qpic.cn', '.wechat.com')
_MAX_BYTES = 4 * 1024 * 1024
_MD5 = re.compile(r'^[0-9a-fA-F]{32}$')
_FORMATS = {'GIF': 'image/gif', 'PNG': 'image/png', 'JPEG': 'image/jpeg', 'WEBP': 'image/webp'}
DESCRIBE_PROMPT = ('这是微信聊天里对方发来的一个表情包。用不超过12个字说出它表达的意思或情绪，'
                   '例如“开心比耶”“无语翻白眼”“好的收到”；图上有文字时直接写出那几个字。'
                   '只输出这一句，不要解释，也不要说明图上有没有文字。')


def allowed_url(url: str) -> bool:
    try:
        parts = urllib.parse.urlsplit(str(url))
    except ValueError:
        return False
    host = (parts.hostname or '').lower()
    return parts.scheme in ('http', 'https') and any(host.endswith(s) for s in _ALLOWED_SUFFIXES)


def parse_emoji(xml_text: str) -> dict | None:
    """从表情消息 XML 取 md5 与可下载地址；格式不对返回 None。"""
    text = str(xml_text or '')
    start = text.find('<')
    if start < 0 or len(text) > 64 * 1024:
        return None
    try:
        root = ET.fromstring(text[start:])
    except ET.ParseError:
        return None
    node = root if root.tag == 'emoji' else root.find('.//emoji')
    if node is None:
        return None
    md5 = str(node.get('md5') or '').lower()
    if not _MD5.match(md5):
        return None
    urls = [node.get(name) for name in ('cdnurl', 'thumburl', 'externurl')]
    urls = [u for u in urls if u and allowed_url(u)]
    try:
        width, height = int(node.get('width') or 0), int(node.get('height') or 0)
    except ValueError:
        width = height = 0
    return {'md5': md5, 'urls': urls[:3], 'width': width, 'height': height}


class _SameHostsOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed_url(newurl):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def sniff_image(data: bytes) -> str | None:
    """返回能安全解码的图片 MIME；否则 None。"""
    try:
        from PIL import Image
        with Image.open(io.BytesIO(data)) as image:
            if image.width * image.height > 4096 * 4096:
                return None
            image.verify()
            return _FORMATS.get(image.format)
    except Exception:
        return None


def fetch_sticker(info: dict, timeout: float = 8.0) -> tuple[bytes, str]:
    opener = urllib.request.build_opener(_SameHostsOnly())
    for url in (info or {}).get('urls') or []:
        if not allowed_url(url):
            continue
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'image/*'})
        try:
            with opener.open(request, timeout=timeout) as response:
                data = response.read(_MAX_BYTES + 1)
        except (urllib.error.URLError, OSError, ValueError):
            continue
        if not data or len(data) > _MAX_BYTES:
            continue
        mime = sniff_image(data)
        if mime:
            return data, mime
    raise RuntimeError('表情图片暂时无法下载。')


def clean_description(text: str) -> str:
    line = str(text or '').strip().splitlines()[0] if str(text or '').strip() else ''
    line = re.sub(r'^(表情|这个表情|表情包)[：:\s]*', '', line)
    # 去掉「图上无文字」「没有文字」这类说明分句。
    parts = [p for p in re.split(r'[，,；;]', line) if p.strip() and not re.search(r'(无|没有|未见|不含)文字', p)]
    line = '，'.join(p.strip() for p in parts).strip(' 。.“”"\'「」')
    return line[:24]


class StickerNotes:
    """md5 → 短描述，存在数据目录；只含表情的含义，不含聊天内容。"""

    def __init__(self, directory: Path, limit: int = 3000):
        self.path = Path(directory) / 'sticker-notes.json'
        self.limit = limit
        self.lock = threading.RLock()
        try:
            raw = json.loads(self.path.read_text(encoding='utf-8'))
            items = raw.get('items') if isinstance(raw, dict) else None
        except (OSError, ValueError):
            items = None
        self.items = {k: v for k, v in (items or {}).items()
                      if _MD5.match(str(k)) and isinstance(v, dict) and isinstance(v.get('text'), str)}

    def get(self, md5: str) -> str:
        with self.lock:
            item = self.items.get(str(md5).lower())
            return item['text'] if item else ''

    def put(self, md5: str, text: str) -> str:
        text = clean_description(text)
        md5 = str(md5).lower()
        if not text or not _MD5.match(md5):
            return ''
        with self.lock:
            self.items[md5] = {'text': text, 'at': time.time()}
            if len(self.items) > self.limit:
                for key, _ in sorted(self.items.items(), key=lambda kv: kv[1].get('at', 0))[:len(self.items) - self.limit]:
                    self.items.pop(key, None)
            from .store import _atomic
            _atomic(self.path, {'version': 1, 'items': self.items})
        return text
