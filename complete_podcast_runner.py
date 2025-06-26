#!/usr/bin/env python3
"""
Complete Automated Daily Podcast Runner
Generates full podcast episodes with script, audio, and metadata storage
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from dynamodb_manager import DynamoDBManager
from tts_generator import TTSGenerator

@dataclass
class PodcastEpisode:
    """Data structure for a podcast episode."""
    date: str
    title: str
    script: str
    audio_path: Optional[str] = None
    duration_seconds: Optional[int] = None
    articles_featured: List[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'date': self.date,
            'title': self.title,
            'script': self.script,
            'audio_path': self.audio_path,
            'duration_seconds': self.duration_seconds,
            'articles_featured': self.articles_featured or []
        }

class CompletePodcastGenerator:
    """Complete podcast generation system."""
    
    def __init__(self):
        self.db = DynamoDBManager()
        
        # Initialize TTS
        try:
            self.tts = TTSGenerator()
            self.has_tts = True
            print("✅ TTS Generator initialized")
        except Exception as e:
            print(f"⚠️  TTS initialization failed: {e}")
            self.has_tts = False
        
        # Podcast settings
        self.target_duration = 7 * 60  # 7 minutes
        self.words_per_minute = 180    # Faster delivery
        self.min_score = 50
        self.min_comments = 10
        self.max_articles = 5
        
        print(f"🎙️ Complete Podcast Generator initialized")
        print(f"   Target duration: {self.target_duration//60} minutes")
        print(f"   Article criteria: score >= {self.min_score}, comments >= {self.min_comments}")
    
    def get_quality_articles(self, limit: int = 20) -> List[Dict]:
        """Get high-quality articles for podcast."""
        articles = self.db.get_articles(limit=limit, sort_by='score')
        
        quality_articles = []
        for article in articles:
            score = int(article.get('score', 0))
            comment_count = int(article.get('num_comments', 0))
            
            if score >= self.min_score and comment_count >= self.min_comments:
                quality_articles.append(article)
        
        return quality_articles[:self.max_articles]
    
    def get_article_discussions(self, article_id: str) -> List[Dict]:
        """Get top discussions for an article."""
        try:
            comments = self.db.get_article_comments(article_id)
            # Return top comments (sorted by score if available)
            return comments[:3]  # Top 3 comments
        except Exception as e:
            print(f"⚠️  Error getting comments for {article_id}: {e}")
            return []
    
    def generate_enhanced_script(self, articles: List[Dict]) -> str:
        """Generate an NPR-style podcast script with Beryl as narrator."""
        if not articles:
            return self._generate_fallback_script()
        
        script_parts = []
        
        # NPR-style intro with Beryl
        intro = f"""Good morning, I'm Beryl, and this is your daily tech briefing. Today we're examining {len(articles)} significant developments that are shaping the technology landscape."""
        
        script_parts.append(intro)
        
        # Main content - NPR style story presentation
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'Unknown Title')
            score = int(article.get('score', 0))
            comment_count = int(article.get('num_comments', 0))
            domain = article.get('domain', 'unknown source')
            
            # NPR-style transitions
            if i == 1:
                transition = "Our top story:"
            elif i == len(articles):
                transition = "And finally:"
            else:
                transition = "In other technology news:"
            
            article_script = f"""{transition} {title}

