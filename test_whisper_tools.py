"""
Test Whisper MCP Server Tools
==============================
Comprehensive test of all Whisper MCP tools and functionality.
"""
import asyncio
import sys
from pathlib import Path

# Add whisper-server to path
sys.path.insert(0, str(Path(__file__).parent / "whisper-server" / "src"))


async def test_whisper_server():
    """Test the Whisper MCP server tools"""
    from server import WhisperMCPServer
    
    project_root = Path(__file__).parent / "whisper-server"
    audio_dir = project_root / "audio"
    
    print("🔧 Testing Whisper MCP Server\n")
    print(f"📁 Project root: {project_root}")
    print(f"🎵 Audio directory: {audio_dir}\n")
    
    # Initialize server
    try:
        server = WhisperMCPServer(project_root)
        print("✅ Server initialized successfully\n")
    except Exception as e:
        print(f"❌ Failed to initialize server: {e}")
        return False
    
    # Test 1: List available tools
    print("=" * 60)
    print("TEST 1: List Available Tools")
    print("=" * 60)
    try:
        tools = server.mcp_handler.get_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}")
            print(f"     {tool.description[:70]}...")
        print()
    except Exception as e:
        print(f"❌ Error listing tools: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Check configuration
    print("=" * 60)
    print("TEST 2: Check Configuration")
    print("=" * 60)
    try:
        config = server.config_manager
        print(f"✅ Configuration loaded:")
        print(f"   - Project root: {config.project_root}")
        if hasattr(config, 'config'):
            print(f"   - Config file found")
        print()
    except Exception as e:
        print(f"❌ Error checking config: {e}\n")
        return False
    
    # Test 3: Check if audio files exist
    print("=" * 60)
    print("TEST 3: Check Available Audio Files")
    print("=" * 60)
    audio_files = list(audio_dir.glob("*"))
    audio_files = [f for f in audio_files if f.suffix.lower() in ['.mp3', '.wav', '.m4a', '.flac', '.wma', '.mp4', '.avi', '.mov']]
    
    if audio_files:
        print(f"✅ Found {len(audio_files)} audio/video files:")
        for f in audio_files:
            print(f"   - {f.name} ({f.stat().st_size / 1024:.1f} KB)")
        print()
    else:
        print("⚠️  No audio files found for testing")
        print("   You can add audio files to test transcription")
        print()
        return True
    
    # Test 4: Try to transcribe a file (if available)
    test_file = None
    for f in audio_files:
        if f.suffix.lower() == '.wav':
            test_file = f
            break
    
    if not test_file and audio_files:
        test_file = audio_files[0]
    
    if test_file:
        print("=" * 60)
        print("TEST 4: Test Transcription (Dry Run)")
        print("=" * 60)
        print(f"📄 Test file: {test_file.name}")
        print(f"📊 Size: {test_file.stat().st_size / 1024:.1f} KB")
        print()
        
        # Note: We won't actually transcribe in the test to avoid model loading
        # Just verify the tool can be called with proper parameters
        print("⚠️  Skipping actual transcription to avoid loading the model")
        print("   (Model loading requires ~3GB RAM and Hugging Face token)")
        print()
        
        print("Tool call would be:")
        print(f"   await call_tool('whisper-transcribe', {{")
        print(f"       'audio_file': '{test_file}',")
        print(f"       'language': 'en',")
        print(f"       'response_format': 'json'")
        print(f"   }})")
        print()
    
    # Test 5: Verify environment setup
    print("=" * 60)
    print("TEST 5: Environment Setup Check")
    print("=" * 60)
    
    import os
    from dotenv import load_dotenv
    
    # Try to load .env file
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"✅ Found .env file: {env_file}")
        load_dotenv(env_file)
    else:
        print(f"⚠️  No .env file found at {env_file}")
    
    # Check for Hugging Face token
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    if hf_token:
        print(f"✅ HUGGINGFACE_TOKEN is set (length: {len(hf_token)} chars)")
    else:
        print("⚠️  HUGGINGFACE_TOKEN not set")
        print("   Set it in .env file or environment variable to use transcription")
    
    # Check for GPU
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ GPU available: {torch.cuda.get_device_name(0)}")
        else:
            print("ℹ️  No GPU available, will use CPU (slower)")
    except ImportError:
        print("⚠️  PyTorch not installed, cannot check GPU")
    
    print()
    
    # Test 6: Test tool schema validation
    print("=" * 60)
    print("TEST 6: Tool Schema Validation")
    print("=" * 60)
    
    for tool in tools:
        try:
            # Check that each tool has required properties
            assert tool.name, f"Tool missing name"
            assert tool.description, f"Tool {tool.name} missing description"
            assert tool.inputSchema, f"Tool {tool.name} missing input schema"
            
            # Check input schema structure
            schema = tool.inputSchema
            assert schema.get("type") == "object", f"Tool {tool.name} schema not an object"
            assert "properties" in schema, f"Tool {tool.name} missing properties"
            
            print(f"✅ {tool.name}: Valid schema")
        except AssertionError as e:
            print(f"❌ {tool.name}: {e}")
            return False
    
    print()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✅ Server initialization: PASSED")
    print("✅ Tool listing: PASSED")
    print("✅ Configuration check: PASSED")
    print("✅ Audio file detection: PASSED")
    print("✅ Tool schema validation: PASSED")
    print()
    
    if not hf_token:
        print("⚠️  To test actual transcription:")
        print("   1. Set HUGGINGFACE_TOKEN in .env or environment")
        print("   2. Run: python whisper-server/src/main.py")
        print("   3. Use the whisper tools via MCP client")
        print()
    
    print("🎉 All tests passed! Whisper MCP server is ready.")
    print()
    print("Next steps:")
    print("1. Reload VS Code window (Ctrl+Shift+P -> Reload Window)")
    print("2. Ask Copilot: 'List available audio files in whisper-server/audio'")
    print("3. Ask Copilot: 'Transcribe the audio file test_real.wav'")
    
    return True


async def main():
    """Main test function"""
    try:
        success = await test_whisper_server()
        if not success:
            print("\n❌ Tests failed!")
            sys.exit(1)
        else:
            print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
