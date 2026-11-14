"""Updates travel through the native bridge without model calls."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from desk.controller import Controller
APP = QApplication.instance() or QApplication([])


class ControllerUpdateTests(unittest.TestCase):
    def test_async_check_snapshot_and_single_notification(self):
        with tempfile.TemporaryDirectory() as folder:
            controller = Controller(Path(folder))
            try:
                events = []
                controller.toast.connect(lambda message, level: events.append(message))
                state = {'status': 'available', 'version': '2.7.0', 'message': '合成新版本',
                         'url': 'https://github.com/Tudor1713/ChatBot/releases/tag/v2.7.0'}
                with patch('desk.updates.check_updates', return_value=state):
                    self.assertEqual(controller.handle('check_updates', {}).result(2), state)
                    QTest.qWait(50)
                self.assertEqual(controller.snapshot()['updates'], state)
                controller._on_update_checked(state)
                self.assertEqual(len(events), 1)
                with patch('desk.controller.QDesktopServices.openUrl') as open_url:
                    controller.handle('open_update_release', {})
                    self.assertEqual(open_url.call_args.args[0].toString(), state['url'])
            finally:
                controller.close()

    def test_no_release_link_until_verified_and_close_discards_result(self):
        with tempfile.TemporaryDirectory() as folder:
            controller = Controller(Path(folder))
            with self.assertRaises(ValueError):
                controller.handle('open_update_release', {})
            controller.close()
            controller._on_update_checked({'status': 'available'})
            self.assertEqual(controller.update_state['status'], 'idle')
