"""本机记忆：每个会话一份「关于对方」，另有一份「关于我」。

按会话的稳定 ID（数据库 wxid / 群 ID）区分，同名联系人不会混在一起。只保存在数据目录，
用于给模型的背景；回复时作为参考，不在回复里原样复述。
"""
from __future__ import annotations

import re
import threading
import time
import uuid
from difflib import SequenceMatcher
from pathlib import Path

from .store import _atomic, _load

SELF = 'self'
MAX_TEXT = 120
MAX_ITEMS = 60
MAX_SESSIONS = 500
MAX_AUTO_PER_TURN = 3


def _clean(text) -> str:
    return re.sub(r'\s+', ' ', str(text or '')).strip()[:MAX_TEXT]


def _key(text: str) -> str:
    return re.sub(r'[\s，,。.！!？?；;：:、~～…“”"\'「」]+', '', text).casefold()


class MemoryStore:
    def __init__(self, directory: Path):
        self.path = Path(directory) / 'memory.json'
        self.lock = threading.RLock()
        raw = _load(self.path, {})
        raw = raw if isinstance(raw, dict) else {}
        self.auto = raw.get('auto') is not False
        sessions = raw.get('sessions') if isinstance(raw.get('sessions'), dict) else {}
        self.sessions = {}
        for sid, entry in sessions.items():
            if not isinstance(entry, dict) or not isinstance(entry.get('items'), list):
                continue
            items = [self._valid(item) for item in entry['items']]
            items = [item for item in items if item]
            if items or sid == SELF:
                self.sessions[str(sid)[:256]] = {'title': str(entry.get('title') or '')[:200], 'items': items[-MAX_ITEMS:]}

    @staticmethod
    def _valid(item):
        if not isinstance(item, dict):
            return None
        text = _clean(item.get('text'))
        if not text:
            return None
        return {'id': str(item.get('id') or uuid.uuid4().hex)[:64], 'text': text,
                'source': 'auto' if item.get('source') == 'auto' else 'manual',
                'at': float(item.get('at') or 0) if isinstance(item.get('at'), (int, float)) else 0.0}

    def _save(self):
        if len(self.sessions) > MAX_SESSIONS:
            others = sorted((k for k in self.sessions if k != SELF),
                            key=lambda k: max((i['at'] for i in self.sessions[k]['items']), default=0))
            for key in others[:len(self.sessions) - MAX_SESSIONS]:
                self.sessions.pop(key, None)
        _atomic(self.path, {'version': 1, 'auto': self.auto, 'sessions': self.sessions})

    def items(self, sid: str) -> list[dict]:
        with self.lock:
            return [dict(item) for item in self.sessions.get(str(sid), {}).get('items', [])]

    def count(self, sid: str) -> int:
        with self.lock:
            return len(self.sessions.get(str(sid), {}).get('items', []))

    def view(self, sid: str, title: str = '') -> dict:
        with self.lock:
            return {'auto': self.auto, 'session_id': sid, 'title': title or self.sessions.get(sid, {}).get('title', ''),
                    'items': self.items(sid), 'self': self.items(SELF)}

    def overview(self) -> dict:
        with self.lock:
            people = [{'session_id': sid, 'title': entry['title'] or sid, 'count': len(entry['items']),
                       'latest': max((i['at'] for i in entry['items']), default=0),
                       'preview': entry['items'][-1]['text'] if entry['items'] else ''}
                      for sid, entry in self.sessions.items() if sid != SELF and entry['items']]
            people.sort(key=lambda p: p['latest'], reverse=True)
            return {'auto': self.auto, 'self': self.items(SELF), 'people': people}

    def _similar(self, sid, text):
        key = _key(text)
        for item in self.sessions.get(sid, {}).get('items', []):
            other = _key(item['text'])
            if key == other or (len(key) >= 4 and (key in other or other in key)) or \
                    SequenceMatcher(None, key, other).ratio() >= .8:
                return item
        return None

    def add(self, sid: str, text: str, title: str = '', source: str = 'manual') -> dict | None:
        sid, text = str(sid or '')[:256], _clean(text)
        if not sid or not text:
            raise ValueError('记忆内容不能为空。')
        with self.lock:
            entry = self.sessions.setdefault(sid, {'title': '', 'items': []})
            if title:
                entry['title'] = str(title)[:200]
            existing = self._similar(sid, text)
            if existing:
                return None if source == 'auto' else dict(existing)
            item = {'id': uuid.uuid4().hex, 'text': text, 'source': 'auto' if source == 'auto' else 'manual', 'at': time.time()}
            entry['items'] = (entry['items'] + [item])[-MAX_ITEMS:]
            self._save()
            return dict(item)

    def merge_auto(self, sid: str, title: str, candidates) -> list[dict]:
        if not self.auto or not isinstance(candidates, list):
            return []
        added = []
        for text in candidates[:MAX_AUTO_PER_TURN]:
            if isinstance(text, str) and 4 <= len(_clean(text)) <= MAX_TEXT:
                item = self.add(sid, text, title, source='auto')
                if item:
                    added.append(item)
        return added

    def update(self, item_id: str, text: str) -> dict:
        text = _clean(text)
        if not text:
            raise ValueError('记忆内容不能为空。')
        with self.lock:
            for entry in self.sessions.values():
                for item in entry['items']:
                    if item['id'] == item_id:
                        item.update(text=text, source='manual', at=time.time())
                        self._save()
                        return dict(item)
        raise ValueError('这条记忆已不存在。')

    def delete(self, item_id: str) -> None:
        with self.lock:
            for sid, entry in list(self.sessions.items()):
                kept = [item for item in entry['items'] if item['id'] != item_id]
                if len(kept) != len(entry['items']):
                    entry['items'] = kept
                    if not kept and sid != SELF:
                        self.sessions.pop(sid, None)
                    self._save()
                    return

    def set_auto(self, enabled: bool) -> bool:
        with self.lock:
            self.auto = bool(enabled)
            self._save()
            return self.auto

    def context(self, sid: str, include_self: bool = True) -> str:
        with self.lock:
            parts = []
            about = self.items(sid)
            if about:
                parts.append('关于对方的记忆（参考用，不要在回复里原样复述）：\n' + '\n'.join('- ' + i['text'] for i in about[-30:]))
            mine = self.items(SELF) if include_self else []
            if mine:
                parts.append('关于我自己的记忆：\n' + '\n'.join('- ' + i['text'] for i in mine[-20:]))
            return '\n\n'.join(parts)
