# Circle Nanopayments 集成指南

## 概述

Circle Nanopayments 是 Circle 在 2026 年 5 月推出的 Gas-free USDC 微支付基础设施。最小转账 $0.000001，零 Gas 费，专为 AI Agent 间的高频微小支付设计。

### 为什么 Nanopayments 是 Agent 支付的关键基建

传统支付轨道的 Agent 支付困境：

| 支付方式 | 最小金额 | 手续费 | Agent 友好？ |
|------|:--:|:--:|:--:|
| 信用卡 | ~$1.00 | 2.9% + $0.30 | ❌ 需要人工 checkout |
| 链上 USDC | 任意 | $0.01-$0.50 gas | ❌ 每笔都要 gas |
| **Nanopayments** | **$0.000001** | **$0** | **✅ EIP-3009 离线签名** |

Agent 调一次 LLM API 可能只花 $0.001。用信用卡付这笔钱，手续费是 $0.30——手续费的 300 倍。Nanopayments 解决了这个经济学问题。

## 技术架构

### 三层设计

```
┌──────────────────────────────────┐
│  Agent (Buyer)                   │
│  1. 存 USDC 到 Gateway Wallet    │
│  2. 对每笔支付做 EIP-3009 签名   │
└──────────────┬───────────────────┘
               │ EIP-3009 signature
               ▼
┌──────────────────────────────────┐
│  Circle Gateway                  │
│  3. AWS Nitro Enclave 验证签名   │
│  4. 链下余额扣减                 │
│  5. 返回验证结果 (< 1 秒)        │
└──────────────┬───────────────────┘
               │ 批量聚合
               ▼
┌──────────────────────────────────┐
│  Blockchain (11 chains)          │
│  6. 数千笔合为一笔链上 tx         │
│  7. Gas 成本 $0.02/批次          │
└──────────────────────────────────┘
```

### 关键创新点

1. **EIP-3009 离线签名** — 买家签名后发给卖家，由卖家提交给 Gateway。买家不需要在线等待确认。
2. **TEE 验证** — AWS Nitro Enclave 做签名验证，硬件级安全，不需信任 Circle。
3. **批量结算** — 不是每笔都上链，而是净额批量结算。Gas 只在批次层发生。

## PayGlass 中的 Nanopayments Observer

### 初始化

```python
from engine.tracer import PayGlassTracer
from engine.protocols.nanopayments import NanopaymentsObserver

tracer = PayGlassTracer()
nano = NanopaymentsObserver(tracer)
```

### 追踪一笔纳米支付

```python
trace_id, error = nano.trace_nanopayment(
    buyer_agent="data-agent-7",
    seller_service="https://feeds.circle.com/btc-usd",
    amount_usdc=0.000050,  # $0.00005 — 仅 5 hundred-thousandths
    chain="arbitrum",
)

if error:
    print(f"❌ {error}")
else:
    trace = tracer.get_trace(trace_id)
    print(f"✅ {trace.summary()}")
```

### 7 个事件详解

| # | 事件类型 | 状态 | 说明 |
|:--:|------|:--:|------|
| 1 | `deposit_check` | PENDING | 检查买家在 Gateway Wallet 的余额 |
| 2 | `authorization` | PENDING | EIP-3009 授权签名已生成 |
| 3 | `tee_verification` | VERIFIED | AWS Nitro Enclave 验证签名通过 |
| 4 | `balance_deduction` | VERIFIED | 链下余额已扣减 |
| 5 | `resource_delivered` | VERIFIED | 资源已交付（< 1 秒） |
| 6 | `batch` | BATCHED | 纳入批量结算批次 |
| 7 | `settlement` | SETTLED | 链上结算完成 |

### 验证闸门

NanopaymentsObserver 在第一步就执行金额验证：

```python
# ❌ 低于 $0.000001 → 立即 FAILED
trace_id, error = nano.trace_nanopayment(
    buyer_agent="test-agent",
    seller_service="https://test.example.com",
    amount_usdc=0.0000005,  # 5e-7 < 1e-6
)
# error = "Amount $5e-07 below minimum $1e-06"
# 追踪中只有 1 个 FAILED 事件
```

### 批量结算

```python
# 一次结算多笔支付
nano.batch_settle(
    trace_ids=["abc123", "def456", "ghi789"],
    batch_id="batch-20260605-001",
    tx_hash="0xnano...batch",
    chain="arbitrum",
)
```

## 调试常见问题

### 问题 1：金额低于最低门槛

**症状**：`validation_failed` 事件。

**排查**：
```python
MIN_NANO_AMOUNT = 0.000001
if amount_usdc < MIN_NANO_AMOUNT:
    print(f"Amount ${amount_usdc} below minimum ${MIN_NANO_AMOUNT}")
    print("Use x402 for sub-nanopayment amounts, or batch multiple calls")
```

### 问题 2：TEE 验证失败

**症状**：`tee_verification` 事件状态 FAILED。

**排查**：
- EIP-3009 签名是否过期（默认 1 小时）
- nonce 是否重复
- Gateway Wallet 是否有足够 USDC

### 问题 3：跨链余额不足

**症状**：`deposit_check` 事件 metadata 中 `balance_ok: false`。

**排查**：
- 确认 USDC 存入了正确的链上的 Gateway Wallet
- 不同链的余额是独立的——Arbitrum 上的余额不能用于 Optimism 上的支付

### 问题 4：批量结算延迟

**正常行为**。批量结算是周期性的，不是每笔即时。查看 `batch` 和 `settlement` 事件之间的时间差来确认结算间隔。

## 链支持

Circle Nanopayments 支持 11 条 EVM 链：

| 链 | 确认时间 | 推荐场景 |
|------|:--:|------|
| Arbitrum | ~2s | 通用（推荐） |
| Optimism | ~2s | 通用 |
| Base | ~2s | Coinbase 生态 |
| Avalanche | ~1s | 高频交易 |
| Polygon | ~2s | 低成本 |
| +6 条 | — | — |

## 与 x402 的关系

Nanopayments 和 x402 不是竞争关系——它们是互补的：

- **x402** 是应用层协议（HTTP 标准），回答"怎么请求支付"
- **Nanopayments** 是结算层（支付轨道），回答"怎么结算支付"

Circle 的协议无关策略意味着 x402 支付通过 Circle Gateway 结算时，和纯 Nanopayments 走的是同一条结算轨道。这正是 PayGlass 跨协议观测的价值——你可以追踪一笔 x402 支付从 HTTP 402 到 Gateway 批量结算的完整生命周期。
