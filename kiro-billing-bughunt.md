# kiro.dev 计费系统 Bug 猎取（授权内）

对象：app.kiro.dev 计费（AppSync + Cognito + Stripe）。黑盒只在测试环境。

规则快照：Free 50 / Pro 1000 / Pro+ 2000 / ProMax 5000 / Power 10000；首月升级按比例收费但发满额；首购 $20；add-on $0.04/积分。

## B1 比例费套利

月末订阅 → 付 1/30 费用拿整月积分，次日重置再拿一份。$20 优惠可能吞掉全部比例费。

## B2 竞态

并发扣减 / 并发购买 / 兑换双花 / 消耗后退款。

## B3 兑换码

可预测、重放、错误提示枚举。

## B4 支付回调

`/payment/success` 是否信任客户端 session_id；webhook 是否验签。

## B5 多 IdP / 删号

首购标记按账号 UUID → 重建刷 $20。

## B6 GraphQL

introspection、无鉴权 mutation、IDOR。
