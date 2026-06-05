"""
Circle Nanopayments Protocol Observer — Gas-free USDC micro-payment rail.

Tracks the Nanopayments flow:
  1. Buyer deposits USDC into Gateway Wallet (one-time on-chain tx)
  2. Buyer signs EIP-3009 authorization for each payment
  3. Seller sends signature to Circle Gateway
  4. Gateway verifies via AWS Nitro Enclave (TEE)
  5. Gateway deducts from off-chain balance
  6. Seller delivers resource (<1s after verification)
  7. Gateway batches thousands of payments → single on-chain settlement

Key invariants:
  - Per-payment gas: ZERO (gas only at batch level)
  - Minimum amount: $0.000001
  - Verification: <1 second
  - Settlement: periodic (configurable)
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from ..tracer import TraceEvent, EventStatus, Protocol, PayGlassTracer


GATEWAY_WALLET = "0xGatewayWallet"  # placeholder for Circle Gateway contract
MIN_NANO_AMOUNT = 0.000001  # $0.000001


@dataclass
class NanopaymentRequest:
    """Simulates a Circle Nanopayment request."""
    buyer_agent: str
    seller_service: str
    amount_usdc: float
    chain: str = "arbitrum"

    def validate(self) -> Optional[str]:
        """Validate payment parameters. Returns error message or None."""
        if self.amount_usdc < MIN_NANO_AMOUNT:
            return f"Amount ${self.amount_usdc} below minimum ${MIN_NANO_AMOUNT}"
        return None

    def to_authorization(self) -> dict:
        """Generate simulated EIP-3009 authorization for Nanopayments."""
        nonce = uuid.uuid4().hex[:16]
        message = (
            f"circle-gateway:{self.buyer_agent}→{self.seller_service}:"
            f"{self.amount_usdc}USDC:{nonce}"
        )
        sig_hash = hashlib.sha256(message.encode()).hexdigest()
        return {
            "eip3009_signature": f"0x{sig_hash[:64]}",
            "nonce": nonce,
            "amount": str(self.amount_usdc),
            "token": "USDC",
            "expiry": int(time.time()) + 3600,
            "gateway": "circle",
            "chain": self.chain,
        }


class NanopaymentsObserver:
    """Observes and normalizes Circle Nanopayments lifecycle events.

    Usage:
        tracer = PayGlassTracer()
        obs = NanopaymentsObserver(tracer)
        trace_id = obs.trace_nanopayment(buyer, seller, amount, chain)
    """

    def __init__(self, tracer: PayGlassTracer):
        self.tracer = tracer
        tracer.register_observer(Protocol.NANOPAYMENTS, self)

    def trace_nanopayment(
        self,
        buyer_agent: str,
        seller_service: str,
        amount_usdc: float,
        chain: str = "arbitrum",
    ) -> tuple[str, Optional[str]]:
        """Trace a complete Nanopayment flow. Returns (trace_id, error).

        If validation fails, returns (trace_id, error_message) where error_message is set.
        The trace will contain a FAILED event.
        """
        payment = NanopaymentRequest(
            buyer_agent=buyer_agent,
            seller_service=seller_service,
            amount_usdc=amount_usdc,
            chain=chain,
        )

        trace_id = hashlib.sha256(
            f"nano:{buyer_agent}:{seller_service}:{uuid.uuid4().hex}".encode()
        ).hexdigest()[:16]

        now_ms = int(time.time() * 1000)

        # Validation gate
        error = payment.validate()
        if error:
            self.tracer.ingest(TraceEvent(
                trace_id=trace_id,
                protocol=Protocol.NANOPAYMENTS,
                event_type="validation_failed",
                status=EventStatus.FAILED,
                timestamp_ms=now_ms,
                amount_usdc=amount_usdc,
                source_agent=buyer_agent,
                target_service=seller_service,
                chain=chain,
                error=error,
            ))
            return trace_id, error

        # Event 1: Deposit check (buyer must have USDC in Gateway Wallet)
        self.tracer.ingest(TraceEvent(
            trace_id=trace_id,
            protocol=Protocol.NANOPAYMENTS,
            event_type="deposit_check",
            status=EventStatus.PENDING,
            timestamp_ms=now_ms,
            amount_usdc=amount_usdc,
            source_agent=buyer_agent,
            target_service=seller_service,
            chain=chain,
            metadata={"wallet": GATEWAY_WALLET, "balance_ok": True},
        ))

        # Event 2: EIP-3009 authorization signed
        auth = payment.to_authorization()
        self.tracer.ingest(TraceEvent(
            trace_id=trace_id,
            protocol=Protocol.NANOPAYMENTS,
            event_type="authorization",
            status=EventStatus.PENDING,
            timestamp_ms=now_ms + 10,
            amount_usdc=amount_usdc,
            source_agent=buyer_agent,
            target_service=seller_service,
            chain=chain,
            metadata=auth,
        ))

        # Event 3: Gateway TEE verification
        self.tracer.ingest(TraceEvent(
            trace_id=trace_id,
            protocol=Protocol.NANOPAYMENTS,
            event_type="tee_verification",
            status=EventStatus.VERIFIED,
            timestamp_ms=now_ms + 500,
            amount_usdc=amount_usdc,
            source_agent=buyer_agent,
            target_service=seller_service,
            chain=chain,
            metadata={
                "enclave": "aws-nitro",
                "verification_ms": 450,
                "signature_valid": True,
            },
        ))

        # Event 4: Off-chain balance deduction
        self.tracer.ingest(TraceEvent(
            trace_id=trace_id,
            protocol=Protocol.NANOPAYMENTS,
            event_type="balance_deduction",
            status=EventStatus.VERIFIED,
            timestamp_ms=now_ms + 520,
            amount_usdc=amount_usdc,
            source_agent=buyer_agent,
            target_service=seller_service,
            chain=chain,
            metadata={"new_balance": f"${1000.0 - amount_usdc:.6f}"},
        ))

        # Event 5: Resource delivered (sub-second from authorization)
        self.tracer.ingest(TraceEvent(
            trace_id=trace_id,
            protocol=Protocol.NANOPAYMENTS,
            event_type="resource_delivered",
            status=EventStatus.VERIFIED,
            timestamp_ms=now_ms + 800,
            amount_usdc=amount_usdc,
            source_agent=buyer_agent,
            target_service=seller_service,
            chain=chain,
            metadata={"delivery_ms": 790},
        ))

        return trace_id, None

    def batch_settle(
        self,
        trace_ids: list[str],
        batch_id: str,
        tx_hash: str,
        chain: str = "arbitrum",
    ):
        """Settle multiple nanopayments in a single batch on-chain transaction."""
        now_ms = int(time.time() * 1000)

        for tid in trace_ids:
            trace = self.tracer.get_trace(tid)
            if not trace:
                continue

            # Batch event
            self.tracer.ingest(TraceEvent(
                trace_id=tid,
                protocol=Protocol.NANOPAYMENTS,
                event_type="batch",
                status=EventStatus.BATCHED,
                timestamp_ms=now_ms,
                amount_usdc=trace.total_amount_usdc,
                source_agent=trace.events[0].source_agent,
                target_service=trace.events[0].target_service,
                chain=chain,
                batch_id=batch_id,
                metadata={"batch_size": len(trace_ids), "gas_saved": "per-payment: $0"},
            ))

            # Settlement finality
            self.tracer.ingest(TraceEvent(
                trace_id=tid,
                protocol=Protocol.NANOPAYMENTS,
                event_type="settlement",
                status=EventStatus.SETTLED,
                timestamp_ms=now_ms + 2000,
                amount_usdc=trace.total_amount_usdc,
                source_agent=trace.events[0].source_agent,
                target_service=trace.events[0].target_service,
                chain=chain,
                tx_hash=tx_hash,
                metadata={"confirmations": 1, "final": True, "gas_cost_batch": "$0.02"},
            ))
