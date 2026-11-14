# ChatBot 2.6.1

本地微信对话助手。以聊天记录为上下文，生成可检查的判断、候选回复、话题建议与会话记忆。Windows 使用 Python/PySide6 后端和本地 HTML/JavaScript 界面。

[下载 Windows 版](https://github.com/Tudor1713/ChatBot/releases/latest) · [版本发布与升级](docs/RELEASING.md)

## 启动

安装目录运行 `ChatBot.exe`，或双击桌面 `ChatBot` 快捷方式。源码目录也提供 `启动ChatBot.cmd`。同一份数据只运行一个实例；重复启动会唤回原窗口。

工作台保留一个主界面，设置抽屉提供模型、自动回复、记忆和外观四页。首次使用请填写自己的 Base URL、模型名与 API Key；旧用户保留原来的加密凭证。前端按需显示聊天记录，不改变后台分析使用的上下文。

## 2.6.1 更新

- 修复本机数据库模式“填入微信”误报未连接；保存设置后及时同步来源。
- 新增自动及手动版本检查，可查看发行说明并前往 GitHub 下载。
- 桌面快捷方式启动后读取所选消息来源；自动回复仍需明确启用。

## 数据与更新

用户配置、加密凭证、记忆和历史在安装目录 `data/`，更新程序时保留该目录。自动回复只有明确开启后才使用；验证版本用合成数据和本机模型模拟服务，避免收费调用。

自动检查仅获取公开 GitHub 版本信息，不上传任何聊天或密钥。新用户的发行包不含个人配置和数据。数据库模式需要有效的本机连接配置；也可选择微信窗口 OCR 或导入归档。

## 开发资料

- [前后端结构](docs/ARCHITECTURE.md)
- [构建与检查](docs/DEVELOPMENT.md)
- [数据说明](docs/PRIVACY.md)
- [发行说明](docs/releases/2.6.1.md)
- [工程检查点](docs/PROJECT_MEMORY.md)
- [验证记录](docs/testing/ChatBot.tdd.md)

项目内容、代码与文档均归属本项目 ChatBot，版权声明见 `LICENSE`；运行时依赖的来源与许可证见 `THIRD_PARTY_NOTICES.md`。
