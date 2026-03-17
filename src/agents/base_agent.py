"""
Base Agent - integrates StateMachine, ShortTermMemory, and a tool registry.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable
from datetime import datetime

from .state_machine import AgentState, StateMachine
from .memory import ShortTermMemory

logger = logging.getLogger(__name__)


class BaseAgent(ABC):

    def __init__(self, agent_name: str, capabilities: list[str] = None, mcp_enabled: bool = False):
        self.agent_name = agent_name
        self.capabilities = capabilities or []
        self.mcp_enabled = mcp_enabled
        self.mcp_client = None
        self.logger = logging.getLogger(f"agent.{agent_name}")
        self.metrics = {"tasks_completed": 0, "errors": 0, "start_time": datetime.utcnow()}

        # State machine
        self._sm = StateMachine(AgentState.INITIALIZED)

        # Short-term memory (reset each pipeline run by orchestrator)
        self.memory = ShortTermMemory()

        # Long-term memory — injected by orchestrator when DB is available
        self.long_term_memory = None

        # Tool registry: name -> callable
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
        self._set_state(AgentState.READY)
        return True

    def log_action(self, action: str, details: dict[str, Any] = None):
        self.logger.info(f"[{self.agent_name}] {action}")

    async def shutdown(self):
        await self._cleanup_agent()
        if self.mcp_client:
            await self.mcp_client.disconnect()

    # ── Abstract interface ────────────────────────────────────────────────────

    @abstractmethod
    async def _initialize_agent(self): pass

    @abstractmethod
    def _register_custom_handlers(self): pass

    @abstractmethod
    async def process_request(self, request: dict[str, Any]) -> dict[str, Any]: pass

    @abstractmethod
    async def _cleanup_agent(self): pass
