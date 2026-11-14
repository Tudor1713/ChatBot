"""Public GitHub release notifications. Never uploads state or installs code."""
from __future__ import annotations

import json
import re
import sys
import urllib.request

REPOSITORY = 'Tudor1713/ChatBot'
_REPO = re.compile(r'[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+\Z')
_VERSION = re.compile(r'v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z')


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Release API redirects are refused')


def open_api(request, timeout):
    return urllib.request.build_opener(_NoRedirect()).open(request, timeout=timeout)


def select_release(rows, current, repository, platform):
    if not isinstance(rows, list) or not _REPO.fullmatch(repository):
        raise ValueError('Invalid release response')
    installed = _VERSION.fullmatch(current)
    if not installed:
        raise ValueError('Invalid installed version')
    candidates = []
    for row in rows[:30]:
        if not isinstance(row, dict) or row.get('draft') is not False or row.get('prerelease') is not False or not row.get('published_at'):
            continue
        tag = row.get('tag_name')
        match = _VERSION.fullmatch(tag) if isinstance(tag, str) else None
        if not match:
            continue
        version = '.'.join(match.groups())
        url = f'https://github.com/{repository}/releases/tag/{tag}'
        if row.get('html_url') != url:
            continue
        assets = row.get('assets')
        suffix = '-Windows.zip' if platform == 'win32' else '-macOS-' if platform == 'darwin' else None
        if not suffix or not isinstance(assets, list):
            continue
        prefix = f'ChatBot-{version}'
        usable = any(isinstance(a, dict) and isinstance(a.get('name'), str)
                     and (a['name'] == prefix + suffix if platform == 'win32' else
                          a['name'].startswith(prefix + suffix) and a['name'].endswith('.zip'))
                     and isinstance(a.get('size'), int) and a['size'] > 0 for a in assets)
        if not usable:
            continue
        notes = row.get('body') if isinstance(row.get('body'), str) else ''
        candidates.append((tuple(map(int, match.groups())), version, url, notes[:6000]))
    if not candidates:
        return {'status': 'unpublished', 'message': '暂时没有适用于此系统的正式发布版。'}
    number, version, url, notes = max(candidates, key=lambda r: r[0])
    newer = number > tuple(map(int, installed.groups()))
    return {'status': 'available' if newer else 'current', 'version': version,
            'url': url, 'notes': notes,
            'message': f'发现 ChatBot {version}，可前往发布页下载。' if newer else '当前已是最新版本。'}


def check_updates(current, repository=REPOSITORY, platform=None):
    if not repository:
        return {'status': 'unconfigured', 'message': '尚未设置更新仓库。'}
    try:
        if not _REPO.fullmatch(repository):
            raise ValueError('Invalid repository')
        request = urllib.request.Request(
            f'https://api.github.com/repos/{repository}/releases?per_page=30',
            headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'ChatBot-Update-Check',
                     'X-GitHub-Api-Version': '2022-11-28'})
        with open_api(request, timeout=12) as response:
            raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError('Oversized release response')
        return select_release(json.loads(raw), current, repository, platform or sys.platform)
    except Exception:
        return {'status': 'error', 'message': '暂时无法检查更新，请确认网络后重试；仍可正常使用。'}
