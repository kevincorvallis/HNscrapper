import os
import unittest
from dotenv import load_dotenv
"""Basic ElevenLabs API check using unittest."""

load_dotenv()

@unittest.skipIf(not os.environ.get("ELEVENLABS_API_KEY"), "ELEVENLABS_API_KEY not set")
class TestElevenLabsClient(unittest.TestCase):
    """Tests for the ElevenLabs client."""

    def setUp(self):
        self.api_key = os.environ.get("ELEVENLABS_API_KEY")
        try:
            from elevenlabs.client import ElevenLabs
        except Exception as e:
            self.skipTest(f"ElevenLabs import failed: {e}")
        self.client = ElevenLabs(api_key=self.api_key)

    def test_client_creation_and_voices(self):
        """Client initializes and returns at least one available voice."""
        voices = self.client.voices.get_all()
        self.assertTrue(voices.voices, "No voices returned from API")


if __name__ == "__main__":
    unittest.main()
