"""
Text-to-Speech (TTS) Generator using ElevenLabs
Converts podcast scripts to MP3 audio files.
"""

import os
import json
import boto3
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
try:
    # For versions <1.0 use high-level generate/save helpers
    from elevenlabs import generate, save
    ELEVENLABS_MODERN = False
except Exception:  # pragma: no cover - fallback for newer versions
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_MODERN = True
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSGenerator:
    """Handles text-to-speech generation using ElevenLabs API"""
    
    def __init__(self):
        """Initialize ElevenLabs client"""
        self.api_key = os.environ.get('ELEVENLABS_API_KEY')
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable not set")
        
        if ELEVENLABS_MODERN:
            self.client = ElevenLabs(api_key=self.api_key)
        else:
            self.client = None
        
        # Default voice settings - Custom voice for Beryl narrator
        self.voice_id = "EaS81u0gurcdfMeSxlCk"  # Custom voice (Beryl)
        self.voice_settings = {
            "stability": 0.75,  # More stable for NPR-style delivery
            "similarity_boost": 0.85,
            "style": 0.15,  # Subtle style for professional news delivery
            "use_speaker_boost": True
        }
        
        # Audio output directory
        self.audio_dir = Path("audio_files")
        self.audio_dir.mkdir(exist_ok=True)
        
    def list_available_voices(self) -> list:
        """Get list of available voices from ElevenLabs"""
        try:
            if ELEVENLABS_MODERN:
                response = self.client.voices.get_all()
                raw_voices = response.voices
            else:
                from elevenlabs import voices
                raw_voices = voices().voices

            voice_list = []
            for voice in raw_voices:
                voice_list.append({
                    "id": getattr(voice, 'voice_id', getattr(voice, 'id', '')),
                    "name": getattr(voice, 'name', 'Unknown'),
                    "category": getattr(voice, 'category', 'Unknown'),
                    "description": getattr(voice, 'description', 'No description')
                })
            return voice_list
        except Exception as e:
            logger.error(f"Error fetching voices: {str(e)}")
            return []
    
    def generate_speech(self, text: str, output_filename: str = None, voice_id: str = None) -> Optional[str]:
        """
        Generate speech from text and save to MP3 file
        
        Args:
            text: Text to convert to speech
            output_filename: Optional custom filename (without extension)
            voice_id: Optional voice ID to use (defaults to class default)
            
        Returns:
            Path to generated MP3 file or None if failed
        """
        try:
            # Use provided voice_id or default
            selected_voice = voice_id or self.voice_id
            
            # Generate filename if not provided
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"podcast_{timestamp}"
            
            # Ensure .mp3 extension
            if not output_filename.endswith('.mp3'):
                output_filename += '.mp3'
            
            output_path = self.audio_dir / output_filename
            
            logger.info(f"Generating speech for {len(text)} characters using voice {selected_voice}")
            
            if ELEVENLABS_MODERN:
                audio_response = self.client.text_to_speech.convert(
                    voice_id=selected_voice,
                    text=text,
                    model_id="eleven_multilingual_v2",
                    voice_settings={
                        **self.voice_settings,
                        "stability": 0.6,
                        "similarity_boost": 0.8,
                        "style": 0.3,
                        "use_speaker_boost": True,
                    },
                    output_format="mp3_44100_128",
                )

                with open(output_path, "wb") as f:
                    for chunk in audio_response:
                        f.write(chunk)
            else:
                audio = generate(
                    text=text,
                    voice=selected_voice,
                    model="eleven_monolingual_v1",
                    api_key=self.api_key,
                    output_format="mp3_44100_128",
                )
                with open(output_path, "wb") as f:
                    f.write(audio)
            
            logger.info(f"Audio saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            return None
    
    def generate_podcast_episode(self, podcast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate a complete podcast episode from podcast data
        
        Args:
            podcast_data: Dictionary containing podcast script and metadata
            
        Returns:
            Updated podcast data with audio_url, or None if failed
        """
        try:
            # Extract script from podcast data
            script = podcast_data.get('script', '')
            if not script:
                logger.error("No script found in podcast data")
                return None
            
            # Generate filename based on podcast data
            date = podcast_data.get('date', datetime.now().strftime('%Y-%m-%d'))
            filename = f"hn_podcast_{date.replace('-', '_')}"
            
            # Generate audio
            audio_path = self.generate_speech(script, filename)
            if not audio_path:
                return None
            
            # Update podcast data with audio information
            podcast_data['audio_url'] = audio_path
            podcast_data['audio_generated_at'] = datetime.now().isoformat()
            podcast_data['audio_duration_estimate'] = self.estimate_duration(script)
            
            return podcast_data
            
        except Exception as e:
            logger.error(f"Error generating podcast episode: {str(e)}")
            return None
    
    def estimate_duration(self, text: str) -> float:
        """
        Estimate audio duration based on text length
        Rough estimate: ~150 words per minute for natural speech
        """
        word_count = len(text.split())
        minutes = word_count / 150  # Average speaking rate
        return round(minutes, 2)
    
    def get_character_count(self) -> Dict[str, int]:
        """
        Get character usage information from ElevenLabs
        (Useful for tracking usage against monthly limits)
        """
        try:
            if ELEVENLABS_MODERN:
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
            else:
                from elevenlabs import user
                sub = user.Subscription.from_api()
                return {
                    "characters_used": sub.character_count,
                    "character_limit": sub.character_limit,
                    "can_extend_character_limit": sub.can_extend_character_limit
                }
        except Exception as e:
            logger.error(f"Error getting character count: {str(e)}")
            return {}

def main():
    """Test function to demonstrate TTS functionality"""
    try:
        # Initialize TTS generator
        tts = TTSGenerator()
        
        # Get available voices
        print("Available voices:")
        voices = tts.list_available_voices()
        for voice in voices[:5]:  # Show first 5 voices
            print(f"  {voice['name']} ({voice['id']}) - {voice['category']}")
        
        # Get character usage
        usage = tts.get_character_count()
        if usage and not usage.get('error'):
            print(f"\nCharacter usage: {usage.get('characters_used', 'N/A')}/{usage.get('character_limit', 'N/A')}")
        
        # Test script
        test_script = """
        Welcome to today's Hacker News podcast. I'm your AI host, bringing you the most interesting discussions from the tech community.
        
        Today's top story discusses the future of artificial intelligence and its impact on software development. 
        The community had fascinating insights about the balance between automation and human creativity.
        
        This has been your Hacker News daily digest. Thank you for listening!
        """
        
        print(f"\nGenerating test audio for {len(test_script)} characters...")
        
        # Generate test audio
        audio_path = tts.generate_speech(test_script, "test_podcast")
        
        if audio_path:
            print(f"✅ Test audio generated successfully: {audio_path}")
            print(f"Estimated duration: {tts.estimate_duration(test_script)} minutes")
        else:
            print("❌ Failed to generate test audio")
            
    except Exception as e:
        print(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()