This report from {domain} highlights important trends in the technology sector. The story has generated significant interest, suggesting its relevance to current industry developments and future implications for how we interact with technology."""
            
            script_parts.append(article_script)
        
        # NPR-style outro
        outro = f"""That's your technology briefing for today. I'm Beryl. These {len(articles)} stories reflect the ongoing evolution of our digital world. We'll return tomorrow with more insights from the technology sector."""
        
        script_parts.append(outro)
        
        return "\n\n".join(script_parts)
    
    def _generate_fallback_script(self) -> str:
        """Fallback NPR-style script when no articles are available."""
        return """Good morning, I'm Beryl, and this is your daily tech briefing.

Today we're experiencing a quieter period in technology news. While there aren't major breaking developments in our coverage areas, this provides an opportunity to reflect on the broader trends shaping our digital landscape.

The technology sector continues its rapid evolution, with ongoing advances in artificial intelligence, software development, and digital infrastructure that will define our technological future.

I'm Beryl. We'll return tomorrow with the latest from the world of technology."""
    
    def estimate_duration(self, script: str) -> int:
        """Estimate audio duration in seconds."""
        word_count = len(script.split())
        return int(word_count / self.words_per_minute * 60)
    
    def generate_audio(self, script: str, filename: str) -> Optional[str]:
        """Generate audio file from script."""
        if not self.has_tts:
            print("⚠️  TTS not available, skipping audio generation")
            return None
        
        try:
            print("🎵 Generating podcast audio...")
            audio_path = self.tts.generate_speech(
                text=script,
                output_filename=filename
            )
            
            if audio_path:
                print(f"✅ Audio generated: {audio_path}")
                return audio_path
            else:
                print("❌ Audio generation failed")
                return None
                
        except Exception as e:
            print(f"❌ Audio generation error: {e}")
            return None
    
    def save_episode_metadata(self, episode: PodcastEpisode):
        """Save episode metadata to DynamoDB."""
        try:
            episode_data = episode.to_dict()
            episode_data['type'] = 'podcast_episode'
            episode_data['created_at'] = datetime.now().isoformat()
            episode_data['hn_id'] = episode.date  # Use date as ID
            
            # Save to analyses table
            self.db.insert_analysis(episode_data)
            print("✅ Episode metadata saved to database")
            
        except Exception as e:
            print(f"❌ Failed to save episode metadata: {e}")
    
    def attach_to_articles(self, episode: PodcastEpisode, article_ids: List[str]):
        """Attach podcast reference to featured articles."""
        try:
            for article_id in article_ids:
                # Get the article first
                article = self.db.get_article(article_id)
                if article:
                    # Update the article with podcast info
                    article['podcast_episode_date'] = episode.date
                    article['podcast_episode_title'] = episode.title
                    
                    if episode.audio_path:
                        article['podcast_audio_path'] = episode.audio_path
                    
                    # Save the updated article
                    self.db.insert_article(article)
            
            print(f"✅ Podcast attached to {len(article_ids)} articles")
            
        except Exception as e:
            print(f"⚠️  Could not attach to all articles: {e}")
    
    def generate_complete_episode(self, date: str = None) -> Optional[PodcastEpisode]:
        """Generate a complete podcast episode."""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n🎙️ Generating complete podcast episode for {date}")
        print("=" * 60)
        
        # Step 1: Get articles
        print("📰 Selecting articles...")
        articles = self.get_quality_articles()
        
        if not articles:
            print("❌ No qualifying articles found")
            # Still generate a fallback episode
            articles = []
        
        print(f"✅ Selected {len(articles)} articles for podcast")
        
        # Step 2: Generate script
        print("📝 Generating podcast script...")
        script = self.generate_enhanced_script(articles)
        estimated_duration = self.estimate_duration(script)
        
        print(f"✅ Script generated: {len(script.split())} words, ~{estimated_duration//60}:{estimated_duration%60:02d}")
        
        # Step 3: Create episode metadata
        episode_title = f"Hacker News Daily - {datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y')}"
        
        episode = PodcastEpisode(
            date=date,
            title=episode_title,
            script=script,
            duration_seconds=estimated_duration,
            articles_featured=[article.get('hn_id', '') for article in articles]
        )
        
        # Step 4: Generate audio
        if self.has_tts:
            audio_filename = f"hn_daily_{date.replace('-', '')}.mp3"
            audio_path = self.generate_audio(script, audio_filename)
            episode.audio_path = audio_path
        
        # Step 5: Save metadata
        print("💾 Saving episode metadata...")
        self.save_episode_metadata(episode)
        
        # Step 6: Attach to articles
        if articles:
            print("🔗 Linking episode to articles...")
            article_ids = [article.get('hn_id', '') for article in articles]
            self.attach_to_articles(episode, article_ids)
        
        print(f"\n✅ Episode generation complete!")
        print(f"   Title: {episode.title}")
        print(f"   Articles featured: {len(articles)}")
        print(f"   Script: {len(script.split())} words")
        print(f"   Duration: ~{estimated_duration//60}:{estimated_duration%60:02d}")
        if episode.audio_path:
            print(f"   Audio: {episode.audio_path}")
        
        return episode
    
    def get_recent_episodes(self, days: int = 7) -> List[Dict]:
        """Get recent podcast episodes."""
        episodes = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            try:
                episode_data = self.db.get_analysis(date)
                if episode_data and episode_data.get('type') == 'podcast_episode':
                    episodes.append(episode_data)
            except:
                continue
        
        return episodes

def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Hacker News Daily Podcast')
    parser.add_argument('--date', type=str, help='Date (YYYY-MM-DD)', default=None)
    parser.add_argument('--list', action='store_true', help='List recent episodes')
    
    args = parser.parse_args()
    
    generator = CompletePodcastGenerator()
    
    if args.list:
        print("\n📚 Recent Episodes:")
        episodes = generator.get_recent_episodes(7)
        
        if episodes:
            for episode in episodes:
                date = episode.get('date', 'Unknown date')
                title = episode.get('title', 'Unknown title')
                duration = episode.get('duration_seconds', 0)
                audio_path = episode.get('audio_path', '')
                
                print(f"   📅 {date}: {title}")
                print(f"      Duration: ~{duration//60}:{duration%60:02d}")
                if audio_path:
                    print(f"      Audio: {audio_path}")
                print()
        else:
            print("   No episodes found")
    else:
        # Generate episode
        episode = generator.generate_complete_episode(args.date)
        
        if episode:
            print("\n🎉 Episode ready for distribution!")
        else:
            print("\n❌ Episode generation failed")

if __name__ == "__main__":
    main()
