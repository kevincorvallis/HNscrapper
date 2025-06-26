"""
Mock TTS Generator for Development and Testing
Creates placeholder audio files and demonstrates the TTS interface
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockTTSGenerator:
    """Mock TTS generator for development and testing"""
    
    def __init__(self):
        """Initialize mock TTS generator"""
        # Audio output directory
        self.audio_dir = Path("audio_files")
        self.audio_dir.mkdir(exist_ok=True)
        
        logger.info("Mock TTS Generator initialized")
        
    def list_available_voices(self) -> list:
        """Return mock voice list"""
        return [
            {"id": "adam", "name": "Adam", "category": "premade", "description": "Friendly male voice"},
            {"id": "alice", "name": "Alice", "category": "premade", "description": "Professional female voice"},
            {"id": "brian", "name": "Brian", "category": "premade", "description": "Casual male voice"},
            {"id": "charlotte", "name": "Charlotte", "category": "premade", "description": "Warm female voice"},
            {"id": "daniel", "name": "Daniel", "category": "premade", "description": "Clear male voice"}
        ]
    
    def generate_speech(self, text: str, output_filename: str = None, voice_id: str = None) -> Optional[str]:
        """
        Generate a mock audio file with metadata about the speech
        """
        try:
            # Generate filename if not provided
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"podcast_{timestamp}"
            
            # Ensure .mp3 extension
            if not output_filename.endswith('.mp3'):
                output_filename += '.mp3'
            
            output_path = self.audio_dir / output_filename
            
            # Create mock metadata file
            metadata = {
                "text": text,
                "voice_id": voice_id or "adam",
                "character_count": len(text),
                "word_count": len(text.split()),
                "estimated_duration_minutes": self.estimate_duration(text),
                "generated_at": datetime.now().isoformat(),
                "mock_file": True,
                "note": "This is a mock audio file. Replace with real ElevenLabs TTS when API key is working."
            }
            
            # Write metadata as JSON (simulating audio file)
            with open(output_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Mock audio file created: {output_path}")
            logger.info(f"Text length: {len(text)} characters, estimated duration: {self.estimate_duration(text)} minutes")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error generating mock speech: {str(e)}")
            return None
    
    def generate_podcast_episode(self, podcast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a mock podcast episode"""
        try:
            # Extract script from podcast data
            script = podcast_data.get('script', '')
            if not script:
                logger.error("No script found in podcast data")
                return None
            
            # Generate filename based on podcast data
            date = podcast_data.get('date', datetime.now().strftime('%Y-%m-%d'))
            filename = f"hn_podcast_{date.replace('-', '_')}"
            
            # Generate mock audio
            audio_path = self.generate_speech(script, filename)
            if not audio_path:
                return None
            
            # Update podcast data with audio information
            podcast_data['audio_url'] = audio_path
            podcast_data['audio_generated_at'] = datetime.now().isoformat()
            podcast_data['audio_duration_estimate'] = self.estimate_duration(script)
            podcast_data['mock_audio'] = True
            
            return podcast_data
            
        except Exception as e:
            logger.error(f"Error generating mock podcast episode: {str(e)}")
            return None
    
    def estimate_duration(self, text: str) -> float:
        """Estimate audio duration based on text length"""
        word_count = len(text.split())
        minutes = word_count / 150  # Average speaking rate
        return round(minutes, 2)
    
    def get_character_count(self) -> Dict[str, int]:
        """Return mock character usage"""
        return {
            "characters_used": 1500,
            "character_limit": 10000,
            "can_extend_character_limit": True,
            "mock_data": True
        }

