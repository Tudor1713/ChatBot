#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$(uname -s)" != Darwin ]]; then
  echo 'The macOS bundle must be built on macOS.' >&2
  exit 1
fi
PYTHON=.venv/bin/python
if [[ -e outputs/build/ChatBot.app ]]; then
  echo 'Use a clean build directory; an existing app bundle will not be overwritten.' >&2
  exit 1
fi
"$PYTHON" scripts/fetch_font.py
"$PYTHON" scripts/check_secrets.py --tree .
QT_QPA_PLATFORM=offscreen "$PYTHON" -m unittest discover -s tests -v
"$PYTHON" -m PyInstaller --noconfirm --distpath outputs/build --workpath work/build ChatBot.spec
resources=outputs/build/ChatBot.app/Contents/Resources
cp README.md LICENSE THIRD_PARTY_NOTICES.md "$resources/"
cp -R docs "$resources/"
mkdir -p "$resources/licenses"
"$PYTHON" scripts/collect_licenses.py --output "$resources/licenses/runtime"
/usr/bin/codesign --force --sign - outputs/build/ChatBot.app
/usr/bin/codesign --verify --deep --strict outputs/build/ChatBot.app
"$PYTHON" scripts/package_macos.py
