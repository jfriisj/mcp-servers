#!/usr/bin/env python3
"""
Test script to verify Whisper transcription functionality in Docker container.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, "/app/src")

from config import ConfigurationManager
from whisper_runner import WhisperRunner


async def test_transcription():
    """Test actual transcription functionality."""
    print("🎵 Testing Whisper transcription functionality...")

    try:
        # Initialize configuration and runner
        config_manager = ConfigurationManager(Path("/app"))
        runner = WhisperRunner(config_manager)

        # Test with a short audio file
        test_file = Path("/app/audio/test_short.wav")
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return

        print(f"📁 Testing with file: {test_file}")
        print(f"📊 File size: {test_file.stat().st_size} bytes")

        # Perform transcription
        print("🎯 Starting transcription...")
        result = await runner.transcribe_audio(str(test_file))

        print("✅ Transcription completed!")
        print(f"📝 Text length: {len(result.get('text', ''))} characters")
        print(f"🎯 Language: {result.get('language', 'unknown')}")
        text = result.get("text", "")
        if len(text) > 200:
            print(f'📄 Sample text: "{text[:200]}..."')
        else:
            print(f'📄 Sample text: "{text}"')

        print("🎉 Transcription test passed!")

    except Exception as e:
        print(f"❌ Transcription test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_transcription())
