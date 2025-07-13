"""
Simple test to verify ElevenLabs API key and connection
"""

import os
import pytest
from dotenv import load_dotenv

try:
    from elevenlabs.client import ElevenLabs
except Exception as e:  # pragma: no cover - optional dependency
    pytest.skip(f"elevenlabs not available: {e}", allow_module_level=True)

# Load environment variables
load_dotenv()


def test_api_key():
    """Test the ElevenLabs API key"""
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    print(f"API Key loaded: {api_key is not None}")

    if api_key:
        print(f"API Key format: {'sk_' in api_key}")
        print(f"API Key length: {len(api_key)}")

        try:
            client = ElevenLabs(api_key=api_key)
            print("Client created successfully")

            # Try a simple API call
            voices = client.voices.get_all()
            print(f"✅ API working! Found {len(voices.voices)} voices")

            # Show first few voices
            for voice in voices.voices[:3]:
                print(f"  - {voice.name} ({voice.voice_id})")

        except Exception as e:
            print(f"❌ API Error: {str(e)}")
    else:
        print("❌ No API key found")


if __name__ == "__main__":
    test_api_key()
