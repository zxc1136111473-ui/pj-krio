# B55–B58（第十轮）

- **B55** #4751 子代理权限误判；#10403 工具静默拒绝（IDE 正常）
- **B56** GitLab PAT api scope 存进 Kiro Web
- **B57** #10877 headless 每次泄漏一个 KAS acp-server 进程
- **B58** #10670 execute_bash 可读环境变量（含 KIRO_API_KEY）

端点：kaa-assets 根 403；signin/oauth 对任意 redirect_uri 仍 200（SPA 壳，待浏览器实测）。
