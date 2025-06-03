#!/usr/bin/env python3
"""
Pre-processor for generating and storing OpenAI analyses.
This runs once to generate all analyses and saves them to the database.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

# OpenAI client
from openai import OpenAI
openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY')) if os.environ.get('OPENAI_API_KEY') else None


class AnalysisPreprocessor:
    """Pre-processes articles and comments using OpenAI and stores results in database."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables for storing analyses."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for article summaries and key insights
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS article_analyses (
                hn_id TEXT PRIMARY KEY,
                title TEXT,
                url TEXT,
                domain TEXT,
                summary TEXT,
                key_insights TEXT,
                main_themes TEXT,
                sentiment_analysis TEXT,
                discussion_quality_score INTEGER,
                controversy_level TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for comment analyses and curation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comment_analyses (
                comment_id TEXT PRIMARY KEY,
                hn_id TEXT,
                parent_id TEXT,
                author TEXT,
                comment_text TEXT,
                analysis_summary TEXT,
                key_points TEXT,
                sentiment TEXT,
                quality_score INTEGER,
                is_insightful BOOLEAN,
                is_controversial BOOLEAN,
                thread_summary TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hn_id) REFERENCES article_analyses (hn_id)
            )
        ''')
        
        # Table for discussion threads and conversations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discussion_threads (
                thread_id TEXT PRIMARY KEY,
                hn_id TEXT,
                root_comment_id TEXT,
                thread_summary TEXT,
                main_debate_points TEXT,
                participant_count INTEGER,
                thread_quality_score INTEGER,
                is_featured_discussion BOOLEAN DEFAULT FALSE,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hn_id) REFERENCES article_analyses (hn_id)
            )
        ''')
        
        # Table for featured content recommendations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS featured_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hn_id TEXT,
                content_type TEXT, -- 'article', 'comment', 'thread'
                content_id TEXT,
                feature_reason TEXT,
                ranking_score REAL,
                is_active BOOLEAN DEFAULT TRUE,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hn_id) REFERENCES article_analyses (hn_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database tables initialized")
    
    def load_articles_data(self) -> List[Dict]:
        """Load articles from JSON file."""
        json_path = os.path.join(project_root, 'data', 'enhanced_hn_articles.json')
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                articles = json.load(f)
            print(f"✅ Loaded {len(articles)} articles from JSON")
            return articles
        except FileNotFoundError:
            print(f"❌ Articles file not found: {json_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error loading JSON: {e}")
            return []
    
    def analyze_article(self, article: Dict) -> Dict:
        """Generate comprehensive analysis for an article using OpenAI."""
        if not openai_client:
            return self._generate_fallback_analysis(article)
        
        try:
            # Prepare article content for analysis
            title = article.get('title', 'Unknown Title')
            content = (article.get('content') or '')[:3000]  # Limit content length, handle None
            url = article.get('url', '')
            comment_count = len(article.get('comments', []))
            
            # Count total comments recursively
            total_comments = self._count_comments_recursive(article.get('comments', []))
            
            # Get top-level comments for context
            top_comments = []
            for comment in article.get('comments', [])[:5]:
                if comment.get('text'):
                    top_comments.append({
                        'author': comment.get('by', 'Anonymous'),
                        'text': comment.get('text', '')[:500],
                        'replies': len(comment.get('replies', []))
                    })
            
            # Create analysis prompt
            prompt = f"""
            Analyze this Hacker News article and its discussion:
            
            Title: {title}
            URL: {url}
            Content: {content}
            Total Comments: {total_comments}
            
            Top Comments:
            {self._format_comments_for_prompt(top_comments)}
            
            Please provide a comprehensive analysis in JSON format with the following fields:
            1. summary: A 2-3 sentence summary of the article
            2. key_insights: 3-5 key insights from both article and comments
            3. main_themes: Main discussion themes (comma-separated)
            4. sentiment_analysis: Overall sentiment (positive/negative/mixed/neutral)
            5. discussion_quality_score: Score 1-10 for discussion quality
            6. controversy_level: low/medium/high based on disagreement in comments
            
            Focus on what makes this discussion valuable and interesting.
            """
            
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert analyst of technical discussions and online communities. Provide insightful analysis in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                analysis = self._parse_analysis_text(analysis_text)
            
            # Add computed metrics
            analysis['total_comments'] = total_comments
            analysis['article_length'] = len(content)
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing article {article.get('hn_id', 'unknown')}: {e}")
            return self._generate_fallback_analysis(article)
    
    def analyze_comment_thread(self, comments: List[Dict], article_context: Dict) -> Dict:
        """Analyze a comment thread for interesting discussions."""
        if not openai_client or not comments:
            return self._generate_fallback_thread_analysis(comments)
        
        try:
            # Prepare thread context
            thread_text = ""
            participant_count = set()
            
            for i, comment in enumerate(comments[:10]):  # Limit to first 10 comments
                author = comment.get('by', 'Anonymous')
                text = comment.get('text', '')[:300]
                participant_count.add(author)
                thread_text += f"\n{author}: {text}\n"
            
            if not thread_text.strip():
                return self._generate_fallback_thread_analysis(comments)
            
            prompt = f"""
            Analyze this Hacker News comment thread from the article "{article_context.get('title', 'Unknown')}":
            
            Thread:
            {thread_text}
            
            Participants: {len(participant_count)}
            
            Please analyze in JSON format:
            1. thread_summary: 1-2 sentence summary of the main discussion
            2. main_debate_points: Key points of debate/discussion (comma-separated)
            3. thread_quality_score: Score 1-10 for insight and value
            4. is_featured_discussion: true/false if this is particularly interesting
            
            Focus on substantive technical or intellectual content.
            """
            
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at identifying valuable technical discussions. Provide analysis in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError:
                analysis = self._parse_thread_analysis_text(analysis_text)
            
            analysis['participant_count'] = len(participant_count)
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing comment thread: {e}")
            return self._generate_fallback_thread_analysis(comments)
    
    def curate_top_comments(self, comments: List[Dict], article_context: Dict) -> List[Dict]:
        """Curate and analyze individual comments for quality and insights."""
        curated_comments = []
        
        # Flatten comments for analysis
        flat_comments = []
        self._flatten_comments(comments, flat_comments)
        
        # Sort by length and potential quality
        quality_comments = [
            comment for comment in flat_comments 
            if comment.get('text') and len(comment.get('text', '')) > 100
        ]
        
        # Analyze top comments
        for comment in quality_comments[:20]:  # Limit to top 20 for cost control
            analysis = self._analyze_single_comment(comment, article_context)
            if analysis and analysis.get('quality_score', 0) >= 6:
                curated_comments.append({
                    'comment': comment,
                    'analysis': analysis
                })
        
        # Sort by quality score
        curated_comments.sort(key=lambda x: x['analysis'].get('quality_score', 0), reverse=True)
        return curated_comments[:10]  # Return top 10
    
    def _analyze_single_comment(self, comment: Dict, article_context: Dict) -> Dict:
        """Analyze a single comment for quality and insights."""
        if not openai_client:
            return self._generate_fallback_comment_analysis(comment)
        
        try:
            text = (comment.get('text') or '')[:500]
            author = comment.get('by', 'Anonymous')
            
            if len(text) < 50:  # Skip very short comments
                return None
            
            prompt = f"""
            Analyze this Hacker News comment on "{article_context.get('title', 'Unknown')}":
            
            Author: {author}
            Comment: {text}
            
            Rate in JSON format:
            1. quality_score: 1-10 score for insight/value
            2. key_points: Main points made (brief list)
            3. sentiment: positive/negative/neutral
            4. is_insightful: true/false for exceptional insight
            5. is_controversial: true/false for controversial take
            
            Focus on technical merit, novel insights, or valuable perspectives.
            """
            
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Rate comment quality objectively. Provide valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.2
            )
            
            analysis_text = response.choices[0].message.content
            try:
                return json.loads(analysis_text)
            except json.JSONDecodeError:
                return self._parse_comment_analysis_text(analysis_text)
                
        except Exception as e:
            print(f"❌ Error analyzing comment: {e}")
            return self._generate_fallback_comment_analysis(comment)
    
    def process_all_articles(self, limit: Optional[int] = None):
        """Process all articles and generate analyses."""
        articles = self.load_articles_data()
        
        if limit:
            articles = articles[:limit]
        
        print(f"🔄 Processing {len(articles)} articles...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for i, article in enumerate(articles):
            hn_id = article.get('hn_id', str(i))
            
            # Check if already processed
            cursor.execute('SELECT hn_id FROM article_analyses WHERE hn_id = ?', (hn_id,))
            if cursor.fetchone():
                print(f"⏭️  Skipping already processed article: {hn_id}")
                continue
            
            print(f"🔍 Processing article {i+1}/{len(articles)}: {article.get('title', 'Unknown')[:50]}...")
            
            # Analyze article
            article_analysis = self.analyze_article(article)
            
            # Store article analysis
            cursor.execute('''
                INSERT INTO article_analyses 
                (hn_id, title, url, domain, summary, key_insights, main_themes, 
                 sentiment_analysis, discussion_quality_score, controversy_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(hn_id),
                str(article.get('title', '')),
                str(article.get('url', '')),
                str(article.get('domain', '')),
                str(article_analysis.get('summary', '')),
                str(', '.join(article_analysis.get('key_insights', [])) if isinstance(article_analysis.get('key_insights'), list) else str(article_analysis.get('key_insights', ''))),
                str(article_analysis.get('main_themes', '')),
                str(article_analysis.get('sentiment_analysis', '')),
                int(article_analysis.get('discussion_quality_score', 5)),
                str(article_analysis.get('controversy_level', 'low'))
            ))
            
            # Analyze and store top comments
            curated_comments = self.curate_top_comments(article.get('comments', []), article)
            for comment_data in curated_comments:
                comment = comment_data['comment']
                analysis = comment_data['analysis']
                
                cursor.execute('''
                    INSERT INTO comment_analyses 
                    (comment_id, hn_id, parent_id, author, comment_text, analysis_summary,
                     key_points, sentiment, quality_score, is_insightful, is_controversial)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(comment.get('id', f"{hn_id}_comment_{len(curated_comments)}")),
                    str(hn_id),
                    str(comment.get('parent', '')),
                    str(comment.get('by', 'Anonymous')),
                    str((comment.get('text') or '')[:1000]),  # Limit text length
                    str(', '.join(analysis.get('key_points', [])) if isinstance(analysis.get('key_points'), list) else str(analysis.get('key_points', ''))),
                    str(', '.join(analysis.get('key_points', [])) if isinstance(analysis.get('key_points'), list) else str(analysis.get('key_points', ''))),
                    str(analysis.get('sentiment', 'neutral')),
                    int(analysis.get('quality_score', 5)),
                    bool(analysis.get('is_insightful', False)),
                    bool(analysis.get('is_controversial', False))
                ))
            
            # Analyze discussion threads
            if article.get('comments'):
                thread_analysis = self.analyze_comment_thread(article.get('comments', []), article)
                thread_id = f"{hn_id}_main_thread"
                
                cursor.execute('''
                    INSERT INTO discussion_threads 
                    (thread_id, hn_id, root_comment_id, thread_summary, main_debate_points,
                     participant_count, thread_quality_score, is_featured_discussion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(thread_id),
                    str(hn_id),
                    str(article.get('comments', [{}])[0].get('id', '') if article.get('comments') else ''),
                    str(thread_analysis.get('thread_summary', '')),
                    str(thread_analysis.get('main_debate_points', '')),
                    int(thread_analysis.get('participant_count', 0)),
                    int(thread_analysis.get('thread_quality_score', 5)),
                    bool(thread_analysis.get('is_featured_discussion', False))
                ))
            
            conn.commit()
            
            # Rate limiting - small delay between requests
            if openai_client:
                import time
                time.sleep(1)
        
        conn.close()
        print(f"✅ Completed processing {len(articles)} articles")
    
    # Helper methods
    def _count_comments_recursive(self, comments: List[Dict]) -> int:
        """Count all comments including nested replies."""
        count = len(comments)
        for comment in comments:
            count += self._count_comments_recursive(comment.get('replies', []))
        return count
    
    def _flatten_comments(self, comments: List[Dict], flat_list: List[Dict], level: int = 0):
        """Flatten nested comments structure."""
        for comment in comments:
            comment['level'] = level
            flat_list.append(comment)
            self._flatten_comments(comment.get('replies', []), flat_list, level + 1)
    
    def _format_comments_for_prompt(self, comments: List[Dict]) -> str:
        """Format comments for inclusion in OpenAI prompt."""
        formatted = ""
        for comment in comments:
            formatted += f"- {comment['author']}: {comment['text'][:200]}...\n"
        return formatted
    
    # Fallback methods for when OpenAI is not available
    def _generate_fallback_analysis(self, article: Dict) -> Dict:
        """Generate basic analysis without OpenAI."""
        content_length = len(article.get('content') or '')
        comment_count = self._count_comments_recursive(article.get('comments', []))
        
        return {
            'summary': f"Article about {article.get('title', 'Unknown topic')} with {comment_count} comments.",
            'key_insights': ['Technical discussion', 'Community engagement', 'Industry relevance'],
            'main_themes': 'technology, discussion, community',
            'sentiment_analysis': 'neutral',
            'discussion_quality_score': min(10, max(1, comment_count // 10 + 3)),
            'controversy_level': 'low' if comment_count < 50 else 'medium'
        }
    
    def _generate_fallback_thread_analysis(self, comments: List[Dict]) -> Dict:
        """Generate basic thread analysis without OpenAI."""
        return {
            'thread_summary': f"Discussion thread with {len(comments)} participants.",
            'main_debate_points': 'technical implementation, best practices',
            'thread_quality_score': min(10, len(comments)),
            'is_featured_discussion': len(comments) > 5,
            'participant_count': len(set(c.get('by', 'Anonymous') for c in comments))
        }
    
    def _generate_fallback_comment_analysis(self, comment: Dict) -> Dict:
        """Generate basic comment analysis without OpenAI."""
        text_length = len(comment.get('text') or '')
        return {
            'quality_score': min(10, max(1, text_length // 50 + 3)),
            'key_points': ['Technical insight', 'Relevant experience'],
            'sentiment': 'neutral',
            'is_insightful': text_length > 200,
            'is_controversial': False
        }
    
    def _parse_analysis_text(self, text: str) -> Dict:
        """Parse analysis from non-JSON response."""
        return {
            'summary': text[:200] + '...',
            'key_insights': ['Analysis generated'],
            'main_themes': 'discussion',
            'sentiment_analysis': 'neutral',
            'discussion_quality_score': 5,
            'controversy_level': 'low'
        }
    
    def _parse_thread_analysis_text(self, text: str) -> Dict:
        """Parse thread analysis from non-JSON response."""
        return {
            'thread_summary': text[:100] + '...',
            'main_debate_points': 'various topics',
            'thread_quality_score': 5,
            'is_featured_discussion': False
        }
    
    def _parse_comment_analysis_text(self, text: str) -> Dict:
        """Parse comment analysis from non-JSON response."""
        return {
            'quality_score': 5,
            'key_points': ['Generated analysis'],
            'sentiment': 'neutral',
            'is_insightful': False,
            'is_controversial': False
        }


def main():
    """Main function to run the preprocessing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process HN articles for analysis')
    parser.add_argument('--limit', type=int, default=50, help='Number of articles to process (default: 50)')
    parser.add_argument('--all', action='store_true', help='Process all articles')
    args = parser.parse_args()
    
    print("🚀 Starting Analysis Preprocessing...")
    
    # Setup paths
    db_path = os.path.join(project_root, 'data', 'enhanced_hn_articles.db')
    
    # Create preprocessor
    processor = AnalysisPreprocessor(db_path)
    
    # Process articles
    limit = None if args.all else args.limit
    processor.process_all_articles(limit=limit)
    
    print("✅ Analysis preprocessing completed!")


if __name__ == '__main__':
    main()
