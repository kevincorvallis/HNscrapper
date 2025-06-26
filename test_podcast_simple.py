#!/usr/bin/env python3
"""
Simple test for podcast generation without OpenAI dependency
"""

import os
from datetime import datetime, timedelta
from dynamodb_manager import DynamoDBManager
from tts_generator import TTSGenerator

def test_podcast_generation():
    """Test podcast generation with current data."""
    
    # Initialize components
    db = DynamoDBManager()
    
    print("🎙️ Testing Podcast Generation")
    print("=" * 40)
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"📅 Looking for articles from {today} and {yesterday}")
    
    # Get recent articles
    articles = db.get_articles(limit=20, sort_by='score')
    print(f"📰 Found {len(articles)} total articles")
    
    # Filter for high-quality articles
    quality_articles = []
    for article in articles:
        score = int(article.get('score', 0))
        comment_count = int(article.get('num_comments', 0))
        
        if score >= 50 and comment_count >= 10:
            quality_articles.append(article)
    
    print(f"✨ Found {len(quality_articles)} high-quality articles")
    
    if quality_articles:
        print("\n📊 Top Articles:")
        for i, article in enumerate(quality_articles[:5], 1):
            print(f"   {i}. {article.get('title', 'No title')[:60]}...")
            print(f"      Score: {article.get('score', 0)}, Comments: {article.get('num_comments', 0)}")
    
    # Generate a simple script
    script = generate_simple_script(quality_articles[:3])
    print(f"\n📝 Generated script ({len(script.split())} words)")
    
    # Test TTS
    try:
        tts = TTSGenerator()
        print("✅ TTS Generator ready")
        
        # For testing, use a short sample
        test_script = "Hello! This is a test of the Hacker News Daily podcast system. Today we're covering the most engaging tech discussions from the community."
        
        print("🎵 Generating test audio...")
        audio_path = tts.generate_speech(
            text=test_script,
            output_filename="test_podcast.mp3"
        )
        
        if audio_path:
            print(f"✅ Test audio generated: {audio_path}")
        else:
            print("❌ Audio generation failed")
            
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
    
    return quality_articles, script

def generate_simple_script(articles):
    """Generate a simple podcast script without OpenAI."""
    
    if not articles:
        return "Welcome to Hacker News Daily. Unfortunately, no qualifying stories are available today."
    
    script_parts = []
    
    # Intro
    script_parts.append(
        f"Welcome to Hacker News Daily, your briefing on today's most engaging tech stories. "
        f"I'm covering {len(articles)} fascinating discussions that caught the community's attention."
    )
    
    # Stories
    for i, article in enumerate(articles, 1):
        title = article.get('title', 'Unknown title')
        score = article.get('score', 0)
        comments = article.get('num_comments', 0)
        domain = article.get('domain', 'unknown source')
        
        story = f"""
        Story {i}: {title}
        
        This story from {domain} scored {score} points and generated {comments} comments. 
        The discussion shows strong community engagement, with readers sharing insights 
        and perspectives on this topic.
        """
        
        script_parts.append(story.strip())
    
    # Outro
    script_parts.append(
        f"That wraps up today's Hacker News Daily. These {len(articles)} stories represent "
        f"the best discussions from the tech community. Keep building, keep learning, "
        f"and we'll see you next time."
    )
    
    return "\n\n".join(script_parts)

if __name__ == "__main__":
    test_podcast_generation()
