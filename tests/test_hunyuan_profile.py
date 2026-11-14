"""Offline transport policy; never contacts WorkBuddy."""
import sys,json,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from core.client import Route,post_json
from core.model_profile import profile_for,apply_model_profile
from test_engine import FakeOpener

class HunyuanProfileTests(unittest.TestCase):
    def test_highest_advertised_hy4_context_and_supported_effort(self):
        p=profile_for('hy4-preview-f')
        self.assertEqual(p['context_tokens'],1000000)
        self.assertEqual(p['effort'],'high')
        self.assertEqual(profile_for('hy4free')['context_tokens'],960000)
        self.assertEqual(profile_for('hy3')['context_tokens'],192000)

    def test_all_local_hunyuan_requests_include_thinking_and_full_output_budget(self):
        route=Route('http://127.0.0.1:8788/v1/chat/completions','hy4-preview-f','synthetic-test-key','chat')
        opener=FakeOpener(lambda r,p:{'choices':[{'message':{'content':'{}'}}]})
        with patch('urllib.request.build_opener',return_value=opener):
            post_json(route,{'model':route.model,'messages':[],'max_tokens':4096,'thinking':{'type':'disabled'}})
        payload=opener.requests[0][1]
        self.assertEqual(payload['reasoning_effort'],'high')
        self.assertEqual(payload['thinking'],{'type':'enabled'})
        self.assertEqual(payload['max_tokens'],64000)
        self.assertNotIn('context_length',payload) # Window is a model capability, not an API input.
        self.assertEqual(payload['temperature'],.9)

    def test_non_hunyuan_and_external_endpoints_are_unchanged(self):
        payload={'model':'hy3','max_tokens':12}
        self.assertEqual(apply_model_profile(Route('https://example.com/v1','hy3','x','chat'),payload),payload)
        self.assertEqual(apply_model_profile(Route('http://127.0.0.1:8788/v1','deepseek-v4.1-flash','x','chat'),payload),payload)

if __name__=='__main__':unittest.main()
