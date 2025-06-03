#!/usr/bin/env python3
"""
Smart Enhancement Script - Quality over Quantity
Focuses on key discussions, improved summaries, and thematic analysis.
"""

import json
import logging
import sqlite3
import time
from datetime import datetime
from typing import Dict, List, Optional
import requests
from urllib.parse import quote_plus, urlparse
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/kevin/Downloads/HNscrapper/logs/smart_enhancement.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SmartDiscussionEnhancer:
    """Smart enhancement focusing on quality discussions and insights."""
    
    def __init__(self, db_path='/Users/kevin/Downloads/HNscrapper/data/enhanced_hn_articles.db'):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.setup_enhanced_schema()
    
    def setup_enhanced_schema(self):
        """Create enhanced schema for quality-focused data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Key discussions table - only the most important discussions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS key_discussions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_hn_id TEXT NOT NULL,
                source TEXT NOT NULL,  -- 'hackernews', 'reddit', 'twitter'
                discussion_title TEXT,
                key_points TEXT,  -- JSON array of main points
                participant_count INTEGER,
                quality_score REAL,
                insight_level TEXT,  -- 'high', 'medium', 'low'
                controversy_level TEXT,  -- 'high', 'medium', 'low', 'none'
                discussion_summary TEXT,
                top_comments TEXT,  -- JSON array of best 3-5 comments
                themes TEXT,  -- JSON array of discussion themes
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Enhanced article insights
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS article_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_hn_id TEXT NOT NULL UNIQUE,
                main_summary TEXT,
                key_themes TEXT,  -- JSON array
                expert_opinions TEXT,  -- JSON array of expert insights
                controversy_analysis TEXT,
                community_sentiment TEXT,  -- 'positive', 'negative', 'mixed', 'neutral'
                practical_implications TEXT,
                follow_up_questions TEXT,  -- JSON array
                credibility_assessment TEXT,
                discussion_quality_score REAL,
                total_engagement_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Curated comments - only the best ones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS curated_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_hn_id TEXT NOT NULL,
                source TEXT NOT NULL,
                author TEXT,
                comment_text TEXT,
                insight_type TEXT,  -- 'expert', 'practical', 'critical', 'informative'
                quality_score REAL,
                upvotes INTEGER DEFAULT 0,
                engagement_metrics TEXT,  -- JSON
                why_selected TEXT,  -- Reason for curation
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Smart enhancement schema created successfully")
    
    def extract_key_hn_comments(self, hn_id, limit=10):
        """Extract only the highest quality HN comments."""
        try:
            url = f"https://hacker-news.firebaseio.com/v0/item/{hn_id}.json"
            response = self.session.get(url)
            
            if response.status_code != 200:
                return []
            
            article_data = response.json()
            if not article_data or 'kids' not in article_data:
                return []
            
            comments = []
            
            def fetch_comment_tree(comment_id, depth=0, max_depth=3):
                if depth > max_depth:
                    return
                
                try:
                    comment_url = f"https://hacker-news.firebaseio.com/v0/item/{comment_id}.json"
                    comment_response = self.session.get(comment_url)
                    
                    if comment_response.status_code == 200:
                        comment_data = comment_response.json()
                        
                        if comment_data and 'text' in comment_data and 'deleted' not in comment_data:
                            comment_text = comment_data['text']
                            
                            # Quality filters
                            if (len(comment_text) > 100 and  # Substantial length
                                len(comment_text) < 2000 and  # Not too long
                                not comment_text.lower().startswith(('lol', 'haha', '+1', 'this.', 'agreed')) and  # Not low-effort
                                '.' in comment_text):  # Contains complete sentences
                                
                                quality_score = self.calculate_comment_quality(comment_text)
                                
                                if quality_score > 0.6:  # Only high-quality comments
                                    comments.append({
                                        'id': comment_data['id'],
                                        'author': comment_data.get('by', 'unknown'),
                                        'text': comment_text,
                                        'score': comment_data.get('score', 0),
                                        'time': comment_data.get('time', 0),
                                        'depth': depth,
                                        'quality_score': quality_score
                                    })
                            
                            # Recursively fetch replies (but limit depth)
                            if 'kids' in comment_data and depth < 2:
                                for kid_id in comment_data['kids'][:3]:  # Only top 3 replies
                                    fetch_comment_tree(kid_id, depth + 1, max_depth)
                    
                    time.sleep(0.1)  # Rate limiting
                except Exception as e:
                    logger.warning(f"Error fetching comment {comment_id}: {e}")
            
            # Process top-level comments
            for comment_id in article_data['kids'][:20]:  # Only check top 20 comments
                fetch_comment_tree(comment_id)
            
            # Sort by quality score and return top comments
            comments.sort(key=lambda x: x['quality_score'], reverse=True)
            return comments[:limit]
            
        except Exception as e:
            logger.error(f"Error extracting HN comments for {hn_id}: {e}")
            return []
    
    def calculate_comment_quality(self, text):
        """Calculate quality score for a comment based on various factors."""
        score = 0.5  # Base score
        
        # Length factor (sweet spot: 200-800 chars)
        length = len(text)
        if 200 <= length <= 800:
            score += 0.2
        elif 100 <= length < 200 or 800 < length <= 1200:
            score += 0.1
        
        # Content quality indicators
        quality_indicators = [
            r'\b(however|therefore|furthermore|moreover|additionally)\b',  # Logical connectors
            r'\b(experience|implementation|production|solution)\b',  # Practical terms
            r'\b(research|study|analysis|data|evidence)\b',  # Research terms
            r'\b(consider|suggest|recommend|alternative)\b',  # Constructive language
            r'[?].*[?]',  # Thoughtful questions
            r'\b(I think|In my opinion|From my experience)\b',  # Personal insight
        ]
        
        for pattern in quality_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.05
        
        # Negative indicators
        negative_indicators = [
            r'\b(wtf|lol|lmao|rofl)\b',  # Internet slang
            r'^(This\.|Same\.|Agreed\.|Exactly\.)',  # Low-effort responses
            r'[!]{3,}',  # Excessive exclamation
            r'[A-Z]{10,}',  # Excessive caps
        ]
        
        for pattern in negative_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                score -= 0.1
        
        return max(0, min(1, score))
    
    def find_reddit_discussions(self, title, url, limit=3):
        """Find relevant Reddit discussions with quality filtering."""
        try:
            discussions = []
            
            # Search Reddit for the article
            search_query = quote_plus(title[:100])  # Limit query length
            reddit_url = f"https://www.reddit.com/search.json?q={search_query}&type=link&limit=10"
            
            response = self.session.get(reddit_url)
            if response.status_code == 200:
                data = response.json()
                
                for post in data.get('data', {}).get('children', []):
                    post_data = post['data']
                    
                    # Quality filters for Reddit posts
                    if (post_data.get('score', 0) > 5 and  # Minimum score
                        post_data.get('num_comments', 0) > 3 and  # Has discussion
                        not post_data.get('over_18', False)):  # SFW content
                        
                        discussions.append({
                            'url': f"https://www.reddit.com{post_data['permalink']}",
                            'subreddit': post_data['subreddit'],
                            'title': post_data['title'],
                            'score': post_data['score'],
                            'comments': post_data['num_comments'],
                            'post_id': post_data['id']
                        })
            
            # Sort by engagement and return top discussions
            discussions.sort(key=lambda x: x['score'] + x['comments'], reverse=True)
            return discussions[:limit]
            
        except Exception as e:
            logger.error(f"Error finding Reddit discussions: {e}")
            return []
    
    def extract_reddit_insights(self, post_id, limit=5):
        """Extract key insights from Reddit discussion."""
        try:
            reddit_json_url = f"https://www.reddit.com/comments/{post_id}.json"
            response = self.session.get(reddit_json_url)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            insights = []
            
            def process_comment(comment_data, depth=0):
                if depth > 2 or not isinstance(comment_data, dict):
                    return
                
                comment_info = comment_data.get('data', {})
                body = comment_info.get('body', '')
                
                if (body and body != '[deleted]' and 
                    len(body) > 50 and 
                    comment_info.get('score', 0) > 2):  # Quality threshold
                    
                    quality_score = self.calculate_comment_quality(body)
                    if quality_score > 0.6:
                        insights.append({
                            'author': comment_info.get('author', 'unknown'),
                            'text': body,
                            'score': comment_info.get('score', 0),
                            'quality_score': quality_score
                        })
                
                # Process replies
                replies = comment_info.get('replies', {})
                if isinstance(replies, dict) and 'data' in replies:
                    for reply in replies['data'].get('children', [])[:3]:
                        process_comment(reply, depth + 1)
            
            # Process top-level comments
            if len(data) > 1 and 'data' in data[1]:
                for comment in data[1]['data'].get('children', [])[:10]:
                    process_comment(comment)
            
            # Sort by quality and return best insights
            insights.sort(key=lambda x: x['quality_score'] * x['score'], reverse=True)
            return insights[:limit]
            
        except Exception as e:
            logger.error(f"Error extracting Reddit insights: {e}")
            return []
    
    def analyze_discussion_themes(self, comments):
        """Analyze themes from collected comments."""
        all_text = ' '.join([c['text'] for c in comments])
        
        # Simple theme extraction based on keywords
        themes = []
        
        theme_patterns = {
            'Technical Implementation': r'\b(code|implementation|architecture|design|technical|engineering)\b',
            'Business Impact': r'\b(business|revenue|profit|market|competition|strategy)\b',
            'User Experience': r'\b(user|experience|interface|usability|design|UX|UI)\b',
            'Performance': r'\b(performance|speed|latency|optimization|scale|scaling)\b',
            'Security': r'\b(security|privacy|vulnerability|encryption|attack)\b',
            'Cost/Economics': r'\b(cost|price|expensive|cheap|budget|economics)\b',
            'Future Trends': r'\b(future|trend|prediction|evolution|next|upcoming)\b',
            'Criticism/Concerns': r'\b(concern|problem|issue|flaw|criticism|downside)\b'
        }
        
        for theme, pattern in theme_patterns.items():
            if re.search(pattern, all_text, re.IGNORECASE):
                # Count occurrences for relevance scoring
                matches = len(re.findall(pattern, all_text, re.IGNORECASE))
                if matches >= 2:  # Theme must appear multiple times
                    themes.append({
                        'theme': theme,
                        'relevance_score': min(matches / 10, 1.0)
                    })
        
        return sorted(themes, key=lambda x: x['relevance_score'], reverse=True)
    
    def generate_enhanced_summary(self, title, url, hn_comments, reddit_discussions):
        """Generate an enhanced summary with key insights."""
        try:
            # Collect key points from comments
            key_points = []
            expert_opinions = []
            
            # Analyze HN comments
            for comment in hn_comments[:5]:
                if len(comment['text']) > 150:
                    # Extract first sentence or key insight
                    sentences = comment['text'].split('. ')
                    key_insight = sentences[0][:200] + '...' if len(sentences[0]) > 200 else sentences[0]
                    
                    if comment['quality_score'] > 0.8:
                        expert_opinions.append({
                            'author': comment['author'],
                            'insight': key_insight,
                            'source': 'hackernews'
                        })
                    else:
                        key_points.append(key_insight)
            
            # Analyze Reddit discussions
            for discussion in reddit_discussions:
                key_points.append(f"Reddit discussion in r/{discussion['subreddit']} with {discussion['comments']} comments")
            
            # Generate themes
            all_comments = hn_comments + [{'text': d.get('title', '')} for d in reddit_discussions]
            themes = self.analyze_discussion_themes(all_comments)
            
            # Determine sentiment
            positive_words = ['great', 'excellent', 'good', 'helpful', 'useful', 'interesting']
            negative_words = ['bad', 'terrible', 'awful', 'useless', 'boring', 'problematic']
            
            all_text = ' '.join([c['text'] for c in hn_comments]).lower()
            positive_count = sum(1 for word in positive_words if word in all_text)
            negative_count = sum(1 for word in negative_words if word in all_text)
            
            if positive_count > negative_count * 1.5:
                sentiment = 'positive'
            elif negative_count > positive_count * 1.5:
                sentiment = 'negative'
            else:
                sentiment = 'mixed'
            
            return {
                'main_summary': f"Article discussion analysis: {len(hn_comments)} quality HN comments, {len(reddit_discussions)} Reddit discussions",
                'key_themes': [t['theme'] for t in themes[:5]],
                'expert_opinions': expert_opinions[:3],
                'community_sentiment': sentiment,
                'discussion_quality_score': sum(c['quality_score'] for c in hn_comments) / len(hn_comments) if hn_comments else 0,
                'total_engagement_score': len(hn_comments) + sum(d['comments'] for d in reddit_discussions)
            }
            
        except Exception as e:
            logger.error(f"Error generating enhanced summary: {e}")
            return None
    
    def enhance_article_smart(self, hn_id, title, url):
        """Smart enhancement of a single article."""
        logger.info(f"Smart enhancing article {hn_id}: {title}")
        
        try:
            # 1. Extract high-quality HN comments
            hn_comments = self.extract_key_hn_comments(hn_id, limit=10)
            logger.info(f"Found {len(hn_comments)} quality HN comments")
            
            # 2. Find relevant Reddit discussions
            reddit_discussions = self.find_reddit_discussions(title, url, limit=3)
            logger.info(f"Found {len(reddit_discussions)} Reddit discussions")
            
            # 3. Extract Reddit insights
            reddit_insights = []
            for discussion in reddit_discussions:
                insights = self.extract_reddit_insights(discussion['post_id'], limit=3)
                reddit_insights.extend(insights)
                time.sleep(1)  # Rate limiting
            
            logger.info(f"Extracted {len(reddit_insights)} Reddit insights")
            
            # 4. Generate enhanced summary
            summary = self.generate_enhanced_summary(title, url, hn_comments, reddit_discussions)
            
            # 5. Store results in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # Store article insights
                if summary:
                    cursor.execute('''
                        INSERT OR REPLACE INTO article_insights (
                            article_hn_id, main_summary, key_themes, expert_opinions,
                            community_sentiment, discussion_quality_score, total_engagement_score
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (hn_id, summary['main_summary'], 
                         json.dumps(summary['key_themes']),
                         json.dumps(summary['expert_opinions']),
                         summary['community_sentiment'],
                         summary['discussion_quality_score'],
                         summary['total_engagement_score']))
                
                # Store curated HN comments
                for comment in hn_comments[:5]:  # Only store top 5
                    cursor.execute('''
                        INSERT INTO curated_comments (
                            article_hn_id, source, author, comment_text,
                            insight_type, quality_score, upvotes, why_selected
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (hn_id, 'hackernews', comment['author'], comment['text'],
                         'expert' if comment['quality_score'] > 0.8 else 'informative',
                         comment['quality_score'], comment.get('score', 0),
                         f"Quality score: {comment['quality_score']:.2f}"))
                
                # Store curated Reddit insights
                for insight in reddit_insights[:3]:  # Only store top 3
                    cursor.execute('''
                        INSERT INTO curated_comments (
                            article_hn_id, source, author, comment_text,
                            insight_type, quality_score, upvotes, why_selected
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (hn_id, 'reddit', insight['author'], insight['text'],
                         'expert' if insight['quality_score'] > 0.8 else 'informative',
                         insight['quality_score'], insight.get('score', 0),
                         f"Quality score: {insight['quality_score']:.2f}"))
                
                # Store key discussions summary
                themes = self.analyze_discussion_themes(hn_comments + reddit_insights)
                cursor.execute('''
                    INSERT INTO key_discussions (
                        article_hn_id, source, discussion_title, key_points,
                        participant_count, quality_score, themes, discussion_summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (hn_id, 'combined', title,
                     json.dumps([summary['main_summary']] if summary else []),
                     len(hn_comments) + len(reddit_insights),
                     summary['discussion_quality_score'] if summary else 0,
                     json.dumps([t['theme'] for t in themes[:5]]),
                     f"Enhanced discussion with {len(hn_comments)} HN comments and {len(reddit_discussions)} Reddit threads"))
                
                conn.commit()
                logger.info(f"Successfully enhanced article {hn_id}")
                
            except Exception as e:
                logger.error(f"Database error for article {hn_id}: {e}")
                conn.rollback()
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error in smart enhancement of article {hn_id}: {e}")
    
    def enhance_remaining_articles(self, limit=None):
        """Enhance all remaining articles with smart approach."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get articles that haven't been smart-enhanced yet
        query = """
            SELECT hn_id, title, url 
            FROM article_analyses 
            WHERE hn_id NOT IN (SELECT DISTINCT article_hn_id FROM article_insights)
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        articles = cursor.fetchall()
        conn.close()
        
        logger.info(f"Starting smart enhancement of {len(articles)} articles")
        
        for i, (hn_id, title, url) in enumerate(articles, 1):
            logger.info(f"Processing article {i}/{len(articles)}: {hn_id}")
            self.enhance_article_smart(hn_id, title, url)
            
            # Progress updates with longer pauses for API rate limiting
            if i % 3 == 0:
                logger.info(f"Completed {i}/{len(articles)} articles - taking a break...")
                time.sleep(10)  # Longer pause every 3 articles
            else:
                time.sleep(5)  # Short pause between articles

def main():
    """Main function to run smart enhancement."""
    print("🚀 Starting Smart Discussion Enhancement - ALL ARTICLES")
    print("============================================================")
    print("🎯 Focus: Quality over quantity")
    print("   • High-quality comments only")
    print("   • Enhanced summaries with themes")
    print("   • Key insights and expert opinions")
    print("   • Community sentiment analysis")
    print("============================================================")
    
    enhancer = SmartDiscussionEnhancer()
    
    # Process all remaining articles
    print("🔍 Processing ALL remaining articles with smart enhancement...")
    enhancer.enhance_remaining_articles(limit=None)  # Process all articles
    
    print("\n✅ Smart enhancement complete! Check the new tables:")
    print("  • article_insights - Enhanced summaries with themes")
    print("  • curated_comments - Only high-quality comments")
    print("  • key_discussions - Discussion summaries and themes")

if __name__ == "__main__":
    main()