"""每个会话的设定：聊天目的、补充背景、是否自动分析。按会话稳定 ID 存在数据目录。"""
from __future__ import annotations

import threading
import time
from pathlib import Path

from .store import _atomic, _load

MAX_GOAL = 200
MAX_CONTEXT = 2000
MAX_SESSIONS = 500


def _text(value, limit):
    return str(value or '').strip()[:limit]


class SessionProfiles:
    def __init__(self, directory: Path):
        self.path = Path(directory) / 'session-profiles.json'
        self.lock = threading.RLock()
        raw = _load(self.path, {})
        sessions = raw.get('sessions') if isinstance(raw, dict) and isinstance(raw.get('sessions'), dict) else {}
        self.sessions = {}
        for sid, entry in sessions.items():
            if isinstance(entry, dict):
                self.sessions[str(sid)[:256]] = {
                    'title': _text(entry.get('title'), 200), 'goal': _text(entry.get('goal'), MAX_GOAL),
                    'context': _text(entry.get('context'), MAX_CONTEXT), 'auto_analyze': entry.get('auto_analyze') is True,
                    'updated': float(entry.get('updated') or 0) if isinstance(entry.get('updated'), (int, float)) else 0.0}

    def get(self, sid: str) -> dict:
        with self.lock:
            entry = self.sessions.get(str(sid)) or {}
            return {'goal': entry.get('goal', ''), 'context': entry.get('context', ''),
                    'auto_analyze': bool(entry.get('auto_analyze'))}

    def update(self, sid: str, title: str = '', **fields) -> dict:
        sid = str(sid or '')[:256]
        if not sid:
            raise ValueError('请先选择一个会话。')
        with self.lock:
            entry = self.sessions.setdefault(sid, {'title': '', 'goal': '', 'context': '', 'auto_analyze': False, 'updated': 0.0})
            if title:
                entry['title'] = _text(title, 200)
            if 'goal' in fields:
                entry['goal'] = _text(fields['goal'], MAX_GOAL)
            if 'context' in fields:
                entry['context'] = _text(fields['context'], MAX_CONTEXT)
            if 'auto_analyze' in fields:
                entry['auto_analyze'] = bool(fields['auto_analyze'])
            entry['updated'] = time.time()
            if not (entry['goal'] or entry['context'] or entry['auto_analyze']):
                self.sessions.pop(sid, None)
            if len(self.sessions) > MAX_SESSIONS:
                for key in sorted(self.sessions, key=lambda k: self.sessions[k]['updated'])[:len(self.sessions) - MAX_SESSIONS]:
                    self.sessions.pop(key, None)
            _atomic(self.path, {'version': 1, 'sessions': self.sessions})
            return self.get(sid)

    def auto_sessions(self) -> set[str]:
        with self.lock:
            return {sid for sid, entry in self.sessions.items() if entry.get('auto_analyze')}

    def selected(self) -> list[dict]:
        with self.lock:
            return [{'session_id': sid, 'title': entry['title'] or sid}
                    for sid, entry in self.sessions.items() if entry.get('auto_analyze')]

    def context_text(self, sid: str) -> str:
        profile = self.get(sid)
        parts = []
        if profile['goal']:
            parts.append('这段聊天我的目的：' + profile['goal'] +
                         '（回复要在自然回应对方的前提下朝这个目的推进一小步，不要生硬转话题，不能编造事实。）')
        if profile['context']:
            parts.append('我补充的背景：\n' + profile['context'])
        return '\n\n'.join(parts)
