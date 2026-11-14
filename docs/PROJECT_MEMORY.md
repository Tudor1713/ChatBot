# ChatBot 工程检查点

2026-11-14，2.6.1。本文件只记录工程事实，不保存私人路径、会话内容或凭证。

- Windows 桌面应用：Python/PySide6 + 本地 QtWebEngine/QtWebChannel；当前界面为单工作台和模型/自动回复/记忆/外观四个设置页。
- 产品名称与构建统一为 ChatBot，规格为 `ChatBot.spec`，源码入口 `启动ChatBot.cmd`，程序 `ChatBot.exe`；版权与归属为本项目 ChatBot。
- 用户数据在安装目录 `data/`；更新二进制不得覆盖数据。旧文档与生成物已归档到任务工作区。
- `desk/instance.py` 使用按数据目录隔离的文件锁和本机 socket，重复启动激活已有窗口。
- `controller.emit()` 在 16 毫秒窗口合并更新；关闭停止状态定时器，bootstrap 仍返回即时快照。
- `ui/timeline.js` 以 200 条为初始窗口，按需展开和自动揭示定位消息；复用未变化消息节点；签名需排序对象字段以适配 Qt QVariant 字段顺序。
- `--safe-start` 只在内存抑制启动自动任务；截图只能使用 `--demo`。
- 2.6.1：CaptureService.configure 同步来源但不启动观察；构造与保存设置时调用，修复读取会话后手动填入误报未连接。当前建议与历史建议均有合成回归。
- updates.py 只读取固定 GitHub 仓库的正式发布信息；启动延迟和 6 小时定时检查，设置底部手动检查。下载和覆盖由用户执行，保留 data；发版见 docs/RELEASING.md。
- 本轮合成单元回归及原生 Qt UI 检查已通过；真实收费模型、微信实际发送和 macOS 构建未验证。最终构建与启动证据见任务验收记录。

构建前运行源码隐私扫描与单元测试，使用 `scripts/build.ps1`。真实私聊窗口不截图；不得用收费推理验证改动。
