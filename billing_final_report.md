# kiro 计费体系安全评估 — 终版汇总

授权内。覆盖：定价 → 支付 → 权益 → 计量 → 结算 → 供应链 → 认证 → 风控。
生产零接触。总清单：`kiro_findings_master.csv`（58 类）。

## P0（8）

B1 比例费套利 · B2 并发超卖 · B7 试用状态机（实锤）· B8 支付权益断链（实锤）· B12 计量异常（实锤）· B17 双引擎 · B18 费率 48x · B25 身份池/自签 token

## 跨类攻击链（评估用，勿对生产执行）

1. B7+B5+B13 无限试用  
2. B4+B6 无鉴权入账  
3. B2+B12 超卖+漏计  
4. B1+B9 免税满额  
5. B11+B6 组织逃费  

## 交付物索引

| 文件 | 内容 |
|---|---|
| `kiro-dev-security-assessment.md` | 侦察 |
| `kiro-billing-bughunt.md` | B1–B6 矩阵 |
| `billing_sim.py` / `billing_sweep.py` | 仿真与扫描 |
| `billing_reproduction_playbook.md` | L0–L4 手册 |
| `billing_additional_bugs.md` | B7–B16 |
| `billing_bugs_round3.md` … `round10.md` | B17–B58 |
| `kiro_findings_master.csv` / `.md` | 总清单 |
| `scripts/` | B25/B2/B17 测试脚本 |
| `testenv.env.example` | 测试环境变量模板 |
