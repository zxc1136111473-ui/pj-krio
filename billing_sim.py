#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kiro 计费规则仿真 + 6 类缺陷 PoC（本地，不打生产）"""
import threading, time
from datetime import datetime, timedelta
from dataclasses import dataclass, field

TIERS = {
    "Free":  {"price": 0,   "credits": 50},
    "Pro":   {"price": 20,  "credits": 1000},
    "Pro+":  {"price": 40,  "credits": 2000},
    "ProMax":{"price": 100, "credits": 5000},
    "Power": {"price": 200, "credits": 10000},
}
ADDON_PRICE = 0.04
FIRST_PURCHASE_COUPON = 20
DAYS_IN_MONTH = 30

def prorate(day, fee):
    return round((DAYS_IN_MONTH - day + 1) / DAYS_IN_MONTH * fee, 2)

@dataclass
class AddonPack:
    credits: float
    expiry: datetime

@dataclass
class Account:
    id: str
    plan: str = "Free"
    plan_credits: float = 0.0
    addons: list = field(default_factory=list)
    first_upgrade: bool = True
    paid: float = 0.0
    refunded: float = 0.0
    consumed: float = 0.0
    ledger: list = field(default_factory=list)

    def log(self, s): self.ledger.append(s)

    def consume(self, amount, atomic=False):
        if atomic:
            avail = self.available()
            if amount > avail:
                return False
            rest = amount
            if self.plan_credits >= rest:
                self.plan_credits -= rest
            else:
                rest -= self.plan_credits; self.plan_credits = 0
                for p in sorted(self.addons, key=lambda x: x.expiry):
                    if rest <= 0: break
                    take = min(p.credits, rest)
                    p.credits -= take; rest -= take
            self.consumed += amount
            return True
        time.sleep(0.001)
        self.plan_credits -= amount
        self.consumed += amount
        return True

    def available(self):
        return self.plan_credits + sum(p.credits for p in self.addons)

    def upgrade(self, tier, day):
        refund = self.paid - self.refunded
        self.refunded += refund
        charge = TIERS[tier]["price"]
        if self.first_upgrade:
            charge = max(0, charge - FIRST_PURCHASE_COUPON)
            self.first_upgrade = False
        self.paid += charge
        self.plan = tier
        self.plan_credits = float(TIERS[tier]["credits"])
        return charge, refund

    def subscribe_first(self, tier, day):
        fee = prorate(day, TIERS[tier]["price"])
        if self.first_upgrade:
            fee = max(0, fee - FIRST_PURCHASE_COUPON)
            self.first_upgrade = False
        self.paid += fee
        self.plan = tier
        self.plan_credits = float(TIERS[tier]["credits"])
        return fee

    def monthly_reset(self):
        self.plan_credits = float(TIERS[self.plan]["credits"])

class BuggyAPI:
    def __init__(self):
        self.accounts = {}
        self.redeemed = set()

    def graphql(self, mutation, token=None, params=None):
        p = params or {}
        if mutation.startswith("redeemCode"):
            return self.redeem(p["code"], p.get("account_id"))
        if mutation.startswith("getAccount"):
            return self.accounts[p["account_id"]]
        if mutation.startswith("paymentSuccess"):
            return self.payment_success(p.get("session_id"), p.get("account_id"))
        raise ValueError(mutation)

    def redeem(self, code, account_id):
        if code in self.redeemed:
            return {"ok": False, "err": "already used"}
        self.redeemed.add(code)
        acct = self.accounts[account_id]
        acct.plan_credits += 100
        return {"ok": True, "credits": 100}

    def payment_success(self, session_id, account_id):
        acct = self.accounts[account_id]
        acct.plan_credits += 125
        return {"ok": True, "granted": 125}

api = BuggyAPI()
A = Account("A"); B = Account("B")
api.accounts = {"A": A, "B": B}

print("=" * 72)
print("B1  比例计费 + 首购优惠 套利")
print("=" * 72)
x = Account("x1"); fee = x.subscribe_first("Pro", 1)
print(f"月初首购 Pro: 付 ${fee} 得 1000 积分")
y = Account("y1"); fee = y.subscribe_first("Pro", 28)
print(f"月末(28日)首购 Pro: 付 ${fee} 得 1000 积分")
y.monthly_reset()
print(f"次月重置后再得 1000. 合计 ${fee} 得 2000")
z = Account("z1")
for i, (tier, day) in enumerate([("Pro", 5), ("Pro+", 10), ("ProMax", 15), ("Pro+", 20), ("ProMax", 25)]):
    z.upgrade(tier, day)
print(f"升级舞步: 档 {z.plan} 额度 {z.plan_credits}, 实付 ${z.paid}, 退款 ${z.refunded}, 净 ${z.paid - z.refunded}")

print()
print("=" * 72)
print("B2  并发扣减竞态")
print("=" * 72)
r = Account("race"); r.subscribe_first("Pro", 1); r.plan_credits = 1000
before = r.available()
def burn():
    for _ in range(25):
        r.consume(20)
threads = [threading.Thread(target=burn) for _ in range(20)]
[t.start() for t in threads]; [t.join() for t in threads]
print(f"余额 {before} -> {r.available()}, consumed={r.consumed}")

print()
print("=" * 72)
print("B3  兑换码枚举")
print("=" * 72)
victim = Account("v"); api.accounts["v"] = victim
for i in range(1, 4):
    print(api.redeem(f"KIRO-2026-{i:04d}", "v"))
print(f"余额: {victim.plan_credits}")

print()
print("=" * 72)
print("B4  伪造支付回调")
print("=" * 72)
hack = Account("h"); api.accounts["h"] = hack
print(api.payment_success("cs_FAKE123", "h"))
print(api.payment_success("cs_FAKE999", "h"))
print(f"未付款余额: {hack.plan_credits}")

print()
print("=" * 72)
print("B5  账号合并 / 首购重置")
print("=" * 72)
m1, m2 = Account("m1"), Account("m2")
m1.subscribe_first("Pro", 10); m2.subscribe_first("Pro", 10)
print(f"合并后积分 {m1.plan_credits + m2.plan_credits}")

print()
print("=" * 72)
print("B6  GraphQL 鉴权 / IDOR")
print("=" * 72)
victim2 = Account("victim2"); victim2.subscribe_first("ProMax", 3)
api.accounts["victim2"] = victim2
print("无 token redeem:", api.graphql("redeemCode", params={"code": "KIRO-2026-9999", "account_id": "v"}))
print("A token 读 victim2:", api.graphql("getAccount", token="A_TOKEN", params={"account_id": "victim2"}) is not None)
