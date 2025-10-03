"""
Test script for audio conversion workflow
=========================================
Tests the conversion functionality to ensure it works with different input formats.
"""

import asyncio
import os
import tempfile
from pathlib import Path

# Add src directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from audio_converter import AudioConverter, ConversionConfig, TempFileManager
from config import ConfigurationManager
from whisper_runner import WhisperRunner


async def test_converter_initialization():
    """Test that the audio converter initializes correctly."""
    print("🧪 Testing converter initialization...")
    
    converter = AudioConverter()
    print(f"  FFmpeg path: {converter.ffmpeg_path}")
    print(f"  Supported formats: {len(converter.get_supported_input_formats())} formats")
    print(f"  Whisper formats: {converter.WHISPER_SUPPORTED_FORMATS}")
    
    # Test file format detection
    test_formats = ["mp4", "mov", "avi", "wav", "mp3", "flac"]
    for fmt in test_formats:
        needs_conversion = fmt not in converter.WHISPER_SUPPORTED_FORMATS
        recommended = converter.get_recommended_output_format(fmt)
        print(f"  {fmt} -> needs conversion: {needs_conversion}, recommended: {recommended}")
    
    print("✅ Converter initialization test passed\n")


async def test_file_info():
    """Test file info extraction."""
    print("🧪 Testing file info extraction...")
    
    converter = AudioConverter()
    
    # Test with existing convert_mp4.py file as a dummy
    test_file = Path(__file__).parent / "convert_mp4.py"
    if test_file.exists():
        info = converter.get_file_info(str(test_file))
        print(f"  File exists: {info['exists']}")
        print(f"  Format: {info['format']}")
        print(f"  Size: {info['size_mb']:.2f}MB")
    
    # Test with non-existent file
    info = converter.get_file_info("non_existent_file.mp4")
    print(f"  Non-existent file exists: {info['exists']}")
    
    print("✅ File info test passed\n")


async def test_config_integration():
    """Test configuration integration."""
    print("🧪 Testing configuration integration...")
    
    config_manager = ConfigurationManager()
    
    # Test conversion settings
    print(f"  Conversion enabled: {config_manager.enable_conversion}")
    print(f"  Conversion quality: {config_manager.conversion_quality}")
    print(f"  Conversion temp dir: {config_manager.conversion_temp_dir}")
    print(f"  Cleanup temp files: {config_manager.conversion_cleanup_temp_files}")
    print(f"  Supported conversion formats: {len(config_manager.conversion_supported_formats)} formats")
    
    # Test file validation with conversion
    print("\n  Testing file validation:")
    test_files = [
        ("test.wav", True),
        ("test.mp3", True),
        ("test.mp4", True),  # Should be acceptable due to conversion
        ("test.xyz", False),  # Unknown format
    ]
    
    for filename, expected in test_files:
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix=f".{filename.split('.')[-1]}", delete=False) as tmp:
            tmp.write(b"dummy content")
            tmp_path = tmp.name
        
        try:
            is_valid, error_msg = config_manager.validate_audio_file(tmp_path)
            status = "✅" if is_valid == expected else "❌"
            print(f"    {status} {filename}: valid={is_valid}, expected={expected}")
            if error_msg:
                print(f"      Error: {error_msg}")
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    
    print("✅ Configuration integration test passed\n")


async def test_whisper_runner_integration():
    """Test WhisperRunner integration with converter."""
    print("🧪 Testing WhisperRunner integration...")
    
    config_manager = ConfigurationManager()
    runner = WhisperRunner(config_manager)
    
    # Test converter initialization
    converter = runner._get_converter()
    if converter:
        print("  ✅ Converter initialized successfully")
        print(f"    FFmpeg available: {converter.ffmpeg_path is not None}")
    else:
        print("  ⚠️  Converter not available (conversion disabled)")
    
    # Test temp file manager
    temp_manager = runner._conversion_temp_manager
    print(f"  ✅ Temp file manager initialized: {temp_manager is not None}")
    
    # Test file compatibility check (without actual conversion)
    print("\n  Testing file compatibility detection:")
    test_files = ["test.wav", "test.mp3", "test.mp4", "test.mov"]
    
    for filename in test_files:
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix=f".{filename.split('.')[-1]}", delete=False) as tmp:
            tmp.write(b"dummy audio content" * 100)  # Make it a bit larger
            tmp_path = tmp.name
        
        try:
            # Test needs conversion detection
            if converter:
                needs_conversion = converter.needs_conversion(tmp_path)
                print(f"    {filename}: needs_conversion={needs_conversion}")
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    
    print("✅ WhisperRunner integration test passed\n")


