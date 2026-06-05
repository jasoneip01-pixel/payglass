# PayGlass 快速入门

## 5 分钟上手

### 安装

```bash
git clone https://github.com/jasoneip01-pixel/payglass.git
cd payglass
```

PayGlass 是纯 Python，无外部依赖。

### 跑 Demo

```bash
python3 demo.py
```

输出 8 个支付场景的完整追踪报告，并生成 `dashboard/data.json`。

### 看 Dashboard

```bash
python3 -m http.server 8080 -d dashboard/
# 浏览器打开 http://localhost:8080
```

### 追踪你的第一个支付

```python
from engine.tracer import PayGlassTracer
from engine.protocols.nanopayments import NanopaymentsObserver

tracer = PayGlassTracer()
nano = NanopaymentsObserver(tracer)

# 追踪一笔 $0.000050 的纳米支付
trace_id, error = nano.trace_nanopayment(
    buyer_agent="my-research-agent",
    seller_service="https://api.example.com/llm/v1/chat",
    amount_usdc=0.000050,
    chain="arbitrum",
)

if error:
    print(f"❌ Payment failed: {error}")
else:
    trace = tracer.get_trace(trace_id)
    print(f"✅ Trace: {trace.summary()}")
```

## 核心概念

### TraceEvent

每个支付中的一步。一条完整的支付追踪由 5-7 个 TraceEvent 组成。

```python
TraceEvent(
    trace_id="abc123",           # 唯一追踪 ID
    protocol=Protocol.X402,      # 协议
    event_type="signature",      # 事件类型
    status=EventStatus.VERIFIED, # 当前状态
    amount_usdc=0.01,           # 金额 (USDC)
    source_agent="agent-42",    # 付款 Agent
    target_service="https://...", # 收款服务
)
```

### 事件生命周期

```
PENDING → VERIFIED → BATCHED → SETTLED
              ↓
           FAILED
```

### 协议 Observer

每个协议有自己的 Observer，负责将协议特定的事件归一化为统一的 TraceEvent。

| Observer | 协议 | 事件数 | 特殊能力 |
|----------|------|:--:|------|
| `X402Observer` | x402 | 7 | HTTP 402 → 批量结算 |
| `NanopaymentsObserver` | Circle Nano | 7 | 验证闸门 + TEE |
| `StripeSPTObserver` | Stripe SPT | 5 | Stub（待 API 公开） |

## 常见场景

### 1. 调试支付失败

```python
trace = tracer.get_trace("payment-id")
for event in trace.events:
    if event.status == EventStatus.FAILED:
        print(f"❌ Failed at {event.event_type}: {event.error}")
```

### 2. 监控支付延迟

```python
trace = tracer.get_trace("payment-id")
if trace.latency_ms and trace.latency_ms > 5000:
    print(f"⚠️ Slow payment: {trace.latency_ms}ms")
```

### 3. 跨协议用量对比

```python
dash = tracer.dashboard()
for proto, stats in dash['by_protocol'].items():
    print(f"{proto}: {stats['count']} payments, ${stats['volume_usdc']:.2f}")
```

## 下一步

- [架构深度解析](architecture.md)
- [x402 协议集成指南](protocols/x402.md)
- [Circle Nanopayments 指南](protocols/nanopayments.md)
- [Circle Skill 使用指南](circle-skill.md)
