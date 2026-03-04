# A2A Communication & MCP Server Architecture

## Overview

This document explains how Agent-to-Agent (A2A) communication works with the MCP (Model Context Protocol) server in the University Timetable Management System.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (Port 8765)                    │
│                  WebSocket Message Router                    │
└──────┬──────────────┬──────────────┬──────────────┬─────────┘
       │              │              │              │
   WebSocket     WebSocket      WebSocket      WebSocket
       │              │              │              │
┌──────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐ ┌─────▼──────────┐
│ Constraint  │ │Optimiza- │ │  Conflict  │ │   Resource     │
│   Agent     │ │tion Agent│ │ Resolution │ │  Allocation    │
│             │ │          │ │   Agent    │ │     Agent      │
└─────────────┘ └──────────┘ └────────────┘ └────────────────┘
```

## Components

### 1. MCP Server (`mcp_server/server.py`)
- **Purpose**: Central message router for all agents
- **Port**: 8765
- **Protocol**: WebSocket
- **Functions**:
  - Register agents
  - Route messages between agents
  - Queue messages if receiver offline
  - Track active connections

### 2. MCP Client (`mcp_server/client.py`)
- **Purpose**: Library for agents to connect to MCP server
- **Functions**:
  - Connect to MCP server
  - Send messages to other agents
  - Receive messages from other agents
  - Handle reconnection

### 3. Agent Orchestrator (`agents/orchestrator.py`)
- **Purpose**: Coordinates A2A workflow
- **Functions**:
  - Manages agent lifecycle
  - Logs all A2A messages
  - Coordinates multi-agent tasks
  - Returns communication logs

### 4. Individual Agents
- **Constraint Agent**: Validates rules
- **Optimization Agent**: Generates schedules
- **Conflict Resolution Agent**: Resolves conflicts
- **Resource Allocation Agent**: Allocates resources

## Communication Flow

### Scenario 1: Local A2A (Current Implementation)

```
User Request
    ↓
Orchestrator
    ↓
┌─────────────────────────────────────────┐
│ A2A Communication (Direct Function Calls)│
├─────────────────────────────────────────┤
│ 1. Orchestrator → ResourceAgent        │
│    result = resource_agent.allocate()  │
│                                         │
│ 2. Orchestrator → OptimizationAgent    │
│    result = optimization_agent.solve() │
│                                         │
│ 3. Orchestrator → ConstraintAgent      │
│    result = constraint_agent.validate()│
│                                         │
│ 4. ConstraintAgent → ConflictAgent     │
│    result = conflict_agent.resolve()   │
└─────────────────────────────────────────┘
    ↓
Response to User
```

### Scenario 2: Distributed A2A (With MCP Server)

```
User Request
    ↓
Orchestrator (connects to MCP)
    ↓
┌─────────────────────────────────────────┐
│ A2A via MCP (WebSocket Messages)       │
├─────────────────────────────────────────┤
│ 1. Orchestrator → MCP Server           │
│    Message: {                           │
│      sender: "Orchestrator",            │
│      receiver: "ResourceAgent",         │
│      method: "allocate_rooms",          │
│      params: {...}                      │
│    }                                    │
│    ↓                                    │
│    MCP Server → ResourceAgent           │
│    ↓                                    │
│    ResourceAgent → MCP Server           │
│    ↓                                    │
│    MCP Server → Orchestrator            │
│                                         │
│ 2. Orchestrator → OptimizationAgent    │
│    (via MCP Server)                     │
│                                         │
│ 3. Orchestrator → ConstraintAgent      │
│    (via MCP Server)                     │
└─────────────────────────────────────────┘
    ↓
