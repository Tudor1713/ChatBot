"""WorkBuddy capabilities checked 2026-11-09; no network or credential IO.

Window sizes are model capabilities, not invented Chat Completions fields.
"""
from urllib.parse import urlsplit
import ipaddress

def profile_for(model):
    model=str(model).lower()
    if model=='hy4-preview-f':context=1000000
    elif model.startswith(('hy4','hunyuan-4')):context=960000
    elif model.startswith(('hy3','hunyuan-3')):context=192000
    else:return None
    return {'context_tokens':context,'max_output_tokens':64000,'effort':'high'}

def apply_model_profile(route,payload):
    profile=profile_for(route.model);host=urlsplit(route.url).hostname or ''
    try:local=ipaddress.ip_address(host).is_loopback
    except ValueError:local=host=='localhost'
    if not profile or not local:return payload
    # This shared budget includes reasoning and final content.
    return {**payload,'reasoning_effort':profile['effort'],'thinking':{'type':'enabled'},
            'max_tokens':profile['max_output_tokens'],'temperature':.9,'top_p':1}
