"""Synthetic regression for filling before background observation starts."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from PySide6.QtWidgets import QApplication
from desk.controller import Controller
from desk.store import Store
from desk.capture_service import CaptureService

APP = QApplication.instance() or QApplication([])


class ConnectionLifecycleTests(unittest.TestCase):
    def test_switching_to_archive_stops_background_observation(self):
        service = CaptureService(lambda *_: None)
        service._config = {'source': 'wechat_db'}
        service._wanted.set()
        service._once.set()
        epoch = service._control_epoch
        service.configure({'source': 'archive'})
        self.assertFalse(service._wanted.is_set())
        self.assertFalse(service._once.is_set())
        self.assertGreater(service._control_epoch, epoch)

    def setUp(self):
        for name, value in (('keychain_set', None), ('keychain_get', '{}')):
            mocked = patch('desk.platforms.' + name, return_value=value)
            mocked.start()
            self.addCleanup(mocked.stop)

    def test_history_fill_uses_saved_source_while_observation_is_paused(self):
        with tempfile.TemporaryDirectory() as folder:
            Store(Path(folder)).save_config({'source': 'wechat_db'})
            controller = Controller(Path(folder))
            try:
                controller.sessions['synthetic'] = {'id': 'synthetic', 'title': '合成会话', 'source': 'wechat_db', 'messages': []}
                controller.current_id = 'synthetic'
                entry = controller.reply_history.record('synthetic', '合成会话', '合成来信', [{'text': '历史建议'}])
                capture = controller.capture
                with patch.object(capture, '_fill_db_worker', return_value={'success': True}), \
                     patch.object(capture, '_ensure_thread', side_effect=capture._drain_requests):
                    result = controller.handle('fill_history_reply', {'session_id': 'synthetic', 'entry_id': entry, 'index': 0}).result(2)
                self.assertTrue(result['success'])
                self.assertFalse(capture._wanted.is_set())
            finally:
                controller.close()

    def test_saved_database_source_can_fill_without_starting_observation(self):
        with tempfile.TemporaryDirectory() as folder:
            Store(Path(folder)).save_config({'source': 'wechat_db'})
            controller = Controller(Path(folder))
            try:
                controller.sessions['synthetic'] = {'id': 'synthetic', 'title': '合成会话',
                    'source': 'wechat_db', 'messages': []}
                controller.results['synthetic'] = {'candidates': [{'text': '合成建议'}]}
                capture = controller.capture
                with patch.object(capture, '_fill_db_worker', return_value={'success': True}) as fill, \
                     patch.object(capture, '_send_db_worker') as send, \
                     patch.object(capture, '_ensure_thread', side_effect=capture._drain_requests):
                    result = controller.handle('fill_reply', {'session_id': 'synthetic', 'index': 0}).result(2)
                self.assertTrue(result['success'])
                fill.assert_called_once()
                send.assert_not_called()
                self.assertFalse(capture._wanted.is_set())
            finally:
                controller.close()

    def test_saving_source_synchronizes_capture_without_arming_send(self):
        with tempfile.TemporaryDirectory() as folder:
            controller = Controller(Path(folder))
            try:
                controller.handle('save_config', {'config': {'source': 'wechat_db'}})
                self.assertEqual(controller.capture._config.get('source'), 'wechat_db')
                self.assertFalse(controller.capture._wanted.is_set())
                self.assertFalse(controller.auto_policy['enabled'])
            finally:
                controller.close()
