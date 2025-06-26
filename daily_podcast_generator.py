#!/usr/bin/env python3
"""
Daily Podcast Generator for Hacker News
Generates 5-10 minute podcast episodes from top daily articles and discussions
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
class PodcastEpisode:
    """Data structure for a podcast episode."""
    date: str
    title: str
    script: str
    audio_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    articles_featured: List[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'date': self.date,
            'title': self.title,
            'script': self.script,
            'audio_url': self.audio_url,
            'duration_seconds': self.duration_seconds,
            'articles_featured': self.articles_featured or []
        }

class DailyPodcastGenerator:
    """Generates daily podcast episodes from Hacker News articles."""
    
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
        self.target_duration = 7 * 60  # 7 minutes target
        self.min_duration = 5 * 60     # 5 minutes minimum
        self.max_duration = 10 * 60    # 10 minutes maximum
        self.words_per_minute = 160    # Average speaking speed
        
        # Article selection criteria
        self.min_score = 50           # Minimum article score
        self.min_comments = 10        # Minimum comment count
        self.max_articles = 5         # Maximum articles per episode
        
        print(f"🎙️ Daily Podcast Generator initialized")
        print(f"   Target duration: {self.target_duration//60} minutes")
        print(f"   Article criteria: score >= {self.min_score}, comments >= {self.min_comments}")
    
    def get_daily_articles(self, date: str = None) -> List[Dict]:
        """Get top articles for a specific date."""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"📰 Fetching articles for {date}...")
        
        # Get articles from DynamoDB for the specified date
        try:
            articles = self.db.get_articles_by_date(date)
            
            # Filter and sort articles
            filtered_articles = []
            for article in articles:
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
            
            print(f"   Found {len(articles)} total articles")
            print(f"   Selected {len(selected_articles)} articles for podcast")
            
            return selected_articles
            
        except Exception as e:
            print(f"❌ Error fetching articles: {e}")
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
                
                # Quality criteria
                if (score >= 3 and 
                    len(text) >= 100 and 
                    len(text) <= 1000 and
                    not text.lower().startswith('[deleted]')):
                    quality_comments.append(comment)
            
            # Sort by score and limit
            quality_comments.sort(key=lambda x: x.get('score', 0), reverse=True)
            return quality_comments[:5]  # Top 5 comments
            
        except Exception as e:
            print(f"⚠️  Error fetching comments for {article_id}: {e}")
            return []
    
    def calculate_target_words(self) -> int:
        """Calculate target word count for the script."""
        return int(self.target_duration * self.words_per_minute / 60)
    
    def generate_podcast_script(self, articles: List[Dict]) -> str:
        """Generate a podcast script from selected articles."""
        if not articles:
            return self._generate_fallback_script()
        
        target_words = self.calculate_target_words()
        
        if self.has_openai:
            return self._generate_openai_script(articles, target_words)
        else:
            return self._generate_template_script(articles, target_words)
    
    def _generate_openai_script(self, articles: List[Dict], target_words: int) -> str:
        """Generate script using OpenAI."""
        try:
            # Prepare article summaries with discussions
            article_data = []
            for article in articles:
                discussions = self.get_article_discussions(article.get('id', ''))
                article_data.append({
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'score': article.get('score', 0),
                    'comment_count': article.get('comment_count', 0),
                    'top_comments': [c.get('text', '')[:200] for c in discussions[:3]]
                })
            
            prompt = f"""
            Create a {target_words}-word NPR-style podcast script for a daily tech news briefing. The host is Beryl.
            
            Style guidelines:
            - NPR-style professional yet accessible tone
            - Smooth, authoritative delivery like Morning Edition or All Things Considered
            - Focus on the significance and impact of each story
            - Explain technical concepts clearly for general audience
            - Use thoughtful transitions between stories
            - No mention of specific comments or community reactions
            - Present news objectively with context and analysis
            
            Stories to cover:
            {json.dumps(article_data, indent=2)}
            
            Structure:
            1. Opening: "Good morning, I'm Beryl, and this is your daily briefing
            2. Present each story with context, significance, and implications
            3. Smooth transitions between stories
            4. Closing: Brief wrap-up and sign-off
            
            Write in a conversational NPR news style. Generate only the script text, no formatting or stage directions.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are Beryl, an NPR-style tech news host with a warm, authoritative voice. You present news with the professionalism of NPR's Morning Edition, making complex topics accessible to a general audience."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=target_words * 2,
                temperature=0.6
            )
            
            script = response.choices[0].message.content.strip()
            print(f"✅ Generated OpenAI script ({len(script.split())} words)")
            return script
            
        except Exception as e:
            print(f"❌ OpenAI script generation failed: {e}")
            return self._generate_template_script(articles, target_words)
    
    def _generate_template_script(self, articles: List[Dict], target_words: int) -> str:
        """Generate NPR-style script using templates (fallback)."""
        script_parts = []
        
        # NPR-style intro with Beryl
        script_parts.append(
            f"Good morning, I'm Beryl, and this is your daily briefing. "
            f"Today we're looking at {len(articles)} significant developments"
        )
        
        # Articles in NPR style
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'Unknown Title')
            score = article.get('score', 0)
            comment_count = article.get('comment_count', 0)
            domain = article.get('domain', 'unknown source')
            
            # NPR-style story presentation
            if i == 1:
                transition = "Our top story today:"
            elif i == len(articles):
                transition = "And finally:"
            else:
                transition = "In other news:"
            
            article_script = f"""
            {transition} {title}
            
            This development from {domain} has drawn significant attention in the tech community, 
            indicating its potential impact on the industry. The story highlights important trends 
            we're seeing in  today, from innovation in software development to changes 
            in how we approach digital infrastructure.
            """
            
            script_parts.append(article_script.strip())
        
        # NPR-style outro
        script_parts.append(
            f"That's your tech briefing for today. I'm Beryl. These stories represent "
            f"the evolving landscape of  and its impact on our world. "
            f"We'll be back tomorrow with more insights from the intersection of  and society."
        )
        
        script = "\n\n".join(script_parts)
        print(f"✅ Generated NPR-style template script ({len(script.split())} words)")
        return script
    
    def _generate_fallback_script(self) -> str:
        """Generate a fallback NPR-style script when no articles are available."""
        return """
        Good morning, I'm Beryl, and this is your daily tech briefing. 
        
        Today we're experiencing a quieter moment in the news cycle. 
        I'm Beryl, thank you for listening.
        """
    
    def generate_audio_with_elevenlabs(self, script: str) -> Optional[str]:
        """Generate audio using ElevenLabs TTS."""
        if not self.has_tts:
            print("⚠️  TTS not configured, skipping audio generation")
            return None
        
        try:
            print("🎵 Generating audio with ElevenLabs...")
            
            # Generate timestamp for unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"podcast_{timestamp}.mp3"
            
            # Use the TTS generator
            audio_path = self.tts.generate_speech(
                text=script,
                output_filename=filename,
                voice_id=None  # Use default voice
            )
            
            if audio_path:
                print(f"✅ Audio generated: {audio_path}")
                return audio_path
            else:
                print("❌ Audio generation failed")
                return None
                
        except Exception as e:
            print(f"❌ Audio generation failed: {e}")
            return None
    
    def upload_audio_to_storage(self, audio_path: str) -> Optional[str]:
        """Upload audio to cloud storage and return URL."""
        # This is a placeholder for cloud storage integration
        # You can implement S3, CloudFlare, or other storage here
        
        print(f"📁 Audio file ready for upload: {audio_path}")
        print("   Implement cloud storage integration as needed")
        
        # For now, return a local file URL
        return f"file://{audio_path}"
    
    def save_episode_to_db(self, episode: PodcastEpisode):
        """Save podcast episode metadata to DynamoDB."""
        try:
            episode_data = episode.to_dict()
            episode_data['type'] = 'podcast_episode'
            episode_data['created_at'] = datetime.now().isoformat()
            
            # Use date as the primary key
            self.db.put_item('hn_analyses', episode_data, pk_value=episode.date)
            print(f"✅ Episode metadata saved to database")
            
        except Exception as e:
            print(f"❌ Failed to save episode: {e}")
    
    def attach_episode_to_articles(self, episode: PodcastEpisode, article_ids: List[str]):
        """Attach podcast episode reference to featured articles."""
        try:
            for article_id in article_ids:
                # Update article with podcast reference
                update_data = {
                    'podcast_episode_date': episode.date,
                    'podcast_episode_title': episode.title
                }
                
                if episode.audio_url:
                    update_data['podcast_audio_url'] = episode.audio_url
                
                self.db.update_item('hn_articles', article_id, update_data)
            
            print(f"✅ Podcast attached to {len(article_ids)} articles")
            
        except Exception as e:
            print(f"❌ Failed to attach episode to articles: {e}")
    
    def generate_daily_episode(self, date: str = None) -> Optional[PodcastEpisode]:
        """Generate a complete daily podcast episode."""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n🎙️ Generating daily podcast for {date}")
        print("=" * 50)
        
        # Step 1: Get articles
        articles = self.get_daily_articles(date)
        if not articles:
            print("❌ No qualifying articles found for today")
            return None
        
        # Step 2: Generate script
        print("\n📝 Generating podcast script...")
        script = self.generate_podcast_script(articles)
        
        if not script:
            print("❌ Failed to generate script")
            return None
        
        # Step 3: Create episode metadata
        episode_title = f"Hacker News Daily - {datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y')}"
        
        episode = PodcastEpisode(
            date=date,
            title=episode_title,
            script=script,
            articles_featured=[article.get('id', '') for article in articles]
        )
        
        # Step 4: Generate audio
        audio_path = self.generate_audio_with_elevenlabs(script)
        if audio_path:
            # Step 5: Upload audio (placeholder)
            audio_url = self.upload_audio_to_storage(audio_path)
            episode.audio_url = audio_url
            
            # Estimate duration based on word count
            word_count = len(script.split())
            estimated_duration = int(word_count / self.words_per_minute * 60)
            episode.duration_seconds = estimated_duration
        
        # Step 6: Save to database
        self.save_episode_to_db(episode)
        
        # Step 7: Attach to articles
        article_ids = [article.get('id', '') for article in articles]
        self.attach_episode_to_articles(episode, article_ids)
        
        print(f"\n✅ Daily podcast episode generated successfully!")
        print(f"   Title: {episode.title}")
        print(f"   Articles featured: {len(articles)}")
        print(f"   Script length: {len(script.split())} words")
        if episode.duration_seconds:
            print(f"   Estimated duration: {episode.duration_seconds//60}:{episode.duration_seconds%60:02d}")
        if episode.audio_url:
            print(f"   Audio: {episode.audio_url}")
        
        return episode
    
    def get_recent_episodes(self, days: int = 7) -> List[Dict]:
        """Get recent podcast episodes."""
        try:
            # Query recent episodes from DynamoDB
            episodes = []
            
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                try:
                    episode_data = self.db.get_item('hn_analyses', date)
                    if episode_data and episode_data.get('type') == 'podcast_episode':
                        episodes.append(episode_data)
                except:
                    continue  # Episode doesn't exist for this date
            
            return episodes
            
        except Exception as e:
            print(f"❌ Error fetching recent episodes: {e}")
            return []

def main():
    """Main function for testing."""
    generator = DailyPodcastGenerator()
    
    # Generate today's episode
    episode = generator.generate_daily_episode()
    
    if episode:
        print("\n🎉 Episode generation complete!")
        
        # Show recent episodes
        print("\n📚 Recent episodes:")
        recent = generator.get_recent_episodes(3)
        for ep in recent:
            print(f"   {ep.get('date')}: {ep.get('title')}")
    else:
        print("\n❌ Episode generation failed")

if __name__ == "__main__":
    main()