Response to User
```

## Message Format

### MCP Message Structure

```python
{
    "id": "msg_12345",              # Unique message ID
    "method": "allocate_rooms",     # Action to perform
    "params": {                     # Data for the action
        "requirements": [...],
        "rooms": [...]
    },
    "sender": "Orchestrator",       # Who sent it
    "receiver": "ResourceAgent",    # Who should receive it
    "timestamp": 1234567890.123     # When it was sent
}
```

### A2A Log Entry

```python
{
    "sender": "Orchestrator",
    "receiver": "ResourceAllocationAgent",
    "message": "Allocate rooms for divisions",
    "data": {...},                  # Optional data
    "timestamp": "2024-01-15 10:30:00"
}
```

## Setup Instructions

### Option 1: Local A2A (No MCP Server)

**Current setup - agents communicate directly**

```bash
# Just start backend
cd backend
python main.py
```

**Pros:**
- Simple setup
- Fast communication
- No network overhead

**Cons:**
- All agents must run on same machine
- No distributed deployment

### Option 2: Distributed A2A (With MCP Server)

**Agents communicate via MCP server**

#### Step 1: Start MCP Server
```bash
cd mcp_server
python server.py
```

#### Step 2: Start Backend with MCP
```bash
cd backend
python main_with_mcp.py
```

#### Step 3: Agents Connect to MCP
Each agent connects to `ws://localhost:8765`

**Pros:**
- Agents can run on different machines
- Scalable architecture
- Message logging and monitoring

**Cons:**
- More complex setup
- Network latency
- Requires MCP server running

## Usage Examples

### Example 1: Local A2A Communication

```python
# In orchestrator.py

def generate_timetable(self, input_data):
    # Direct function call
    self.log_message("Orchestrator", "ResourceAgent", "Allocate rooms")
    result = self.resource_agent.allocate_rooms(...)
    
    self.log_message("Orchestrator", "OptimizationAgent", "Generate timetable")
    timetable = self.optimization_agent.optimize_timetable(...)
    
    return {
        'timetable': timetable,
        'message_log': self.message_log  # A2A communication log
    }
```

### Example 2: MCP-Based A2A Communication

```python
# In orchestrator_with_mcp.py

async def generate_timetable(self, input_data):
    # Connect to MCP
    mcp_client = MCPClient("Orchestrator")
    await mcp_client.connect()
    
    # Send message via MCP
    response = await mcp_client.send_message(
        receiver="ResourceAgent",
        method="allocate_rooms",
        params=input_data
    )
    
    # Wait for response
    result = await mcp_client.wait_for_response(response['message_id'])
    
    return result
```

## Monitoring A2A Communication

### View Communication Logs

**In Frontend:**
```javascript
// TimetableView.jsx shows message_log
{message_log.map((msg, idx) => (
    <div key={idx}>
        {msg.sender} → {msg.receiver}: {msg.message}
    </div>
))}
```

**In Backend:**
```python
# Access logs from orchestrator
orchestrator = AgentOrchestrator()
result = orchestrator.generate_timetable(data)

for msg in result['message_log']:
    print(f"{msg['sender']} → {msg['receiver']}: {msg['message']}")
```

## Configuration

### Enable/Disable MCP

**File: `config/config.py`**

```python
class Config:
    # A2A Communication
    USE_MCP_SERVER = False  # Set to True to use MCP server
    MCP_HOST = "localhost"
    MCP_PORT = 8765
    
    # Agent Settings
    AGENT_TIMEOUT = 60
    MAX_RETRIES = 3
```

## Testing

### Test Local A2A

```bash
cd agents
python test_agents.py
```

### Test MCP Server

```bash
# Terminal 1: Start MCP server
cd mcp_server
python server.py

# Terminal 2: Test client
python test_mcp_client.py
```

## Troubleshooting

### MCP Server Won't Start

**Error: Port 8765 already in use**
```bash
netstat -ano | findstr :8765
taskkill /PID <PID> /F
```

### Agent Can't Connect to MCP

**Check:**
1. MCP server is running
2. Firewall allows port 8765
3. Correct host/port in config

### Messages Not Delivered

**Check:**
1. Both agents are registered
2. Agent names match exactly
3. Check MCP server logs

## Best Practices

1. **Use Local A2A for development** - Simpler and faster
2. **Use MCP for production** - Better scalability
3. **Always log A2A messages** - Essential for debugging
4. **Handle connection failures** - Implement retry logic
5. **Monitor message queue** - Prevent memory issues

## Future Enhancements

- [ ] Message persistence (save to database)
- [ ] Message replay for debugging
- [ ] Agent health monitoring
- [ ] Load balancing across multiple agents
- [ ] Message encryption for security
- [ ] Agent discovery service
- [ ] Distributed tracing
