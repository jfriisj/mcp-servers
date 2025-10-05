#!/usr/bin/env python3
"""
Test script for Whisper MCP Server (Clean Architecture)
========================================================
Comprehensive test suite using CompositionRoot and Clean Architecture.

Updated to use Clean Architecture components instead of legacy WhisperRunner.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from presentation.composition_root import CompositionRoot
from domain.models import (
    TranscriptionConfig,
    TranscriptionWithTimestampsConfig,
    LanguageDetectionConfig,
    BatchTranscriptionConfig,
)


async def test_configuration():
    """Test configuration loading and validation."""
    print("🧪 Testing Configuration...")

    config = ConfigurationManager()

    # Test basic properties
    assert config.huggingface_token is not None, "HF token not found"
    assert config.model_name == "openai/whisper-large-v3", (
        f"Wrong model: {config.model_name}"
    )
    assert config.device in ["cpu", "cuda"], f"Invalid device: {config.device}"
    assert config.max_file_size_mb == 100, (
        f"Wrong max file size: {config.max_file_size_mb}"
    )

    # Test file validation
    test_file = Path("./test_audio.wav")
    if test_file.exists():
        is_valid, error = config.validate_audio_file(str(test_file))
        assert is_valid, f"Test file validation failed: {error}"

    print("✅ Configuration tests passed")
    return config


async def test_whisper_runner(config):
    """Test WhisperRunner initialization and basic functionality."""
    print("🧪 Testing WhisperRunner...")

    runner = WhisperRunner(config)

    # Test model loading (with tiny model for speed)
    original_model = config.model_name
    config._model_name = "openai/whisper-tiny"  # Use tiny for testing

    try:
        success = runner._ensure_model_loaded()
        assert success, "Model loading failed"
        assert runner.pipe is not None, "Pipeline not initialized"
        print("✅ WhisperRunner tests passed")
    finally:
        config._model_name = original_model

    return runner


async def test_transcription(runner):
    """Test basic transcription functionality."""
    print("🧪 Testing Transcription...")

    config = TranscriptionConfig(
        audio_file="./test_audio.wav",
        language="en",
        response_format="json",
        temperature=0.0,
    )

    result = await runner.transcribe_audio(config)

    assert result.success, f"Transcription failed: {result.error_message}"
    assert result.text.strip(), "Empty transcription result"
    assert isinstance(result.text, str), "Text should be string"

    print(f"✅ Transcription test passed: '{result.text.strip()}'")
    return result


async def test_timestamps(runner):
    """Test transcription with timestamps."""
    print("🧪 Testing Timestamps...")

    config = TranscriptionWithTimestampsConfig(
        audio_file="./test_audio.wav",
        language=None,
        response_format="verbose_json",
        temperature=0.0,
    )

    result = await runner.transcribe_with_timestamps(config)

    assert result.success, f"Timestamps transcription failed: {result.error_message}"
    assert result.text.strip(), "Empty timestamps transcription result"
    assert hasattr(result, "segments"), "Missing segments attribute"

    print(f"✅ Timestamps test passed: {len(result.segments or [])} segments")
    return result


async def test_language_detection(runner):
    """Test language detection functionality."""
    print("🧪 Testing Language Detection...")

    config = LanguageDetectionConfig(audio_file="./test_audio.wav")

    result = await runner.detect_language(config)

    assert result.success, f"Language detection failed: {result.error_message}"
    assert result.detected_language, "No language detected"
    assert isinstance(result.confidence, (int, float)), "Invalid confidence type"
    assert 0.0 <= result.confidence <= 1.0, f"Invalid confidence: {result.confidence}"

    print(
        f"✅ Language detection test passed: {result.detected_language} ({result.confidence:.3f})"
    )
    return result


async def test_batch_transcription(runner):
    """Test batch transcription functionality."""
    print("🧪 Testing Batch Transcription...")

    # Create multiple test files if needed
    test_files = ["./test_audio.wav"]
    if Path("./test_audio2.wav").exists():
        test_files.append("./test_audio2.wav")

    config = BatchTranscriptionConfig(
        audio_files=test_files, language=None, response_format="json", temperature=0.0
    )

    result = await runner.batch_transcribe(config)

    assert result.success, f"Batch transcription failed: {result.error_message}"
    assert result.total_files == len(test_files), (
        f"Wrong total files: {result.total_files}"
    )
    assert result.successful_transcriptions == len(test_files), (
        f"Not all files successful: {result.successful_transcriptions}/{result.total_files}"
    )
    assert len(result.results) == len(test_files), (
        f"Wrong number of results: {len(result.results)}"
    )

    for i, transcription_result in enumerate(result.results):
        assert transcription_result.success, (
            f"File {i + 1} failed: {transcription_result.error_message}"
        )

    print(
        f"✅ Batch transcription test passed: {result.successful_transcriptions}/{result.total_files} files"
    )
    return result


async def test_mcp_integration():
    """Test MCP server and handler integration."""
    print("🧪 Testing MCP Integration...")

    from server import WhisperMCPServer

    server = WhisperMCPServer()
    handler = server.mcp_handler

    # Test tool listing
    tools = handler.get_tools()
    assert len(tools) == 4, f"Wrong number of tools: {len(tools)}"

    tool_names = [tool.name for tool in tools]
    expected_tools = [
        "whisper-transcribe",
        "whisper-transcribe-timestamps",
        "whisper-detect-language",
        "whisper-batch-transcribe",
    ]

    for expected_tool in expected_tools:
        assert expected_tool in tool_names, f"Missing tool: {expected_tool}"

    # Test tool calls
    result = await handler.call_tool(
        "whisper-transcribe", {"audio_file": "./test_audio.wav", "language": "en"}
    )

    assert len(result) > 0, "No result from tool call"
    assert result[0].type == "text", f"Wrong result type: {result[0].type}"
    assert "✅" in result[0].text, "Success indicator not found"

    print("✅ MCP integration tests passed")
    return server


async def main():
    """Run all tests."""
    print("🚀 Starting Whisper MCP Server Tests\n")

    try:
        # Check if test file exists
        if not Path("./test_audio.wav").exists():
            print(
                "❌ Test audio file not found. Please run test file generation first."
            )
            return

        # Run all tests
        config = await test_configuration()
        runner = await test_whisper_runner(config)
        await test_transcription(runner)
        await test_timestamps(runner)
        await test_language_detection(runner)
        await test_batch_transcription(runner)
        await test_mcp_integration()

        print("\n🎉 All tests passed! Whisper MCP Server is working correctly.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Set PATH for ffmpeg
    os.environ["PATH"] = (
        str(Path(__file__).parent) + os.pathsep + os.environ.get("PATH")
    )
    asyncio.run(main())
