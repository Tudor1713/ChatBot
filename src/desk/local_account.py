"""DPAPI-protected account for a user's explicitly connected local WeChat.

Only validated raw database keys are stored. This module never scans processes,
exports messages, or makes network requests.
"""
import base64
import json
import os
from pathlib import Path
import re
from .store import _crypt, _atomic

def _validate(record):
    if not isinstance(record,dict):raise ValueError('本机微信连接配置无效。')
    root=Path(str(record.get('root') or '')).expanduser()
    keys=record.get('keys');wxid=record.get('wxid')
    if (not root.is_absolute() or '..' in root.parts or not root.is_dir() or root.is_symlink()
        or not isinstance(wxid,str) or not re.fullmatch(r'[A-Za-z0-9_@.\-]{1,256}',wxid)
        or not isinstance(keys,dict) or not 1<=len(keys)<=10000
        or any(not re.fullmatch(r'[a-fA-F0-9]{32}',str(k)) or not re.fullmatch(r'[a-fA-F0-9]{64}',str(v)) for k,v in keys.items())):
        raise ValueError('本机微信连接配置无效。')
    return {'root':str(root.resolve()),'wxid':wxid,'keys':{k.lower():v.lower() for k,v in keys.items()}}

def save_account(path,root,wxid,keys):
    record=_validate({'root':str(root),'wxid':wxid,'keys':keys})
    sealed=base64.b64encode(_crypt(json.dumps(record).encode('utf-8'))).decode('ascii')
    _atomic(Path(path),{'version':1,'protected':sealed})

def load_account(path=None):
    if path is None:
        directory=os.environ.get('CHATBOT_DATA_DIR')
        if not directory:raise ValueError('尚未连接本机微信数据库。')
        path=Path(directory)/'wechat-account.json'
    path=Path(path)
    try:
        if path.is_symlink() or path.stat().st_size>2*1024*1024:raise ValueError()
        obj=json.loads(path.read_text(encoding='utf-8'))
        record=json.loads(_crypt(base64.b64decode(obj['protected'],validate=True),True))
        return _validate(record)
    except Exception:
        raise ValueError('无法读取当前用户的本机微信连接，请重新连接。') from None
