#!/usr/bin/env python3
"""
🍯 Pookie B News Daily - DynamoDB MCP Server
Provides enhanced database operations for the HN scraper via MCP protocol.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from dynamodb_manager import DynamoDBManager

# Initialize the MCP server
app = Server("pookie-b-dynamodb-server")

# Initialize DynamoDB manager
try:
    db_manager = DynamoDBManager()
    print("✅ DynamoDB MCP Server initialized successfully", file=sys.stderr)
except Exception as e:
    print(f"❌ Failed to initialize DynamoDB: {e}", file=sys.stderr)
    db_manager = None

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools for the DynamoDB MCP server."""
    return [
        Tool(
            name="get_trending_articles",
            description="Get articles with highest vote momentum and engagement",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of articles to return", "default": 10},
                    "hours": {"type": "integer", "description": "Time window in hours for trending calculation", "default": 24}
                }
            }
        ),
        Tool(
            name="analyze_article_trends",
            description="Analyze voting and engagement trends over time",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Number of days to analyze", "default": 7},
                    "category": {"type": "string", "description": "Optional category filter", "default": "all"}
                }
            }
        ),
        Tool(
            name="get_domain_insights",
            description="Get insights about top domains and their performance",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of domains to analyze", "default": 20}
                }
            }
        ),
        Tool(
            name="find_similar_articles",
            description="Find articles similar to a given article based on content and metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "article_id": {"type": "string", "description": "HN article ID"},
                    "limit": {"type": "integer", "description": "Number of similar articles to return", "default": 5}
                }
            }
        ),
        Tool(
            name="get_user_activity_insights",
            description="Analyze user posting and commenting patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "HN username"},
                    "days": {"type": "integer", "description": "Days of history to analyze", "default": 30}
                }
            }
        ),
        Tool(
            name="get_daily_summary",
            description="Generate a comprehensive daily summary for Pookie B News",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format", "default": "today"}
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for the DynamoDB MCP server."""
    
    if not db_manager:
        return [TextContent(
            type="text",
            text=json.dumps({"error": "DynamoDB not available"})
        )]
    
    try:
        if name == "get_trending_articles":
            result = await get_trending_articles(arguments)
        elif name == "analyze_article_trends":
            result = await analyze_article_trends(arguments)
        elif name == "get_domain_insights":
            result = await get_domain_insights(arguments)
        elif name == "find_similar_articles":
            result = await find_similar_articles(arguments)
        elif name == "get_user_activity_insights":
            result = await get_user_activity_insights(arguments)
        elif name == "get_daily_summary":
            result = await get_daily_summary(arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}
            
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)})
        )]

async def get_trending_articles(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get articles with highest vote momentum."""
    limit = args.get("limit", 10)
    hours = args.get("hours", 24)
    
    # Get recent articles
    recent_articles = db_manager.get_articles(limit=limit*3, sort_by="recent")
    
    # Calculate momentum (simplified - in production you'd track vote changes over time)
    trending = []
    for article in recent_articles:
        score = article.get('score', 0)
        comments = article.get('num_comments', 0)
        
        # Simple momentum calculation based on score/comments ratio and recency
        scraped_at = article.get('scraped_at', '')
        if scraped_at:
            try:
                scraped_time = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
                hours_ago = (datetime.now() - scraped_time.replace(tzinfo=None)).total_seconds() / 3600
                
                # Boost recent articles
                time_factor = max(0.1, 1 - (hours_ago / 24))
                momentum = (score + comments * 2) * time_factor
                
                article['momentum_score'] = round(momentum, 2)
                article['hours_ago'] = round(hours_ago, 1)
                trending.append(article)
            except:
                continue
    
    # Sort by momentum and return top articles
    trending.sort(key=lambda x: x.get('momentum_score', 0), reverse=True)
    
    return {
        "trending_articles": trending[:limit],
        "total_analyzed": len(recent_articles),
        "time_window_hours": hours,
        "generated_at": datetime.now().isoformat()
    }

async def analyze_article_trends(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze voting and engagement trends."""
    days = args.get("days", 7)
    category = args.get("category", "all")
    
    # Get articles from the past N days
    all_articles = db_manager.get_articles(limit=1000, sort_by="recent")
    
    # Filter by date range
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_articles = []
    
    for article in all_articles:
        scraped_at = article.get('scraped_at', '')
        if scraped_at:
            try:
                article_date = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
                if article_date.replace(tzinfo=None) >= cutoff_date:
                    recent_articles.append(article)
            except:
                continue
    
    # Analyze trends
    total_articles = len(recent_articles)
    total_score = sum(a.get('score', 0) for a in recent_articles)
    total_comments = sum(a.get('num_comments', 0) for a in recent_articles)
    
    # Domain analysis
    domain_stats = {}
    for article in recent_articles:
        domain = article.get('domain', 'unknown')
        if domain not in domain_stats:
            domain_stats[domain] = {'count': 0, 'total_score': 0, 'total_comments': 0}
        domain_stats[domain]['count'] += 1
        domain_stats[domain]['total_score'] += article.get('score', 0)
        domain_stats[domain]['total_comments'] += article.get('num_comments', 0)
    
    # Top domains
    top_domains = sorted(domain_stats.items(), key=lambda x: x[1]['total_score'], reverse=True)[:10]
    
    return {
        "analysis_period_days": days,
        "total_articles": total_articles,
        "average_score": round(total_score / max(total_articles, 1), 1),
        "average_comments": round(total_comments / max(total_articles, 1), 1),
        "top_domains": [
            {
                "domain": domain,
                "articles": stats['count'],
                "avg_score": round(stats['total_score'] / stats['count'], 1),
                "avg_comments": round(stats['total_comments'] / stats['count'], 1)
            }
            for domain, stats in top_domains
        ],
        "generated_at": datetime.now().isoformat()
    }

async def get_domain_insights(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get insights about top domains."""
    limit = args.get("limit", 20)
    
    # Get domain statistics
    stats = db_manager.get_stats()
    domains = stats.get('domains', [])
    
    domain_insights = []
    for domain_info in domains[:limit]:
        domain = domain_info.get('domain', '')
        count = domain_info.get('count', 0)
        
        # Get articles from this domain
        all_articles = db_manager.get_articles(limit=500)
        domain_articles = [a for a in all_articles if a.get('domain') == domain]
        
        if domain_articles:
            scores = [a.get('score', 0) for a in domain_articles]
            comments = [a.get('num_comments', 0) for a in domain_articles]
            
            domain_insights.append({
                "domain": domain,
                "total_articles": count,
                "avg_score": round(sum(scores) / len(scores), 1),
                "max_score": max(scores),
                "avg_comments": round(sum(comments) / len(comments), 1),
                "engagement_ratio": round(sum(comments) / max(sum(scores), 1), 2)
            })
    
    return {
        "domain_insights": domain_insights,
        "total_domains_analyzed": len(domain_insights),
        "generated_at": datetime.now().isoformat()
    }

async def find_similar_articles(args: Dict[str, Any]) -> Dict[str, Any]:
    """Find similar articles based on content and metrics."""
    article_id = args.get("article_id", "")
    limit = args.get("limit", 5)
    
    if not article_id:
        return {"error": "article_id is required"}
    
    # Get the target article
    target_article = db_manager.get_article(article_id)
    if not target_article:
        return {"error": f"Article {article_id} not found"}
    
    # Get all articles and find similar ones
    all_articles = db_manager.get_articles(limit=500)
    similar_articles = []
    
    target_score = target_article.get('score', 0)
    target_comments = target_article.get('num_comments', 0)
    target_domain = target_article.get('domain', '')
    target_title = target_article.get('title', '').lower()
    
    for article in all_articles:
        if article.get('hn_id') == article_id:
            continue
            
        # Calculate similarity score
        score_diff = abs(article.get('score', 0) - target_score)
        comment_diff = abs(article.get('num_comments', 0) - target_comments)
        
        # Domain bonus
        domain_bonus = 1.5 if article.get('domain') == target_domain else 1.0
        
        # Title similarity (basic keyword matching)
        article_title = article.get('title', '').lower()
        common_words = set(target_title.split()) & set(article_title.split())
        title_similarity = len(common_words) / max(len(target_title.split()), 1)
        
        # Overall similarity score (lower is better for score/comment diff, higher for title)
        similarity = (domain_bonus + title_similarity * 2) / (1 + score_diff/100 + comment_diff/10)
        
        similar_articles.append({
            **article,
            'similarity_score': round(similarity, 3)
        })
    
    # Sort by similarity and return top results
    similar_articles.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    return {
        "target_article": target_article,
        "similar_articles": similar_articles[:limit],
        "total_analyzed": len(all_articles),
        "generated_at": datetime.now().isoformat()
    }

async def get_user_activity_insights(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze user posting and commenting patterns."""
    username = args.get("username", "")
    days = args.get("days", 30)
    
    if not username:
        return {"error": "username is required"}
    
    # Get articles and comments by this user
    all_articles = db_manager.get_articles(limit=1000)
    user_articles = [a for a in all_articles if a.get('author') == username]
    
    # Get user comments (if available in your comment storage)
    user_comments = []  # This would need comment data from your system
    
    if not user_articles:
        return {"error": f"No articles found for user {username}"}
    
    # Analyze posting patterns
    scores = [a.get('score', 0) for a in user_articles]
    comments = [a.get('num_comments', 0) for a in user_articles]
    domains = [a.get('domain', '') for a in user_articles]
    
    # Domain frequency
    domain_freq = {}
    for domain in domains:
        domain_freq[domain] = domain_freq.get(domain, 0) + 1
    
    top_domains = sorted(domain_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "username": username,
        "analysis_period_days": days,
        "total_articles": len(user_articles),
        "avg_score": round(sum(scores) / len(scores), 1),
        "max_score": max(scores),
        "avg_comments_per_article": round(sum(comments) / len(comments), 1),
        "top_domains": [{"domain": d, "count": c} for d, c in top_domains],
        "recent_articles": user_articles[:5],
        "generated_at": datetime.now().isoformat()
    }

async def get_daily_summary(args: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a comprehensive daily summary."""
    date_str = args.get("date", "today")
    
    if date_str == "today":
        target_date = datetime.now().strftime('%Y-%m-%d')
    else:
        target_date = date_str
    
    # Get today's articles
    todays_articles = db_manager.get_todays_articles(50)
    best_articles = db_manager.get_best_articles(10)
    
    # Calculate daily metrics
    if todays_articles:
        daily_scores = [a.get('score', 0) for a in todays_articles]
        daily_comments = [a.get('num_comments', 0) for a in todays_articles]
        
        top_article = max(todays_articles, key=lambda x: x.get('score', 0))
        most_discussed = max(todays_articles, key=lambda x: x.get('num_comments', 0))
    else:
        daily_scores = [0]
        daily_comments = [0]
        top_article = None
        most_discussed = None
    
    return {
        "date": target_date,
        "summary": {
            "total_articles_today": len(todays_articles),
            "avg_score_today": round(sum(daily_scores) / max(len(daily_scores), 1), 1),
            "total_comments_today": sum(daily_comments),
            "top_article": top_article,
            "most_discussed": most_discussed
        },
        "best_articles": best_articles[:5],
        "todays_highlights": todays_articles[:5],
        "generated_at": datetime.now().isoformat()
    }

async def main():
    """Run the DynamoDB MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    print("🍯 Starting Pookie B News Daily - DynamoDB MCP Server", file=sys.stderr)
    asyncio.run(main())
