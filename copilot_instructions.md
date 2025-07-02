# 🍯 Pookie B News Daily - GitHub Copilot Instructions

## Project Overview

This is a Hacker News scraper and analytics platform enhanced with **Model Context Protocol (MCP) servers** for advanced AI capabilities. The project integrates DynamoDB for data storage, real-time scraping, and AI-powered insights.

## MCP Server Architecture

### Available MCP Servers

1. **DynamoDB MCP Server** (`mcp_servers/dynamodb_server.py`)
   - Database operations and analytics
   - Article trending analysis
   - User activity insights
   - Daily summaries

2. **Scraper MCP Server** (`mcp_servers/scraper_server.py`)
   - Web scraping operations
   - Content analysis
   - Trending topic detection
   - Article summarization

3. **MCP Client Manager** (`api/mcp_client.py`)
   - Manages MCP server connections
   - Provides fallback functionality
   - Handles async operations

## Key File Structure

```
/Users/kle/Downloads/HNscrapper/
├── mcp_servers/
│   ├── dynamodb_server.py       # DynamoDB MCP server
│   ├── scraper_server.py        # Scraper MCP server
│   ├── test_client.py           # MCP testing client
│   ├── requirements.txt         # MCP dependencies
│   └── claude_desktop_config.json # Claude config
├── api/
│   ├── index.py                 # Main Flask app with MCP integration
│   ├── mcp_client.py            # MCP client manager
│   └── templates/index.html     # Enhanced template with MCP features
├── dynamodb_manager.py          # DynamoDB operations
└── MCP_INTEGRATION_GUIDE.md     # Detailed MCP documentation
```

## How to Leverage MCP Servers

### 1. Direct Claude Integration

The MCP servers are configured to work directly with Claude Desktop. Use these commands:

#### DynamoDB Analytics Commands:
```
Use get_trending_articles to show me the top 15 trending HN articles with momentum scores.

Use analyze_article_trends to analyze voting patterns over the last 7 days.

Use get_domain_insights to show me which domains are performing best on HN.

Use find_similar_articles for article ID 12345 to find related content.

Use get_user_activity_insights for username "pg" to analyze their posting patterns.

Use get_daily_summary to generate today's comprehensive HN summary.
```

#### Scraper & Analysis Commands:
```
Use scrape_hn_frontpage to get the latest 30 articles from HN frontpage.

Use scrape_hn_best to get the top 20 articles from HN /best page.

Use analyze_article_content for URL https://example.com/article to get readability metrics.

Use get_trending_topics to show current trending topics from the last 24 hours.

Use generate_article_summary for article ID 12345 with summary_type "technical".
```

### 2. Flask App Integration

The web app (`/mcp` route) demonstrates MCP integration:

```python
# Example: Get trending articles via MCP
trending_data = await mcp_client.call_dynamodb_tool(
    "get_trending_articles", 
    {"limit": 15}
)

# Example: Get AI insights
topics_data = await mcp_client.call_scraper_tool(
    "get_trending_topics", 
    {"hours": 24}
)
```

### 3. Testing MCP Servers

```bash
# Test all MCP servers
cd /Users/kle/Downloads/HNscrapper
python mcp_servers/test_client.py

# Test specific server
python mcp_servers/dynamodb_server.py
python mcp_servers/scraper_server.py
```

## Development Workflows

### Adding New MCP Tools

1. **For DynamoDB operations:**
   - Add tool definition to `dynamodb_server.py` in `list_tools()`
   - Implement handler function
   - Add to `call_tool()` dispatcher
   - Test with `test_client.py`

2. **For Scraping operations:**
   - Add tool definition to `scraper_server.py`
   - Implement async handler
   - Add fallback logic in `mcp_client.py`
   - Test integration

### Extending Analytics

When adding new analytics features, consider:

```python
# Example: New trending analysis tool
Tool(
    name="analyze_domain_trends",
    description="Analyze trending patterns by domain over time",
    inputSchema={
        "type": "object",
        "properties": {
            "domain": {"type": "string", "description": "Domain to analyze"},
            "days": {"type": "integer", "description": "Days to analyze", "default": 30},
            "include_competitors": {"type": "boolean", "default": True}
        }
    }
)
```

## Common MCP Use Cases

### 1. Content Discovery
```
# Find trending content
Use get_trending_articles with limit 20 to find hot discussions.

# Discover similar content
Use find_similar_articles for the top article to find related discussions.
```