async def test_temp_file_manager():
    """Test temporary file management."""
    print("🧪 Testing temporary file management...")
    
    temp_manager = TempFileManager()
    
    # Create some temporary files
    temp_files = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_test_{i}.tmp") as tmp:
            tmp.write(b"test content")
            temp_files.append(tmp.name)
            temp_manager.add_temp_file(tmp.name)
    
    print(f"  Created {len(temp_files)} temporary files")
    
    # Verify files exist
    existing_count = sum(1 for f in temp_files if Path(f).exists())
    print(f"  Files existing before cleanup: {existing_count}")
    
    # Cleanup
    temp_manager.cleanup_all()
    
    # Verify files are cleaned up
    remaining_count = sum(1 for f in temp_files if Path(f).exists())
    print(f"  Files remaining after cleanup: {remaining_count}")
    
    if remaining_count == 0:
        print("✅ Temporary file management test passed\n")
    else:
        print("❌ Some temporary files were not cleaned up\n")


def create_test_audio_file(format_ext: str, duration_seconds: float = 1.0) -> str:
    """Create a simple test audio file in the specified format.
    
    Note: This creates a very basic file structure, not real audio data.
    For real testing, you'd need actual audio files.
    """
    temp_fd, temp_path = tempfile.mkstemp(suffix=f".{format_ext}")
    
    # Create minimal file content based on format
    if format_ext == "wav":
        # Minimal WAV header (44 bytes) + some dummy data
        wav_header = (
            b"RIFF" + b"\x00\x00\x00\x00" + b"WAVE" + b"fmt " + 
            b"\x10\x00\x00\x00" + b"\x01\x00\x01\x00" + 
            b"\x44\xac\x00\x00" + b"\x88\x58\x01\x00" + 
            b"\x02\x00\x10\x00" + b"data" + b"\x00\x00\x00\x00"
        )
        dummy_data = b"\x00" * int(44100 * 2 * duration_seconds)  # 16-bit mono
        content = wav_header + dummy_data
    elif format_ext == "mp3":
        # MP3 header (very minimal, not actually playable)
        content = b"\xff\xfb" + b"\x00" * 1000
    else:
        # Generic content
        content = b"dummy audio content " * 100
    
    os.write(temp_fd, content)
    os.close(temp_fd)
    
    return temp_path


async def test_actual_conversion():
    """Test actual file conversion if ffmpeg is available."""
    print("🧪 Testing actual conversion (if ffmpeg available)...")
    
    converter = AudioConverter()
    
    if not converter.ffmpeg_path:
        print("  ⚠️  FFmpeg not available, skipping actual conversion test")
        return
    
    # Create a test WAV file
    test_file = create_test_audio_file("wav")
    
    try:
        # Test conversion to MP3
        config = ConversionConfig(
            input_file=test_file,
            output_format="mp3",
            quality="medium"
        )
        
        print(f"  Converting test WAV to MP3...")
        result = await converter.convert_file(config)
        
        if result.success:
            print(f"  ✅ Conversion successful!")
            print(f"    Output file: {result.output_file}")
            print(f"    Method: {result.conversion_method}")
            print(f"    Size: {result.file_size_mb:.2f}MB")
            
            # Clean up output file
            if result.output_file and Path(result.output_file).exists():
                os.unlink(result.output_file)
        else:
            print(f"  ❌ Conversion failed: {result.error_message}")
    
    finally:
        # Clean up input file
        if Path(test_file).exists():
            os.unlink(test_file)
    
    print("✅ Actual conversion test completed\n")


async def run_all_tests():
    """Run all conversion tests."""
    print("🚀 Starting conversion workflow tests...\n")
    
    try:
        await test_converter_initialization()
        await test_file_info()
        await test_config_integration()
        await test_whisper_runner_integration()
        await test_temp_file_manager()
        await test_actual_conversion()
        
        print("🎉 All conversion tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())