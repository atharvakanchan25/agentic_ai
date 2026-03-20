"""
Agent Security
- HMAC-signed identity tokens for every agent call
- Input payload sanitization (size limits, type enforcement)
- Per-agent rate limiting (token bucket)
- Audit log of every agent invocation
"""
import hashlib
import hmac
import time
import uuid
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# ── HMAC token signing ────────────────────────────────────────────────────────

def _get_secret() -> bytes:
    import config
    return config.SECRET_KEY.encode()


def sign_agent_call(agent_name: str, method: str, run_id: str) -> str:
    """
    Returns an HMAC-SHA256 token for a specific agent/method/run_id triple.
    The orchestrator generates this; the agent verifies it before executing.
    """
    payload = f"{agent_name}:{method}:{run_id}:{int(time.time() // 60)}"
    return hmac.new(_get_secret(), payload.encode(), hashlib.sha256).hexdigest()


def verify_agent_call(token: str, agent_name: str, method: str, run_id: str) -> bool:
    """
    Verifies the token. Accepts tokens from the current minute and the previous
    minute to handle clock skew at minute boundaries.
    """
    now = int(time.time() // 60)
    for ts in [now, now - 1]:
        payload = f"{agent_name}:{method}:{run_id}:{ts}"
        expected = hmac.new(_get_secret(), payload.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(token, expected):
            return True
    return False


# ── Input sanitization ────────────────────────────────────────────────────────

MAX_PAYLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_LIST_LENGTH   = 10_000
MAX_STRING_LENGTH = 50_000


def sanitize_payload(payload: Any, _depth: int = 0) -> Any:
    """
    Recursively sanitize agent input:
    - Truncate oversized strings
    - Truncate oversized lists
    - Reject payloads that exceed MAX_PAYLOAD_BYTES
    - Strip None keys from dicts
    """
    if _depth > 20:
        return {}  # prevent infinite recursion on deeply nested input

    if isinstance(payload, str):
        if len(payload) > MAX_STRING_LENGTH:
            logger.warning(f"[Security] String truncated from {len(payload)} to {MAX_STRING_LENGTH} chars")
            return payload[:MAX_STRING_LENGTH]
        return payload

    if isinstance(payload, list):
        if len(payload) > MAX_LIST_LENGTH:
            logger.warning(f"[Security] List truncated from {len(payload)} to {MAX_LIST_LENGTH} items")
            payload = payload[:MAX_LIST_LENGTH]
        return [sanitize_payload(item, _depth + 1) for item in payload]

    if isinstance(payload, dict):
        return {
            k: sanitize_payload(v, _depth + 1)
            for k, v in payload.items()
            if k is not None
        }

    return payload


def check_payload_size(payload: dict) -> bool:
    import json
    size = len(json.dumps(payload).encode())
    if size > MAX_PAYLOAD_BYTES:
        logger.error(f"[Security] Payload too large: {size} bytes (max {MAX_PAYLOAD_BYTES})")
        return False
    return True


# ── Per-agent rate limiter (token bucket) ─────────────────────────────────────

class RateLimiter:
    """
    Token bucket rate limiter per agent.
    Default: 60 calls/minute per agent.
    """

    def __init__(self, calls_per_minute: int = 60):
        self._rate      = calls_per_minute / 60.0   # tokens per second
        self._capacity  = calls_per_minute
        self._buckets: dict[str, dict] = defaultdict(lambda: {
            "tokens": calls_per_minute,
            "last_refill": time.time(),
        })

    def allow(self, agent_name: str) -> bool:
        bucket = self._buckets[agent_name]
        now    = time.time()
        elapsed = now - bucket["last_refill"]
        bucket["tokens"] = min(
            self._capacity,
            bucket["tokens"] + elapsed * self._rate
        )
        bucket["last_refill"] = now

        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True

        logger.warning(f"[Security] Rate limit hit for agent '{agent_name}'")
        return False


# ── Audit log ─────────────────────────────────────────────────────────────────

class AuditLog:
    """In-memory audit log of every agent invocation. Capped at 10,000 entries."""

    MAX_ENTRIES = 10_000

    def __init__(self):
        self._log: list[dict] = []

    def record(self, agent_name: str, method: str, run_id: str,
               status: str, duration_ms: float, error: str = ""):
        entry = {
            "id":          str(uuid.uuid4()),
            "timestamp":   datetime.utcnow().isoformat(),
            "agent":       agent_name,
            "method":      method,
            "run_id":      run_id,
            "status":      status,
            "duration_ms": round(duration_ms, 2),
            "error":       error,
        }
        self._log.append(entry)
        if len(self._log) > self.MAX_ENTRIES:
            self._log = self._log[-self.MAX_ENTRIES:]

    def recent(self, limit: int = 100) -> list[dict]:
        return self._log[-limit:]

    def by_agent(self, agent_name: str, limit: int = 50) -> list[dict]:
        return [e for e in self._log if e["agent"] == agent_name][-limit:]

    def errors(self, limit: int = 50) -> list[dict]:
        return [e for e in self._log if e["status"] == "error"][-limit:]


# Singletons used across the app
rate_limiter = RateLimiter(calls_per_minute=120)
audit_log    = AuditLog()
