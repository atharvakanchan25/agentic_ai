"""
SLIM Protocol (Structured, Lightweight, Integrity-checked Messaging)
Every agent call is wrapped in a SLIM envelope that provides:
  - Versioned message schema
  - HMAC integrity signature
  - Trace context propagation (trace_id, span_id)
  - Sender/receiver identity
  - Timestamp + TTL (reject stale messages)
  - Correlation ID for request/response matching
"""
import hashlib
import hmac
import json
import time
import uuid
import logging
from typing import Any

logger = logging.getLogger(__name__)

SLIM_VERSION   = "1.0"
MESSAGE_TTL_S  = 300   # reject messages older than 5 minutes


def _get_secret() -> bytes:
    import config
    return config.SECRET_KEY.encode()


# ── Envelope creation ─────────────────────────────────────────────────────────

def create_envelope(
    sender: str,
    receiver: str,
    method: str,
    params: dict,
    run_id: str = "",
    trace_id: str = "",
    span_id: str = "",
    correlation_id: str = "",
) -> dict:
    """
    Wraps a method call in a SLIM envelope with HMAC signature.
    """
    envelope = {
        "slim_version":    SLIM_VERSION,
        "message_id":      str(uuid.uuid4()),
        "correlation_id":  correlation_id or str(uuid.uuid4()),
        "timestamp":       time.time(),
        "ttl":             MESSAGE_TTL_S,
        "sender":          sender,
        "receiver":        receiver,
        "method":          method,
        "params":          params,
        "run_id":          run_id,
        "trace_context": {
            "trace_id": trace_id,
            "span_id":  span_id,
        },
        "signature":       "",   # filled below
    }
    envelope["signature"] = _sign(envelope)
    return envelope


def _sign(envelope: dict) -> str:
    """HMAC-SHA256 over the canonical fields (excludes the signature field itself)."""
    canonical = json.dumps({
        k: v for k, v in envelope.items() if k != "signature"
    }, sort_keys=True, separators=(",", ":"))
    return hmac.new(_get_secret(), canonical.encode(), hashlib.sha256).hexdigest()


# ── Envelope validation ───────────────────────────────────────────────────────

class SLIMValidationError(Exception):
    pass


def validate_envelope(envelope: dict) -> None:
    """
    Validates a SLIM envelope. Raises SLIMValidationError on any failure.
    Checks: version, required fields, TTL, HMAC signature.
    """
    if not isinstance(envelope, dict):
        raise SLIMValidationError("Envelope must be a dict")

    if envelope.get("slim_version") != SLIM_VERSION:
        raise SLIMValidationError(
            f"Unsupported SLIM version: {envelope.get('slim_version')} (expected {SLIM_VERSION})"
        )

    for field in ["message_id", "sender", "receiver", "method", "timestamp", "signature"]:
        if not envelope.get(field):
            raise SLIMValidationError(f"Missing required field: {field}")

    # TTL check
    age = time.time() - envelope["timestamp"]
    if age > envelope.get("ttl", MESSAGE_TTL_S):
        raise SLIMValidationError(f"Message expired: age={age:.1f}s > ttl={envelope.get('ttl')}s")

    if age < -10:
        raise SLIMValidationError(f"Message timestamp is in the future: age={age:.1f}s")

    # Signature check
    received_sig = envelope["signature"]
    expected_sig = _sign(envelope)
    if not hmac.compare_digest(received_sig, expected_sig):
        raise SLIMValidationError("HMAC signature mismatch — message may have been tampered")


# ── Envelope unwrapping ───────────────────────────────────────────────────────

def unwrap(envelope: dict) -> tuple[str, dict]:
    """
    Validates and unwraps a SLIM envelope.
    Returns (method, params) on success.
    Raises SLIMValidationError on failure.
    """
    validate_envelope(envelope)
    return envelope["method"], envelope.get("params", {})


def create_response(request_envelope: dict, result: dict, sender: str) -> dict:
    """Creates a SLIM response envelope correlated to the request."""
    return create_envelope(
        sender=sender,
        receiver=request_envelope["sender"],
        method=f"{request_envelope['method']}.response",
        params=result,
        run_id=request_envelope.get("run_id", ""),
        trace_id=request_envelope.get("trace_context", {}).get("trace_id", ""),
        span_id=request_envelope.get("trace_context", {}).get("span_id", ""),
        correlation_id=request_envelope.get("correlation_id", ""),
    )
