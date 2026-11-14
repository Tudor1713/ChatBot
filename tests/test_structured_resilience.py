"""Offline reproductions of empty, truncated and noncanonical model outputs."""
import json,sys
import io,urllib.error
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from core.client import Route,ProviderError,post_json
from core.engine import analyze
from core.draft import parse_bundle,draft_bundle
from core.questions import judge_questions
from test_engine import FakeOpener,decisions,MESSAGES

ROUTE=Route('http://127.0.0.1:8788/v1/chat/completions','deepseek-v4.1-flash','synthetic-test-key','chat_json')
CFG={'base_url':'http://127.0.0.1:8788/v1','model_name':ROUTE.model,'api_key':'synthetic-test-key'}
def response(content,finish='stop',**message):
    return {'choices':[{'finish_reason':finish,'message':{'content':content,**message}}], 'usage':{'total_tokens':12}}
def valid():return {'answers':{'true_intent':{'type':'choice','choice':'casual_chat','confidence':.8}}}
def bundle():return {'candidates':[f'合成建议{i}' for i in range(5)],'topics':{k:[{'title':'合成话题','opener':'聊聊这个？','reason':'待确认','evidence_ids':[]}] for k in ('missed','their','mine')}}

class AdapterResilienceTests(unittest.TestCase):
    def call(self,outputs,route=ROUTE):
        values=iter(outputs);opener=FakeOpener(lambda r,p:next(values))
        with patch('urllib.request.build_opener',return_value=opener):
            result=post_json(route,{'questions':judge_questions(),'state':{'chat':{'messages':MESSAGES}}},timeout=10)
        return result,opener.requests

    def test_gateway_request_prevents_reasoning_only_output_and_requires_json(self):
        result,calls=self.call([response(json.dumps(valid()))])
        p=calls[0][1]
        self.assertEqual(p['response_format'],{'type':'json_object'})
        self.assertEqual(p['thinking'],{'type':'disabled'})
        self.assertEqual(p['reasoning_effort'],'none')
        self.assertGreaterEqual(p['max_tokens'],4096)

    def test_content_blocks_are_read_as_final_text(self):
        result,_=self.call([response([{'type':'text','text':json.dumps(valid())}])])
        self.assertEqual(result['answers']['true_intent']['choice'],'casual_chat')

    def test_empty_truncated_response_retries_once_and_does_not_use_reasoning_as_answer(self):
        result,calls=self.call([response(None,'length',reasoning_content='private internal reasoning'),response(json.dumps(valid()))])
        self.assertEqual(len(calls),2);self.assertIn('true_intent',result['answers'])
        self.assertNotIn('private internal reasoning',json.dumps([payload for _,payload,_ in calls]))

    def test_complete_fields_survive_a_truncated_tail_without_fabrication(self):
        partial='{"answers":{"true_intent":{"type":"choice","choice":"casual_chat","confidence":0.8},"danger_level":{"score":'
        result,calls=self.call([response(partial,'length')])
        self.assertIn('true_intent',result['answers']);self.assertNotIn('danger_level',result['answers'])
        self.assertEqual(len(calls),1)

    def test_trailing_comma_bom_and_nested_answers_are_accepted(self):
        text='\ufeff说明：```json\n{"data":{"answers":{"true_intent":{"choice":"casual_chat","confidence":"0.8",},},},}\n```'
        result,_=self.call([response(text)])
        self.assertEqual(result['answers']['true_intent']['confidence'],.8)

    def test_invalid_output_is_bounded_and_error_does_not_blame_model_or_echo_content(self):
        opener=FakeOpener(lambda r,p:response('synthetic-private-chat not json'))
        with patch('urllib.request.build_opener',return_value=opener):
            with self.assertRaises(ProviderError) as caught:
                post_json(ROUTE,{'questions':judge_questions(),'state':{}},timeout=10)
        self.assertEqual(len(opener.requests),2)
        self.assertNotIn('synthetic-private-chat',str(caught.exception))
        self.assertNotIn('请换一个',str(caught.exception))

    def test_arbitrary_gateway_does_not_receive_deepseek_specific_switches(self):
        route=Route('https://custom.example/v1/chat/completions',ROUTE.model,'test','chat_json')
        result,calls=self.call([response(json.dumps(valid()))],route)
        self.assertNotIn('thinking',calls[0][1]);self.assertNotIn('reasoning_effort',calls[0][1])

    def test_semantically_invalid_answers_retry_then_valid_output(self):
        result,calls=self.call([response('{"answers":{"true_intent":{"choice":"made_up"}}}'),response(json.dumps(valid()))])
        self.assertEqual(len(calls),2)
        self.assertEqual(result['answers']['true_intent']['choice'],'casual_chat')

