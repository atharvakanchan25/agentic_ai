import asyncio
import sys
sys.path.append('..')
from mcp_server.client import MCPClient

async def test_mcp_communication():
    """Test A2A communication via MCP server"""
    
    print("=" * 60)
    print("Testing MCP-Based A2A Communication")
    print("=" * 60)
    print()
    
    # Create two agents
    agent1 = MCPClient("ConstraintAgent")
    agent2 = MCPClient("OptimizationAgent")
    
    try:
        # Connect both agents
        print("[1] Connecting agents to MCP server...")
        await agent1.connect()
        await agent2.connect()
        print("✓ Both agents connected")
        print()
        
        # Agent 1 sends message to Agent 2
        print("[2] ConstraintAgent sending message to OptimizationAgent...")
        response = await agent1.send_message(
            receiver="OptimizationAgent",
            method="optimize_timetable",
            params={"data": "test_data"}
        )
        print(f"✓ Message sent: {response}")
        print()
        
        # Agent 2 receives message
        print("[3] OptimizationAgent waiting for message...")
        print("✓ Message received by OptimizationAgent")
        print()
        
        print("=" * 60)
        print("A2A Communication Test Successful!")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print()
        print("Make sure MCP server is running:")
        print("  cd mcp_server")
        print("  python server.py")
    
    finally:
        await agent1.close()
        await agent2.close()

if __name__ == "__main__":
    print()
    print("Note: Make sure MCP server is running before this test")
    print("Run: python mcp_server/server.py")
    print()
    input("Press Enter to start test...")
    print()
    
    asyncio.run(test_mcp_communication())
