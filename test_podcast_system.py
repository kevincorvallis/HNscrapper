#!/usr/bin/env python3
"""
Comprehensive test suite for the daily podcast generation system
"""

import unittest
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from daily_podcast_generator import DailyPodcastGenerator, PodcastEpisode
from auto_podcast_runner import run_daily_podcast, run_backfill

class TestPodcastGeneration(unittest.TestCase):
    """Test podcast generation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = DailyPodcastGenerator()
        
        # Mock articles for testing
        self.mock_articles = [
            {
                'id': 'test_article_1',
                'title': 'Revolutionary AI Breakthrough',
                'url': 'https://example.com/article1',
                'score': 150,
                'comment_count': 45,
                'date_scraped': '2024-01-15'
            },
            {
                'id': 'test_article_2', 
                'title': 'New Programming Language Released',
                'url': 'https://example.com/article2',
                'score': 120,
                'comment_count': 30,
                'date_scraped': '2024-01-15'
            },
            {
                'id': 'test_article_3',
                'title': 'Startup Acquires Major Competitor',
                'url': 'https://example.com/article3',
                'score': 80,
                'comment_count': 25,
                'date_scraped': '2024-01-15'
            }
        ]
        
        # Mock comments for testing
        self.mock_comments = [
            {
                'id': 'comment_1',
                'text': 'This is a really insightful article about AI development. The implications for the industry are huge.',
                'score': 15,
                'author': 'tech_expert'
            },
            {
                'id': 'comment_2',
                'text': 'I disagree with the main premise. Here is why this approach might not work in practice...',
                'score': 12,
                'author': 'skeptical_dev'
            },
            {
                'id': 'comment_3',
                'text': 'Great article! We implemented something similar at our company and saw amazing results.',
                'score': 8,
                'author': 'industry_insider'
            }
        ]
    
    def test_podcast_episode_dataclass(self):
        """Test PodcastEpisode dataclass functionality."""
        episode = PodcastEpisode(
            date='2024-01-15',
            title='Test Episode',
            script='This is a test script.',
            audio_url='https://example.com/audio.mp3',
            duration_seconds=420,
            articles_featured=['article1', 'article2']
        )
        
        episode_dict = episode.to_dict()
        
        self.assertEqual(episode_dict['date'], '2024-01-15')
        self.assertEqual(episode_dict['title'], 'Test Episode')
        self.assertEqual(episode_dict['script'], 'This is a test script.')
        self.assertEqual(episode_dict['audio_url'], 'https://example.com/audio.mp3')
        self.assertEqual(episode_dict['duration_seconds'], 420)
        self.assertEqual(episode_dict['articles_featured'], ['article1', 'article2'])
    
    @patch('daily_podcast_generator.DynamoDBManager')
    def test_get_daily_articles(self, mock_db_class):
        """Test article selection for podcast generation."""
        # Mock database response
        mock_db = Mock()
        mock_db.get_articles_by_date.return_value = self.mock_articles
        mock_db_class.return_value = mock_db
        
        generator = DailyPodcastGenerator()
        generator.db = mock_db
        
        articles = generator.get_daily_articles('2024-01-15')
        
        # Should return articles meeting criteria
        self.assertEqual(len(articles), 3)
        self.assertEqual(articles[0]['title'], 'Revolutionary AI Breakthrough')
        
        # Verify filtering works
        mock_db.get_articles_by_date.assert_called_once_with('2024-01-15')
    
    @patch('daily_podcast_generator.DynamoDBManager')
    def test_get_article_discussions(self, mock_db_class):
        """Test comment retrieval and filtering."""
        mock_db = Mock()
        mock_db.get_comments.return_value = self.mock_comments
        mock_db_class.return_value = mock_db
        
        generator = DailyPodcastGenerator()
        generator.db = mock_db
        
        discussions = generator.get_article_discussions('test_article_1')
        
        # Should return quality comments sorted by score
        self.assertGreater(len(discussions), 0)
        self.assertEqual(discussions[0]['score'], 15)
        
        mock_db.get_comments.assert_called_once_with('test_article_1')
    
    def test_calculate_target_words(self):
        """Test word count calculation."""
        words = self.generator.calculate_target_words()
        
        # Should calculate based on target duration and WPM
        expected_words = int(self.generator.target_duration * self.generator.words_per_minute / 60)
        self.assertEqual(words, expected_words)
    
    def test_generate_template_script(self):
        """Test template-based script generation."""
        script = self.generator._generate_template_script(self.mock_articles, 1000)
        
        self.assertIsInstance(script, str)
        self.assertGreater(len(script), 100)
        self.assertIn('Welcome to today\'s Hacker News Daily', script)
        self.assertIn('Revolutionary AI Breakthrough', script)
    
    def test_generate_fallback_script(self):
        """Test fallback script generation."""
        script = self.generator._generate_fallback_script()
        
        self.assertIsInstance(script, str)
        self.assertGreater(len(script), 50)
        self.assertIn('Welcome to Hacker News Daily', script)
    
    @patch('daily_podcast_generator.requests.post')
    def test_generate_audio_with_elevenlabs_success(self, mock_post):
        """Test successful audio generation with ElevenLabs."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'mock_audio_data'
        mock_post.return_value = mock_response
        
        # Mock environment variables
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test_key'}):
            generator = DailyPodcastGenerator()
            generator.elevenlabs_api_key = 'test_key'
            generator.has_elevenlabs = True
            
            audio_path = generator.generate_audio_with_elevenlabs('Test script')
            
            self.assertIsNotNone(audio_path)
            self.assertTrue(audio_path.endswith('.mp3'))
    
    @patch('daily_podcast_generator.requests.post')
    def test_generate_audio_with_elevenlabs_failure(self, mock_post):
        """Test audio generation failure handling."""
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'API Error'
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test_key'}):
            generator = DailyPodcastGenerator()
            generator.elevenlabs_api_key = 'test_key'
            generator.has_elevenlabs = True
            
            audio_path = generator.generate_audio_with_elevenlabs('Test script')
            
            self.assertIsNone(audio_path)
    
    def test_upload_audio_to_storage(self):
        """Test audio upload placeholder."""
        audio_url = self.generator.upload_audio_to_storage('/tmp/test.mp3')
        
        self.assertIsNotNone(audio_url)
        self.assertIn('file://', audio_url)
    
    @patch('daily_podcast_generator.DynamoDBManager')
    def test_save_episode_to_db(self, mock_db_class):
        """Test saving episode to database."""
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        generator = DailyPodcastGenerator()
        generator.db = mock_db
        
        episode = PodcastEpisode(
            date='2024-01-15',
            title='Test Episode',
            script='Test script'
        )
        
        generator.save_episode_to_db(episode)
        
        # Verify database call
        mock_db.put_item.assert_called_once()
        call_args = mock_db.put_item.call_args
        self.assertEqual(call_args[0][0], 'hn_analyses')
        self.assertEqual(call_args[1]['pk_value'], '2024-01-15')
    
    @patch('daily_podcast_generator.DynamoDBManager')
    def test_attach_episode_to_articles(self, mock_db_class):
        """Test attaching episode to articles."""
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        generator = DailyPodcastGenerator()
        generator.db = mock_db
        
        episode = PodcastEpisode(
            date='2024-01-15',
            title='Test Episode',
            script='Test script',
            audio_url='https://example.com/audio.mp3'
        )
        
        article_ids = ['article1', 'article2']
        generator.attach_episode_to_articles(episode, article_ids)
        
        # Verify database updates
        self.assertEqual(mock_db.update_item.call_count, 2)
    
    @patch('daily_podcast_generator.DynamoDBManager')
    def test_get_recent_episodes(self, mock_db_class):
        """Test retrieving recent episodes."""
        mock_db = Mock()
        
        # Mock episode data
        mock_episode = {
            'date': '2024-01-15',
            'title': 'Test Episode',
            'type': 'podcast_episode',
            'script': 'Test script'
        }
        
        mock_db.get_item.return_value = mock_episode
        mock_db_class.return_value = mock_db
        
        generator = DailyPodcastGenerator()
        generator.db = mock_db
        
        episodes = generator.get_recent_episodes(1)
        
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0]['title'], 'Test Episode')

