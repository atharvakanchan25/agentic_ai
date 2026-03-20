"""
A2A Protocol (Agent-to-Agent)
Implements Google's A2A spec concepts:
  - AgentCard: self-describing capability manifest for each agent
  - AgentRegistry: central discovery of all registered agents
  - A2ATask: structured task delegation between agents via SLIM envelopes
  - Capability-based routing: find the right agent for a given capability
"""
import uuid
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ── Agent Card ────────────────────────────────────────────────────────────────

@dataclass
class AgentCard:
    """
    Self-describing manifest for an agent.
    Published to the AgentRegistry on startup.
    """
    agent_id:     str
    agent_name:   str
    version:      str = "1.0"
    description:  str = ""
    capabilities: list[str] = field(default_factory=list)
    input_schema: dict = field(default_factory=dict)   # JSON-schema style hints
    output_schema: dict = field(default_factory=dict)
    max_concurrency: int = 1
    trusted: bool = True   # set False for untrusted/external agents

    def to_dict(self) -> dict:
        return asdict(self)


# ── A2A Task ──────────────────────────────────────────────────────────────────

@dataclass
class A2ATask:
    """
    A structured task sent from one agent to another.
    Wraps the SLIM envelope concept at the application layer.
    """
    task_id:    str = field(default_factory=lambda: str(uuid.uuid4()))
    sender:     str = ""
    receiver:   str = ""
    capability: str = ""          # which capability is being invoked
    method:     str = ""
    params:     dict = field(default_factory=dict)
    run_id:     str = ""
    created_at: float = field(default_factory=time.time)
    status:     str = "pending"   # pending | running | completed | failed
    result:     Optional[dict] = None
    error:      Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ── Agent Registry ────────────────────────────────────────────────────────────

class AgentRegistry:
    """
    Central registry where agents publish their AgentCards.
    Supports capability-based lookup and health tracking.
    """

    def __init__(self):
        self._cards:    dict[str, AgentCard] = {}       # agent_name → card
        self._handlers: dict[str, Any] = {}             # agent_name → agent instance
        self._task_log: list[dict] = []

    def register(self, card: AgentCard, handler: Any = None) -> None:
        self._cards[card.agent_name] = card
        if handler:
            self._handlers[card.agent_name] = handler
        logger.info(f"[A2A] Registered agent '{card.agent_name}' with capabilities: {card.capabilities}")

    def get_card(self, agent_name: str) -> Optional[AgentCard]:
        return self._cards.get(agent_name)

    def find_by_capability(self, capability: str) -> list[AgentCard]:
        """Returns all trusted agents that advertise the given capability."""
        return [
            card for card in self._cards.values()
            if capability in card.capabilities and card.trusted
        ]

    def list_all(self) -> list[dict]:
        return [card.to_dict() for card in self._cards.values()]

    async def delegate(self, task: A2ATask) -> A2ATask:
        """
        Delegate a task to the target agent.
        Uses SLIM envelope for the actual call.
        Validates that the receiver advertises the requested capability.
        """
        from src.slim.protocol import create_envelope, validate_envelope, SLIMValidationError
        from src.observability.telemetry import get_current_trace_id, get_current_span_id

        task.status = "running"
        self._task_log.append(task.to_dict())

        # ── Capability check ──────────────────────────────────────────────────
        card = self._cards.get(task.receiver)
        if not card:
            task.status = "failed"
            task.error  = f"Agent '{task.receiver}' not registered"
            logger.error(f"[A2A] {task.error}")
            return task

        if task.capability and task.capability not in card.capabilities:
            task.status = "failed"
            task.error  = (
                f"Agent '{task.receiver}' does not advertise capability '{task.capability}'. "
                f"Available: {card.capabilities}"
            )
            logger.error(f"[A2A] {task.error}")
            return task

        if not card.trusted:
            task.status = "failed"
            task.error  = f"Agent '{task.receiver}' is not trusted"
            logger.error(f"[A2A] {task.error}")
            return task

        # ── Build + validate SLIM envelope ────────────────────────────────────
        envelope = create_envelope(
            sender=task.sender,
            receiver=task.receiver,
            method=task.method,
            params=task.params,
            run_id=task.run_id,
            trace_id=get_current_trace_id(),
            span_id=get_current_span_id(),
            correlation_id=task.task_id,
        )

        try:
            validate_envelope(envelope)
        except SLIMValidationError as e:
            task.status = "failed"
            task.error  = f"SLIM validation failed: {e}"
            logger.error(f"[A2A] {task.error}")
            return task

        # ── Dispatch to handler ───────────────────────────────────────────────
        handler = self._handlers.get(task.receiver)
        if not handler:
            task.status = "failed"
            task.error  = f"No handler registered for agent '{task.receiver}'"
            return task

        try:
            result = await handler.process_request({
                "method": task.method,
                "params": task.params,
                "_slim_envelope": envelope,
            })
            task.result = result
            task.status = "completed"
            logger.info(f"[A2A] Task {task.task_id} completed: {task.sender} → {task.receiver}.{task.method}")
        except Exception as e:
            task.status = "failed"
            task.error  = str(e)
            logger.error(f"[A2A] Task {task.task_id} failed: {e}")

        return task

    def task_history(self, limit: int = 50) -> list[dict]:
        return self._task_log[-limit:]


# ── Singleton registry ────────────────────────────────────────────────────────

agent_registry = AgentRegistry()
