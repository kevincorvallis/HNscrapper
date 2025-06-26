#!/usr/bin/env python3
"""
Weekly Podcast Generator for Hacker News
Generates comprehensive weekly podcast episodes covering the week's top stories
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from dynamodb_manager import DynamoDBManager
from tts_generator import TTSGenerator
from dotenv import load_dotenv
import openai

load_dotenv()

@dataclass
class WeeklyPodcastEpisode:
    """Data structure for a weekly podcast episode."""
    week_start: str
    week_end: str
    title: str
    script: str
    audio_url: Optional[str] = None
    audio_path: Optional[str] = None
    duration_seconds: Optional[int] = None
    articles_featured: List[str] = None
    episode_type: str = "weekly"
    
    def to_dict(self) -> Dict:
        return {
            'week_start': self.week_start,
            'week_end': self.week_end,
            'title': self.title,
            'script': self.script,
            'audio_url': self.audio_url,
            'audio_path': self.audio_path,
            'duration_seconds': self.duration_seconds,
            'articles_featured': self.articles_featured or [],
            'episode_type': self.episode_type,
            'date': self.week_start  # For compatibility
        }

class WeeklyPodcastGenerator:
    """Generates weekly podcast episodes from Hacker News articles."""
    
    def __init__(self):
        self.db = DynamoDBManager()
        
        # Initialize TTS Generator
        try:
            self.tts = TTSGenerator()
            self.has_tts = True
            print("✅ TTS Generator initialized")
        except Exception as e:
            print(f"⚠️  TTS initialization failed: {e}")
            self.has_tts = False
        
        # Initialize OpenAI client
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
            print("⚠️  No OpenAI API key found")
            self.has_openai = False
        
        # Podcast generation parameters
        self.target_duration = 15 * 60  # 15 minutes target for weekly
        self.min_duration = 10 * 60     # 10 minutes minimum
        self.max_duration = 20 * 60     # 20 minutes maximum
        self.words_per_minute = 160     # Average speaking speed
        
        # Article selection criteria
        self.min_score = 50             # Lower threshold for weekly (was 100)
        self.min_comments = 15          # Lower threshold for weekly (was 25)
        self.max_articles = 8           # Slightly fewer for weekly (was 10)
        
        print(f"🎙️ Weekly Podcast Generator initialized")
        print(f"   Target duration: {self.target_duration//60} minutes")
        print(f"   Article criteria: score >= {self.min_score}, comments >= {self.min_comments}")
    
    def get_week_date_range(self, date: str = None) -> Tuple[str, str]:
        """Get the start and end dates for the past 7 days (Sunday to Saturday)."""
        if not date:
            today = datetime.now()
        else:
            today = datetime.strptime(date, '%Y-%m-%d')
        
        # Get the past 7 days ending today
        week_end = today
        week_start = today - timedelta(days=6)
        
        return week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')
    
    def get_weekly_articles(self, week_start: str, week_end: str) -> List[Dict]:
        """Get top articles for a specific week."""
        print(f"📰 Fetching articles for week {week_start} to {week_end}...")
        
        try:
            # Get articles from DynamoDB for the week
            all_articles = []
            current_date = datetime.strptime(week_start, '%Y-%m-%d')
            end_date = datetime.strptime(week_end, '%Y-%m-%d')
            
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                try:
                    daily_articles = self.db.get_articles_by_date(date_str)
                    all_articles.extend(daily_articles)
                except Exception as e:
                    print(f"⚠️  No articles found for {date_str}: {e}")
                current_date += timedelta(days=1)
            
            # Filter and sort articles
            filtered_articles = []
            for article in all_articles:
                score = article.get('score', 0)
                comment_count = article.get('comment_count', 0)
                
                if score >= self.min_score and comment_count >= self.min_comments:
                    filtered_articles.append(article)
            
            # Sort by engagement score (combination of score and comments)
            filtered_articles.sort(
                key=lambda x: x.get('score', 0) + (x.get('comment_count', 0) * 2),
                reverse=True
            )
            
            # Limit to max articles
            selected_articles = filtered_articles[:self.max_articles]
            
            print(f"   Found {len(all_articles)} total articles")
            print(f"   Selected {len(selected_articles)} articles for weekly podcast")
            
            return selected_articles
            
        except Exception as e:
            print(f"❌ Error fetching weekly articles: {e}")
            return []
    
    def get_article_discussions(self, article_id: str) -> List[Dict]:
        """Get the most engaging discussions for an article."""
        try:
            comments = self.db.get_comments(article_id)
            
            # Filter for high-quality comments
            quality_comments = []
            for comment in comments:
                score = comment.get('score', 0)
                text = comment.get('text', '')
                
                # Quality criteria (slightly higher for weekly)
                if (score >= 5 and 
                    len(text) >= 150 and 
                    len(text) <= 1000 and
                    not text.lower().startswith('[deleted]')):
                    quality_comments.append(comment)
            
            # Sort by score and limit
            quality_comments.sort(key=lambda x: x.get('score', 0), reverse=True)
            return quality_comments[:3]  # Top 3 comments for weekly
            
        except Exception as e:
            print(f"⚠️  Error fetching comments for {article_id}: {e}")
            return []
    
    def calculate_target_words(self) -> int:
        """Calculate target word count for the script."""
        return int(self.target_duration * self.words_per_minute / 60)
    
    def categorize_articles(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize articles by domain/topic."""
        categories = {
            'Technology & Development': [],
            'Business & Startups': [],
            'Science & Research': [],
            'Industry News': [],
            'Community Discussions': []
        }
        
        for article in articles:
            domain = article.get('domain', '').lower()
            title = article.get('title', '').lower()
            
            # Technology
            if any(tech in domain for tech in ['github.com', 'stackoverflow.com', 'openai.com', 'google.com']):
                categories['Technology & Development'].append(article)
            elif any(tech in title for tech in ['ai', 'programming', 'software', 'developer', 'code']):
                categories['Technology & Development'].append(article)
            # Business
            elif any(biz in domain for biz in ['techcrunch.com', 'bloomberg.com', 'wsj.com']):
                categories['Business & Startups'].append(article)
            elif any(biz in title for biz in ['startup', 'funding', 'ipo', 'business']):
                categories['Business & Startups'].append(article)
            # Science
            elif any(sci in domain for sci in ['nature.com', 'science.org', 'arxiv.org']):
                categories['Science & Research'].append(article)
            elif any(sci in title for sci in ['research', 'study', 'science']):
                categories['Science & Research'].append(article)
            # Community
            elif 'ycombinator.com' in domain or 'Show HN' in article.get('title', ''):
                categories['Community Discussions'].append(article)
            else:
                categories['Industry News'].append(article)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def generate_weekly_script(self, articles: List[Dict]) -> str:
        """Generate a comprehensive weekly podcast script."""
        if not articles:
            return self._generate_fallback_script()
        
        target_words = self.calculate_target_words()
        
        if self.has_openai:
            return self._generate_openai_weekly_script(articles, target_words)
        else:
            return self._generate_template_weekly_script(articles, target_words)
    
    def _generate_openai_weekly_script(self, articles: List[Dict], target_words: int) -> str:
        """Generate weekly script using OpenAI."""
        try:
            # Categorize articles
            categorized = self.categorize_articles(articles)
            
            # Prepare article summaries
            article_data = []
            for category, cat_articles in categorized.items():
                for article in cat_articles:
                    discussions = self.get_article_discussions(article.get('id', ''))
                    article_data.append({
                        'category': category,
                        'title': article.get('title', ''),
                        'url': article.get('url', ''),
                        'score': article.get('score', 0),
                        'comment_count': article.get('comment_count', 0),
                        'top_comments': [c.get('text', '')[:200] for c in discussions[:2]]
                    })
            
            # Get week range
            week_start, week_end = self.get_week_date_range()
            week_start_formatted = datetime.strptime(week_start, '%Y-%m-%d').strftime('%B %d')
            week_end_formatted = datetime.strptime(week_end, '%Y-%m-%d').strftime('%B %d, %Y')
            
            prompt = f"""
            Create a {target_words}-word NPR-style weekly podcast script covering the most significant stories from Hacker News.
            
            Period: Past 7 days ({week_start_formatted} to {week_end_formatted})
            
            Style guidelines:
            - NPR-style professional, thoughtful delivery (like Weekend Edition)
            - Host is Beryl
            - Focus on trends, patterns, and broader implications from the past week
            - Group related stories thematically
            - Explain significance and context for each story
            - Use smooth transitions between segments
            - Present diverse perspectives and analysis
            - Make technical concepts accessible
            
            Stories by category:
            {json.dumps(article_data, indent=2)}
            
            Structure:
            1. Opening: Weekly review overview and what we're covering from the past 7 days
            2. Main segments organized by theme/category
            3. Analysis of trends and patterns observed this week
            4. Closing: Key takeaways and sign-off
            
            Write in a conversational NPR weekly review style. Generate only the script text.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are Beryl, an NPR-style host for a weekly technology and innovation review. You present news with the depth and analysis of NPR's Weekend Edition, making complex topics accessible while highlighting broader trends and implications."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=target_words * 2,
                temperature=0.7
            )
            
            script = response.choices[0].message.content.strip()
            print(f"✅ Generated OpenAI weekly script ({len(script.split())} words)")
            return script
            
        except Exception as e:
            print(f"❌ OpenAI weekly script generation failed: {e}")
            return self._generate_template_weekly_script(articles, target_words)
    
    def _generate_template_weekly_script(self, articles: List[Dict], target_words: int) -> str:
        """Generate weekly NPR-style script using templates (fallback)."""
        script_parts = []
        
        # Get week range
        week_start, week_end = self.get_week_date_range()
        week_start_formatted = datetime.strptime(week_start, '%Y-%m-%d').strftime('%B %d')
        week_end_formatted = datetime.strptime(week_end, '%Y-%m-%d').strftime('%B %d, %Y')
        
        # Categorize articles
        categorized = self.categorize_articles(articles)
        
        # NPR-style weekly intro
        script_parts.append(
            f"Good morning, I'm Beryl, and this is your weekly review from Hacker News. "
            f"Looking back at the past seven days, from {week_start_formatted} to {week_end_formatted}, "
            f"we're examining {len(articles)} significant stories that captured the community's attention. "
            f"From emerging technologies to industry developments, these stories reflect the ongoing "
            f"conversations and trends that shaped the week in innovation and beyond."
        )
        
        # Process each category
        for category, cat_articles in categorized.items():
            if not cat_articles:
                continue
                
            script_parts.append(f"\nIn {category.lower()}, we saw several noteworthy developments.")
            
            for article in cat_articles[:3]:  # Limit per category
                title = article.get('title', 'Unknown Title')
                score = article.get('score', 0)
                comment_count = article.get('comment_count', 0)
                domain = article.get('domain', 'unknown source')
                
                article_script = f"""
                {title} drew significant attention from {domain}, generating {comment_count} comments 
                and reaching {score} points. This story highlights important trends we're seeing in 
                {category.lower()}, reflecting the community's interest in how these developments 
                might shape the future of innovation and technology.
                """
                
                script_parts.append(article_script.strip())
        
        # NPR-style weekly outro
        script_parts.append(
            f"\nReflecting on this past week, we see continuing themes of innovation, "
            f"community engagement, and the ongoing dialogue about technology's role in society. "
            f"These conversations from Hacker News provide valuable insights into the trends "
            f"worth watching as we move into the coming week. I'm Beryl, and we'll be back "
            f"next Sunday with another review of the stories shaping our digital future."
        )
        
        script = "\n\n".join(script_parts)
        print(f"✅ Generated NPR-style weekly template script ({len(script.split())} words)")
        return script
    
    def _generate_fallback_script(self) -> str:
        """Generate a fallback weekly script when no articles are available."""
        week_start, week_end = self.get_week_date_range()
        week_start_formatted = datetime.strptime(week_start, '%Y-%m-%d').strftime('%B %d')
        week_end_formatted = datetime.strptime(week_end, '%Y-%m-%d').strftime('%B %d, %Y')
        
        return f"""
        Good morning, I'm Beryl, and this is your weekly review from Hacker News.
        
        Looking back at the past seven days, from {week_start_formatted} to {week_end_formatted}, 
        we're experiencing a quieter period in major story developments. While there aren't 
        significant breaking stories in our focus areas this week, this provides an opportunity 
        to reflect on ongoing trends and anticipate what's ahead.
        
        The innovation community continues to evolve, with discussions spanning technology, 
        business, science, and community building. These conversations shape how we think 
        about the future of digital innovation and its impact on society.
        
        We'll return next Sunday with the latest developments and community discussions from 
        the past week. I'm Beryl, thank you for listening to this week's review.
        """
    
    def generate_audio_with_elevenlabs(self, script: str, week_start: str) -> Optional[str]:
        """Generate audio using ElevenLabs TTS."""
        if not self.has_tts:
            print("⚠️  TTS not configured, skipping audio generation")
            return None
        
        try:
            print("🎵 Generating weekly podcast audio...")
            
            # Generate filename with week start date
            week_formatted = datetime.strptime(week_start, '%Y-%m-%d').strftime('%Y%m%d')
            filename = f"hn_weekly_{week_formatted}.mp3"
            
            # Use the TTS generator
            audio_path = self.tts.generate_speech(
                text=script,
                output_filename=filename,
                voice_id=None  # Use default voice
            )
            
            if audio_path:
                print(f"✅ Weekly audio generated: {audio_path}")
                return audio_path
            else:
                print("❌ Weekly audio generation failed")
                return None
                
        except Exception as e:
            print(f"❌ Weekly audio generation failed: {e}")
            return None
    
    def save_weekly_episode_to_db(self, episode: WeeklyPodcastEpisode):
        """Save weekly podcast episode metadata to DynamoDB."""
        try:
            episode_data = episode.to_dict()
            episode_data['type'] = 'weekly_podcast_episode'
            episode_data['created_at'] = datetime.now().isoformat()
            
            # Use week_start as the primary key with 'weekly_' prefix
            pk_value = f"weekly_{episode.week_start}"
            self.db.put_item('hn_analyses', episode_data, pk_value=pk_value)
            print(f"✅ Weekly episode metadata saved to database")
            
        except Exception as e:
            print(f"❌ Failed to save weekly episode: {e}")
    
    def generate_weekly_episode(self, date: str = None) -> Optional[WeeklyPodcastEpisode]:
        """Generate a complete weekly podcast episode."""
        week_start, week_end = self.get_week_date_range(date)
        
        print(f"\n🎙️ Generating weekly podcast for {week_start} to {week_end}")
        print("=" * 60)
        
        # Step 1: Get articles for the week
        articles = self.get_weekly_articles(week_start, week_end)
        if not articles:
            print("❌ No qualifying articles found for this week")
            return None
        
        # Step 2: Generate script
        print("\n📝 Generating weekly podcast script...")
        script = self.generate_weekly_script(articles)
        
        if not script:
            print("❌ Failed to generate weekly script")
            return None
        
        # Step 3: Create episode metadata
        week_start_formatted = datetime.strptime(week_start, '%Y-%m-%d').strftime('%B %d')
        week_end_formatted = datetime.strptime(week_end, '%Y-%m-%d').strftime('%B %d, %Y')
        episode_title = f"Hacker News Weekly Review - Past 7 Days ({week_start_formatted} to {week_end_formatted})"
        
        episode = WeeklyPodcastEpisode(
            week_start=week_start,
            week_end=week_end,
            title=episode_title,
            script=script,
            articles_featured=[article.get('id', '') for article in articles]
        )
        
        # Step 4: Generate audio
        audio_path = self.generate_audio_with_elevenlabs(script, week_start)
        if audio_path:
            episode.audio_path = audio_path
            episode.audio_url = f"/audio/{audio_path.split('/')[-1]}"
            
            # Estimate duration based on word count
            word_count = len(script.split())
            estimated_duration = int(word_count / self.words_per_minute * 60)
            episode.duration_seconds = estimated_duration
        
        # Step 5: Save to database
        self.save_weekly_episode_to_db(episode)
        
        print(f"\n✅ Weekly podcast episode generated successfully!")
        print(f"   Title: {episode.title}")
        print(f"   Week: {week_start} to {week_end}")
        print(f"   Articles featured: {len(articles)}")
        print(f"   Script length: {len(script.split())} words")
        if episode.duration_seconds:
            print(f"   Estimated duration: {episode.duration_seconds//60}:{episode.duration_seconds%60:02d}")
        if episode.audio_path:
            print(f"   Audio: {episode.audio_path}")
        
        return episode
    
    def get_recent_weekly_episodes(self, weeks: int = 4) -> List[Dict]:
        """Get recent weekly podcast episodes."""
        try:
            episodes = []
            
            for i in range(weeks):
                # Get past 7-day periods
                current_date = datetime.now() - timedelta(weeks=i)
                week_start = current_date - timedelta(days=6)
                week_start_str = week_start.strftime('%Y-%m-%d')
                
                try:
                    pk_value = f"weekly_{week_start_str}"
                    episode_data = self.db.get_item('hn_analyses', pk_value)
                    if episode_data and episode_data.get('type') == 'weekly_podcast_episode':
                        episodes.append(episode_data)
                except:
                    continue  # Episode doesn't exist for this week
            
            return episodes
            
        except Exception as e:
            print(f"❌ Error fetching recent weekly episodes: {e}")
            return []

    def should_generate_weekly_episode(self) -> bool:
        """Check if we should generate a weekly episode (on Sundays)."""
        today = datetime.now()
        return today.weekday() == 6  # Sunday is 6
    
    def get_current_week_id(self) -> str:
        """Get the identifier for the current week."""
        week_start, week_end = self.get_week_date_range()
        return week_start

def main():
    """Main function for testing weekly podcast generation."""
    generator = WeeklyPodcastGenerator()
    
    # Generate this week's episode
    episode = generator.generate_weekly_episode()
    
    if episode:
        print("\n🎉 Weekly episode generation complete!")
        
        # Show recent episodes
        print("\n📚 Recent weekly episodes:")
        recent = generator.get_recent_weekly_episodes(4)
        for ep in recent:
            print(f"   {ep.get('week_start')} to {ep.get('week_end')}: {ep.get('title')}")
    else:
        print("\n❌ Weekly episode generation failed")

if __name__ == "__main__":
    main()
