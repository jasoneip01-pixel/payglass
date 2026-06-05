"""
PayGlass Core Tracer — Unified payment flow observability across protocols.

Tracks the full lifecycle of an Agent payment:
  EIP-3009 signature → Gateway verification → batch settlement → on-chain finality

Supports three protocols:
  - x402: HTTP-native agent payment standard
  - Circle Nanopayments: Gas-free USDC micro-payment rail  
  - Stripe SPT: Agent commerce via Stripe (stub, private preview)

Architecture:
  Each protocol has an Observer that normalizes events into a common TraceEvent schema.
  The Tracer aggregates across protocols and exposes a unified timeline.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional

# ── Unified Event Model ──────────────────────────────────────────────

class EventStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    BATCHED = "batched"
    SETTLED = "settled"
    FAILED = "failed"
    DISPUTED = "disputed"

class Protocol(Enum):
    X402 = "x402"
    NANOPAYMENTS = "circle-nanopayments"
    STRIPE_SPT = "stripe-spt"

@dataclass
class TraceEvent:
    """A single step in a payment's lifecycle, normalized across protocols."""
    trace_id: str
    protocol: Protocol
    event_type: str              # e.g. "signature", "verification", "batch", "settlement"
    status: EventStatus
    timestamp_ms: int
    amount_usdc: float           # denominated in USDC
    source_agent: str            # agent identifier
    target_service: str          # service/resource being paid for
    chain: Optional[str] = None  # blockchain (for on-chain events)
    tx_hash: Optional[str] = None
    batch_id: Optional[str] = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["protocol"] = self.protocol.value
        d["status"] = self.status.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

# ── Tracer ────────────────────────────────────────────────────────────

@dataclass
class PaymentTrace:
    """Full lifecycle trace of a single payment."""
    payment_id: str
    protocol: Protocol
    events: list[TraceEvent] = field(default_factory=list)
    created_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    total_amount_usdc: float = 0.0
    settlement_time_ms: Optional[int] = None  # time from first event to settlement

    @property
    def latency_ms(self) -> Optional[int]:
        if not self.events:
            return None
        first = self.events[0].timestamp_ms
        settled = [e for e in self.events if e.status == EventStatus.SETTLED]
        if settled:
            return settled[-1].timestamp_ms - first
        return None

    @property
    def is_complete(self) -> bool:
        return any(e.status == EventStatus.SETTLED for e in self.events)

    @property
    def has_errors(self) -> bool:
        return any(e.status == EventStatus.FAILED for e in self.events)

    def summary(self) -> dict:
        return {
            "payment_id": self.payment_id,
            "protocol": self.protocol.value,
            "amount": f"${self.total_amount_usdc:.6f}",
            "events": len(self.events),
            "latency_ms": self.latency_ms,
            "complete": self.is_complete,
            "errors": self.has_errors,
            "settlement_time_ms": self.settlement_time_ms,
        }

class PayGlassTracer:
    """Cross-protocol payment observability engine.

    Usage:
        tracer = PayGlassTracer()
        tracer.ingest(event)       # feed normalized events
        trace = tracer.get_trace(payment_id)  # retrieve full trace
        dashboard = tracer.dashboard()        # aggregated view
    """

    def __init__(self):
        self._traces: dict[str, PaymentTrace] = {}
        self._observers: dict[Protocol, object] = {}

    def register_observer(self, protocol: Protocol, observer):
        """Register a protocol observer for auto-normalization."""
        self._observers[protocol] = observer

    def ingest(self, event: TraceEvent) -> PaymentTrace:
        """Ingest a normalized event, creating or updating a payment trace."""
        if event.trace_id not in self._traces:
            trace = PaymentTrace(
                payment_id=event.trace_id,
                protocol=event.protocol,
                total_amount_usdc=event.amount_usdc,
            )
            self._traces[event.trace_id] = trace
        else:
            trace = self._traces[event.trace_id]

        trace.events.append(event)

        if event.status == EventStatus.SETTLED:
            trace.settlement_time_ms = event.timestamp_ms

        return trace

    def get_trace(self, payment_id: str) -> Optional[PaymentTrace]:
        return self._traces.get(payment_id)

    def list_traces(self, protocol: Optional[Protocol] = None) -> list[PaymentTrace]:
        traces = list(self._traces.values())
        if protocol:
            traces = [t for t in traces if t.protocol == protocol]
        return sorted(traces, key=lambda t: t.created_at_ms, reverse=True)

    def dashboard(self) -> dict:
        """Aggregated dashboard data for the unified view."""
        traces = list(self._traces.values())
        by_protocol = {}
        for t in traces:
            p = t.protocol.value
            if p not in by_protocol:
                by_protocol[p] = {"count": 0, "volume_usdc": 0.0, "errors": 0, "avg_latency_ms": 0}
            stats = by_protocol[p]
            stats["count"] += 1
            stats["volume_usdc"] += t.total_amount_usdc
            if t.has_errors:
                stats["errors"] += 1
            if t.latency_ms:
                stats["avg_latency_ms"] += t.latency_ms

        for p in by_protocol:
            if by_protocol[p]["count"] > 0:
                by_protocol[p]["avg_latency_ms"] //= by_protocol[p]["count"]

        error_traces = [t.summary() for t in traces if t.has_errors]
        pending = [t.summary() for t in traces if not t.is_complete and not t.has_errors]

        return {
            "total_payments": len(traces),
            "total_volume_usdc": sum(t.total_amount_usdc for t in traces),
            "by_protocol": by_protocol,
            "error_traces": error_traces,
            "pending_traces": pending,
            "recent_traces": [t.summary() for t in traces[:20]],
        }

    def to_json(self) -> str:
        return json.dumps(self.dashboard(), indent=2)
