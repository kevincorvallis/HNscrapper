#!/usr/bin/env python3
"""
Test client for Pookie B News Daily MCP Servers
"""

import asyncio
import json
import sys
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_dynamodb_server():
    """Test the DynamoDB MCP server."""
    print("🍯 Testing DynamoDB MCP Server...")
    
    # Server parameters
    server_params = StdioServerParameters(
        command="/Users/kle/Downloads/HNscrapper/venv/bin/python",
        args=["/Users/kle/Downloads/HNscrapper/mcp_servers/dynamodb_server.py"],
        env={"PYTHONPATH": "/Users/kle/Downloads/HNscrapper"}
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize
                await session.initialize()
                print("✅ Server initialized successfully")
                
                # List tools
                tools = await session.list_tools()
                print(f"✅ Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # Test a simple tool call
                print("\n🔍 Testing get_daily_summary tool...")
                result = await session.call_tool(
                    "get_daily_summary",
                    {"date": "today"}
                )
                print("✅ Tool call successful:")
                print(json.dumps(json.loads(result.content[0].text), indent=2)[:500] + "...")
                
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        import traceback
        traceback.print_exc()

async def test_scraper_server():
    """Test the Scraper MCP server."""
    print("\n🍯 Testing Scraper MCP Server...")
    
    # Server parameters
    server_params = StdioServerParameters(
        command="/Users/kle/Downloads/HNscrapper/venv/bin/python",
        args=["/Users/kle/Downloads/HNscrapper/mcp_servers/scraper_server.py"],
        env={"PYTHONPATH": "/Users/kle/Downloads/HNscrapper"}
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize
                await session.initialize()
                print("✅ Server initialized successfully")
                
                # List tools
                tools = await session.list_tools()
                print(f"✅ Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # Test a simple tool call
                print("\n🔍 Testing get_trending_topics tool...")
                result = await session.call_tool(
                    "get_trending_topics",
                    {"hours": 24}
                )
                print("✅ Tool call successful:")
                print(json.dumps(json.loads(result.content[0].text), indent=2))
                
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests."""
    print("🍯 Starting Pookie B News Daily MCP Server Tests\n")
    
    await test_dynamodb_server()
    await test_scraper_server()
    
    print("\n🍯 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
