import asyncio
import websockets
import json
from typing import Dict, Any, Callable
import uuid
import time

class MCPClient:
    """MCP Client for agent communication"""
    
    def __init__(self, agent_name: str, server_url: str = "ws://localhost:8765"):
        self.agent_name = agent_name
        self.server_url = server_url
        self.websocket = None
        self.message_handlers = {}
        self.connected = False
    
    async def connect(self):
        """Connect to MCP server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            
            # Register with server
            register_msg = {
                "method": "register",
                "params": {"agent_name": self.agent_name}
            }
            await self.websocket.send(json.dumps(register_msg))
            
            response = await self.websocket.recv()
            result = json.loads(response)
            
            if result.get("status") == "registered":
                self.connected = True
                print(f"Agent {self.agent_name} connected to MCP server")
                
                # Start message listener
                asyncio.create_task(self._listen_for_messages())
            
        except Exception as e:
            print(f"Failed to connect to MCP server: {e}")
    
    async def _listen_for_messages(self):
        """Listen for incoming messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                method = data.get("method")
                
                if method in self.message_handlers:
                    handler = self.message_handlers[method]
                    await handler(data)
        
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            print(f"Agent {self.agent_name} disconnected from MCP server")
    
    def register_handler(self, method: str, handler: Callable):
        """Register message handler"""
        self.message_handlers[method] = handler
    
    async def send_message(self, receiver: str, method: str, params: Dict[str, Any]):
        """Send message to another agent"""
        if not self.connected:
            raise Exception("Not connected to MCP server")
        
        message = {
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params,
            "sender": self.agent_name,
            "receiver": receiver,
            "timestamp": time.time()
        }
        
        await self.websocket.send(json.dumps(message))
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False

# Example usage
async def example_agent():
    client = MCPClient("ExampleAgent")
    
    async def handle_request(data):
        print(f"Received request: {data}")
    
    client.register_handler("process_request", handle_request)
    
    await client.connect()
    
    # Send a message to another agent
    await client.send_message(
        receiver="ConstraintAgent",
        method="validate_constraints",
        params={"timetable": []}
    )
    
    # Keep running
    await asyncio.sleep(10)
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(example_agent())