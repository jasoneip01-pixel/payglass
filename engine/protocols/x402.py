"""
x402 Protocol Observer — HTTP-native Agent payment standard.

Tracks the x402 payment flow:
  1. Agent sends HTTP request → receives 402 Payment Required
  2. Agent creates EIP-3009 USDC authorization signature
  3. Agent retries request with Payment header (x402 token + signature)
  4. Server verifies signature → delivers resource
  5. Gateway batches settlement on-chain

Reference: https://x402.org
Integration: Circle Gateway for batch settlement
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from ..tracer import TraceEvent, EventStatus, Protocol, PayGlassTracer


@dataclass
class X402PaymentRequest:
    """Simulates an x402 payment request for tracing."""
    resource_url: str
    amount_usdc: float
    source_agent: str
    chain: str = "arbitrum"  # default chain
    gateway: str = "circle"  # settlement gateway

    def to_signature(self) -> dict:
        """Generate a simulated EIP-3009 authorization."""
        nonce = uuid.uuid4().hex[:16]
        message = f"{self.resource_url}|{self.amount_usdc}|{self.source_agent}|{nonce}"
        sig_hash = hashlib.sha256(message.encode()).hexdigest()
        return {
            "eip3009_signature": f"0x{sig_hash[:64]}",
            "nonce": nonce,
            "amount": str(self.amount_usdc),
            "token": "USDC",
            "expiry": int(time.time()) + 3600,
        }


class X402Observer:
    """Observes and normalizes x402 payment lifecycle events.

    Usage:
        tracer = PayGlassTracer()
        obs = X402Observer(tracer)
        trace = obs.trace_payment(resource_url, amount, agent)
    """

    def __init__(self, tracer: PayGlassTracer):
        self.tracer = tracer
        tracer.register_observer(Protocol.X402, self)

    def trace_payment(
        self,
        resource_url: str,
        amount_usdc: float,
        source_agent: str,
        chain: str = "arbitrum",
    ) -> str:
        """Trace a complete x402 payment flow. Returns trace_id."""
        payment = X402PaymentRequest(
            resource_url=resource_url,
            amount_usdc=amount_usdc,
            source_agent=source_agent,
            chain=chain,
        )
        trace_id = hashlib.sha256(
            f"x402:{resource_url}:{source_agent}:{uuid.uuid4().hex}".encode()
        ).hexdigest()[:16]

        now_ms = int(time.time() * 1000)

        # Event 1: 402 Payment Required received
        self.tracer.ingest(TraceEvent(
            trace_id=trace_id,
            protocol=Protocol.X402,
            event_type="402_response",
            status=EventStatus.PENDING,
            timestamp_ms=now_ms,
            amount_usdc=amount_usdc,
            source_agent=source_agent,
            target_service=resource_url,
            metadata={"http_status": 402, "payment_header": "x402"},
        ))

        # Event 2: EIP-3009 signature created
        sig = payment.to_signature()
        self.tracer.ingest(TraceEvent(
            trace_id=trace_id,
            protocol=Protocol.X402,
            event_type="signature",
            status=EventStatus.PENDING,
            timestamp_ms=now_ms + 50,
            amount_usdc=amount_usdc,
            source_agent=source_agent,
            target_service=resource_url,
            metadata=sig,
        ))

        # Event 3: Payment header sent, request retried
        self.tracer.ingest(TraceEvent(
            trace_id=trace_id,
            protocol=Protocol.X402,
            event_type="payment_header",
            status=EventStatus.PENDING,
            timestamp_ms=now_ms + 100,
            amount_usdc=amount_usdc,
            source_agent=source_agent,
            target_service=resource_url,
        ))

        # Event 4: Gateway verification
        self.tracer.ingest(TraceEvent(
            trace_id=trace_id,
            protocol=Protocol.X402,
            event_type="verification",
            status=EventStatus.VERIFIED,
            timestamp_ms=now_ms + 500,
            amount_usdc=amount_usdc,
            source_agent=source_agent,
            target_service=resource_url,
            metadata={"gateway": "circle", "verifier": "aws-nitro-enclave"},
        ))

        # Event 5: Resource delivered
        self.tracer.ingest(TraceEvent(
            trace_id=trace_id,
            protocol=Protocol.X402,
            event_type="resource_delivered",
            status=EventStatus.VERIFIED,
            timestamp_ms=now_ms + 600,
            amount_usdc=amount_usdc,
            source_agent=source_agent,
            target_service=resource_url,
        ))

        return trace_id

    def settle_batch(self, trace_id: str, batch_id: str, tx_hash: str, chain: str = "arbitrum"):
        """Mark a payment as settled via batch on-chain settlement."""
        trace = self.tracer.get_trace(trace_id)
        if not trace:
            return

        now_ms = int(time.time() * 1000)

        # Event 6: Batch aggregation
        self.tracer.ingest(TraceEvent(
            trace_id=trace_id,
            protocol=Protocol.X402,
            event_type="batch",
            status=EventStatus.BATCHED,
            timestamp_ms=now_ms,
            amount_usdc=trace.total_amount_usdc,
            source_agent=trace.events[0].source_agent,
            target_service=trace.events[0].target_service,
            batch_id=batch_id,
            chain=chain,
            metadata={"batch_size": 1000, "settlement_gateway": "circle"},
        ))

        # Event 7: On-chain finality
        self.tracer.ingest(TraceEvent(
            trace_id=trace_id,
            protocol=Protocol.X402,
            event_type="settlement",
            status=EventStatus.SETTLED,
            timestamp_ms=now_ms + 2000,
            amount_usdc=trace.total_amount_usdc,
            source_agent=trace.events[0].source_agent,
            target_service=trace.events[0].target_service,
            chain=chain,
            tx_hash=tx_hash,
            metadata={"confirmations": 1, "final": True},
        ))
