
import sys
sys.path.insert(0, '/app/src')
from config import ConfigurationManager
from whisper_runner import WhisperRunner
import asyncio

async def test():
    config = ConfigurationManager()
    runner = WhisperRunner(config)
    
    # Test file existence
    import os
    print('Files in /app/audio:', os.listdir('/app/audio'))
    
    # Test transcription
    from models import TranscriptionConfig
    result = await runner.transcribe_audio(TranscriptionConfig(audio_file='/app/audio/test1.mp3', language='en'))
    print('Result:', result)

if __name__ == '__main__':
    asyncio.run(test())

