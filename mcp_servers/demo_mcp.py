#!/usr/bin/env python3
"""
🍯 Quick MCP Demo - Show How to Use MCP Servers
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.mcp_client import mcp_client

async def demo_mcp_capabilities():
    """Demonstrate MCP server capabilities."""
    print("🍯 Pookie B News Daily - MCP Server Demo\n")
    
    # Test 1: Get trending topics
    print("1️⃣ Getting trending topics...")
    topics_result = await mcp_client.call_scraper_tool("get_trending_topics", {"hours": 24})
    
    if "trending_topics" in topics_result:
        print(f"   ✅ Found {len(topics_result['trending_topics'])} trending topics:")
        for topic in topics_result["trending_topics"][:3]:
            print(f"   📈 {topic['topic']}: {topic['mentions']} mentions ({int(topic['trend_score']*100)}% trend)")
    else:
        print(f"   ❌ Error: {topics_result.get('error', 'Unknown error')}")
    
    print()
    
    # Test 2: Get daily summary (will use fallback data since no DynamoDB)
    print("2️⃣ Getting daily summary...")
    summary_result = await mcp_client.call_dynamodb_tool("get_daily_summary", {"date": "today"})
    
    if "summary" in summary_result:
        summary = summary_result["summary"]
        print(f"   ✅ Daily Summary:")
        print(f"   📊 Total articles today: {summary.get('total_articles_today', 0)}")
        print(f"   ⭐ Average score: {summary.get('avg_score_today', 0)}")
        if summary.get("top_article"):
            print(f"   🏆 Top article: {summary['top_article'].get('title', 'Unknown')[:50]}...")
    else:
        print(f"   ⚠️ Using fallback mode: {summary_result.get('error', 'Unknown')}")
    
    print()
    
    # Test 3: Analyze article content (example URL)
    print("3️⃣ Analyzing article content...")
    content_result = await mcp_client.call_scraper_tool("analyze_article_content", {
        "url": "https://news.ycombinator.com",
        "include_readability": True
    })
    
    if "word_count" in content_result:
        print(f"   ✅ Content analysis:")
        print(f"   📝 Word count: {content_result['word_count']}")
        print(f"   📖 Estimated read time: {content_result['estimated_read_time']} minutes")
        if "readability" in content_result:
            print(f"   📊 Reading level: {content_result['readability'].get('reading_level', 'Unknown')}")
    else:
        print(f"   ❌ Content analysis error: {content_result.get('error', 'Unknown')}")
    
    print()
    
    # Test 4: Get trending articles (will use fallback)
    print("4️⃣ Getting trending articles...")
    trending_result = await mcp_client.call_dynamodb_tool("get_trending_articles", {"limit": 3})
    
    if "trending_articles" in trending_result or "articles" in trending_result:
        articles = trending_result.get("trending_articles", trending_result.get("articles", []))
        print(f"   ✅ Found {len(articles)} trending articles:")
        for i, article in enumerate(articles[:3], 1):
            title = article.get("title", "No title")
            score = article.get("score", 0)
            print(f"   {i}. {title[:50]}... (Score: {score})")
    else:
        print(f"   ⚠️ Using fallback mode: {trending_result.get('error', 'No articles')}")
    
    print()
    print("🎉 MCP Demo Complete!")
    print("\n📋 What you can do with these MCP servers:")
    print("   • Use from Claude Desktop with the configured tools")
    print("   • Integrate into your Flask web app")
    print("   • Build automated analysis workflows")
    print("   • Create custom AI-powered insights")
    
    print("\n🚀 Next steps:")
    print("   1. Restart Claude Desktop to load the MCP configuration")
    print("   2. Try these commands in Claude:")
    print("      - 'Use get_trending_topics to show me current trends'")
    print("      - 'Use analyze_article_content for URL: https://example.com'")
    print("      - 'Use get_daily_summary to create today's briefing'")

if __name__ == "__main__":
    asyncio.run(demo_mcp_capabilities())
