#!/usr/bin/env python3
"""
PayGlass Demo — Simulate end-to-end Agent payment flows across all three tracks.

Runs realistic scenarios:
  1. x402: Pay-per-call LLM API ($0.01)
  2. x402: Data oracle query ($0.02)
  3. x402: Bulk model inference ($25.00)
  4. Nanopayments: Sub-cent price feed ($0.000050)
  5. Nanopayments: API metering ($0.001)
  6. Nanopayments: Validation failure (below $0.000001)
  7. Nanopayments: Wallet top-up ($99.98)
  8. Stripe SPT: E-commerce checkout ($15.99)

Output: JSON dashboard + HTML visualization-ready data.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.tracer import PayGlassTracer
from engine.protocols.x402 import X402Observer
from engine.protocols.nanopayments import NanopaymentsObserver
from engine.protocols.stripe_spt import StripeSPTObserver


def run_demo():
    tracer = PayGlassTracer()
    x402 = X402Observer(tracer)
    nano = NanopaymentsObserver(tracer)
    spt = StripeSPTObserver(tracer)

    print("🔍 PayGlass Demo — Agent Payment Observatory")
    print("=" * 60)

    # ── Track 1: x402 Protocol ──────────────────────────────
    print("\n📡 Track 1: x402 Protocol")

    # Scenario A: Pay-per-call LLM
    tid1 = x402.trace_payment(
        resource_url="https://api.openai.com/v1/chat/completions",
        amount_usdc=0.01,
        source_agent="research-agent-42",
        chain="arbitrum",
    )
    print(f"  ✅ LLM API call: {tid1} — $0.01")

    # Scenario B: Data oracle
    tid2 = x402.trace_payment(
        resource_url="https://oracle.chainlink.com/eth-usd",
        amount_usdc=0.02,
        source_agent="trading-agent-7",
        chain="arbitrum",
    )
    print(f"  ✅ Oracle query: {tid2} — $0.02")

    # Scenario C: Bulk inference
    tid3 = x402.trace_payment(
        resource_url="https://inference.example.com/batch/v1",
        amount_usdc=25.00,
        source_agent="analytics-agent-3",
        chain="optimism",
    )
    print(f"  ✅ Batch inference: {tid3} — $25.00")

    # Settle x402 batch
    x402.settle_batch(tid1, "batch-x402-001", "0xabc123...settle1", "arbitrum")
    x402.settle_batch(tid2, "batch-x402-001", "0xabc123...settle1", "arbitrum")
    x402.settle_batch(tid3, "batch-x402-002", "0xdef456...settle2", "optimism")
    print(f"  📦 Batch settled: 2 batches (3 payments)")

    # ── Track 2: Circle Nanopayments ────────────────────────
    print("\n📡 Track 2: Circle Nanopayments")

    # Scenario D: Sub-cent price feed (typical nanopayment use case)
    tid4, err4 = nano.trace_nanopayment(
        buyer_agent="data-agent-7",
        seller_service="https://feeds.circle.com/btc-usd",
        amount_usdc=0.000050,  # 5 hundred-thousandths
        chain="arbitrum",
    )
    if err4:
        print(f"  ❌ Price feed: {err4}")
    else:
        print(f"  ✅ Nanopayment price feed: {tid4} — $0.000050")

    # Scenario E: API metering at scale
    tid5, err5 = nano.trace_nanopayment(
        buyer_agent="monitor-agent-1",
        seller_service="https://metrics.example.com/api/v2/query",
        amount_usdc=0.001,
        chain="arbitrum",
    )
    if err5:
        print(f"  ❌ API metering: {err5}")
    else:
        print(f"  ✅ API metering: {tid5} — $0.001")

    # Scenario F: Validation failure — below minimum
    tid6, err6 = nano.trace_nanopayment(
        buyer_agent="test-agent-0",
        seller_service="https://test.example.com/ping",
        amount_usdc=0.0000005,  # BELOW $0.000001 minimum
        chain="arbitrum",
    )
    if err6:
        print(f"  ⚠️  Validation caught: {err6}")
    else:
        print(f"  ❌ Should have failed validation!")

    # Scenario G: Wallet top-up (large nanopayment)
    tid7, err7 = nano.trace_nanopayment(
        buyer_agent="treasury-agent-0",
        seller_service="https://gateway.circle.com/deposit",
        amount_usdc=99.98,
        chain="arbitrum",
    )
    if err7:
        print(f"  ❌ Deposit: {err7}")
    else:
        print(f"  ✅ Wallet deposit: {tid7} — $99.98")

    # Batch settle nanopayments
    nano.batch_settle(
        trace_ids=[tid4, tid5, tid7],
        batch_id="batch-nano-001",
        tx_hash="0xnano001...batch",
        chain="arbitrum",
    )
    print(f"  📦 Batch settled: 1 batch (3 payments), gas: $0.02 total")

    # ── Track 3: Stripe SPT ─────────────────────────────────
    print("\n📡 Track 3: Stripe SPT (stub)")

    tid8 = spt.trace_payment(
        resource_url="https://shop.example.com/api/checkout",
        amount_usdc=15.99,
        source_agent="shopping-agent-3",
    )
    print(f"  ✅ E-commerce checkout: {tid8} — $15.99")

    # ── Dashboard ───────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📊 DASHBOARD")
    print("=" * 60)

    dashboard = tracer.dashboard()
    print(json.dumps(dashboard, indent=2))

    # Write dashboard JSON for the HTML to consume
    json_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "dashboard", "data.json"
    )
    with open(json_path, "w") as f:
        json.dump(dashboard, f, indent=2)
    print(f"\n💾 Dashboard data written to {json_path}")

    # Summary
    total = dashboard["total_payments"]
    volume = dashboard["total_volume_usdc"]
    errors = len(dashboard["error_traces"])
    print(f"\n🎯 Summary: {total} payments, ${volume:.6f} volume, {errors} errors")
    print(f"   Protocols: {json.dumps(dashboard['by_protocol'], indent=2)}")

    return dashboard


if __name__ == "__main__":
    run_demo()
