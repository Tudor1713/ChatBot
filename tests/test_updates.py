"""Release checks use local fixtures; no requests to GitHub in this suite."""
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


class UpdateTests(unittest.TestCase):
    def release(self, version='2.7.0', **changes):
        return {'tag_name': 'v' + version, 'draft': False, 'prerelease': False,
                'published_at': '2026-11-14T00:00:00Z', 'body': '合成版本说明',
                'html_url': 'https://github.com/example/chatbot/releases/tag/v' + version,
                'assets': [{'name': 'ChatBot-' + version + '-Windows.zip', 'size': 123}], **changes}

    def test_numeric_versions_and_publish_filters(self):
        from desk.updates import select_release
        rows = [self.release('3.0.0', draft=True), self.release('2.11.0', prerelease=True),
                self.release('2.10.0'), self.release('2.9.0')]
        result = select_release(rows, '2.9.0', 'example/chatbot', 'win32')
        self.assertEqual(result['version'], '2.10.0')
        self.assertEqual(result['status'], 'available')
        self.assertEqual(select_release(rows, '2.10.0', 'example/chatbot', 'win32')['status'], 'current')

    def test_only_published_correct_repository_platform_assets_are_eligible(self):
        from desk.updates import select_release
        rows = [self.release(html_url='https://evil.example/releases/tag/v2.7.0'),
                self.release(published_at=None), self.release(assets=[]),
                self.release('2.8.0', assets=[{'name': 'ChatBot-2.8.0-macOS-arm64.zip', 'size': 100}]),
                self.release('99.0.0', html_url='https://github.com/example/chatbot/releases/tag/v99.0.0?x=1')]
        self.assertEqual(select_release(rows, '2.6.1', 'example/chatbot', 'win32')['status'], 'unpublished')

    def test_invalid_payload_is_safe_and_notes_are_bounded(self):
        from desk.updates import select_release
        with self.assertRaises(ValueError):
            select_release({}, '2.6.1', 'example/chatbot', 'win32')
        result = select_release([None, self.release(body='x' * 20000)], '2.6.1', 'example/chatbot', 'win32')
        self.assertLessEqual(len(result['notes']), 6000)

    def test_check_uses_fixed_api_no_credentials_or_user_data(self):
        from desk import updates
        seen = []
        def request(req, timeout):
            seen.append((req.full_url, dict(req.header_items()), timeout))
            return io.BytesIO(json.dumps([self.release()]).encode())
        with patch.object(updates, 'open_api', side_effect=request):
            self.assertEqual(updates.check_updates('2.6.1', 'example/chatbot', 'win32')['status'], 'available')
        self.assertEqual(seen[0][0], 'https://api.github.com/repos/example/chatbot/releases?per_page=30')
        self.assertNotIn('Authorization', seen[0][1])
        self.assertLessEqual(seen[0][2], 15)

    def test_disabled_invalid_repository_and_network_failure(self):
        from desk import updates
        with patch.object(updates, 'open_api', side_effect=OSError('private failure')) as request:
            self.assertEqual(updates.check_updates('2.6.1', '', 'win32')['status'], 'unconfigured')
            self.assertEqual(updates.check_updates('2.6.1', '../other', 'win32')['status'], 'error')
            request.assert_not_called()
            result = updates.check_updates('2.6.1', 'example/chatbot', 'win32')
        self.assertEqual(result['status'], 'error')
        self.assertNotIn('private failure', str(result))

    def test_oversized_response_is_rejected(self):
        from desk import updates
        with patch.object(updates, 'open_api', return_value=io.BytesIO(b' ' * (1024 * 1024 + 1))):
            self.assertEqual(updates.check_updates('2.6.1', 'example/chatbot', 'win32')['status'], 'error')
