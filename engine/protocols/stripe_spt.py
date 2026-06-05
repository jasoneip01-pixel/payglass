"""
Stripe SPT Protocol Observer — Agent commerce via Stripe (stub).

Stripe SPT (Session Payment Token) is in private preview.
This observer provides the trace schema and stubs for when the API becomes available.

SPT flow (based on public docs):
  1. Agent session established with Link agent wallet
  2. Token created for payment authorization
  3. Payment processed through Stripe rails
  4. Settlement via existing card/ACH networks

Note: This is a stub. Real integration requires Stripe SPT API access.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from typing import Optional

from ..tracer import TraceEvent, EventStatus, Protocol, PayGlassTracer


class StripeSPTObserver:
    """Stub observer for Stripe SPT payments.

    Will be activated when Stripe SPT enters public beta.
    Currently records placeholder traces for dashboard completeness.
    """

    def __init__(self, tracer: PayGlassTracer):
        self.tracer = tracer
        tracer.register_observer(Protocol.STRIPE_SPT, self)

    def trace_payment(
        self,
        resource_url: str,
        amount_usdc: float,
        source_agent: str,
        payment_method: str = "link_agent_wallet",
    ) -> str:
        """Record a Stripe SPT payment trace (stub)."""
        trace_id = hashlib.sha256(
            f"spt:{resource_url}:{source_agent}:{uuid.uuid4().hex}".encode()
        ).hexdigest()[:16]

        now_ms = int(time.time() * 1000)

        steps = [
            ("session_init", EventStatus.PENDING, now_ms, {"wallet": payment_method}),
            ("token_create", EventStatus.PENDING, now_ms + 50, {}),
            ("authorization", EventStatus.VERIFIED, now_ms + 300, {"processor": "stripe"}),
            ("payment_complete", EventStatus.VERIFIED, now_ms + 800, {}),
            ("settlement", EventStatus.SETTLED, now_ms + 2000, {"network": "card/ach"}),
        ]

        for event_type, status, ts, meta in steps:
            self.tracer.ingest(TraceEvent(
                trace_id=trace_id,
                protocol=Protocol.STRIPE_SPT,
                event_type=event_type,
                status=status,
                timestamp_ms=ts,
                amount_usdc=amount_usdc,
                source_agent=source_agent,
                target_service=resource_url,
                metadata=meta,
            ))

        return trace_id
