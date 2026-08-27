# kiro 计费缺陷复现手册（授权内）

配套：`billing_sim.py`、`billing_sweep.py`、`kiro-billing-bughunt.md`、`kiro_findings_master.csv`

执行边界：黑盒只在 **beta/gamma + 测试账号 + Stripe 测试卡**。生产只读取证。
公网：beta=403，gamma=Amazon 内部 Federate，需公司 VPN。

## 深度分层

| 层 | 名称 | 状态 |
|---|---|---|
| L0 | 规则推演 | 完成 |
| L1 | 本地仿真 | 完成（billing_sim / sweep） |
| L2 | 测试环境黑盒 | 待执行（见 scripts/） |
| L3 | 生产只读取证 | 待执行（SQL 见下） |
| L4 | 代码级确认 | 待执行 |

## L2 快照模板

```
用例: Bx-y  时间: <ISO>  账号: A
操作前余额:  操作后余额:
请求:  响应:
判定: 通过/不通过
```

## L3 取证 SQL（只读）

```sql
SELECT user_id, plan, paid_amount, subscribed_at FROM subscriptions
WHERE paid_amount = 0 AND plan IN ('ProMax','Power') AND EXTRACT(DAY FROM subscribed_at) >= 25;

SELECT user_id, balance FROM balances WHERE balance < 0;

SELECT user_id, COUNT(*) FROM coupon_redemptions GROUP BY user_id HAVING COUNT(*) > 1;

SELECT code, COUNT(DISTINCT user_id) FROM redeem_events GROUP BY code HAVING COUNT(DISTINCT user_id) > 1;

SELECT credit_events.* FROM credit_events
LEFT JOIN stripe_sessions s USING (session_id)
WHERE credit_events.type='grant' AND s.id IS NULL;
```

## 脚本

- `scripts/b25_identity_pool.sh`
- `scripts/b2_race.py`
- `scripts/b17_b1_checkout.md`
