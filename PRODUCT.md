# PayGlass 产品定义说明书

> v0.1.0 | 2026-06-05 | 内部草案
>
> **一句话定位**：Agent 支付世界的 Datadog——一面玻璃看尽所有 Agent 支付流量。

---

## 1. 产品定位

### 1.1 是什么

PayGlass 是跨协议 Agent 支付可观测性引擎。它不在支付流中（不处理资金），而是在支付流之上（观测、追踪、诊断）。

```
Agent 支付栈
┌──────────────────────────────────────┐
│            PayGlass                   │  ← 我们在这里：观测层
│   Dashboard · Tracer · Observers      │
├──────────────────────────────────────┤
│  Stripe SPT  │  x402  │  Circle Nano │  ← 协议层
├──────────────────────────────────────┤
│  Card/ACH    │  USDC  │  USDC        │  ← 结算层
└──────────────────────────────────────┘
```

### 1.2 不是什么

- ❌ 不是支付协议——不处理资金流
- ❌ 不是支付网关——不托管私钥
- ❌ 不是合规工具——不需要牌照
- ❌ 不是 Stripe/x402/Circle 的竞争对手——是它们的观测层

### 1.3 核心隐喻

> Datadog 让 DevOps 在一面玻璃上看所有服务的健康状态。
> PayGlass 让 Agent 开发者在一面玻璃上看所有支付的状态。

---

## 2. 问题陈述

### 2.1 市场现状：三条轨道并行，无人观测

| 轨道 | 建设者 | 状态 | 核心创新 |
|------|--------|:--:|------|
| **Stripe Agent OS** | Stripe | Private Preview | 从支付处理器进化为 Agent 商业 OS |
| **x402 Protocol** | 开放标准社区 | 已发布 | HTTP 原生支付，无账户无会话 |
| **Circle Nanopayments** | Circle | 主网 (2026-05) | Gas-free USDC 微支付，$0.000001 起 |

三条轨道的共同特征：**都在建，都还没人做观测**。

### 2.2 开发者的三大痛点

| 痛点 | 现状 | PayGlass 解法 |
|------|------|--------------|
| **协议选型瘫痪** | 3 个协议，各有优劣，不知道选哪个 | 三轨统一 Dashboard，同屏对比延迟/成本/错误率 |
| **支付流黑箱** | EIP-3009 签名→TEE 验证→批量结算，6+ 步中间态，任何一步失败都是黑箱 | 逐事件追踪，可视化管线，精确定位失败点 |
| **跨链不可见** | 11 条链+3 个网关，一笔支付跨链后消失在黑洞里 | 跨链追踪，batch→tx→confirmation 全链路可见 |

### 2.3 为什么现在

**窗口判断：12-18 个月。**

- Stripe SPT 还在 private preview（2026 年 Q3 前不会公开）
- x402 协议刚稳定，生态在早期
- Circle Nanopayments 5 月才上主网，Agent Stack 5 月发布
- 三条轨道都还没统一——**碎片化峰值 = PayGlass 最大窗口**

AWS/Stripe/Circle 最终会统一底层。在他们统一之前，PayGlass 是唯一不需要选边的观测层。

---

## 3. 目标用户

### 3.1 用户画像

| 画像 | 描述 | 痛点权重 | 获取渠道 |
|------|------|:--:|------|
| **Agent 框架开发者** | 在 LangChain/CrewAI/OpenClaw 上构建 Agent 的开发者，需要集成支付 | 🔴 高 | x402 Discord, GitHub, Agent 框架社区 |
| **API/算力服务商** | 通过 Agent 支付出售 API 调用/推理算力的服务商，已接入 MPP/x402 | 🟡 中 | Stripe 生态, MPP 文档 |
| **Web3 支付工程师** | 熟悉 USDC/EIP-3009，在构建 Agent-to-Agent 支付场景 | 🟡 中 | Circle 开发者社区, ETHGlobal |
| **DevOps/SRE** | 运维 Agent 系统的工程师，需要支付可靠性监控 | 🟢 低 | Datadog/Grafana 生态 |

### 3.2 2027 年第一批用户预测

| 用户类型 | 来源 | 转化路径 |
|------|------|------|
| x402 集成者 | x402 Discord / GitHub | 接入 x402→遇到调试困难→搜索解决方案→发现 PayGlass |
| 被支付方（API 服务商） | Stripe MPP 生态 | 已在 MPP 收款→想扩展到 x402→需要跨协议对账 |
| Solver（做市商/对冲基金） | 做市商网络 | 跨链套利→需要跨链支付追踪 |

