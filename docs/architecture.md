# PayGlass 架构深度解析

## 设计哲学

PayGlass 遵循三个架构原则：

1. **协议无关** — 核心引擎不依赖任何具体协议的实现细节
2. **事件归一化** — 所有协议的支付事件映射到统一的 TraceEvent 模型
3. **只读观测** — PayGlass 从不修改支付状态，只观测和记录

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   Dashboard Layer                     │
│  index.html  ←  data.json  ←  tracer.dashboard()    │
├─────────────────────────────────────────────────────┤
│                    Engine Layer                       │
│  PayGlassTracer                                      │
│  ├── _traces: dict[str, PaymentTrace]                │
│  ├── ingest(event) → PaymentTrace                    │
│  ├── get_trace(id) → PaymentTrace                   │
│  └── dashboard() → dict                              │
├─────────────────────────────────────────────────────┤
│                Protocol Adapter Layer                 │
│  X402Observer  │  NanopaymentsObserver  │  SptObserver│
│  └─ normalize() → TraceEvent                          │
├─────────────────────────────────────────────────────┤
│                 Real-world APIs                        │
│  Stripe API  │  x402 SDK  │  Circle Gateway API       │
└─────────────────────────────────────────────────────┘
```

## 核心组件

### 1. PayGlassTracer

追踪引擎的核心。维护所有支付追踪的内存存储，提供统一的查询和聚合接口。

```python
class PayGlassTracer:
    _traces: dict[str, PaymentTrace]    # 所有支付追踪
    _observers: dict[Protocol, object]  # 已注册的协议观测器

    def ingest(self, event: TraceEvent) -> PaymentTrace
    def get_trace(self, payment_id: str) -> Optional[PaymentTrace]
    def list_traces(self, protocol=None) -> list[PaymentTrace]
    def dashboard(self) -> dict
```

**设计决策**：内存存储而非持久化。v0.1 阶段不需要数据库——Agent 支付的量还没有大到需要持久化。v0.2 会添加 SQLite 支持。

### 2. TraceEvent

统一的事件模型。所有协议的事件归一化到这个 schema。

```python
@dataclass
class TraceEvent:
    trace_id: str           # 归属的支付追踪 ID
    protocol: Protocol      # 来源协议
    event_type: str         # 事件类型（协议特定 + 通用）
    status: EventStatus     # PENDING | VERIFIED | BATCHED | SETTLED | FAILED
    timestamp_ms: int       # Unix 毫秒时间戳
    amount_usdc: float      # USDC 金额（归一化）
    source_agent: str       # 付款 Agent
    target_service: str     # 收款服务/资源
    chain: Optional[str]    # 区块链（可选）
    tx_hash: Optional[str]  # 交易哈希（可选）
    batch_id: Optional[str] # 批次 ID（可选）
    error: Optional[str]    # 错误信息（可选）
    metadata: dict          # 协议特定元数据
```

### 3. Protocol Observers

每个协议有一个 Observer，职责是将协议原生事件转换为 TraceEvent。

#### X402Observer

x402 支付流的 7 个事件：

```
HTTP Request → 402 Payment Required → EIP-3009 Signature
→ Payment Header Retry → Gateway Verification
→ Resource Delivered → Batch → Settlement
```

#### NanopaymentsObserver

Circle Nanopayments 的 7 个事件：

```
Deposit Check → EIP-3009 Authorization → TEE Verification (AWS Nitro)
→ Off-chain Balance Deduction → Resource Delivered
→ Batch → On-chain Settlement
```

**验证闸门**：NanopaymentsObserver 在第一步就检查金额是否 ≥ $0.000001。低于最低金额的支付立即产生 FAILED 事件，不再走后续流程。

#### StripeSPTObserver (Stub)

Stripe SPT 的 5 个占位事件。Stripe SPT 仍在 private preview，API 未公开。Observer 结构已就位，API 公开后可立即接入。

## 数据流

### 写路径（支付追踪）

```
1. Observer.trace_payment() 或 .trace_nanopayment()
   ↓
2. 创建 TraceEvent 序列（模拟/真实 API 响应）
   ↓
3. tracer.ingest(event) → 创建/更新 PaymentTrace
   ↓
4. tracer.settle_batch() → 添加结算事件
```

### 读路径（Dashboard 查询）

```
1. tracer.dashboard()
   ↓
2. 聚合：按协议分组 → 统计 count/volume/latency/errors
   ↓
3. 输出 JSON → data.json
   ↓
4. Dashboard HTML 读取 data.json → 渲染
```

## 可扩展性

### 添加新协议

1. 创建 `engine/protocols/new_protocol.py`
2. 实现 Observer 类，注册到 Protocol 枚举
3. 在 `__init__.py` 导出
4. Dashboard 自动识别新协议

```python
# 新协议只需实现一个 Observer
class NewProtocolObserver:
    def __init__(self, tracer: PayGlassTracer):
        self.tracer = tracer

    def trace_payment(self, ...) -> str:
        # 创建 TraceEvent 序列
        # 调用 tracer.ingest() 逐个注入
        return trace_id
```

### 添加新事件类型

TraceEvent.event_type 是自由文本——不需要修改核心引擎就能添加新事件类型。Dashboard 会自动渲染。

## 局限与下一步

| 局限 | v0.2 解决方式 |
|------|-------------|
| 模拟数据 | 接入真实 x402 SDK / Circle Gateway API |
| 内存存储 | SQLite 持久化 + 查询历史 |
| 单实例 | 多租户隔离 |
| 静态 Dashboard | WebSocket 实时推送 |
| 无告警 | 规则引擎（延迟/失败率阈值） |