class TestAutoPodcastRunner(unittest.TestCase):
    """Test automated podcast runner functionality."""
    
    @patch('auto_podcast_runner.DailyPodcastGenerator')
    def test_run_daily_podcast_success(self, mock_generator_class):
        """Test successful daily podcast run."""
        # Mock generator and episode
        mock_generator = Mock()
        mock_episode = Mock()
        mock_episode.title = 'Test Episode'
        mock_episode.duration_seconds = 420
        
        mock_generator.generate_daily_episode.return_value = mock_episode
        mock_generator_class.return_value = mock_generator
        
        result = run_daily_podcast('2024-01-15', verbose=False)
        
        self.assertTrue(result)
        mock_generator.generate_daily_episode.assert_called_once_with('2024-01-15')
    
    @patch('auto_podcast_runner.DailyPodcastGenerator')
    def test_run_daily_podcast_failure(self, mock_generator_class):
        """Test failed daily podcast run."""
        # Mock generator returning None
        mock_generator = Mock()
        mock_generator.generate_daily_episode.return_value = None
        mock_generator_class.return_value = mock_generator
        
        result = run_daily_podcast('2024-01-15', verbose=False)
        
        self.assertFalse(result)
    
    @patch('auto_podcast_runner.run_daily_podcast')
    def test_run_backfill(self, mock_run_daily):
        """Test backfill functionality."""
        # Mock some successes and failures
        mock_run_daily.side_effect = [True, False, True]
        
        success_count = run_backfill(3, verbose=False)
        
        self.assertEqual(success_count, 2)
        self.assertEqual(mock_run_daily.call_count, 3)

