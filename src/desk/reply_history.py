"""每个会话历次生成的回复建议，以及自动回复实际发出的那条。只保存在数据目录。"""
from __future__ import annotations

import threading
import time
import uuid
from pathlib import Path

from .store import _atomic, _load

MAX_PER_SESSION = 40
MAX_SESSIONS = 300


class ReplyHistory:
    def __init__(self, directory: Path):
        self.path = Path(directory) / 'reply-history.json'
        self.lock = threading.RLock()
        raw = _load(self.path, {})
        sessions = raw.get('sessions') if isinstance(raw, dict) and isinstance(raw.get('sessions'), dict) else {}
        self.sessions = {str(k)[:256]: v for k, v in sessions.items()
                         if isinstance(v, dict) and isinstance(v.get('items'), list)}

    def _save(self):
        if len(self.sessions) > MAX_SESSIONS:
            oldest = sorted(self.sessions, key=lambda k: max((i.get('at', 0) for i in self.sessions[k]['items']), default=0))
            for key in oldest[:len(self.sessions) - MAX_SESSIONS]:
                self.sessions.pop(key, None)
        _atomic(self.path, {'version': 1, 'sessions': self.sessions})

    def record(self, sid: str, title: str, reply_to: str, candidates, best_index=None, auto: bool = False) -> str | None:
        texts = [str(c.get('text') if isinstance(c, dict) else c).strip()[:2000] for c in (candidates or [])]
        texts = [t for t in texts if t][:5]
        if not sid or not texts:
            return None
        with self.lock:
            entry = self.sessions.setdefault(str(sid)[:256], {'title': '', 'items': []})
            entry['title'] = str(title or entry['title'])[:200]
            last = entry['items'][-1] if entry['items'] else None
            if last and last.get('candidates') == texts:
                return last['id']
            item = {'id': uuid.uuid4().hex, 'at': time.time(), 'reply_to': str(reply_to or '').strip()[:120],
                    'candidates': texts, 'best_index': best_index if isinstance(best_index, int) and 0 <= best_index < len(texts) else None,
                    'auto': bool(auto), 'sent': None}
            entry['items'] = (entry['items'] + [item])[-MAX_PER_SESSION:]
            self._save()
            return item['id']

    def mark_sent(self, sid: str, text: str, status: str) -> None:
        text = str(text or '').strip()
        if not sid or not text:
            return
        with self.lock:
            entry = self.sessions.get(str(sid))
            if not entry:
                return
            for item in reversed(entry['items']):
                if text in item.get('candidates', []):
                    item['sent'] = {'text': text, 'status': status, 'at': time.time()}
                    self._save()
                    return

    def items(self, sid: str) -> list[dict]:
        with self.lock:
            return [dict(item) for item in reversed(self.sessions.get(str(sid), {}).get('items', []))]

    def count(self, sid: str) -> int:
        with self.lock:
            return len(self.sessions.get(str(sid), {}).get('items', []))

    def text(self, sid: str, entry_id: str, index: int) -> str:
        with self.lock:
            for item in self.sessions.get(str(sid), {}).get('items', []):
                if item['id'] == entry_id and 0 <= index < len(item['candidates']):
                    return item['candidates'][index]
        raise ValueError('这条历史回复已不存在。')

    def clear(self, sid: str) -> None:
        with self.lock:
            if self.sessions.pop(str(sid), None) is not None:
                self._save()
