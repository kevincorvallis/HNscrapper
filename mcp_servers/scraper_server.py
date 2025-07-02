#!/usr/bin/env python3
"""
🍯 Pookie B News Daily - Scraper MCP Server
Provides HN scraping and analysis operations via MCP protocol.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Initialize the MCP server
app = Server("pookie-b-scraper-server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools for the Scraper MCP server."""
    return [
        Tool(
            name="scrape_hn_frontpage",
            description="Scrape the current HN frontpage for fresh articles",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of articles to scrape", "default": 30}
                }
            }
        ),
        Tool(
            name="scrape_hn_best",
            description="Scrape the HN /best page for top articles",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of articles to scrape", "default": 30}
                }
            }
        ),
        Tool(
            name="analyze_article_content",
            description="Extract and analyze article content from a URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Article URL to analyze"},
                    "include_readability": {"type": "boolean", "description": "Include readability metrics", "default": True}
                }
            }
        ),
        Tool(
            name="generate_article_summary",
            description="Generate AI-powered summary of an article",
            inputSchema={
                "type": "object",
                "properties": {
                    "article_id": {"type": "string", "description": "HN article ID"},
                    "summary_type": {"type": "string", "description": "Type of summary: 'brief', 'detailed', 'technical'", "default": "brief"}
                }
            }
        ),
        Tool(
            name="get_trending_topics",
            description="Analyze current trending topics from recent articles",
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {"type": "integer", "description": "Hours to look back for trending analysis", "default": 24}
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for the Scraper MCP server."""
    
    try:
        if name == "scrape_hn_frontpage":
            result = await scrape_hn_frontpage(arguments)
        elif name == "scrape_hn_best":
            result = await scrape_hn_best(arguments)
        elif name == "analyze_article_content":
            result = await analyze_article_content(arguments)
        elif name == "generate_article_summary":
            result = await generate_article_summary(arguments)
        elif name == "get_trending_topics":
            result = await get_trending_topics(arguments)
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

async def scrape_hn_frontpage(args: Dict[str, Any]) -> Dict[str, Any]:
    """Scrape HN frontpage using the existing scraper."""
    limit = args.get("limit", 30)
    
    try:
        # Import and use the existing scraper
        from api.scrape import scrape_hn_articles
        
        articles = scrape_hn_articles(limit)
        
        return {
            "source": "hn_frontpage",
            "articles_scraped": len(articles),
            "limit_requested": limit,
            "articles": articles,
            "scraped_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to scrape frontpage: {str(e)}"}

async def scrape_hn_best(args: Dict[str, Any]) -> Dict[str, Any]:
    """Scrape HN /best page."""
    limit = args.get("limit", 30)
    
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Scrape the /best page
        response = requests.get("https://news.ycombinator.com/best", headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # Parse articles from /best page
        rows = soup.find_all('tr', class_='athing')[:limit]
        
        for row in rows:
            try:
                title_elem = row.find('span', class_='titleline')
                if not title_elem:
                    continue
                    
                link_elem = title_elem.find('a')
                title = link_elem.text.strip() if link_elem else "No title"
                url = link_elem.get('href', '') if link_elem else ""
                
                # Get article ID
                article_id = row.get('id', '')
                
                # Get score and comments from next row
                next_row = row.find_next_sibling('tr')
                score = 0
                comments = 0
                author = ""
                
                if next_row:
                    score_elem = next_row.find('span', class_='score')
                    score = int(score_elem.text.split()[0]) if score_elem else 0
                    
                    author_elem = next_row.find('a', class_='hnuser')
                    author = author_elem.text if author_elem else ""
                    
                    comment_link = next_row.find('a', href=lambda x: x and 'item?id=' in x)
                    if comment_link and 'comment' in comment_link.text:
                        try:
                            comments = int(comment_link.text.split()[0])
                        except:
                            comments = 0
                
                articles.append({
                    'hn_id': article_id,
                    'title': title,
                    'url': url,
                    'score': score,
                    'author': author,
                    'num_comments': comments,
                    'scraped_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"Error parsing article: {e}")
                continue
        
        return {
            "source": "hn_best",
            "articles_scraped": len(articles),
            "limit_requested": limit,
            "articles": articles,
            "scraped_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Failed to scrape /best page: {str(e)}"}

async def analyze_article_content(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze article content from URL."""
    url = args.get("url", "")
    include_readability = args.get("include_readability", True)
    
    if not url:
        return {"error": "URL is required"}
    
    try:
        import requests
        from bs4 import BeautifulSoup
        import textstat
        
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract text content
        for script in soup(["script", "style"]):
            script.extract()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Basic analysis
        word_count = len(text.split())
        char_count = len(text)
        
        result = {
            "url": url,
            "word_count": word_count,
            "character_count": char_count,
            "estimated_read_time": max(1, word_count // 200),  # ~200 WPM
            "content_preview": text[:500] + "..." if len(text) > 500 else text
        }
        
        # Add readability metrics if requested
        if include_readability and text:
            try:
                result["readability"] = {
                    "flesch_score": textstat.flesch_reading_ease(text),
                    "grade_level": textstat.flesch_kincaid_grade(text),
                    "reading_level": textstat.text_standard(text, float_output=False)
                }
            except Exception as e:
                result["readability_error"] = str(e)
        
        return result
        
    except Exception as e:
        return {"error": f"Failed to analyze article: {str(e)}"}

async def generate_article_summary(args: Dict[str, Any]) -> Dict[str, Any]:
    """Generate AI summary of an article."""
    article_id = args.get("article_id", "")
    summary_type = args.get("summary_type", "brief")
    
    # This would integrate with your AI service (OpenAI, Anthropic, etc.)
    # For now, return a placeholder
    return {
        "article_id": article_id,
        "summary_type": summary_type,
        "summary": "AI summary generation not yet implemented. This would use OpenAI/Anthropic API to generate summaries.",
        "generated_at": datetime.now().isoformat(),
        "status": "placeholder"
    }

async def get_trending_topics(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze trending topics from recent articles."""
    hours = args.get("hours", 24)
    
    try:
        # This would analyze recent articles for trending keywords/topics
        # For now, return a placeholder with some example data
        return {
            "time_window_hours": hours,
            "trending_topics": [
                {"topic": "AI", "mentions": 25, "trend_score": 0.85},
                {"topic": "Python", "mentions": 18, "trend_score": 0.72},
                {"topic": "JavaScript", "mentions": 15, "trend_score": 0.68},
                {"topic": "Machine Learning", "mentions": 12, "trend_score": 0.65},
                {"topic": "Startup", "mentions": 10, "trend_score": 0.58}
            ],
            "analysis_note": "Trending topic analysis not fully implemented yet",
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to analyze trending topics: {str(e)}"}

async def main():
    """Run the Scraper MCP server.""" 
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    print("🍯 Starting Pookie B News Daily - Scraper MCP Server", file=sys.stderr)
    asyncio.run(main())