---

## 4. 竞争格局

### 4.1 竞争矩阵

| | 观测范围 | 协议覆盖 | 资金处理 | 牌照需求 |
|------|:--:|:--:|:--:|:--:|
| **PayGlass** | 全部 | x402 + Nano + SPT | ❌ 不碰 | ❌ 无 |
| Stripe Dashboard | Stripe 交易 | 仅 SPT | ✅ 处理 | ✅ 需要 |
| Circle Gateway | 仅 Nano | 仅 Nanopayments | ✅ 处理 | ✅ 需要 |
| Etherscan | 链上交易 | 全部链上 | ❌ 不碰 | ❌ 无 |

**PayGlass 的差异化**：Etherscan 能看到链上结算，但看不到链下的签名→验证→批量过程。PayGlass 覆盖的是 EIP-3009 签名到链上结算之间的**灰色地带**——这是 Etherscan 盲区，也是开发者最痛的调试区。

### 4.2 威胁

| 威胁 | 概率 | 影响 | 应对 |
|------|:--:|:--:|------|
| Stripe 把观测做到 MPP 里 | 中 | 高 | 不被锁定在 Stripe 生态——跨协议是护城河 |
| Circle Gateway 开源观测模块 | 低 | 中 | 单协议观测≠跨协议，碎片化越严重我们越有价值 |
| AWS AgentCore 自带监控 | 中 | 中 | 云厂商监控是基础设施级，不是应用级——支付流可视化更上层 |

---

## 5. 产品架构

### 5.1 三层架构

```
┌────────────────────────────────────────┐
│          Dashboard (HTML/Web)           │  ← 展示层
│   Stats · Tracks · Pipeline · Traces   │
├────────────────────────────────────────┤
│          PayGlass Tracer (Python)       │  ← 引擎层
│   Unified TraceEvent · Aggregation     │
├──────────┬──────────┬─────────────────┤
│  SPT Obs │ x402 Obs │  Nano Obs       │  ← 协议适配层
│  (stub)  │ EIP-3009 │  Gateway+TEE    │
└──────────┴──────────┴─────────────────┘
```

### 5.2 核心数据模型

```
TraceEvent {
  trace_id:      唯一追踪 ID
  protocol:      x402 | circle-nanopayments | stripe-spt
  event_type:    signature | verification | batch | settlement | ...
  status:        pending → verified → batched → settled
                 ↓
                 failed | disputed
  amount_usdc:   金额（统一 USDC 计价）
  source_agent:  付款 Agent 标识
  target_service:收款方/资源 URL
  chain:         区块链（链上事件）
  tx_hash:       交易哈希（结算后）
  batch_id:      批次 ID（批量结算）
  metadata:      协议特定元数据
}
```

### 5.3 协议覆盖矩阵

| 协议 | 状态 | 事件数 | 关键特性 |
|------|:--:|:--:|------|
| **x402** | ✅ 完整 | 7 事件 | HTTP 402 → EIP-3009 → Gateway 验证 → 批量结算 |
| **Circle Nanopayments** | ✅ 完整 | 7 事件 | 存款检查 → TEE 验证 → 链下扣减 → 批量结算 |
| **Stripe SPT** | 🟡 Stub | 5 事件 | Session → Token → Auth → Payment → Settlement |

---

## 6. 功能路线图

### v0.1.0 (当前 — 2026-06-05)

- [x] 统一 TraceEvent 数据模型
- [x] x402 协议观测器（完整 7 事件流）
- [x] Circle Nanopayments 观测器（含验证闸门）
- [x] Stripe SPT 观测器（stub）
- [x] Circle Skill (SKILL.md)
- [x] 三轨统一 Dashboard (HTML)
- [x] 8 场景 Demo

### v0.2.0 (目标：2026 Q3)

- [ ] **真实 x402 SDK 集成** — 不再模拟，直接截获 x402 HTTP 头
- [ ] **Circle Gateway Webhook 接收器** — 实时接收批量结算事件
- [ ] **Stripe SPT 真实集成** — SPT public beta 发布后接入
- [ ] **实时 Dashboard** — WebSocket 推送替代静态 JSON
- [ ] **告警规则引擎** — 支付延迟 > 阈值 / 验证失败率 > X% → 告警
- [ ] **支付流回放** — 历史支付流的时间轴回放

### v1.0.0 (目标：2027 Q1)

