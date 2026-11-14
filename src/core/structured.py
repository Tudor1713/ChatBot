"""Conservative JSON transport helpers: never turn reasoning into an answer.

Repairs are limited to whitespace/control characters and trailing commas outside
strings. Incomplete fields may be recovered only when their value fully decodes.
No evaluation, fabricated fields, network IO or logging is performed here.
"""
from __future__ import annotations
import ipaddress
import json
import re
from itertools import islice
from urllib.parse import urlsplit

class StructuredOutputError(ValueError):
    def __init__(self, reason='invalid', retryable=True):
        self.reason=reason
        self.retryable=retryable
        super().__init__({'empty':'模型返回了空正文','truncated':'模型输出被截断',
                          'refusal':'模型未提供本次结果','invalid':'模型返回的结构尚不可用'}.get(reason,'模型返回的结构尚不可用'))

def completion_text(response):
    try:
        choice=response['choices'][0]; message=choice['message']
        if message.get('refusal'):raise StructuredOutputError('refusal',False)
        content=message.get('content')
        if isinstance(content,list):
            content=''.join(p.get('text','') for p in content if isinstance(p,dict) and isinstance(p.get('text'),str))
        if not isinstance(content,str) or not content.strip():
            if isinstance(message.get('parsed'),(dict,list)):
                content=json.dumps(message['parsed'],ensure_ascii=False)
            elif len(message.get('tool_calls') or [])==1:
                content=message['tool_calls'][0].get('function',{}).get('arguments')
        if not isinstance(content,str) or not content.strip():
            raise StructuredOutputError('truncated' if choice.get('finish_reason')=='length' else 'empty')
        return content
    except StructuredOutputError:raise
    except (KeyError,IndexError,TypeError,AttributeError):
        raise StructuredOutputError('invalid') from None

def clean_json_text(text):
    text=str(text).lstrip('\ufeff').strip()
    # A complete visible think block is boilerplate; an unfinished one contains
    # no trustworthy final answer, even if it quotes example JSON.
    text=re.sub(r'<think>.*?</think>','',text,flags=re.S|re.I).strip()
    if re.search(r'<think>',text,re.I):raise StructuredOutputError('truncated')
    result=[];quoted=False;escaped=False
    for i,ch in enumerate(text):
        if quoted:
            if escaped:result.append(ch);escaped=False
            elif ch=='\\':result.append(ch);escaped=True
            elif ch=='"':result.append(ch);quoted=False
            elif ord(ch)<32:result.append(json.dumps(ch)[1:-1])
            else:result.append(ch)
        elif ch=='"':quoted=True;result.append(ch)
        elif ch==',':
            j=i+1
            while j<len(text) and text[j].isspace():j+=1
            if j>=len(text) or text[j] not in '}]':result.append(ch)
        else:result.append(ch)
    return ''.join(result)

def json_values(text):
    cleaned=clean_json_text(text)
    try:
        whole=json.loads(cleaned)
        if isinstance(whole,str):cleaned=clean_json_text(whole)
        elif isinstance(whole,(dict,list)):
            yield whole
    except ValueError:pass
    decoder=json.JSONDecoder()
    for match in islice(re.finditer(r'[\[{]',cleaned),512):
        try:
            value,_=decoder.raw_decode(cleaned[match.start():])
            if isinstance(value,(dict,list)):yield value
        except ValueError:continue

def complete_field(text,key):
    cleaned=clean_json_text(text)
    pattern=re.escape(json.dumps(str(key)))+r'\s*:\s*'
    for match in re.finditer(pattern,cleaned):
        try:return json.JSONDecoder().raw_decode(cleaned[match.end():])[0]
        except ValueError:continue
    return None

def structured_options(route,payload):
    result={**payload,'response_format':{'type':'json_object'}}
    host=urlsplit(route.url).hostname or ''
    try:loopback=ipaddress.ip_address(host).is_loopback
    except ValueError:loopback=host=='localhost'
    if host=='openrouter.ai':result['reasoning']={'enabled':False}
    elif host=='api.deepseek.com':result['thinking']={'type':'disabled'}
    elif loopback and route.model.lower().startswith('deepseek'):
        # The locally installed WorkBuddy gateway accepts both switches and
        # otherwise injects thinking=enabled plus the default effort level.
        result.update(thinking={'type':'disabled'},reasoning_effort='none')
    return result
