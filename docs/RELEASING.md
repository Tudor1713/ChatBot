# GitHub 发版与更新提醒

更新来源固定为 `Tudor1713/ChatBot` 的 GitHub Releases。仅上传源码不会触发客户端版本提示。

1. 修改 `src/desk/version.py`、`scripts/windows_version.txt` 和前端演示默认版本，使用递增的三段数字，例如 `2.6.2`。
2. 新增 `docs/releases/2.6.2.md`，说明变更和实际验证范围。
3. 执行源码隐私扫描、单元测试、合成 UI 检查与构建。使用 `scripts/package_portable.py` 为全新构建目录打包，不能把个人安装目录直接压缩。
4. 推送到 main 后，Actions 的 `Desktop checks and release` 自动检查并构建两个系统；都通过后发布正式版。也可手动运行，勾选 `prerelease` 可发布预览版。
5. Windows 资源必须命名为 `ChatBot-2.6.2-Windows.zip`，macOS 为 `ChatBot-2.6.2-macOS-<架构>.zip`。同时提供 SHA-256 校验文件。

也可手动创建 Release：标签为 `v2.6.2`，附上验证过的 ZIP 与 SHA-256，取消 Draft 和 Pre-release。已发布版本的文件保持不变；有修复就增加版本号再发布。

客户端在启动后约 12 秒检查一次，随后每 6 小时检查；设置底部“检查更新”可随时检查。仅比较数字版本、已发布正式版及当前系统可用的安装包；草稿、预览版、无安装包的版本不提示。GitHub 不可达时继续使用现有版本。

这是一套更新提醒和下载入口，未实现后台下载、签名安装与自动替换。Windows 用户升级时先退出 ChatBot，将发行包中的程序文件复制到原目录，保留 `data/`。全新用户自行填写模型 API 配置并设置消息来源；本机数据库模式需要已有的有效本地连接配置，也可使用可见窗口 OCR 或导入归档。

源码只包含审核过的代码、文档和合成素材。API 凭证、数据库密钥、聊天、会话记忆、个人配置、真实截图和数据目录不得进入 Git、CI 或 Release。
