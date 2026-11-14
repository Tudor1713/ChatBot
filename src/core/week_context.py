"""Rolling seven-day conversation context. No IO or model calls."""
from __future__ import annotations
from datetime import datetime
import math

WEEK_SECONDS = 7 * 86400
MAX_CONTEXT_CHARS = 400000

def timestamp(value):
    if isinstance(value, bool): return None
    if isinstance(value, (int, float)):
        n=float(value)
        if not math.isfinite(n) or n <= 0: return None
        return n / 1000 if n > 1e12 else n
    if isinstance(value, str):
        try: return timestamp(float(value))
        except ValueError:
            try: return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
            except (ValueError, OverflowError): return None
    return None

def select_week(messages, now, *, complete=False, source='collected'):
    start=now-WEEK_SECONDS; selected=[]; seen=set(); unknown=0
    for m in messages:
        stamp=timestamp(m.get('timestamp'))
        if stamp is not None and not start <= stamp <= now: continue
        identity=m.get('id') or (stamp,m.get('side'),m.get('text'),m.get('sender'))
        if identity in seen: continue
        seen.add(identity)
        item=dict(m)
        if stamp is None: unknown+=1
        else: item['timestamp']=stamp
        selected.append(item)
    # Undated OCR remains visible but never claims seven-day completeness.
    selected.sort(key=lambda m:timestamp(m.get('timestamp')) or now)
    media=sum(m.get('kind','text') not in ('text','') for m in selected)
    meta={'days':7,'start':start,'end':now,'message_count':len(selected),
          'complete':bool(complete and not unknown),'source':source,
          'unknown_time_count':unknown,'media_count':media,
          'scope':'当前会话 · 本机可用记录'}
    return selected,meta

def collect_week(fetch_page, now, *, source='wechat_db'):
    rows=[]; cursor=None; cursors=set(); complete=False
    while True:
        page=fetch_page(cursor)
        if not isinstance(page,dict) or not isinstance(page.get('items'),list):
            raise ValueError('最近7天记录读取失败：分页格式无效。')
        if page.get('available') is False:
            raise ValueError('最近7天记录来源当前不可用，请检查连接。')
        batch=page['items']; rows.extend(batch)
        dates=[timestamp(m.get('timestamp')) for m in batch]
        if any(t is not None and t < now-WEEK_SECONDS for t in dates) or not page.get('has_more'):
            complete=True;break
        nxt=page.get('next_cursor')
        signature=repr(nxt)
        if nxt is None or signature in cursors or not batch:
            raise ValueError('最近7天记录未读完：分页游标没有前进，请重新读取。')
        cursors.add(signature);cursor=nxt
    return select_week(rows,now,complete=complete,source=source)

def build_week_state(messages,config,meta,background='',reply_to=None):
    cleaned=[]
    for i,m in enumerate(messages):
        side=m.get('side',m.get('from'))
        if side=='her':side='other'
        text=m.get('text')
        if side not in ('me','other','unknown') or not isinstance(text,str) or not text.strip():continue
        item={'id':str(m.get('id') or f'context-{i}'),'from':side,'text':text.strip()}
        if m.get('sender_name') or m.get('sender'):item['name']=str(m.get('sender_name') or m['sender'])[:200]
        if m.get('timestamp'):item['timestamp']=m['timestamp']
        if m.get('kind'):item['kind']=m['kind']
        cleaned.append(item)
    if sum(len(m['text']) for m in cleaned)>MAX_CONTEXT_CHARS:
        raise ValueError('最近7天文字超过40万字的单次分析上限，未截断或提交；请先缩短范围。')
    chat={'relationship':str(config.get('relationship') or '未指定关系'),
          'messages':cleaned,'latest_from':cleaned[-1]['from'] if cleaned else 'other',
          'is_group':any('name' in m for m in cleaned)}
    if reply_to:chat['reply_to']=str(reply_to)
    return {'chat':chat,'context_window':dict(meta),'background':str(background or '')[:16000],
            'my_interests':str(config.get('my_interests') or '')[:2000]}
