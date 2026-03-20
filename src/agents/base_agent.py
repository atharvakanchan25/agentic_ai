"""
Base Agent - integrates:
  - StateMachine + ShortTermMemory
  - Security: HMAC token verification, rate limiting, input sanitization, audit log
  - OpenTelemetry: per-call spans with attributes
  - SLIM protocol: envelope validation on every process_request call
  - A2A: publishes an AgentCard to the global registry on init
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable
from datetime import datetime

from .state_machine import AgentState, StateMachine
from .memory import ShortTermMemory

logger = logging.getLogger(__name__)


class BaseAgent(ABC):

    def __init__(self, agent_name: str, capabilities: list[str] = None,
                 mcp_enabled: bool = False, trusted: bool = True):
        self.agent_name  = agent_name
        self.capabilities = capabilities or []
        self.mcp_enabled  = mcp_enabled
        self.mcp_client   = None
        self.trusted      = trusted
        self.logger       = logging.getLogger(f"agent.{agent_name}")
        self.metrics      = {"tasks_completed": 0, "errors": 0, "start_time": datetime.utcnow()}

        self._sm              = StateMachine(AgentState.INITIALIZED)
        self.memory           = ShortTermMemory()
        self.long_term_memory = None
        self._tools: dict[str, Callable] = {}

    # ── State helpers ─────────────────────────────────────────────────────────

    @property
    def state(self) -> AgentState:
        return self._sm.state

    def _set_state(self, new_state: AgentState) -> None:
        self._sm.transition(new_state)
        self.logger.debug(f"[{self.agent_name}] state → {new_state.name}")

    # ── Tool registry ─────────────────────────────────────────────────────────

    def register_tool(self, name: str, fn: Callable) -> None:
        self._tools[name] = fn

    def use_tool(self, name: str, **kwargs) -> Any:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered on {self.agent_name}")
        self.logger.debug(f"[{self.agent_name}] using tool: {name}")
        return self._tools[name](**kwargs)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def initialize(self, mcp_server_url: str = "ws://localhost:8765") -> bool:
        if self.mcp_enabled:
            try:
                from src.mcp.client import MCPClient
                self.mcp_client = MCPClient(self.agent_name, self.capabilities, mcp_server_url)
                await self.mcp_client.connect()
            except Exception as e:
                self.logger.warning(f"MCP connection failed, running standalone: {e}")

        await self._initialize_agent()
        self._register_a2a()
        self._set_state(AgentState.READY)
        return True

    def _register_a2a(self) -> None:
        """Publish this agent's AgentCard to the global A2A registry."""
        try:
            from src.a2a.registry import agent_registry, AgentCard
            card = AgentCard(
                agent_id=f"{self.agent_name}-{id(self)}",
                agent_name=self.agent_name,
                capabilities=self.capabilities,
                description=self.__class__.__doc__ or "",
                trusted=self.trusted,
            )
            agent_registry.register(card, handler=self)
        except Exception as e:
            self.logger.warning(f"[A2A] Registration failed: {e}")

    def log_action(self, action: str, details: dict[str, Any] = None):
        self.logger.info(f"[{self.agent_name}] {action}")

    async def shutdown(self):
        await self._cleanup_agent()
        if self.mcp_client:
            await self.mcp_client.disconnect()

    # ── Secured process_request wrapper ──────────────────────────────────────

    async def process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Public entry point. Applies security checks, SLIM validation,
        OTEL span, and audit logging before delegating to _handle_request.
        """
        from src.security.agent_security import (
            rate_limiter, audit_log, sanitize_payload, check_payload_size,
            verify_agent_call,
        )
        from src.observability.telemetry import agent_span
        from src.slim.protocol import validate_envelope, SLIMValidationError

        method = request.get("method", "unknown")
        run_id = request.get("params", {}).get("run_id", "") or self.memory.get("run_id", "")
        start  = time.time()

        # ── Rate limit ────────────────────────────────────────────────────────
        if not rate_limiter.allow(self.agent_name):
            err = {"status": "error", "message": f"Rate limit exceeded for {self.agent_name}"}
            audit_log.record(self.agent_name, method, run_id, "rate_limited", 0)
            return err

        # ── SLIM envelope validation (if present) ─────────────────────────────
        slim_envelope = request.get("_slim_envelope")
        if slim_envelope:
            try:
                validate_envelope(slim_envelope)
            except SLIMValidationError as e:
                err = {"status": "error", "message": f"SLIM validation failed: {e}"}
                audit_log.record(self.agent_name, method, run_id, "slim_rejected",
                                 (time.time() - start) * 1000, str(e))
                self.logger.warning(f"[{self.agent_name}] SLIM rejected: {e}")
                return err

        # ── HMAC token verification (if token present) ────────────────────────
        token = request.get("_auth_token")
        if token:
            if not verify_agent_call(token, self.agent_name, method, run_id):
                err = {"status": "error", "message": "Invalid auth token"}
                audit_log.record(self.agent_name, method, run_id, "auth_failed",
                                 (time.time() - start) * 1000)
                self.logger.warning(f"[{self.agent_name}] Auth token rejected for {method}")
                return err

        # ── Input sanitization ────────────────────────────────────────────────
        params = request.get("params", {})
        if not check_payload_size(params):
            err = {"status": "error", "message": "Payload too large"}
            audit_log.record(self.agent_name, method, run_id, "payload_too_large",
                             (time.time() - start) * 1000)
            return err
        request = {**request, "params": sanitize_payload(params)}

        # ── OTEL span + actual execution ──────────────────────────────────────
        status = "success"
        error  = ""
        result: dict = {}

        with agent_span(self.agent_name, method, run_id):
            try:
                self.metrics["tasks_completed"] += 1
                result = await self._handle_request(request)
                if result.get("status") == "error":
                    status = "error"
                    error  = result.get("message", "")
                    self.metrics["errors"] += 1
            except Exception as e:
                status = "error"
                error  = str(e)
                self.metrics["errors"] += 1
                self.logger.error(f"[{self.agent_name}] Unhandled error in {method}: {e}")
                result = {"status": "error", "message": error}

        duration_ms = (time.time() - start) * 1000
        audit_log.record(self.agent_name, method, run_id, status, duration_ms, error)
        return result

    # ── Abstract interface ────────────────────────────────────────────────────

    @abstractmethod
    async def _handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Subclasses implement their logic here (previously process_request)."""
        pass

    @abstractmethod
    async def _initialize_agent(self): pass

    @abstractmethod
    def _register_custom_handlers(self): pass

    @abstractmethod
    async def _cleanup_agent(self): pass
