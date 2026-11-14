# ChatBot 前后端结构

ChatBot 是本地桌面应用：PySide6 提供窗口与事件循环，QtWebEngine 运行本地 HTML/CSS/JavaScript，QtWebChannel 在界面和 Python 控制器之间传递 JSON 请求及状态。

## 前端

- `ui/index.html`：离线资源入口和 CSP；聊天文本使用 textContent，固定本地图标才使用 innerHTML。
- `ui/app.js`：单工作台、设置抽屉、候选回复、快捷键和 RPC。
- `ui/timeline.js`：200 条初始窗口、按需展开、按 ID 复用消息 DOM；Qt 字段排序不影响内容比较。
- `ui/experience.js`：会话选择、媒体、记忆及外观等交互。
- `ui/paper.css`、`ui/minimal.css`：纸面风格与桌面/小窗布局。

## 后端

- `src/main.py`：参数、Qt 窗口、托盘、离线浏览器与启动流程。
- `src/desk/instance.py`：每个数据目录独立锁和本机激活通道。
- `src/desk/bridge.py`：请求结构校验、Future 结果、脱敏错误返回。
- `src/desk/controller.py`：会话状态、任务协调、16 毫秒合并状态更新；bootstrap 直接返回当前快照。
- `src/desk/tasks.py`：可终止的模型子进程与限额后台任务。
- `src/desk/store.py`、`local_account.py`：配置、加密凭证及本机只读连接。
- `src/desk/wechat_sqlcipher.py`、`wechat_db_source.py`：只读 SQLCipher 数据来源。
- `src/core/`：模型协议、上下文整理、回复候选、记忆和说话方式处理。

## 设计边界

界面显示条数与模型分析窗口分开：前端按需显示不删消息，也不缩小后端已加载的上下文。模型请求与耗时读取在后台执行；发送仍经过已有会话核验、名单及限额控制。

现有控制器较大，历史模块仍保留以兼容已有数据与测试。本轮集中修复启动、渲染、桥接和资源管理，没有宣称完成整个项目的模块化重写。
