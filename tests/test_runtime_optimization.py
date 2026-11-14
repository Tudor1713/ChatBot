"""Offline regressions for launch identity, burst updates and worker failures."""
import json
import sys
import tempfile
import unittest
from concurrent.futures import Future
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from desk.controller import Controller
from desk.bridge import Bridge
from desk.tasks import ModelTasks

app = QApplication.instance() or QApplication([])


class RuntimeOptimizationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.capture = patch('desk.capture_service.CaptureService')
        self.capture.start()
        self.addCleanup(self.capture.stop)
        self.ctrl = Controller(Path(self.directory.name))
        self.addCleanup(self.ctrl.close)

    def test_burst_delivers_one_latest_snapshot(self):
        received = []
        self.ctrl.stateChanged.connect(received.append)
        for i in range(100):
            self.ctrl.status['detail'] = str(i)
            self.ctrl.emit()
        QTest.qWait(40)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['status']['detail'], '99')

    def test_close_discards_queued_update(self):
        received = []
        self.ctrl.stateChanged.connect(received.append)
        self.ctrl.emit()
        self.ctrl.close()
        QTest.qWait(40)
        self.assertEqual(received, [])

    def test_invalid_bridge_packet_never_reaches_controller(self):
        bridge = Bridge(self.ctrl)
        responses = []
        bridge.response.connect(lambda raw: responses.append(json.loads(raw)))
        with patch.object(self.ctrl, 'handle') as handle:
            for packet in ([], None, {'id': 'x', 'method': []},
                           {'id': {}, 'method': 'bootstrap'},
                           {'id': 'x', 'method': 'bootstrap', 'params': []}):
                bridge.request(json.dumps(packet))
            handle.assert_not_called()
        self.assertEqual(len(responses), 5)
        self.assertTrue(all(not response['ok'] for response in responses))

    def test_failed_process_start_closes_both_pipe_ends(self):
        tasks = ModelTasks()
        self.addCleanup(tasks.close)
        recv, send, process = Mock(), Mock(), Mock()
        process.start.side_effect = OSError('synthetic spawn failure')
        with patch.object(tasks.context, 'Pipe', return_value=(recv, send)), \
             patch.object(tasks.context, 'Process', return_value=process):
            with self.assertRaises(OSError):
                tasks.submit('test_connection', {})
        recv.close.assert_called_once()
        send.close.assert_called_once()
        process.close.assert_called_once()
        self.assertEqual(tasks.jobs, {})

    def test_bridge_returns_async_result_and_safe_failure(self):
        bridge = Bridge(self.ctrl)
        responses = []
        bridge.response.connect(lambda raw: responses.append(json.loads(raw)))
        future = Future()
        with patch.object(self.ctrl, 'handle', return_value=future):
            bridge.request(json.dumps({'id': 'async-ok', 'method': 'bootstrap'}))
        self.assertEqual(responses, [])
        future.set_result({'success': True})
        self.assertEqual(responses[-1]['data'], {'success': True})
        self.ctrl.store.secrets['api_key'] = 'synthetic-test-only'
        failure = Future()
        with patch.object(self.ctrl, 'handle', return_value=failure):
            bridge.request(json.dumps({'id': 'async-failure', 'method': 'bootstrap'}))
        failure.set_exception(RuntimeError('synthetic-test-only'))
        self.assertFalse(responses[-1]['ok'])
        self.assertNotIn('synthetic-test-only', responses[-1]['error'])

    def test_bridge_returns_immediate_result_and_rejects_oversized_packet(self):
        bridge = Bridge(self.ctrl)
        responses = []
        bridge.response.connect(lambda raw: responses.append(json.loads(raw)))
        bridge.request(json.dumps({'id': 'sync', 'method': 'bootstrap'}))
        self.assertTrue(responses[-1]['ok'])
        self.assertIn('current_session', responses[-1]['data'])
        with patch.object(self.ctrl, 'handle') as handle:
            bridge.request(' ' * 300001)
            handle.assert_not_called()
        self.assertFalse(responses[-1]['ok'])

    def test_second_instance_activates_owner_and_releases_on_exit(self):
        from desk.instance import SingleInstance
        first = SingleInstance(Path(self.directory.name))
        second = SingleInstance(Path(self.directory.name))
        self.addCleanup(first.close)
        self.addCleanup(second.close)
        received = []
        first.activated.connect(lambda: received.append(True))
        self.assertTrue(first.acquire())
        self.assertTrue(first.acquire())
        self.assertFalse(second.acquire())
        QTest.qWait(60)
        self.assertEqual(received, [True])
        first.close()
        self.assertTrue(second.acquire())


if __name__ == '__main__':
    unittest.main()
