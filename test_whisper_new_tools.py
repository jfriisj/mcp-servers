"""
Test the new Whisper MCP server tools
"""
import asyncio
import sys
from pathlib import Path

# Add whisper-server to path
sys.path.insert(0, str(Path(__file__).parent / "whisper-server" / "src"))

from mcp_handler import MCPHandler


class MockWhisperRunner:
    """Mock whisper runner for testing"""
    def __init__(self):
        self.model_name = "openai/whisper-large-v3"
        self.device = "cpu"
        self.compute_type = "default"


async def test_model_info():
    """Test the whisper-model-info tool"""
    print("\n" + "=" * 60)
    print("Testing whisper-model-info")
    print("=" * 60)
    
    handler = MCPHandler(MockWhisperRunner())
    
    result = await handler.call_tool("whisper-model-info", {})
    print(result[0].text)


async def test_audio_info():
    """Test the whisper-audio-info tool"""
    print("\n" + "=" * 60)
    print("Testing whisper-audio-info")
    print("=" * 60)
    
    handler = MCPHandler(MockWhisperRunner())
    
    # Test with an existing audio file
    audio_file = str(Path(__file__).parent / "whisper-server" / "audio" / "test1.mp3")
    
    result = await handler.call_tool(
        "whisper-audio-info",
        {"audio_file": audio_file}
    )
    print(result[0].text)


async def test_get_config():
    """Test the whisper-get-config tool"""
    print("\n" + "=" * 60)
    print("Testing whisper-get-config")
    print("=" * 60)
    
    handler = MCPHandler(MockWhisperRunner())
    
    result = await handler.call_tool("whisper-get-config", {})
    print(result[0].text)


async def test_tools_registered():
    """Test that new tools are registered"""
    print("\n" + "=" * 60)
    print("Testing tool registration")
    print("=" * 60)
    
    handler = MCPHandler(MockWhisperRunner())
    tools = handler.get_tools()
    
    tool_names = [tool.name if hasattr(tool, 'name') else tool['name'] for tool in tools]
    
    print("Registered tools:")
    for name in tool_names:
        print(f"  • {name}")
    
    # Check for new tools
    new_tools = ['whisper-model-info', 'whisper-audio-info', 'whisper-get-config']
    print(f"\nNew tools check:")
    for tool in new_tools:
        status = "✅" if tool in tool_names else "❌"
        print(f"  {status} {tool}")


async def main():
    """Run all tests"""
    print("Testing new Whisper MCP server tools...")
    
    try:
        await test_tools_registered()
        await test_model_info()
        await test_audio_info()
        await test_get_config()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
