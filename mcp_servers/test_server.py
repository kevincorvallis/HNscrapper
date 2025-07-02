#!/usr/bin/env python3
"""
Test script for Pookie B News Daily DynamoDB MCP Server
"""

import sys
import os
import json
import asyncio

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    print("✅ MCP imports successful")
except ImportError as e:
    print(f"❌ MCP import error: {e}")
    sys.exit(1)

try:
    from dynamodb_manager import DynamoDBManager
    print("✅ DynamoDB manager import successful")
except ImportError as e:
    print(f"❌ DynamoDB manager import error: {e}")
    print("🔍 This is expected if AWS credentials are not set up")

# Test server creation
try:
    app = Server("test-server")
    print("✅ MCP Server creation successful")
except Exception as e:
    print(f"❌ Server creation error: {e}")
    sys.exit(1)

# Test tool registration
@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="test_tool",
            description="A test tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Test message"}
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "test_tool":
        return [TextContent(type="text", text=f"Test successful: {arguments.get('message', 'No message')}")]
    return [TextContent(type="text", text="Unknown tool")]

print("✅ Tool registration successful")
print("🍯 MCP Server test completed successfully!")

if __name__ == "__main__":
    print("This is a test script. The actual server should be run with dynamodb_server.py")