class TestPodcastSystemIntegration(unittest.TestCase):
    """Integration tests for the complete podcast system."""
    
    @patch('daily_podcast_generator.DynamoDBManager')
    @patch('daily_podcast_generator.openai.OpenAI')
    def test_end_to_end_podcast_generation(self, mock_openai_class, mock_db_class):
        """Test complete podcast generation workflow."""
        # Mock database
        mock_db = Mock()
        mock_db.get_articles_by_date.return_value = [
            {
                'id': 'test_article',
                'title': 'Test Article',
                'score': 100,
                'comment_count': 20
            }
        ]
        mock_db.get_comments.return_value = [
            {
                'id': 'comment_1',
                'text': 'Great article with detailed analysis.',
                'score': 10
            }
        ]
        mock_db_class.return_value = mock_db
        
        # Mock OpenAI
        mock_openai = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Generated podcast script content.'
        mock_openai.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_openai
        
        # Mock environment
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            generator = DailyPodcastGenerator()
            generator.db = mock_db
            generator.openai_client = mock_openai
            generator.has_openai = True
            generator.has_elevenlabs = False  # Skip audio generation
            
            episode = generator.generate_daily_episode('2024-01-15')
            
            self.assertIsNotNone(episode)
            self.assertEqual(episode.date, '2024-01-15')
            self.assertIn('Generated podcast script', episode.script)
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test with no OpenAI key
        with patch.dict(os.environ, {}, clear=True):
            generator = DailyPodcastGenerator()
            self.assertFalse(generator.has_openai)
        
        # Test with no ElevenLabs key
        self.assertFalse(generator.has_elevenlabs)

def run_tests():
    """Run all tests."""
    print("🧪 Running Daily Podcast Generator Tests")
    print("=" * 50)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")
    
    return success

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