class DraftResilienceTests(unittest.TestCase):
    def test_reply_object_with_preamble_and_trailing_comma_keeps_all_directions(self):
        text='回复如下：\n'+json.dumps(bundle(),ensure_ascii=False)
        text=text[:-1]+',}'
        candidates,topics=parse_bundle(response(text),set())
        self.assertEqual(len(candidates),5);self.assertTrue(all(topics.values()))

    def test_reply_candidates_survive_truncated_topics(self):
        text='{"candidates":'+json.dumps(bundle()['candidates'])+',"topics":{"their":'
        candidates,topics=parse_bundle(response(text,'length'),set())
        self.assertEqual(len(candidates),5)

    def test_drafting_also_disables_gateway_thinking_and_can_retry_empty_body(self):
        values=iter([response(None,'length'),response(json.dumps(bundle()))])
        calls=[]
        def transport(route,payload,**kw):calls.append(payload);return next(values)
        with patch('core.draft.post_json',transport):
            candidates,topics,usage,memory=draft_bundle(Route(ROUTE.url,ROUTE.model,'test','chat'),{'chat':{'messages':[]}},timeout=10)
        self.assertEqual(len(candidates),5);self.assertEqual(len(calls),2)
        self.assertEqual(calls[0]['thinking'],{'type':'disabled'})
        self.assertGreaterEqual(calls[0]['max_tokens'],4096)

class IndependentResultsTests(unittest.TestCase):
    def test_judgment_failure_keeps_five_replies_and_topics_without_fake_ranking(self):
        topics={k:[{'title':'合成','opener':'合成','reason':'待确认','evidence_ids':[]}] for k in ('missed','their','mine')}
        with patch('core.engine._ask',side_effect=ProviderError('判断输出为空')),patch('core.engine.draft_bundle',return_value=(bundle()['candidates'],topics,{})):
            result=analyze(MESSAGES,CFG)
        self.assertEqual(len(result['candidates']),5);self.assertTrue(result['topics'])
        self.assertFalse(result['judgment_available']);self.assertIsNone(result['best_index'])
        self.assertIsNone(result['risk']);self.assertEqual(result['answers'],{})
        self.assertIn('判断',result['warning'])

    def test_total_failure_remains_an_error_and_never_makes_up_replies(self):
        with patch('core.engine._ask',side_effect=ProviderError('判断不可用')),patch('core.engine.draft_bundle',side_effect=ProviderError('生成不可用')):
            with self.assertRaises(ProviderError):analyze(MESSAGES,CFG)

class TransportCompatibilityTests(unittest.TestCase):
    def test_unsupported_json_mode_falls_back_once_but_keeps_no_thinking_switch(self):
        def callback(req,payload):
            if 'response_format' in payload:
                error=b'{"error":{"param":"response_format","message":"response_format is not supported"}}'
                raise urllib.error.HTTPError(req.full_url,400,'bad request',{},io.BytesIO(error))
            return response(json.dumps(valid()))
        opener=FakeOpener(callback)
        with patch('urllib.request.build_opener',return_value=opener):
            result=post_json(ROUTE,{'questions':judge_questions(),'state':{}},timeout=10)
        self.assertEqual(len(opener.requests),2)
        self.assertNotIn('response_format',opener.requests[1][1])
        self.assertEqual(opener.requests[1][1]['thinking'],{'type':'disabled'})

    def test_authentication_errors_never_retry_with_unauthenticated_or_changed_settings(self):
        def callback(req,payload):raise urllib.error.HTTPError(req.full_url,401,'private',{},io.BytesIO(b'private'))
        opener=FakeOpener(callback)
        with patch('urllib.request.build_opener',return_value=opener):
            with self.assertRaises(ProviderError):post_json(ROUTE,{'questions':judge_questions(),'state':{}},timeout=10)
        self.assertEqual(len(opener.requests),1)

    def test_transport_retries_share_timeout_budget(self):
        clock=[0]
        def callback(req,payload):clock[0]+=3;raise TimeoutError('private')
        opener=FakeOpener(callback)
        with patch('urllib.request.build_opener',return_value=opener),patch('core.client.time.monotonic',side_effect=lambda:clock[0]),patch('core.client.time.sleep'):
            with self.assertRaises(ProviderError):post_json(Route(ROUTE.url,ROUTE.model,'test','chat'),{},timeout=2,retries=2)
        self.assertEqual(len(opener.requests),1)

if __name__=='__main__':unittest.main()
