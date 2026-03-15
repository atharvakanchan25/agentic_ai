"""
MCP Client for Agent Communication
"""
import asyncio
import json
import logging
import websockets
from typing import Dict, Any, Callable, Optional
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class MCPClient:
    """MCP Client for agent communication"""
    
    def __init__(self, agent_name: str, capabilities: list = None, server_url: str = "ws://localhost:8765"):
        self.agent_name = agent_name
        self.capabilities = capabilities or []
        self.server_url = server_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.message_handlers: Dict[str, Callable] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
    
    async def connect(self) -> bool:
        """Connect to MCP server"""
        try:
            logger.info(f"[{self.agent_name}] Connecting to MCP server at {self.server_url}")
            
            self.websocket = await websockets.connect(self.server_url)
            
            # Send registration message
            registration_msg = {
                "method": "register",
                "params": {
                    "agent_name": self.agent_name,
                    "capabilities": self.capabilities
                }
            }
            
            await self.websocket.send(json.dumps(registration_msg))
            
            # Wait for confirmation
            response = await self.websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("status") == "registered":
                self.connected = True
                logger.info(f"[{self.agent_name}] Successfully registered with MCP server")
                
                # Start message listener
                asyncio.create_task(self._listen_for_messages())
                return True
            else:
                logger.error(f"[{self.agent_name}] Registration failed: {response_data}")
                return False
                
        except Exception as e:
            logger.error(f"[{self.agent_name}] Failed to connect to MCP server: {e}")
            return False
    
    async def _listen_for_messages(self):
        """Listen for incoming messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    logger.error(f"[{self.agent_name}] Received invalid JSON: {message}")
                except Exception as e:
                    logger.error(f"[{self.agent_name}] Error handling message: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            logger.info(f"[{self.agent_name}] Disconnected from MCP server")
        except Exception as e:
            logger.error(f"[{self.agent_name}] Error in message listener: {e}")
            self.connected = False
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming message"""
        message_id = data.get("id")
        method = data.get("method")
        params = data.get("params", {})
        sender = data.get("sender")
        
        logger.debug(f"[{self.agent_name}] Received message from {sender}: {method}")
        
        # Check if this is a response to a pending request
        if message_id in self.pending_responses:
            future = self.pending_responses.pop(message_id)
            if not future.done():
                future.set_result(data)
            return
        
        # Handle method calls
        if method in self.message_handlers:
            try:
                handler = self.message_handlers[method]
                result = await handler(params)
                
                # Send response back if message has an ID
                if message_id and sender:
                    response = {
                        "id": message_id,
                        "sender": self.agent_name,
                        "receiver": sender,
                        "result": result,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.websocket.send(json.dumps(response))
                    
            except Exception as e:
                logger.error(f"[{self.agent_name}] Error in handler for {method}: {e}")
                
                # Send error response
                if message_id and sender:
                    error_response = {
                        "id": message_id,
                        "sender": self.agent_name,
                        "receiver": sender,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.websocket.send(json.dumps(error_response))
        else:
            logger.warning(f"[{self.agent_name}] No handler for method: {method}")
    
    def register_handler(self, method: str, handler: Callable):
        """Register a message handler"""
        self.message_handlers[method] = handler
        logger.debug(f"[{self.agent_name}] Registered handler for method: {method}")
    
    async def send_message(self, receiver: str, method: str, params: Dict[str, Any], wait_for_response: bool = False) -> Optional[Dict[str, Any]]:
        """Send message to another agent"""
        if not self.connected:
            raise Exception("Not connected to MCP server")
        
        message_id = str(uuid.uuid4())
        message = {
            "id": message_id,
            "sender": self.agent_name,
            "receiver": receiver,
            "method": method,
            "params": params,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Set up response waiting if requested
        response_future = None
        if wait_for_response:
            response_future = asyncio.Future()
            self.pending_responses[message_id] = response_future
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.debug(f"[{self.agent_name}] Sent message to {receiver}: {method}")
            
            if wait_for_response:
                # Wait for response with timeout
                try:
                    response = await asyncio.wait_for(response_future, timeout=30.0)
                    return response
                except asyncio.TimeoutError:
                    logger.error(f"[{self.agent_name}] Timeout waiting for response from {receiver}")
                    self.pending_responses.pop(message_id, None)
                    return None
            
            return {"status": "sent", "message_id": message_id}
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] Failed to send message to {receiver}: {e}")
            if message_id in self.pending_responses:
                self.pending_responses.pop(message_id)
            raise
    
    async def broadcast_message(self, method: str, params: Dict[str, Any]):
        """Broadcast message to all agents"""
        message = {
            "id": str(uuid.uuid4()),
            "sender": self.agent_name,
            "receiver": "broadcast",
            "method": method,
            "params": params,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.websocket.send(json.dumps(message))
        logger.debug(f"[{self.agent_name}] Broadcast message: {method}")
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info(f"[{self.agent_name}] Disconnected from MCP server")
    
    def is_connected(self) -> bool:
        """Check if connected to MCP server"""
        return self.connected