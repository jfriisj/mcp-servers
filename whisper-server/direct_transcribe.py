#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config import ConfigurationManager
from whisper_runner import WhisperRunner
from models import TranscriptionConfig

async def main():
    try:
        print("🚀 Starting direct Whisper transcription...")

        # Initialize configuration
        config = ConfigurationManager()

        # Initialize Whisper runner
        runner = WhisperRunner(config)

        # Configure transcription
        trans_config = TranscriptionConfig(
            audio_file=str(Path('/app/audio/test_short.wav')),
            language='en',
            response_format='json',
            temperature=0.0
        )

        print(f"📝 Transcribing: {trans_config.audio_file}")

        # Run transcription
        result = await runner.transcribe_audio(trans_config)

        if result.success:
            print("✅ Transcription successful!")
            print("📄 Text:", repr(result.text))
            return result.text
        else:
            print("❌ Transcription failed:", result.error_message)
            return None

    except Exception as e:
        print("❌ Error:", str(e))
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(main())
    if result:
        print("\n" + "="*50)
        print("FINAL TRANSCRIPTION RESULT:")
        print(result)
        print("="*50)