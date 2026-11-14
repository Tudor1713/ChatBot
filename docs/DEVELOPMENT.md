# ChatBot 开发与构建

Windows 使用固定 `.venv`，执行 Python 工具时使用 `python -m ...`，不依赖目录移动前生成的命令入口。

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe scripts/check_secrets.py --tree .
.\.venv\Scripts\python.exe scripts/smoke_chatbot.py --output work/chatbot-ui
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build.ps1 -OutputDirectory outputs/build-2.6.1
```

构建输出：`outputs/build-2.6.1/ChatBot/ChatBot.exe`。安装更新时替换程序和 `_internal`，保留安装目录的 `data/`。源码启动入口为 `启动ChatBot.cmd`。

离线运行诊断：

```powershell
ChatBot.exe --self-test-report work/selftest.json
ChatBot.exe --demo --screenshot work/ChatBot.png
ChatBot.exe --safe-start
```

`--demo` 使用独立演示数据；截图参数仅允许演示模式。`--safe-start` 只抑制本次启动的自动任务，不写回用户配置。单实例按数据目录隔离；诊断模式使用临时目录和本机模拟 HTTP 服务。

项目未初始化 Git，本轮检查点用工作区原始源码副本与测试记录保留。项目版权归 ChatBot；运行时依赖许可证见 `THIRD_PARTY_NOTICES.md`。
