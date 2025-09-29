#!/usr/bin/env python3
"""
Test script for Docker Whisper MCP Server with parallel processing
"""

import asyncio
import time
from pathlib import Path


async def test_parallel_processing():
    """Test parallel batch transcription functionality."""

    # Add the src directory to Python path
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "src"))

    from config import ConfigurationManager  # noqa: E402
    from whisper_runner import WhisperRunner  # noqa: E402
    from models import BatchTranscriptionConfig  # noqa: E402

    print("🧪 Testing parallel processing in Whisper MCP Server")

    # Initialize components
    config = ConfigurationManager()
    runner = WhisperRunner(config)

    print("📋 Configuration:")
    print(f"  GPU Enabled: {config.use_gpu}")
    print(f"  Device: {config.device}")
    print(f"  Parallel Processing: {config.parallel_processing_enabled}")
    print(f"  Max Concurrent: {config.max_concurrent_transcriptions}")

    # Check if model can be loaded
    if not runner._ensure_model_loaded():
        print("❌ Cannot load Whisper model. Check Hugging Face token.")
        return

    print("✅ Model loaded successfully")

    # Create test audio files (using existing files)
    audio_dir = Path("audio")
    if not audio_dir.exists():
        print("⚠️  No audio directory found. Creating sample structure...")
        audio_dir.mkdir(exist_ok=True)
        print("📁 Created audio/ directory. Place your test audio files there.")
        return

    audio_files = (list(audio_dir.glob("*.wav")) +
                   list(audio_dir.glob("*.mp3")))
    if not audio_files:
        print("⚠️  No audio files found in audio/ directory.")
        print("💡 Place some .wav or .mp3 files in the audio/ directory")
        print("   to test.")
        return

    # Limit to first 5 files for testing
    test_files = [str(f) for f in audio_files[:5]]
    print(f"🎵 Testing with {len(test_files)} audio files:")
    for i, f in enumerate(test_files, 1):
        print(f"  {i}. {Path(f).name}")

    # Test batch transcription
    print("\n🚀 Starting batch transcription test...")
    batch_config = BatchTranscriptionConfig(
        audio_files=test_files,
        language=None,
        response_format="verbose_json",  # Use verbose_json for timestamps
        temperature=0.0
    )

    start_time = time.time()
    result = await runner.batch_transcribe(batch_config)
    end_time = time.time()

    processing_time = end_time - start_time
    print("\n📊 Results:")
    print(f"  Total files: {result.total_files}")
    print(f"  Successful: {result.successful_transcriptions}")
    print(f"  Failed: {result.failed_transcriptions}")
    print(f"  Processing time: {processing_time:.2f}s")
    print(f"  Overall success: {result.success}")

    if result.results:
        print("\n📝 Sample results:")
        for i, transcription_result in enumerate(result.results[:3]):
            status = "✅" if transcription_result.success else "❌"
            print(f"  File {i+1}: {status}")
            if transcription_result.success:
                text_len = len(transcription_result.text)
                if text_len > 100:
                    text_preview = transcription_result.text[:97] + "..."
                else:
                    text_preview = transcription_result.text
                print(f"    Text: \"{text_preview}\"")
            else:
                print(f"    Error: {transcription_result.error_message}")

    print("\n🎉 Parallel processing test completed!")


if __name__ == "__main__":
    asyncio.run(test_parallel_processing())