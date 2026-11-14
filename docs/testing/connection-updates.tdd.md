# 连接恢复与更新提醒验证

需求来自本次修复：数据库会话能读取时，手动填入应使用同一份保存来源；GitHub 正式发新版后客户端能提示，发布内容不得含个人数据。

## RED / GREEN

- `python -m unittest discover -s tests -p test_connection_lifecycle.py -v`：首次执行出现同一条“请先连接本机微信数据库”异常，保存来源同步检查也失败。实现 configure 后通过；随后补充历史建议路径通过。
- `python -m unittest discover -s tests -p test_updates.py -v`：首次执行因缺少更新模块而失败。实现后 6 项通过，涵盖数字版本比较、草稿/预览版/平台过滤、固定 API、无凭证请求、失败与过大响应。
- `python -m unittest discover -s tests -p test_controller_updates.py -v`：2 项通过，覆盖异步状态、同版通知去重、下载入口与关闭后丢弃结果。
- `python scripts/smoke_chatbot.py --output work/chatbot-ui`：14 项合成 UI 检查通过，包含更新说明与下载按钮；查看实际渲染截图，无 JavaScript 错误。
- `python -m coverage run --source=desk.updates -m unittest discover -s tests -p test_updates.py` 和 `python -m coverage report -m`：更新模块 92% 语句覆盖（60 条，5 条未执行）。不是整个历史工程的覆盖率。

测试不读取真实聊天、不调用付费模型、不执行真实微信填入或发送。全量回归、源码隐私检查和打包检查沿用 build.ps1；本地验证为 Windows，macOS 需由 CI 单独验证。工程在本轮测试前没有 Git 历史，RED/GREEN 证据保存在此，初次发布不包含任何旧运行数据或历史构建。

Windows 完整构建：485 项测试，483 通过、2 项按平台跳过；打包离线自检 14 项通过。源码和发行检查均通过；未对真实联系人执行填入或发送。