class RealTTSGenerator:
    """Real TTS generator using ElevenLabs API"""
    
    def __init__(self):
        """Initialize ElevenLabs client"""
        try:
            from elevenlabs.client import ElevenLabs
            
            self.api_key = os.environ.get('ELEVENLABS_API_KEY')
            if not self.api_key:
                raise ValueError("ELEVENLABS_API_KEY environment variable not set")
            
            self.client = ElevenLabs(api_key=self.api_key)
            
            # Test the connection
            self.client.voices.get_all()
            
            # Default voice settings
            self.voice_id = "pNInz6obpgDQGcFmaJgB"  # Adam voice
            self.voice_settings = {
                "stability": 0.5,
                "similarity_boost": 0.5,
                "style": 0.0,
                "use_speaker_boost": True
            }
            
            # Audio output directory
            self.audio_dir = Path("audio_files")
            self.audio_dir.mkdir(exist_ok=True)
            
            logger.info("Real TTS Generator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize real TTS generator: {str(e)}")
            raise
    
    def list_available_voices(self) -> list:
        """Get list of available voices from ElevenLabs"""
        try:
            response = self.client.voices.get_all()
            voice_list = []
            for voice in response.voices:
                voice_list.append({
                    "id": voice.voice_id,
                    "name": voice.name,
                    "category": getattr(voice, 'category', 'Unknown'),
                    "description": getattr(voice, 'description', 'No description')
                })
            return voice_list
        except Exception as e:
            logger.error(f"Error fetching voices: {str(e)}")
            return []
    
    def generate_speech(self, text: str, output_filename: str = None, voice_id: str = None) -> Optional[str]:
        """Generate real speech from text"""
        try:
            selected_voice = voice_id or self.voice_id
            
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"podcast_{timestamp}"
            
            if not output_filename.endswith('.mp3'):
                output_filename += '.mp3'
            
            output_path = self.audio_dir / output_filename
            
            logger.info(f"Generating real speech for {len(text)} characters using voice {selected_voice}")
            
            # Generate audio using ElevenLabs
            audio_response = self.client.text_to_speech.convert(
                voice_id=selected_voice,
                text=text,
                model_id="eleven_multilingual_v2",
                voice_settings=self.voice_settings
            )
            
            # Save to file
            with open(output_path, "wb") as f:
                for chunk in audio_response:
                    f.write(chunk)
            
            logger.info(f"Real audio saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error generating real speech: {str(e)}")
            return None
    
    def generate_podcast_episode(self, podcast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a real podcast episode"""
        try:
            script = podcast_data.get('script', '')
            if not script:
                logger.error("No script found in podcast data")
                return None
            
            date = podcast_data.get('date', datetime.now().strftime('%Y-%m-%d'))
            filename = f"hn_podcast_{date.replace('-', '_')}"
            
            audio_path = self.generate_speech(script, filename)
            if not audio_path:
                return None
            
            podcast_data['audio_url'] = audio_path
            podcast_data['audio_generated_at'] = datetime.now().isoformat()
            podcast_data['audio_duration_estimate'] = self.estimate_duration(script)
            podcast_data['mock_audio'] = False
            
            return podcast_data
            
        except Exception as e:
            logger.error(f"Error generating real podcast episode: {str(e)}")
            return None
    
    def estimate_duration(self, text: str) -> float:
        """Estimate audio duration based on text length"""
        word_count = len(text.split())
        minutes = word_count / 150
        return round(minutes, 2)
    
    def get_character_count(self) -> Dict[str, int]:
        """Get real character usage from ElevenLabs"""
        try:
            user_info = self.client.user.get()
            subscription = getattr(user_info, 'subscription', None)
            if subscription:
                return {
                    "characters_used": getattr(subscription, 'character_count', 0),
                    "character_limit": getattr(subscription, 'character_limit', 0),
                    "can_extend_character_limit": getattr(subscription, 'can_extend_character_limit', False)
                }
            else:
                return {"error": "No subscription information available"}
        except Exception as e:
            logger.error(f"Error getting character count: {str(e)}")
            return {}

def get_tts_generator():
    """
    Factory function to get the appropriate TTS generator
    Returns RealTTSGenerator if ElevenLabs API key works, otherwise MockTTSGenerator
    """
    try:
        # Try to create real TTS generator
        return RealTTSGenerator()
    except Exception as e:
        logger.warning(f"Cannot use real TTS generator: {str(e)}")
        logger.info("Using mock TTS generator for development")
        return MockTTSGenerator()

def main():
    """Test function to demonstrate TTS functionality"""
    try:
        # Get TTS generator (real or mock)
        tts = get_tts_generator()
        
        print(f"Using TTS generator: {type(tts).__name__}")
        
        # Get available voices
        print("Available voices:")
        voices = tts.list_available_voices()
        for voice in voices[:5]:  # Show first 5 voices
            print(f"  {voice['name']} ({voice['id']}) - {voice['category']}")
        
        # Get character usage
        usage = tts.get_character_count()
        if usage and not usage.get('error'):
            mock_note = " (mock data)" if usage.get('mock_data') else ""
            print(f"\nCharacter usage{mock_note}: {usage.get('characters_used', 'N/A')}/{usage.get('character_limit', 'N/A')}")
        
        # Test script
        test_script = """
        Welcome to today's Hacker News podcast. I'm your AI host, bringing you the most interesting discussions from the tech community.
        
        Today's top story discusses the future of artificial intelligence and its impact on software development. 
        The community had fascinating insights about the balance between automation and human creativity.
        
        This has been your Hacker News daily digest. Thank you for listening!
        """
        
        print(f"\nGenerating audio for {len(test_script)} characters...")
        
        # Generate audio
        audio_path = tts.generate_speech(test_script, "test_podcast")
        
        if audio_path:
            print(f"✅ Audio generated successfully: {audio_path}")
            print(f"Estimated duration: {tts.estimate_duration(test_script)} minutes")
            
            # Show file contents if it's a mock file
            if isinstance(tts, MockTTSGenerator):
                print("\n📄 Mock file contents:")
                with open(audio_path, 'r') as f:
                    mock_data = json.load(f)
                    print(f"  Character count: {mock_data['character_count']}")
                    print(f"  Word count: {mock_data['word_count']}")
                    print(f"  Duration estimate: {mock_data['estimated_duration_minutes']} minutes")
        else:
            print("❌ Failed to generate audio")
            
    except Exception as e:
        print(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()
