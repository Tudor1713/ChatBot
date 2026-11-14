"""Public product and package identity must be consistent."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BrandingTests(unittest.TestCase):
    def test_build_and_launcher_use_current_product(self):
        spec = ROOT / 'ChatBot.spec'
        self.assertTrue(spec.is_file())
        self.assertIn("name='ChatBot'", spec.read_text(encoding='utf-8'))
        self.assertTrue((ROOT / '启动ChatBot.cmd').is_file())
        build = (ROOT / 'scripts/build.ps1').read_text(encoding='utf-8-sig')
        self.assertIn('ChatBot.spec', build)
        self.assertIn("$buildOutput 'ChatBot'", build)

    def test_code_uses_one_product_name(self):
        # Escapes let the regression guard itself keep the current brand only.
        old = ('\u77e5\u5f26', '\u542c\u7b3a',
               '\x7a\x68\x69\x78\x69\x61\x6e', '\x74\x69\x6e\x67\x6a\x69\x61\x6e')
        hits = []
        for folder in ('src', 'ui', 'scripts', 'tests', '.github'):
            for path in (ROOT / folder).rglob('*'):
                if path.suffix not in {'.py', '.js', '.css', '.html', '.svg', '.ps1', '.sh', '.yml'}:
                    continue
                text = path.read_text(encoding='utf-8-sig').casefold()
                if any(name in text or name in path.name.casefold() for name in old):
                    hits.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(hits, [])
