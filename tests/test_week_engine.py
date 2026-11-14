import json,sys,time
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from core.engine import analyze
from test_engine import decisions

class WeekEngineTests(unittest.TestCase):
    def test_full_week_reaches_model_and_all_five_are_ranked(self):
        now=time.time()
        rows=[{'id':f'm{i}','side':'me' if i%2 else 'other','text':f'合成{i}','timestamp':now-i} for i in range(410)]
        seen=[]
        def draft(route,payload,timeout=0,**kwargs):
            material=json.loads(payload['messages'][-1]['content']);seen.append(material)
            value={'candidates':[f'回复{i}' for i in range(5)],'topics':{k:[{'title':'话题','opener':'聊聊这个？','reason':'前文提过','evidence_ids':['m2']}] for k in ('missed','their','mine')}}
            return {'choices':[{'message':{'content':json.dumps(value)}}]}
        def judge(route,payload,timeout=0):
            seen.append(payload['state']);return decisions(payload)
        cfg={'base_url':'http://127.0.0.1:9999/v1','model_name':'synthetic','api_key':'test', 'context_days':7,'my_interests':'摄影'}
        with patch('core.draft.post_json',draft),patch('core.engine.post_json',judge):
            result=analyze(rows,cfg,context_meta={'days':7,'complete':True,'message_count':410})
        self.assertEqual(len(result['candidates']),5)
        self.assertEqual(len(result['topics']),3)
        self.assertEqual(result['best_index'],1)
        self.assertTrue(all(len(s['chat']['messages'])==410 for s in seen))
        self.assertEqual(result['context_window']['message_count'],410)
        self.assertEqual(result['topics']['their'][0]['evidence'][0]['text'],'合成2')

if __name__=='__main__':unittest.main()
