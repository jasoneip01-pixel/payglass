# PayGlass 🔍

**Cross-protocol Agent payment observability.**

One pane of glass for all Agent payment traffic — Stripe SPT · x402 · Circle Nanopayments.

## Why

Three Agent payment protocols are racing to become the standard. Developers are stuck choosing between them. PayGlass doesn't pick a side — it makes all three observable.

| Protocol | Status | Settlement | Per-Payment Cost |
|----------|--------|-----------|-------------------|
| **x402** | HTTP-native standard | Batch (Circle Gateway) | ~$0 |
| **Circle Nanopayments** | Mainnet (May 2026) | Batch (11 chains) | $0 gas |
| **Stripe SPT** | Private preview | Card/ACH | ~2.9% + $0.30 |

## Architecture

```
Dashboard (HTML) ← Tracer (Python) ← Protocol Observers
                                       ├── x402Observer
                                       ├── NanopaymentsObserver
                                       └── StripeSPTObserver
```

## Quick Start

```bash
# Run demo — 8 payment scenarios across all 3 tracks
python3 demo.py

# View dashboard
python3 -m http.server 8080 -d dashboard/
# Open http://localhost:8080
```

## Circle Skill

PayGlass is also available as a Circle Skill for AI agents:

```python
# Any OpenClaw/Cursor/Codex agent can use PayGlass
from engine.tracer import PayGlassTracer
from engine.protocols.nanopayments import NanopaymentsObserver

tracer = PayGlassTracer()
nano = NanopaymentsObserver(tracer)

# Trace a sub-cent payment
tid, err = nano.trace_nanopayment(
    buyer_agent="my-agent",
    seller_service="https://api.example.com/data",
    amount_usdc=0.000050,  # $0.00005
)
```

## Demo Output

```
🎯 Summary: 8 payments, $141.001051 volume, 1 errors
   x402:              3 payments, $25.03,     0 errors
   Circle Nanopayments: 4 payments, $99.98,    1 error (validation catch)
   Stripe SPT:        1 payment,  $15.99,     0 errors
```

## Project Structure

```
payglass/
├── engine/              # Core observability engine
│   ├── tracer.py        # Unified event model + tracer
│   └── protocols/       # Protocol-specific observers
│       ├── x402.py
│       ├── nanopayments.py
│       └── stripe_spt.py
├── skill/
│   └── SKILL.md         # Circle Skill definition
├── dashboard/
│   └── index.html       # Unified dashboard
├── demo.py              # End-to-end demo
└── README.md
```

## License

MIT
