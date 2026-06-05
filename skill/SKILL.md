---
name: payglass
description: >-
  PayGlass — Cross-protocol Agent payment observability.
  Debug and trace payments across Stripe SPT, x402, and Circle Nanopayments.
  Use when: agent payments fail, cross-chain settlement is stuck, EIP-3009
  signature issues, batch settlement delays, or multi-protocol payment debugging.
activation: auto
version: 0.1.0
protocols:
  - x402
  - circle-nanopayments
  - stripe-spt
compatible_with:
  - openclaw
  - claude-code
  - cursor
  - codex
---

# PayGlass — Agent Payment Observability Skill

PayGlass is a cross-protocol observability engine for AI Agent payments. It traces
payments end-to-end across three protocols: **x402** (HTTP-native), **Circle Nanopayments**
(gas-free USDC), and **Stripe SPT** (agent commerce).

## When to Use

- An agent payment is stuck — need to identify which step failed
- Cross-chain settlement is delayed — trace which batch the payment is in
- EIP-3009 signature verification failed — debug the authorization flow
- Multi-protocol payment architecture — need a unified view of all payment traffic
- Performance analysis — compare latency across protocols

## Quick Start

```python
from engine.tracer import PayGlassTracer
from engine.protocols.x402 import X402Observer
from engine.protocols.nanopayments import NanopaymentsObserver
from engine.protocols.stripe_spt import StripeSPTObserver

# Initialize
tracer = PayGlassTracer()
x402 = X402Observer(tracer)
nano = NanopaymentsObserver(tracer)
spt = StripeSPTObserver(tracer)

# Trace an x402 payment
trace_id = x402.trace_payment(
    resource_url="https://api.example.com/llm/v1/chat",
    amount_usdc=0.01,
    source_agent="research-agent-42",
    chain="arbitrum",
)

# Trace a Nanopayment (sub-cent!)
trace_id, err = nano.trace_nanopayment(
    buyer_agent="data-agent-7",
    seller_service="https://oracle.example.com/price-feed",
    amount_usdc=0.000050,  # $0.00005 — 5 hundred-thousandths of a dollar
    chain="arbitrum",
)
if err:
    print(f"Validation failed: {err}")

# Trace Stripe SPT (stub)
trace_id = spt.trace_payment(
    resource_url="https://shop.example.com/api/checkout",
    amount_usdc=15.99,
    source_agent="shopping-agent-3",
)

# Get dashboard
print(tracer.to_json())

# Inspect a specific trace
trace = tracer.get_trace(trace_id)
print(f"Latency: {trace.latency_ms}ms")
print(f"Complete: {trace.is_complete}")
```

## Batch Settlement (Nanopayments + x402)

```python
# Settle multiple nanopayments in one on-chain batch
nano.batch_settle(
    trace_ids=["abc123", "def456", "ghi789"],
    batch_id="batch-20260605-001",
    tx_hash="0x...",
    chain="arbitrum",
)

# Settle an x402 payment
x402.settle_batch(
    trace_id="abc123",
    batch_id="batch-20260605-002",
    tx_hash="0x...",
    chain="arbitrum",
)
```

## Debugging Common Issues

### EIP-3009 Signature Failure
```
Symptom: TraceEvent status=FAILED, event_type="validation_failed"
Check:  Amount below minimum ($0.000001 for Nanopayments)
Fix:     Verify amount >= MIN_NANO_AMOUNT
```

### Cross-chain Balance Mismatch
```
Symptom: Deposit check shows insufficient balance
Check:   Gateway Wallet balance on target chain
Fix:     Bridge USDC to correct chain before payment
```

### Batch Settlement Stuck
```
Symptom: Payment VERIFIED but not BATCHED/SETTLED
Check:   Gateway batch interval configuration
Fix:     Wait for next batch cycle, or trigger manual settlement
```

## Dashboard

The unified dashboard visualizes all three payment tracks in real-time.
Start it with:

```bash
python3 -m http.server 8080 -d /path/to/payglass/dashboard/
```

Or access via the live dashboard HTML at `dashboard/index.html`.

## Architecture

```
┌──────────────────────────────────────────────┐
│              PayGlass Dashboard               │
│     Stripe SPT │ x402 │ Circle Nanopayments   │
├──────────────────────────────────────────────┤
│              PayGlass Tracer                   │
│    Unified event schema (TraceEvent)           │
├──────────┬──────────┬────────────────────────┤
│  Stripe  │   x402   │  Circle Nanopayments   │
│   SPT    │ Observer │      Observer           │
│ Observer │          │                         │
│  (stub)  │ EIP-3009 │  Gateway + TEE + Batch │
├──────────┴──────────┴────────────────────────┤
│              Payment Rails                     │
│   Card/ACH │ HTTP+x402 │ USDC + 11 chains    │
└──────────────────────────────────────────────┘
```

## Protocol Coverage

| Protocol | Status | Min Amount | Settlement | Gas per Payment |
|----------|--------|-----------|------------|-----------------|
| x402 | ✅ Full | Any | Batch (Circle Gateway) | ~$0 (batch) |
| Circle Nanopayments | ✅ Full | $0.000001 | Batch (11 chains) | $0 |
| Stripe SPT | 🟡 Stub | Any | Card/ACH networks | ~2.9% + $0.30 |
