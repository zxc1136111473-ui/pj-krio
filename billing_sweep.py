#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""参数化套利扫描：首购日 × 档位、升级序列、并发超卖。"""
TIERS = {"Free": (0, 50), "Pro": (20, 1000), "Pro+": (40, 2000),
         "ProMax": (100, 5000), "Power": (200, 10000)}
DAYS = 30
COUPON = 20.0

def prorate(day, fee):
    return round((DAYS - day + 1) / DAYS * fee, 2)

class Acct:
    def __init__(self, mode):
        self.mode = mode; self.plan = "Free"; self.plan_credits = 0.0
        self.paid = 0.0; self.refunded = 0.0; self.coupon_used = False
        self.granted_total = 0.0; self.reset_total = 0.0
    def grant(self, t):
        c = float(TIERS[t][1]); self.plan_credits = c; self.granted_total += c
    def reset(self):
        c = float(TIERS[self.plan][1]); self.plan_credits = c; self.reset_total += c
    def subscribe_first(self, tier, day):
        fee = prorate(day, TIERS[tier][0])
        if not self.coupon_used:
            fee = max(0.0, fee - COUPON); self.coupon_used = True
        self.paid += fee; self.plan = tier; self.grant(tier)
        return fee
    @property
    def net(self):
        return self.paid - self.refunded

print("=" * 74)
print("S1  首购日扫描: 日 x 档位 -> 实付$ -> 获得积分(含次月重置)")
print("=" * 74)
print(f"{'day':>3} | " + " | ".join(f"{t:>16}" for t in ["Pro", "Pro+", "ProMax", "Power"]))
print("-" * 74)
zero = 0
for day in range(1, 31):
    row = []
    for t in ["Pro", "Pro+", "ProMax", "Power"]:
        a = Acct("strict"); a.subscribe_first(t, day); a.reset()
        total = a.granted_total + a.reset_total
        row.append(f"{a.net:>5.2f}->{total:>6.0f}")
        if a.net == 0:
            zero += 1
    print(f"{day:>3} | " + " | ".join(row))
print(f"零成本组合: {zero}")
