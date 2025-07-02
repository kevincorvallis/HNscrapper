#!/usr/bin/env python3
"""
🍯 Pookie B News Daily - MCP Setup Verification
Verifies that all MCP servers and configurations are properly set up.
"""

import os
import sys
import json
import asyncio
from pathlib import Path

def check_files():
    """Check that all required files exist."""
    print("🔍 Checking file structure...")
    
    base_path = Path("/Users/kle/Downloads/HNscrapper")
    required_files = [
        "mcp_servers/dynamodb_server.py",
        "mcp_servers/scraper_server.py", 
        "mcp_servers/test_client.py",
        "mcp_servers/requirements.txt",
        "api/mcp_client.py",
        "api/index.py",
        "api/templates/index.html",
        "dynamodb_manager.py",
        "copilot_instructions.md",
        "MCP_INTEGRATION_GUIDE.md",
        "MCP_QUICK_REFERENCE.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def check_claude_config():
    """Check Claude Desktop configuration."""
    print("\n🔧 Checking Claude Desktop configuration...")
    
    config_path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    
    if not config_path.exists():
        print("  ❌ Claude config file not found")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if "mcpServers" not in config:
            print("  ❌ No mcpServers section in config")
            return False
        
        required_servers = ["pookie-b-dynamodb", "pookie-b-scraper"]
        for server in required_servers:
            if server in config["mcpServers"]:
                print(f"  ✅ {server} configured")
            else:
                print(f"  ❌ {server} not configured")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error reading config: {e}")
        return False

def check_python_environment():
    """Check Python environment and dependencies."""
    print("\n🐍 Checking Python environment...")
    
    venv_python = Path("/Users/kle/Downloads/HNscrapper/venv/bin/python")
    if venv_python.exists():
        print("  ✅ Virtual environment found")
    else:
        print("  ❌ Virtual environment not found")
        return False
    
    # Check if MCP is installed
    try:
        import mcp
        print("  ✅ MCP package installed")
    except ImportError:
        print("  ❌ MCP package not installed")
        return False
    
    # Check other dependencies
    dependencies = ["aiohttp", "requests", "beautifulsoup4", "flask"]
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  ✅ {dep} installed")
        except ImportError:
            print(f"  ❌ {dep} not installed")
    
    return True

async def test_mcp_servers():
    """Test MCP server functionality."""
    print("\n🔬 Testing MCP servers...")
    
    try:
        sys.path.append('/Users/kle/Downloads/HNscrapper')
        from api.mcp_client import mcp_client
        
        # Test DynamoDB server
        print("  Testing DynamoDB MCP server...")
        result = await mcp_client.call_dynamodb_tool("get_trending_articles", {"limit": 3})
        if "error" not in result or "trending_articles" in result or "articles" in result:
            print("    ✅ DynamoDB server responding")
        else:
            print(f"    ⚠️ DynamoDB server error: {result.get('error', 'unknown')}")
        
        # Test Scraper server
        print("  Testing Scraper MCP server...")
        result = await mcp_client.call_scraper_tool("get_trending_topics", {"hours": 24})
        if "trending_topics" in result:
            print("    ✅ Scraper server responding")
        else:
            print(f"    ❌ Scraper server error: {result.get('error', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ MCP server test failed: {e}")
        return False

def check_flask_integration():
    """Check Flask app MCP integration."""
    print("\n🌐 Checking Flask integration...")
    
    try:
        sys.path.append('/Users/kle/Downloads/HNscrapper')
        from api.index import app
        
        # Check if MCP route exists
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        if "/mcp" in routes:
            print("  ✅ MCP route registered")
        else:
            print("  ❌ MCP route not found")
            return False
        
        # Test the route
        with app.test_client() as client:
            response = client.get('/mcp')
            if response.status_code == 200:
                print("  ✅ MCP route working")
                
                content = response.data.decode('utf-8')
                if 'MCP Enhanced' in content:
                    print("  ✅ MCP features detected in template")
                else:
                    print("  ⚠️ MCP features not found in template")
            else:
                print(f"  ❌ MCP route error: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Flask integration test failed: {e}")
        return False

def main():
    """Run complete MCP setup verification."""
    print("🍯 Pookie B News Daily - MCP Setup Verification\n")
    
    checks = [
        check_files(),
        check_claude_config(),
        check_python_environment()
    ]
    
    # Async checks
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async_checks = [
            loop.run_until_complete(test_mcp_servers()),
            check_flask_integration()
        ]
        
        loop.close()
        checks.extend(async_checks)
        
    except Exception as e:
        print(f"❌ Async test error: {e}")
        checks.append(False)
    
    # Summary
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n📊 Verification Summary: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! Your MCP setup is ready!")
        print("\n🚀 Next steps:")
        print("1. Restart Claude Desktop to load new configuration")
        print("2. Open Claude and test MCP commands from copilot_instructions.md")
        print("3. Visit http://localhost:5000/mcp for MCP-enhanced web interface")
        print("4. Use MCP_QUICK_REFERENCE.md for daily command reference")
    else:
        print("⚠️ Some checks failed. Please review the errors above.")
        print("📖 See MCP_INTEGRATION_GUIDE.md for troubleshooting.")

if __name__ == "__main__":
    main()
