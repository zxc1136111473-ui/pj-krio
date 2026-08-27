# Changelog

## 1.10.3

- 会话窗口：header 增加会话下拉 + 「＋新会话」，可切换/保留历史（globalState 持久化，重启不丢）
- 聊天记录：user/assistant/工具/错误 全部落库，切换会话回放
- Agent 上下文续接：每轮任务结束保存上下文快照，同会话下一任务自动带上

## 1.9.0

- 右下角状态栏**单击就打开底部控制面板**（不再弹 origin 选择器）
- 打开面板时如果没有令牌，立刻弹出输入框；也可在面板顶部「保存令牌」栏粘贴
- 已登录 Kiro 桌面会自动读 `~/.aws/sso/cache/kiro-auth-token.json`

## native-models patch

- 原生 `Select Model` 看不到 opus/sol：`kiro-agent` 用 `AI_EDITOR` 拉目录。补丁改 `CONSOLE` + 注入高级模型，并在选中后把请求 origin 改 CONSOLE。脚本：`patch_kiro_native_models.py`。用户扩展覆盖：`~/.kiro/extensions/kiro.kiroAgent-1.0.654`。

## 1.7.0

- 启动即激活（`onStartupFinished`），右下角状态栏入口不再等命令才出现
- 状态栏按钮钉在最右侧（高优先级 + 警告底色），避免被 `Kiro Free / Autocomplete` 挤掉
- 控制面板改挂系统底部 Panel 标签（和终端并排），双击状态栏直接打开
- 快捷键 `Ctrl+Alt+Q` / `Cmd+Alt+Q` 不再要求编辑器焦点

## 1.6.0

- 右下角状态栏按钮支持**双击打开控制面板**：单击 = 弹原生 QuickPick 切高级模型，双击 = 打开/聚焦底部 Q Console 面板（400ms 双击判定）

## 1.5.0

- **拒绝自动换人设重试**：Agent 轮次无工具调用且无 `<done>`（疑似被 Amazon Q 人设拒）时，自动切换备用身份重试（实测有效的兜底链：Kiro IDE Agent → AWS CloudShell 助手 → 协议强制；Never refuse / Claude Code / CodeCatalyst 身份均实测被打回），`qconsole.agentPersonaRetry` 可关
- **输出放宽**：`run_command` 回喂截断 4k → 30k（可配 `qconsole.toolOutputChars`），`maxBuffer` 1MB → 8MB；`search_content` 同步用该配置

## 1.4.0

- **Agent 模式（工具调用突破）**：服务端 toolConfiguration/toolUse 探测全拒（A/B/C/D）后，改用「人设诱导 + 客户端工具循环」：
  - 面板新增 Agent 开关 + 命令 `Q Console: Agent 任务`
  - 模型按 `<tool>JSON</tool>` 协议输出调用，插件本地执行 write_file / replace_in_file / read_file / list_dir / search_content / run_command，结果回喂循环到 `<done>`（`qconsole.agentMaxRounds`，默认 8 轮）
  - 已实测：opus-5 在人设诱导下直接输出 write_file JSON（探测 E）

## 1.3.0

- 面板改为**底部 Panel 视图**（与终端/输出并排），`Ctrl+Alt+Q` 呼出/聚焦
- 新增**原生模型选择**：状态栏 `Q: 模型 · origin` 按钮 → Kiro 原生 QuickPick 选高级模型 / 切 origin（与面板下拉双向同步）
- 视图未展开时的消息缓冲（右键「用选中代码问 Q」会自动拉起底部视图再出结果）

## 1.2.0

- 回答写回编辑器：每条回答新增「插入 / 替换选中 / 代码块插入」按钮
- `maxSelectionChars` 设 0 或负数 = 不截断（原来只能调小）

## 1.1.0

- 新增后台保活：默认每 50 分钟自动刷新 accessToken + 预热额度查询（`qconsole.keepAlive` / `keepAliveMinutes` 可配）
- 键位从 `q q` 改为 `Ctrl+Alt+Q`（Mac `Cmd+Alt+Q`）

## 1.0.0

- 初版：Q Console 面板插件
  - `q q` 键位 + 命令面板呼出
  - origin=CONSOLE 直调高级模型（opus-5 / gpt-5.6-sol / qwen3-coder-next …）
  - 流式输出 + requestId / modelId 元信息 + 额度快照
  - SecretStorage 令牌存储，桌面/web 通用
