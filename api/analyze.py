#!/usr/bin/env python3
"""
AI Analysis function for Vercel.
Handles OpenAI-powered comment and article analysis.
"""

import json
import os
from datetime import datetime
from typing import List, Dict

def handler(request):
    """Vercel function handler for AI analysis."""
    
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        # Check if OpenAI is configured
        if not os.environ.get('OPENAI_API_KEY'):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'OpenAI API key not configured'})
            }
        
        # Parse request body
        try:
            data = json.loads(request.body.decode('utf-8'))
        except:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid JSON body'})
            }
        
        analysis_type = data.get('type', 'comment')
        content = data.get('content', '')
        
        if not content:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Content is required'})
            }
        
        # Perform analysis
        if analysis_type == 'comment':
            result = analyze_comment(content)
        elif analysis_type == 'article':
            result = analyze_article(content)
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid analysis type'})
            }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': True,
                'analysis': result,
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def analyze_comment(comment_text: str) -> Dict:
    """Analyze a comment using OpenAI."""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        prompt = f"""
        Analyze this Hacker News comment and provide:
        1. Quality score (1-10)
        2. Sentiment (positive/negative/neutral)
        3. Key insights (brief summary)
        4. Whether it adds value to the discussion
        
        Comment: "{comment_text[:500]}..."
        
        Please respond in JSON format:
        {{
            "quality_score": <1-10>,
            "sentiment": "<positive/negative/neutral>",
            "insights": "<brief summary>",
            "adds_value": <true/false>,
            "reasoning": "<brief explanation>"
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing online discussions and comments for quality and insights."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )
        
        # Parse the JSON response
        analysis_text = response.choices[0].message.content
        
        try:
            analysis = json.loads(analysis_text)
        except:
            # Fallback if JSON parsing fails
            analysis = {
                "quality_score": 5,
                "sentiment": "neutral",
                "insights": "Analysis completed",
                "adds_value": True,
                "reasoning": "AI analysis completed"
            }
        
        return analysis
        
    except Exception as e:
        return {
            "quality_score": 5,
            "sentiment": "neutral",
            "insights": f"Error in analysis: {str(e)}",
            "adds_value": False,
            "reasoning": "Analysis failed"
        }

def analyze_article(article_content: str) -> Dict:
    """Analyze an article using OpenAI."""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        prompt = f"""
        Analyze this article and provide:
        1. Summary (2-3 sentences)
        2. Key insights
        3. Discussion potential (1-10)
        4. Main themes
        
        Article content: "{article_content[:1000]}..."
        
        Please respond in JSON format:
        {{
            "summary": "<2-3 sentence summary>",
            "key_insights": "<main insights>",
            "discussion_potential": <1-10>,
            "main_themes": ["<theme1>", "<theme2>", "<theme3>"],
            "sentiment": "<positive/negative/neutral>"
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing articles and predicting discussion quality."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.3
        )
        
        # Parse the JSON response
        analysis_text = response.choices[0].message.content
        
        try:
            analysis = json.loads(analysis_text)
        except:
            # Fallback if JSON parsing fails
            analysis = {
                "summary": "Article analysis completed",
                "key_insights": "Analysis processed",
                "discussion_potential": 5,
                "main_themes": ["technology", "discussion"],
                "sentiment": "neutral"
            }
        
        return analysis
        
    except Exception as e:
        return {
            "summary": f"Error in analysis: {str(e)}",
            "key_insights": "Analysis failed",
            "discussion_potential": 1,
            "main_themes": ["error"],
            "sentiment": "neutral"
        }

# For local testing
if __name__ == "__main__":
    class MockRequest:
        def __init__(self):
            self.method = 'POST'
            self.body = json.dumps({
                'type': 'comment',
                'content': 'This is a test comment for analysis.'
            }).encode('utf-8')
    
    result = handler(MockRequest())
    print(json.dumps(result, indent=2))
