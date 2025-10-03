"""
Test Actual Whisper Transcription
==================================
Test a real transcription to verify the Whisper model works.
"""
import asyncio
import sys
from pathlib import Path

# Add whisper-server to path
sys.path.insert(0, str(Path(__file__).parent / "whisper-server" / "src"))


async def test_actual_transcription():
    """Test actual audio transcription"""
    from server import WhisperMCPServer
    
    project_root = Path(__file__).parent / "whisper-server"
    audio_file = project_root / "audio" / "test_real.wav"
    
    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return False
    
    print("🎙️ Testing Actual Whisper Transcription\n")
    print(f"📄 File: {audio_file.name}")
    print(f"📊 Size: {audio_file.stat().st_size / 1024:.1f} KB\n")
    
    # Initialize server
    try:
        server = WhisperMCPServer(project_root)
        print("✅ Server initialized\n")
    except Exception as e:
        print(f"❌ Server initialization failed: {e}")
        return False
    
    # Test transcription
    print("🔄 Starting transcription (this may take a minute)...")
    print("   Loading Whisper model...")
    
    try:
        result = await server.mcp_handler.call_tool(
            "whisper-transcribe",
            {
                "audio_file": str(audio_file),
                "language": "en",
                "response_format": "json"
            }
        )
        
        print("✅ Transcription completed!\n")
        print("=" * 60)
        print("RESULT:")
        print("=" * 60)
        
        # Result is a list of TextContent objects
        if result and len(result) > 0:
            text = result[0].text
            print(text)
            print()
            
            # Check if it's an error
            if "Error" in text or "❌" in text:
                print("⚠️  Transcription returned an error")
                return False
            else:
                print("✅ Transcription successful!")
                return True
        else:
            print("⚠️  No result returned")
            return False
            
    except Exception as e:
        print(f"\n❌ Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("=" * 60)
    print("WHISPER TRANSCRIPTION TEST")
    print("=" * 60)
    print()
    
    try:
        success = await test_actual_transcription()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ WHISPER MCP SERVER IS FULLY FUNCTIONAL!")
            print("=" * 60)
            print("\nThe server is ready to use with VS Code Copilot.")
            print("Just reload VS Code and start asking for transcriptions!")
        else:
            print("\n" + "=" * 60)
            print("⚠️  TRANSCRIPTION TEST HAD ISSUES")
            print("=" * 60)
            print("\nCheck the errors above for details.")
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
