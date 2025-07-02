#!/usr/bin/env python3
"""
Simple test server for MCP integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template
from datetime import datetime
import asyncio

# Import MCP client
try:
    from api.mcp_client import mcp_client
    MCP_AVAILABLE = True
    print("✅ MCP client imported")
except ImportError as e:
    MCP_AVAILABLE = False
    print(f"❌ MCP client not available: {e}")

app = Flask(__name__, template_folder='../api/templates')

@app.route('/')
def home():
    """Standard homepage."""
    return render_template('index.html',
        current_date=datetime.now().strftime('%B %d, %Y'),
        current_time=datetime.now().strftime('%I:%M %p'),
        best_articles=[],
        todays_articles=[],
        daily_insights=["🏠 Standard homepage - visit /mcp for enhanced features"],
        mcp_enabled=False
    )

@app.route('/mcp')
def mcp_enhanced():
    """MCP-enhanced homepage."""
    current_date = datetime.now().strftime('%B %d, %Y')
    current_time = datetime.now().strftime('%I:%M %p')
    
    best_articles = []
    todays_articles = []
    daily_insights = []
    trending_topics = []
    mcp_status = "Testing Mode"
    
    if MCP_AVAILABLE:
        try:
            # Test MCP integration
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Test trending topics
                topics_data = loop.run_until_complete(
                    mcp_client.call_scraper_tool("get_trending_topics", {"hours": 24})
                )
                
                if "trending_topics" in topics_data:
                    trending_topics = topics_data["trending_topics"]
                    mcp_status = "Active"
                
                # Generate sample insights
                daily_insights = [
                    "🤖 MCP servers successfully connected!",
                    f"🔥 Found {len(trending_topics)} trending topics",
                    "📊 AI analysis pipeline working",
                    "🍯 Pookie B News enhanced with MCP!"
                ]
                
                # Generate sample articles for demo
                best_articles = [
                    {
                        'title': 'MCP Integration Successfully Deployed',
                        'url': 'https://example.com',
                        'score': 150,
                        'num_comments': 45,
                        'author': 'pookie_b',
                        'domain': 'pookieb.news'
                    },
                    {
                        'title': 'AI-Powered News Analysis Now Live',
                        'url': 'https://example.com',
                        'score': 120,
                        'num_comments': 32,
                        'author': 'ai_news',
                        'domain': 'ai.com'
                    }
                ]
                
            finally:
                loop.close()
                
        except Exception as e:
            print(f"MCP error: {e}")
            mcp_status = f"Error: {str(e)}"
            daily_insights = [f"❌ MCP Error: {str(e)}"]
    else:
        mcp_status = "Not Available"
        daily_insights = ["⚠️ MCP not available - install dependencies"]
    
    return render_template('index.html',
        current_date=current_date,
        current_time=current_time,
        best_articles=best_articles,
        todays_articles=todays_articles,
        daily_insights=daily_insights,
        trending_topics=trending_topics,
        mcp_status=mcp_status,
        mcp_enabled=True
    )

@app.route('/health')
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mcp_available": MCP_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == '__main__':
    print("🍯 Starting Pookie B News MCP Test Server...")
    print("Routes:")
    print("  / - Standard homepage")
    print("  /mcp - MCP-enhanced homepage")
    print("  /health - Health check")
    app.run(debug=True, port=5001)
