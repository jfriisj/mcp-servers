#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/app/src')

import asyncio
from whisper_runner import WhisperRunner
from config import ConfigurationManager
from models import TranscriptionConfig

async def main():
    try:
        print("Starting transcription...")
        config = ConfigurationManager()
        runner = WhisperRunner(config)

        trans_config = TranscriptionConfig(
            audio_file='/app/audio/test_short.wav',
            language='en',
            response_format='json',
            temperature=0.0
        )

        result = await runner.transcribe_audio(trans_config)

        if result.success:
            print("✅ Transcription successful!")
            print("Text:", result.text)
        else:
            print("❌ Transcription failed:", result.error_message)

    except Exception as e:
        print("❌ Error:", str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())