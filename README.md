# PayGlass 🔍

**Agent 支付世界的 Datadog — 一面玻璃看尽所有 Agent 支付流量。**

One pane of glass for all Agent payment traffic — Stripe SPT · x402 · Circle Nanopayments.

---

## 一句话

> 三条 Agent 支付轨道在赛跑。开发者被夹在中间选协议。PayGlass 不选边——让三者都可见。

---

## Why

| 协议 | 建设者 | 状态 | 核心创新 |
|------|--------|:--:|------|
| **x402** | 开放标准 | 已发布 | HTTP 原生支付，无账户无会话 |
| **Circle Nanopayments** | Circle | 主网 (2026-05) | Gas-free USDC，$0.000001 起 |
| **Stripe SPT** | Stripe | Private Preview | Agent 商业全栈 OS |

三条轨道都在建，都还没人做**可观测性**。PayGlass 填这个洞。

---

## 文档

| 文档 | 内容 |
|------|------|
| [PRODUCT.md](PRODUCT.md) | 产品定义说明书 — 定位/用户/竞争/路线图 |
| [docs/getting-started.md](docs/getting-started.md) | 5 分钟快速入门 |
| [docs/architecture.md](docs/architecture.md) | 架构深度解析 |
| [docs/protocols/x402.md](docs/protocols/x402.md) | x402 协议集成指南 |
| [docs/protocols/nanopayments.md](docs/protocols/nanopayments.md) | Circle Nanopayments 指南 |
| [docs/circle-skill.md](docs/circle-skill.md) | Circle Skill 使用指南 |
| [skill/SKILL.md](skill/SKILL.md) | Circle Skill 定义文件 |

---

## 快速开始

```bash
git clone https://github.com/jasoneip01-pixel/payglass.git
cd payglass

# Demo — 8 个支付场景，覆盖全部 3 条轨道
python3 demo.py

# Dashboard
python3 -m http.server 8080 -d dashboard/
# 打开 http://localhost:8080
```

```python
from engine.tracer import PayGlassTracer
from engine.protocols.nanopayments import NanopaymentsObserver

tracer = PayGlassTracer()
nano = NanopaymentsObserver(tracer)

# 追踪一笔 $0.000050 的纳米支付
tid, err = nano.trace_nanopayment(
    buyer_agent="my-agent",
    seller_service="https://api.example.com/data",
    amount_usdc=0.000050,
)
```

---

## 架构

```
Dashboard (HTML) ← Tracer (Python) ← Protocol Observers
                                       ├── X402Observer
                                       ├── NanopaymentsObserver
                                       └── StripeSPTObserver
```

## Demo 输出

```
🎯 Summary: 8 payments, $141.00 volume, 1 error
   x402:               3 payments, $25.03    0 errors
   Circle Nanopayments: 4 payments, $99.98   1 error (validation catch)
   Stripe SPT:         1 payment,  $15.99    0 errors
```

---

## 路线图

| 版本 | 目标 | 时间 |
|:--:|------|------|
| **v0.1** | 核心引擎 + 三轨 Observer + Dashboard + Circle Skill | ✅ 2026-06-05 |
| **v0.2** | 真实 SDK 集成 + WebSocket 实时 Dashboard + 告警 | 2026 Q3 |
| **v1.0** | 多租户 + 协议性能对比 + 成本分析 + CLI | 2027 Q1 |

详见 [PRODUCT.md](PRODUCT.md) §6。

---

## License

MIT