- [ ] **多租户** — Agent 团队各自独立 Dashboard
- [ ] **协议性能对比** — A/B 测试框架：同一支付走两条协议，对比延迟/成本
- [ ] **成本分析** — 跨协议费率对比 + 推荐最优路由
- [ ] **SLA 监控** — 按服务商/协议的可用性追踪
- [ ] **CLI 工具** — `payglass trace <payment_id>` 命令行诊断

### 不会做的（自觉边界）

- ❌ 不建支付协议
- ❌ 不处理资金
- ❌ 不托管钱包
- ❌ 不做合规桥

---

## 7. 商业模型

### 7.1 收入模式

| 层 | 模式 | 价格锚点 |
|:--:|------|------|
| **Free** | 单开发者，10K 支付/月，社区支持 | $0 |
| **Team** | 5 人团队，100K 支付/月，Slack 支持 | $49/月 |
| **Pro** | 无限支付，SLA 监控，告警，SSO | $199/月 |
| **Enterprise** | 私有部署，自定义协议适配器，专属支持 | 议价 |

### 7.2 为什么免费层重要

Agent 支付现在还太小。2026 年的开发者不会为观测工具付费——他们还在验证"Agent 支付到底能不能工作"。免费层是品类教育的代价。

**定价哲学**：不按支付量收费（那是 Stripe 的事），按团队规模和功能收。观测工具的价值和支付量无关——一个 $0.000001 的 bug 和一 $10,000 的 bug，调试难度一样。

---

## 8. 分发策略

### 8.1 三渠道并行

| 渠道 | 策略 | 时间 |
|------|------|------|
| **Circle Skills 市场** | 作为 Circle Skill 分发——Agent 开发者一键安装 | 立即 |
| **x402 社区** | x402 Discord/GitHub 的"推荐调试工具" | v0.2 |
| **Stripe 生态** | Stripe SPT 公开后，作为 SPT 的观测插件 | SPT GA 时 |

### 8.2 Circle Skills 是关键杠杆

Circle Skills 兼容 OpenClaw/Cursor/Codex/Claude Code。Agent 开发者可以用自然语言让 AI 安装 PayGlass。这是零获客成本的渠道——Circle 的开发者生态就是 PayGlass 的分发网络。

---

## 9. 风险与应对

| 风险 | 等级 | 应对 |
|------|:--:|------|
| 窗口关闭（Stripe/Circle 统一底层） | 🔴 高 | 12-18 个月内必须建立开发者心智——"调试 Agent 支付 = PayGlass" |
| 市场太小（Agent 支付还没规模） | 🟡 中 | 免费层 + 社区驱动，等到 2027 年第一批付费用户出现 |
| x402 被边缘化 | 🟡 中 | 协议无关设计——任何新协议出现，加一个 Observer 即可 |
| 合规要求变化 | 🟢 低 | 不处理资金 = 不受支付牌照约束 |

---

## 10. 产品原则

1. **不选边。** PayGlass 不给任何协议背书。观测一切，推荐零。
2. **不可见即不存在。** 支付流中的每一个中间态都必须可见。
3. **开发者优先。** 产品体验从 CLI 开始，不是从销售演示开始。
4. **免费层必须真的好用。** 如果免费层是残废的，品类教育不会发生。
5. **不碰资金。** 这是护城河，也是安全边界。

---

## 附录 A：术语表

| 术语 | 定义 |
|------|------|
| **EIP-3009** | 以太坊改进提案，允许离线签名授权 USDC 转账 |
| **TEE** | 可信执行环境（Trusted Execution Environment），Circle Gateway 用 AWS Nitro Enclave 验证签名 |
| **Batch Settlement** | 批量结算：数千笔链下支付合并为一笔链上交易 |
| **MPP** | Merchant Payment Protocol，Stripe 的 Agent 商户支付协议 |
| **SPT** | Session Payment Token，Stripe 的 Agent 会话支付令牌 |
| **x402** | HTTP 402 Payment Required 标准的 Agent 支付扩展 |
| **Circle Gateway** | Circle 的统一流动性层，支撑 Nanopayments 的批量结算 |

## 附录 B：关键信号时间线

| 日期 | 信号 |
|------|------|
| 2026-03-11 | Circle Nanopayments 测试网上线 |
| 2026-05-03 | Circle Nanopayments 主网上线 |
| 2026-05-08 | Stripe Sessions 2026 — Agent OS 品类宣言 |
| 2026-05-12 | Circle Agent Stack 发布（5 产品套件） |
| 2026-05-27 | Keyrock 报告：Agent 支付 $73M/176M 笔 |
| 2026-06-05 | PayGlass v0.1.0 发布 |
