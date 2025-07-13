#!/usr/bin/env python3
"""
Test NPR-style script generation and TTS with custom voice
"""

import os
import pytest

try:
    from tts_generator import TTSGenerator
except Exception as e:  # pragma: no cover - optional dependency
    pytest.skip(f"elevenlabs not available: {e}", allow_module_level=True)


def test_npr_style_podcast():
    """Test the NPR-style podcast generation with Beryl."""

    # Sample NPR-style script with Beryl
    npr_script = """Good morning, I'm Beryl, and this is your daily tech briefing. Today we're examining three significant developments that are shaping the technology landscape.

Our top story: Apple's new AI integration reaches millions of devices worldwide. This development from Apple's headquarters highlights the company's commitment to bringing artificial intelligence capabilities directly to consumer devices. The announcement signals a major shift in how personal technology will operate, with implications for privacy, productivity, and user interaction.

In other technology news: Open source project gains unprecedented enterprise adoption. This story from the development community demonstrates the growing trust businesses place in collaborative software development. The trend suggests a fundamental change in how corporations approach technology infrastructure and innovation.

And finally: Quantum computing breakthrough promises faster encryption methods. Researchers have achieved a significant milestone that could revolutionize data security across industries. The advancement represents years of scientific collaboration and brings practical quantum applications closer to reality.

That's your technology briefing for today. I'm Beryl. These three stories reflect the ongoing evolution of our digital world. We'll return tomorrow with more insights from the technology sector."""

    print("🎙️ Testing NPR-style Podcast Generation")
    print("=" * 50)
    print(f"📝 Script length: {len(npr_script.split())} words")
    print(f"🎯 Estimated duration: ~{len(npr_script.split()) / 180 * 60:.1f} seconds")

    # Test TTS generation
    try:
        tts = TTSGenerator()
        print(f"✅ TTS initialized with voice: {tts.voice_id}")

        print("🎵 Generating NPR-style audio...")
        audio_path = tts.generate_speech(
            text=npr_script, output_filename="beryl_npr_test.mp3"
        )

        if audio_path:
            print(f"✅ NPR-style audio generated: {audio_path}")
            print(
                f"🎧 Your custom voice Beryl is now ready for NPR-style tech briefings!"
            )
        else:
            print("❌ Audio generation failed")

    except Exception as e:
        print(f"❌ TTS test failed: {e}")


if __name__ == "__main__":
    test_npr_style_podcast()
