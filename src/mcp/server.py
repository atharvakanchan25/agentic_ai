"""
MCP (Model Context Protocol) Server for Agent Communication
Handles inter-agent messaging and coordination
"""
import asyncio
import json
import logging
import websockets
from typing import Dict, Set, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class MCPServer:
    """MCP Server for managing agent communication"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.agent_registry: Dict[str, Dict[str, Any]] = {}
        self.message_log: list = []
        self.running = False
    
    async def register_handler(self, websocket, path):
        """Handle new client connections"""
        try:
            logger.info(f"New connection from {websocket.remote_address}")
            
            # Wait for registration message
            registration_msg = await websocket.recv()
            registration_data = json.loads(registration_msg)
            
            if registration_data.get("method") == "register":
                agent_name = registration_data["params"]["agent_name"]
                capabilities = registration_data["params"].get("capabilities", [])
                
                # Register the agent
                self.clients[agent_name] = websocket
                self.agent_registry[agent_name] = {
                    "capabilities": capabilities,
                    "connected_at": datetime.utcnow().isoformat(),
                    "status": "active",
                    "websocket": websocket
                }
                
                # Send confirmation
                await websocket.send(json.dumps({
                    "status": "registered",
                    "agent_name": agent_name,
                    "server_time": datetime.utcnow().isoformat()
                }))
                
                logger.info(f"Agent {agent_name} registered successfully")
                
                # Handle messages from this agent
                await self.handle_agent_messages(agent_name, websocket)
            
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected during registration")
        except Exception as e:
            logger.error(f"Error in register_handler: {e}")
    
    async def handle_agent_messages(self, agent_name: str, websocket):
        """Handle messages from a registered agent"""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.route_message(agent_name, data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {agent_name}: {message}")
                except Exception as e:
                    logger.error(f"Error processing message from {agent_name}: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Agent {agent_name} disconnected")
            self.cleanup_agent(agent_name)
        except Exception as e:
            logger.error(f"Error handling messages from {agent_name}: {e}")
            self.cleanup_agent(agent_name)
    
    async def route_message(self, sender: str, message: Dict[str, Any]):
        """Route message to the appropriate recipient"""
        receiver = message.get("receiver")
        message_id = message.get("id", str(uuid.uuid4()))
        
        # Log the message
        log_entry = {
            "id": message_id,
            "timestamp": datetime.utcnow().isoformat(),
            "sender": sender,
            "receiver": receiver,
            "method": message.get("method"),
            "status": "routing"
        }
        self.message_log.append(log_entry)
        
        if receiver in self.clients:
            try:
                # Forward message to recipient
                await self.clients[receiver].send(json.dumps(message))
                
                # Update log
                log_entry["status"] = "delivered"
                logger.debug(f"Message routed: {sender} -> {receiver}")
                
            except Exception as e:
                log_entry["status"] = "failed"
                log_entry["error"] = str(e)
                logger.error(f"Failed to route message from {sender} to {receiver}: {e}")
        else:
            log_entry["status"] = "recipient_not_found"
            logger.warning(f"Recipient {receiver} not found for message from {sender}")
    
    def cleanup_agent(self, agent_name: str):
        """Clean up disconnected agent"""
        if agent_name in self.clients:
            del self.clients[agent_name]
        if agent_name in self.agent_registry:
            self.agent_registry[agent_name]["status"] = "disconnected"
            self.agent_registry[agent_name]["disconnected_at"] = datetime.utcnow().isoformat()
    
    async def broadcast_message(self, message: Dict[str, Any], exclude: Optional[str] = None):
        """Broadcast message to all connected agents"""
        for agent_name, websocket in self.clients.items():
            if agent_name != exclude:
                try:
                    await websocket.send(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to broadcast to {agent_name}: {e}")
    
    def get_agent_registry(self) -> Dict[str, Any]:
        """Get current agent registry"""
        return self.agent_registry
    
    def get_message_log(self) -> list:
        """Get message log"""
        return self.message_log
    
    async def start_server(self):
        """Start the MCP server"""
        logger.info(f"Starting MCP Server on {self.host}:{self.port}")
        self.running = True
        
        async with websockets.serve(self.register_handler, self.host, self.port):
            logger.info("MCP Server started successfully")
            while self.running:
                await asyncio.sleep(1)
    
    def stop_server(self):
        """Stop the MCP server"""
        logger.info("Stopping MCP Server")
        self.running = False

# Standalone server runner
async def run_mcp_server():
    """Run MCP server as standalone application"""
    from config import MCP_HOST, MCP_PORT
    
    server = MCPServer(MCP_HOST, MCP_PORT)
    await server.start_server()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_mcp_server())