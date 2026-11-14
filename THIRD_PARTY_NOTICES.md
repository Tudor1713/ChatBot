# Third-party notices

ChatBot 是独立开发的桌面应用，不代表任何第三方产品或服务，也不代表微信官方。

本文件只记录本项目运行时使用的外部依赖及其许可证；依赖的许可文本随程序存放在应用目录的 `licenses/` 下。

## Runtime components

Python (PSF), PySide6 / Qt (LGPLv3 or commercial), RapidOCR (Apache-2.0), ONNX Runtime (MIT), NumPy (BSD), Windows Capture (MIT), Pillow (HPND), and their transitive dependencies retain their respective licenses. Qt libraries are dynamically linked and are distributed as replaceable files in this application directory or macOS bundle. Corresponding upstream source is available from https://code.qt.io/cgit/pyside/pyside-setup.git/ and https://code.qt.io/cgit/qt/ . Installed package metadata and license files are preserved where provided by packaging hooks.

Work Agent 的 PDF 文字提取使用 `pypdf`（BSD-3-Clause，https://github.com/py-pdf/pypdf）。打包时保留其许可文件；扫描版 PDF 不会被误写为已有可读取文字。

WeFlow integration uses its local documented HTTP interface. No database-key extraction binaries or proprietary third-party components are redistributed by this application.

The optional local WeChat database reader uses `sqlcipher3` (Python binding: zlib/libpng-style license in its distributed LICENSE; PyPI metadata: MIT) and SQLCipher (BSD-3-Clause). Source: https://github.com/coleifer/sqlcipher3 and https://github.com/sqlcipher/sqlcipher . 适配器只读取本机当前已配置账号的本机配置数据库，不打包任何第三方专有组件；其数据库密钥仅保存在内存中，不写入 ChatBot 设置，也不生成明文数据库副本。

Some WeChat text payloads are Zstandard-compressed; `zstandard` (BSD-3-Clause, https://github.com/indygreg/python-zstandard) decodes those payloads locally with a bounded output size. Undecodable content is not treated as a replyable text message.

## Noto Sans SC

The UI bundles unmodified Noto Sans SC from Google Fonts under SIL Open Font License 1.1. The copyright and complete license are preserved in `ui/fonts/OFL.txt`. Source, pinned checksum, and build-time download details are in `ui/fonts/README.md`. No proprietary Windows font is redistributed.

## macOS credentials and speech

macOS credential storage uses `keyring` (MIT) with its system Keychain backend. Its packaged dependencies retain their licenses, including importlib_metadata/zipp (Apache-2.0), jaraco.classes/context/functools (MIT), and more-itertools (MIT). Sources and license metadata accompany the runtime. System speech uses the dynamically linked Qt TextToSpeech module and the installed operating-system voice; no voice-cloning model or third-party voice dataset is included.

## Native libraries

OpenCV (Apache-2.0) and its platform-specific native dependencies are bundled by its official wheels. Their `LICENSE` and `LICENSE-3RD-PARTY` files are included with the runtime licenses. On macOS, the replaceable GnuTLS library (LGPL-2.1-or-later) includes public cryptographic self-test vectors. The distribution audit recognizes only complete vectors with reviewed SHA-256 values in that specific native library; other private-key payloads remain rejected. The vectors were compared with [GnuTLS upstream self-tests](https://github.com/gnutls/gnutls/blob/99189278b2938188607e7d0d20bc80cc29b16a9d/lib/crypto-selftests-pk.c). No user credential is accepted through this rule.
