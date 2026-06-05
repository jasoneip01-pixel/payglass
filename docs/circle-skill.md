# PayGlass Circle Skill 使用指南

## 什么是 Circle Skill

Circle Skills 是 Circle 为 AI 编码助手提供的开源指令包。兼容 OpenClaw、Cursor、Claude Code、Codex 等 AI 工具。Agent 开发者可以通过 Skills 让 AI 助手直接调用 Circle 的金融基础设施。

PayGlass 作为 Circle Skill，让 AI 编码助手能够：
1. 追踪 Agent 支付的生命周期
2. 调试支付失败
3. 监控跨协议支付性能

## 安装

### 在 OpenClaw 中使用

将 `skill/SKILL.md` 复制到你的 OpenClaw skills 目录：

```bash
cp skill/SKILL.md ~/workspace/agent/skills/payglass/
```

### 在 Cursor 中使用

在项目根目录创建 `.cursor/rules/payglass.md`：

```bash
cp skill/SKILL.md .cursor/rules/payglass.md
```

### 在 Claude Code 中使用

```bash
cp skill/SKILL.md .claude/skills/payglass.md
```

## 使用场景

### 场景 1：调试支付失败

**用户**："我的 Agent 支付一直失败，帮我看看"

**AI（加载 PayGlass Skill 后）**：
```python
from engine.tracer import PayGlassTracer
from engine.protocols.nanopayments import NanopaymentsObserver

tracer = PayGlassTracer()
nano = NanopaymentsObserver(tracer)

tid, err = nano.trace_nanopayment(
    buyer_agent="my-agent",
    seller_service="https://api.example.com/data",
    amount_usdc=0.01,
)

if err:
    print(f"❌ Payment validation failed: {err}")
    # AI 可以自动建议修复方案
else:
    trace = tracer.get_trace(tid)
    # 检查每个事件的健康状态
```

### 场景 2：跨协议延迟对比

**用户**："x402 和 Nanopayments 哪个更快？"

**AI**：
```python
tracer = PayGlassTracer()
# ... 运行 x402 和 nano 支付 ...
dash = tracer.dashboard()
for proto, stats in dash['by_protocol'].items():
    print(f"{proto}: avg {stats['avg_latency_ms']}ms")
```

### 场景 3：批量结算状态检查

**用户**："昨天的批量结算完成了吗？"

**AI**：
```python
traces = tracer.list_traces()
pending = [t for t in traces if not t.is_complete]
if pending:
    print(f"⚠️ {len(pending)} payments pending settlement")
else:
    print("✅ All payments settled")
```

## Skill 能力矩阵

| 能力 | 触发方式 |
|------|------|
| 追踪单笔支付 | "trace this payment" / "debug payment failure" |
| 查看 Dashboard | "show payment dashboard" / "payment stats" |
| 跨协议对比 | "compare x402 vs nanopayments" |
| 批量结算检查 | "check batch settlement" / "pending settlements" |
| 错误诊断 | "why did this payment fail" / "payment error" |

## 与 Circle Agent Stack 的协同

PayGlass Skill 可以直接与 Circle Agent Stack 的其他组件配合：

```
Circle CLI → 创建 Agent Wallet
Circle Skills → 发现支付服务
PayGlass Skill → 追踪和调试支付 ← 我们在这里
Circle Agent Marketplace → 购买服务
```

这意味着 Agent 开发者可以：
1. 用 Circle CLI 创建钱包
2. 用 Circle Skills 发现和调用支付服务
3. **用 PayGlass Skill 追踪每笔支付的状态**
4. 用 PayGlass Dashboard 统一查看

## 限制

- v0.1 的追踪基于模拟数据（`engine/` 中的 Observer 生成模拟事件流）
- v0.2 将接入真实 Circle Gateway API 和 x402 SDK
- Stripe SPT 追踪为 stub，待 SPT 公开后激活
