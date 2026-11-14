"""Read only one chosen conversation: rolling seven days, or the latest 200 when the week is thin.

近 7 天不足 150 条时，改读这个会话最近的 200 条作为上下文（不论时间）。
"""
import time
from core.week_context import collect_week, select_week, timestamp, WEEK_SECONDS
from .store import normalize_title

MIN_WEEK_MESSAGES = 150
LATEST_FALLBACK = 200


def _clean(rows):
    return [{k: v for k, v in row.items() if k != '_cursor'} for row in rows]


def _native_week(reader, sid, now):
    def page(cursor):
        rows = reader.messages(sid, limit=101, before=cursor,
                               start_time=now - WEEK_SECONDS, end_time=now)
        selected = rows[:100]
        return {'items': _clean(reversed(selected)),
                'has_more': len(rows) > 100,
                'next_cursor': selected[-1]['_cursor'] if len(rows) > 100 else None}
    return collect_week(page, now, source='wechat_db')


def _native_latest(reader, sid, limit=LATEST_FALLBACK):
    # 数据库按时间倒序返回；转成正序。
    return _clean(reversed(reader.messages(sid, limit=limit)))


def _paged_latest(fetch, limit=LATEST_FALLBACK):
    rows, cursor, seen = [], None, set()
    while len(rows) < limit:
        page = fetch(cursor)
        if not isinstance(page, dict) or not isinstance(page.get('items'), list) or page.get('available') is False:
            break
        rows.extend(page['items'])
        nxt = page.get('next_cursor')
        if not page.get('has_more') or nxt is None or repr(nxt) in seen or not page['items']:
            break
        seen.add(repr(nxt))
        cursor = nxt
    unique = {}
    for row in rows:
        unique[row.get('id') or (row.get('timestamp'), row.get('side'), row.get('text'))] = row
    ordered = sorted(unique.values(), key=lambda m: timestamp(m.get('timestamp')) or 0)
    return ordered[-limit:]


def latest_meta(messages, now, source, week_count):
    stamps = [timestamp(m.get('timestamp')) for m in messages]
    known = [s for s in stamps if s]
    return {'days': None, 'mode': 'latest', 'start': min(known) if known else None, 'end': now,
            'message_count': len(messages), 'week_count': week_count, 'complete': True, 'source': source,
            'unknown_time_count': sum(1 for s in stamps if not s),
            'media_count': sum(m.get('kind', 'text') not in ('text', '') for m in messages),
            'scope': f'最近 {len(messages)} 条（近 7 天只有 {week_count} 条）'}


def _with_fallback(week, latest_loader, now, source):
    messages, meta = week
    if meta.get('message_count', 0) >= MIN_WEEK_MESSAGES:
        return messages, meta
    try:
        latest = latest_loader()
    except (ValueError, RuntimeError, OSError):
        return messages, meta
    if len(latest) <= len(messages):
        return messages, meta
    return latest, latest_meta(latest, now, source, meta.get('message_count', 0))


def read_week_context(session, config, fetch_page, native_factory=None, now=None):
    now = time.time() if now is None else now
    source = session.get('source', 'ocr'); sid = session.get('id', '')
    if source == 'wechat_db' and native_factory:
        reader = native_factory()
        return _with_fallback(_native_week(reader, sid, now), lambda: _native_latest(reader, sid), now, source)
    if source in ('wechat_db', 'weflow', 'import'):
        fetch = lambda cursor: fetch_page(config, sid, cursor, 100)
        return _with_fallback(collect_week(fetch, now, source=source), lambda: _paged_latest(fetch), now, source)
    if source == 'ocr' and native_factory:
        try: reader = native_factory()
        except (ValueError, RuntimeError): reader = None
        if reader:
            title = normalize_title(session.get('title', '')); matches = []
            for offset in range(0, 20000, 200):
                page = reader.sessions(200, offset)
                matches.extend(row for row in page if title and normalize_title(row.get('name', '')) == title)
                if len(page) < 200: break
            else: raise ValueError('会话目录未读完，无法唯一核验最近7天所属联系人。')
            if len(matches) > 1: raise ValueError('存在同名联系人，无法确定最近7天属于哪段对话；请从全局会话选择。')
            if len(matches) == 1:
                talker = matches[0]['id']
                return _with_fallback(_native_week(reader, talker, now), lambda: _native_latest(reader, talker), now, 'wechat_db')
    collected = session.get('messages', [])
    return _with_fallback(select_week(collected, now, complete=False, source=source),
                          lambda: list(collected)[-LATEST_FALLBACK:], now, source)