### 2. Market Analysis
```
# Domain analysis
Use get_domain_insights to see which tech companies are trending.

# Topic trends
Use get_trending_topics to identify emerging technologies.
```

### 3. Content Creation
```
# Daily summaries
Use get_daily_summary to create content for newsletters or podcasts.

# Article analysis
Use analyze_article_content to get insights for content curation.
```

### 4. User Research
```
# Influencer analysis
Use get_user_activity_insights for "sama" to analyze Sam Altman's HN activity.

# Community patterns
Use analyze_article_trends to understand community engagement patterns.
```

## Advanced MCP Patterns

### 1. Chained Analysis
```
1. Use get_trending_articles to find hot topics
2. Use find_similar_articles for each to build topic clusters
3. Use analyze_article_content to get readability scores
4. Use get_daily_summary to create comprehensive analysis
```

### 2. Real-time Monitoring
```
1. Use scrape_hn_frontpage every hour
2. Use get_trending_topics to track emerging themes
3. Use analyze_article_trends to spot pattern changes
4. Generate alerts for significant shifts
```

### 3. Content Optimization
```
1. Use get_domain_insights to find successful content patterns
2. Use analyze_article_content to understand what works
3. Use get_user_activity_insights for successful submitters
4. Apply insights to content strategy
```

## Environment Setup

### Python Environment
```bash
cd /Users/kle/Downloads/HNscrapper
source venv/bin/activate
pip install -r mcp_servers/requirements.txt
```

### AWS Configuration (for DynamoDB)
```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-west-2"
```

### Claude Desktop Configuration
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "pookie-b-dynamodb": {
      "command": "/Users/kle/Downloads/HNscrapper/venv/bin/python",
      "args": ["/Users/kle/Downloads/HNscrapper/mcp_servers/dynamodb_server.py"],
      "env": {
        "PYTHONPATH": "/Users/kle/Downloads/HNscrapper"
      }
    },
    "pookie-b-scraper": {
      "command": "/Users/kle/Downloads/HNscrapper/venv/bin/python",
      "args": ["/Users/kle/Downloads/HNscrapper/mcp_servers/scraper_server.py"],
      "env": {
        "PYTHONPATH": "/Users/kle/Downloads/HNscrapper"
      }
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **MCP Server Not Starting**
   - Check Python virtual environment
   - Verify dependencies installed
   - Check file paths in configuration

2. **DynamoDB Connection Failed**
   - Verify AWS credentials
   - Check network connectivity
   - Confirm table permissions

3. **Tool Not Found**
   - Check tool name spelling
   - Verify server registration
   - Test with `test_client.py`

### Debug Commands
```bash
# Test MCP client
python -c "from api.mcp_client import mcp_client; import asyncio; asyncio.run(mcp_client.call_dynamodb_tool('get_trending_articles', {'limit': 5}))"

# Test server directly
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | python mcp_servers/dynamodb_server.py

# Check Flask integration
python -c "from api.index import app; print([rule.rule for rule in app.url_map.iter_rules()])"
```

## Best Practices

### 1. Error Handling
- Always include fallback logic
- Handle async exceptions properly
- Provide meaningful error messages

### 2. Performance
- Use appropriate limits for data queries
- Cache frequently accessed data
- Implement timeout handling

### 3. Security
- Validate all input parameters
- Use environment variables for secrets
- Implement rate limiting for public endpoints

### 4. Monitoring
- Log MCP server interactions
- Track tool usage patterns
- Monitor server health and performance

## Future Enhancements

### Planned MCP Tools
1. **AI Summary Generator** - GPT-powered article summaries
2. **Sentiment Analyzer** - Comment sentiment analysis
3. **Topic Modeler** - Advanced topic clustering
4. **Prediction Engine** - Article success prediction
5. **Real-time Alerts** - Custom notification system

### Integration Opportunities
1. **Slack Bot** - MCP-powered HN updates
2. **Email Newsletters** - Automated content curation
3. **Mobile App** - Real-time insights
4. **Dashboard** - Executive analytics view
5. **API Gateway** - External MCP access

---

## Quick Reference

### Essential MCP Commands for Daily Use:
```
# Morning briefing
Use get_daily_summary to get today's HN overview

# Trend discovery
Use get_trending_articles with limit 10 to see what's hot

# Topic research
Use get_trending_topics to identify emerging themes

# Content analysis
Use scrape_hn_frontpage to get fresh content for analysis

# Deep dive
Use find_similar_articles to explore related discussions
```

This MCP setup transforms your HN scraper into a powerful AI-enhanced analytics platform! 🚀
