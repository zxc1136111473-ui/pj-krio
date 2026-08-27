# kiro.dev 授权内安全评估 — 信息收集阶段报告

> 范围：kiro.dev 及其子域。阶段：被动/非侵入式。未进行主动利用。

## 资产

| 项 | 值 |
|---|---|
| 主站 | Next.js + S3 + CloudFront |
| DNS | Route 53，通配 `*.kiro.dev` |
| 前端 | Algolia、Adobe Analytics、Amplitude、AppSync、Cognito |
| 应用 | app / beta.app / gamma.app（beta 公网 403，gamma 跳 Amazon Federate） |
| 认证 | `*.auth.desktop.kiro.dev`（Cognito Identity，UnknownOperationException） |
| 遥测 | `telemetry*` / `telemetry-v2` |
| Agent | `activity` / `memory` / `gateway.connections.autonomous-agents` |
| 管理 | `management.*` / `internal.runtime.*` / `runtime.*`（含 us-gov） |
| 分发 | `cli.kiro.dev`、`prod.download.desktop.kiro.dev`、`download.crew.kiro.dev` |
| 商城 | shop.kiro.dev（GCP + Prisma Cloud） |
| 开源 | github.com/kirodotdev/Kiro、powers、KiroCrew |

## 安全头（主站，好）

CSP / HSTS preload / X-Frame-Options DENY / nosniff / COOP / Referrer-Policy。无 security.txt（404）。

## 关键观测

- 员工姓名测试子域进生产证书（`weikding.test.auth.desktop` 可解析）
- CLI 安装脚本 S3+KMS，响应头泄露 KMS key ARN
- 桌面认证 token 形态：`aoa|aor` + 载荷 + ECDSA P-384 签名
- 前端 flag：`enableNewBilling` / `enableNewOverages` / `enableStudentPlan` / `enableRevampedPlans`
