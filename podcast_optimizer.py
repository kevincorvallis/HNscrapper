#!/usr/bin/env python3
"""
Podcast-Optimized Comment Storage and Processing
Designed for AI podcast generation with cost optimization
"""

from dynamodb_manager import DynamoDBManager
from dotenv import load_dotenv
import json
import openai
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from collections import defaultdict

load_dotenv()

class PodcastOptimizedCommentProcessor:
    """Optimized comment processor for podcast generation."""
    
    def __init__(self):
        self.db = DynamoDBManager()
        
        # OpenAI client with proper initialization
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            try:
                self.openai_client = openai.OpenAI(api_key=openai_api_key)
                self.has_openai = True
                print("✅ OpenAI client initialized")
            except Exception as e:
                print(f"⚠️  OpenAI initialization failed: {e}")
                self.has_openai = False
        else:
            print("⚠️  No OpenAI API key found, using mock responses")
            self.has_openai = False
        
        # Podcast-specific optimization settings
        self.min_comment_score = 3  # Only store comments with 3+ upvotes
        self.max_comments_per_article = 20  # Reduced from 100 for podcast quality
        self.min_discussion_thread_length = 3  # At least 3 replies for "discussion"
        self.max_thread_depth = 5  # Deeper threads for better discussions
        
        print("🎙️ Initialized podcast-optimized comment processor")
        print(f"   Min comment score: {self.min_comment_score}")
        print(f"   Max comments per article: {self.max_comments_per_article}")
        print(f"   Min discussion thread: {self.min_discussion_thread_length}")
    
    def should_store_comment_for_podcast(self, comment_data: Dict, level: int) -> bool:
        """Determine if comment is worth storing for podcast generation."""
        # Must have good score (engagement indicator)
        if comment_data.get('score', 0) < self.min_comment_score:
            return False
        
        # Skip deleted/dead comments
        if comment_data.get('deleted') or comment_data.get('dead'):
            return False
        
        # Content quality checks
        content = comment_data.get('text', '')
        if len(content) < 50:  # Increased from 10 - need substantial comments
            return False
        
        # Skip pure links or very short responses
        if content.count('http') > 2 or len(content.split()) < 10:
            return False
        
        return True
    
    def extract_discussion_threads(self, article_id: str) -> List[Dict]:
        """Extract discussion threads optimized for podcast narrative."""
        comments = self.db.get_article_comments(article_id)
        
        # Group by thread (parent-child relationships)
        threads = defaultdict(list)
        comment_lookup = {c['comment_id']: c for c in comments}
        
        for comment in comments:
            if comment['level'] == 0:  # Top-level comment
                thread_id = comment['comment_id']
                threads[thread_id].append(comment)
                
                # Find replies
                replies = [c for c in comments if c['parent_id'] == comment['comment_id']]
                replies.sort(key=lambda x: x.get('score', 0), reverse=True)
                threads[thread_id].extend(replies[:5])  # Top 5 replies
        
        # Filter for substantial discussions
        substantial_threads = []
        for thread_id, thread_comments in threads.items():
            if len(thread_comments) >= self.min_discussion_thread_length:
                # Calculate thread engagement score
                total_score = sum(c.get('score', 0) for c in thread_comments)
                thread_data = {
                    'thread_id': thread_id,
                    'comments': thread_comments,
                    'engagement_score': total_score,
                    'comment_count': len(thread_comments)
                }
                substantial_threads.append(thread_data)
        
        # Sort by engagement and return top threads
        substantial_threads.sort(key=lambda x: x['engagement_score'], reverse=True)
        return substantial_threads[:5]  # Top 5 discussions for podcast
    
    def generate_podcast_script(self, article: Dict, discussion_threads: List[Dict]) -> str:
        """Generate podcast script using OpenAI."""
        
        # Prepare context for AI
        article_title = article['title']
        article_url = article.get('url', 'news.ycombinator.com')
        article_score = article.get('score', 0)
        
        # Format discussion threads for AI
        discussions_text = ""
        for i, thread in enumerate(discussion_threads, 1):
            discussions_text += f"\n--- Discussion Thread {i} (Score: {thread['engagement_score']}) ---\n"
            for comment in thread['comments']:
                author = comment.get('author', 'unknown')
                content = comment.get('content', '')[:500]  # Limit for context
                score = comment.get('score', 0)
                level = comment.get('level', 0)
                indent = "  " * level
                discussions_text += f"{indent}• {author} (+{score}): {content}\n"
        
        # Podcast generation prompt
        prompt = f"""You are a podcast narrator summarizing a Hacker News discussion thread titled: "{article_title}".
Your task is to produce a monologue that sounds natural, engaging, and reflective—like a host recapping an online conversation for an audience.

ARTICLE CONTEXT:
- Title: {article_title}
- URL: {article_url}
- Upvotes: {article_score}
- Platform: Hacker News (tech-focused community)

DISCUSSION HIGHLIGHTS:
{discussions_text}

Include the following structure:
Hook/Intro – Introduce the post and its topic in 1–2 sentences.
Highlights – Retell key arguments, reactions, or insights using the phrasing of commenters when impactful, witty, or insightful.
Tone Shifts – Capture tone variety: technical debate, humor, personal anecdotes, skepticism, etc.
Contrasting Takes – Acknowledge when opinions diverge and represent both sides neutrally.
Reflective Close – Wrap up with a general observation or leave the listener with a thought to ponder.

Keep it under 500 words. Do not sanitize informal language unless necessary. Avoid over-polishing. Preserve the energy and technical insights of the thread.
Focus on the most engaging and insightful comments that would interest a tech-savvy audience."""

        try:
            if not self.has_openai:
                # Return a structured mock script for testing
                script = f"""Welcome to today's Hacker News digest. 

Today we're diving into "{article_title}", which sparked quite a discussion with {article_score} upvotes.

Let me walk you through the most interesting takes from the community...

{discussions_text[:300] if discussions_text else 'The discussion covered various technical and philosophical aspects of the topic.'}

The conversation really highlights the diverse perspectives in the tech community. Some users praised the innovative approach, while others questioned the practical implications.

This is exactly the kind of nuanced discussion that makes Hacker News such a valuable platform for tech professionals and enthusiasts.

What's your take on this? The full discussion continues on Hacker News."""
                
                return script
            
            # Real OpenAI integration
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use stable model
                messages=[
                    {"role": "system", "content": "You are an engaging podcast narrator specializing in tech discussions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Error generating podcast script: {e}")
            return None
    
    def save_podcast_episode(self, article_id: str, script: str, metadata: Dict) -> bool:
        """Save podcast episode to database."""
        try:
            episode_data = {
                'hn_id': article_id,
                'script': script,
                'title': metadata.get('title', ''),
                'generated_at': datetime.now().isoformat(),
                'episode_length': len(script.split()),
                'discussion_count': metadata.get('discussion_count', 0),
                'total_engagement': metadata.get('total_engagement', 0)
            }
            
            # We can reuse the analyses table for podcast episodes
            return self.db.insert_analysis({
                'hn_id': f"podcast_{article_id}",
                'title': f"Podcast: {metadata.get('title', '')}",
                'url': metadata.get('url', ''),
                'domain': 'podcast.generated',
                'summary': script,
                'generated_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ Error saving podcast episode: {e}")
            return False
    
    def generate_daily_podcast_episodes(self, days_back: int = 1) -> List[Dict]:
        """Generate podcast episodes for top articles from recent days."""
        print(f"🎙️ Generating podcast episodes for last {days_back} day(s)...")
        
        # Get recent high-engagement articles
        articles = self.db.get_articles(limit=20, sort_by='score')
        
        # Filter for articles with good engagement (score > 50)
        podcast_worthy_articles = [
            a for a in articles 
            if int(a.get('score', 0)) > 50 and int(a.get('num_comments', 0)) > 10
        ]
        
        episodes = []
        
        for i, article in enumerate(podcast_worthy_articles[:5]):  # Top 5 articles
            print(f"\n📰 Processing article {i+1}/5: {article['title'][:50]}...")
            
            # Extract discussion threads
            threads = self.extract_discussion_threads(article['hn_id'])
            
            if not threads:
                print("   ⏭️  No substantial discussions found, skipping")
                continue
            
            print(f"   💬 Found {len(threads)} discussion threads")
            
            # Generate podcast script
            script = self.generate_podcast_script(article, threads)
            
            if script:
                # Save episode
                metadata = {
                    'title': article['title'],
                    'url': article.get('url', ''),
                    'discussion_count': len(threads),
                    'total_engagement': sum(t['engagement_score'] for t in threads)
                }
                
                if self.save_podcast_episode(article['hn_id'], script, metadata):
                    episode = {
                        'article_id': article['hn_id'],
                        'title': article['title'],
                        'script': script,
                        'word_count': len(script.split()),
                        'discussion_threads': len(threads),
                        'engagement_score': metadata['total_engagement']
                    }
                    episodes.append(episode)
                    print(f"   ✅ Generated podcast episode ({len(script.split())} words)")
                else:
                    print("   ❌ Failed to save podcast episode")
            else:
                print("   ❌ Failed to generate script")
        
        print(f"\n🎉 Generated {len(episodes)} podcast episodes!")
        return episodes

def optimize_comment_storage_for_podcasts():
    """Analyze and optimize comment storage for podcast generation."""
    print("📊 OPTIMIZING COMMENT STORAGE FOR PODCASTS")
    print("=" * 60)
    
    db = DynamoDBManager()
    processor = PodcastOptimizedCommentProcessor()
    
    # Analyze current comment quality
    stats = db.get_stats()
    print(f"Current comments: {stats['total_comments']}")
    
    # Sample analysis of comment quality
    articles = db.get_articles(limit=5, sort_by='score')
    
    total_comments_analyzed = 0
    podcast_worthy_comments = 0
    
    for article in articles:
        comments = db.get_article_comments(article['hn_id'])
        total_comments_analyzed += len(comments)
        
        # Simulate quality check (we can't check score from stored comments)
        # In practice, you'd implement this during scraping
        for comment in comments:
            if len(comment.get('content', '')) > 50:  # Basic quality indicator
                podcast_worthy_comments += 1
    
    if total_comments_analyzed > 0:
        quality_ratio = podcast_worthy_comments / total_comments_analyzed
        print(f"Comment quality analysis:")
        print(f"  Total analyzed: {total_comments_analyzed}")
        print(f"  Podcast-worthy: {podcast_worthy_comments}")
        print(f"  Quality ratio: {quality_ratio:.2%}")
        
        # Storage savings calculation
        potential_savings = (1 - quality_ratio) * 100
        print(f"  Potential storage savings: {potential_savings:.1f}%")
    
    print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
    print(f"   • Store only comments with 3+ upvotes")
    print(f"   • Focus on discussion threads (3+ replies)")
    print(f"   • Limit to 20 high-quality comments per article")
    print(f"   • Expected storage reduction: ~70%")
    print(f"   • Expected cost reduction: ~70%")
    print(f"   • Improved podcast quality through curation")

if __name__ == "__main__":
    # Run optimization analysis
    optimize_comment_storage_for_podcasts()
    
    # Test podcast generation
    print(f"\n🧪 TESTING PODCAST GENERATION")
    print("=" * 40)
    
    processor = PodcastOptimizedCommentProcessor()
    episodes = processor.generate_daily_podcast_episodes(days_back=1)
    
    if episodes:
        print(f"\n📋 SAMPLE EPISODE:")
        sample = episodes[0]
        print(f"Title: {sample['title']}")
        print(f"Word count: {sample['word_count']}")
        print(f"Discussions: {sample['discussion_threads']}")
        print(f"Engagement: {sample['engagement_score']}")
        print(f"\nScript preview:")
        print(sample['script'][:200] + "...")
    else:
        print("No episodes generated (may need articles with more engagement)")
