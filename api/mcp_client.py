#!/usr/bin/env python3
"""
MCP Client Manager for Pookie B News Daily
Manages connections to MCP servers from the Flask app.
"""

import asyncio
import json
import sys
import os
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️ MCP not available - using fallback mode")

class MCPClientManager:
    """Manages MCP server connections for the Flask app."""
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.python_path = f"{self.base_path}/venv/bin/python"
        self.mcp_available = MCP_AVAILABLE
        
    async def call_dynamodb_tool(self, tool_name: str, args: Dict = None) -> Dict:
        """Call a tool on the DynamoDB MCP server."""
        if not self.mcp_available:
            return await self._fallback_dynamodb_call(tool_name, args)
            
        try:
            server_params = StdioServerParameters(
                command=self.python_path,
                args=[f"{self.base_path}/mcp_servers/dynamodb_server.py"],
                env={"PYTHONPATH": self.base_path}
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, args or {})
                    return json.loads(result.content[0].text)
                    
        except Exception as e:
            print(f"MCP DynamoDB error: {e}")
            return await self._fallback_dynamodb_call(tool_name, args)
    
    async def call_scraper_tool(self, tool_name: str, args: Dict = None) -> Dict:
        """Call a tool on the Scraper MCP server."""
        if not self.mcp_available:
            return await self._fallback_scraper_call(tool_name, args)
            
        try:
            server_params = StdioServerParameters(
                command=self.python_path,
                args=[f"{self.base_path}/mcp_servers/scraper_server.py"],
                env={"PYTHONPATH": self.base_path}
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, args or {})
                    return json.loads(result.content[0].text)
                    
        except Exception as e:
            print(f"MCP Scraper error: {e}")
            return await self._fallback_scraper_call(tool_name, args)
    
    async def _fallback_dynamodb_call(self, tool_name: str, args: Dict) -> Dict:
        """Fallback to direct database calls when MCP is unavailable."""
        try:
            from dynamodb_manager import DynamoDBManager
            db = DynamoDBManager()
            
            if tool_name == "get_trending_articles":
                limit = args.get("limit", 10) if args else 10
                articles = db.get_best_articles(limit=limit)
                return {
                    "trending_articles": articles,
                    "total_analyzed": len(articles),
                    "generated_at": datetime.now().isoformat()
                }
            elif tool_name == "get_daily_summary":
                best_articles = db.get_best_articles(10)
                todays_articles = db.get_todays_articles(20)
                return {
                    "summary": {
                        "total_articles_today": len(todays_articles),
                        "avg_score_today": sum(a.get('score', 0) for a in todays_articles) / max(len(todays_articles), 1),
                        "top_article": max(todays_articles, key=lambda x: x.get('score', 0)) if todays_articles else None
                    },
                    "best_articles": best_articles,
                    "todays_highlights": todays_articles[:5],
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {"error": f"Fallback database call failed: {str(e)}"}
        
        return {"error": f"Unknown tool: {tool_name}"}
    
    async def _fallback_scraper_call(self, tool_name: str, args: Dict) -> Dict:
        """Fallback scraper calls when MCP is unavailable."""
        try:
            if tool_name == "get_trending_topics":
                return {
                    "trending_topics": [
                        {"topic": "AI", "mentions": 25, "trend_score": 0.85},
                        {"topic": "Python", "mentions": 18, "trend_score": 0.72},
                        {"topic": "JavaScript", "mentions": 15, "trend_score": 0.68},
                        {"topic": "Machine Learning", "mentions": 12, "trend_score": 0.65}
                    ],
                    "generated_at": datetime.now().isoformat(),
                    "note": "Fallback trending data"
                }
                
        except Exception as e:
            return {"error": f"Fallback scraper call failed: {str(e)}"}
        
        return {"error": f"Unknown scraper tool: {tool_name}"}

# Global instance for Flask app
mcp_client = MCPClientManager()
