"""
Base Agent class - works standalone or with MCP
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseAgent(ABC):

    def __init__(self, agent_name: str, capabilities: List[str] = None, mcp_enabled: bool = False):
        self.agent_name = agent_name
        self.capabilities = capabilities or []
        self.mcp_enabled = mcp_enabled
        self.mcp_client = None
        self.status = "initialized"
        self.logger = logging.getLogger(f"agent.{agent_name}")
        self.metrics = {
            "tasks_completed": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }

    async def initialize(self, mcp_server_url: str = "ws://localhost:8765") -> bool:
        if self.mcp_enabled:
            try:
                from src.mcp.client import MCPClient
                self.mcp_client = MCPClient(self.agent_name, self.capabilities, mcp_server_url)
                connected = await self.mcp_client.connect()
                self.status = "connected" if connected else "standalone"
            except Exception as e:
                self.logger.warning(f"MCP connection failed, running standalone: {e}")
                self.status = "standalone"
        else:
            self.status = "standalone"

        await self._initialize_agent()
        self.status = "ready"
        return True

    def log_action(self, action: str, details: Dict[str, Any] = None):
        self.logger.info(f"[{self.agent_name}] {action}")

    async def shutdown(self):
        await self._cleanup_agent()
        if self.mcp_client:
            await self.mcp_client.disconnect()
        self.status = "shutdown"

    @abstractmethod
    async def _initialize_agent(self): pass

    @abstractmethod
    def _register_custom_handlers(self): pass

    @abstractmethod
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    async def _cleanup_agent(self): pass
