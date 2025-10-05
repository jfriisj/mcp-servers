#!/usr/bin/env python3
"""
Docker MCP Test Script for Whisper Server (Clean Architecture)
===============================================================
Tests MCP tools functionality when running in Docker container.

This script can be run:
1. Inside the Docker container to test MCP tools
2. From the host to test Docker container via API
3. As a standalone verification of MCP protocol
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_mcp_server_initialization():
    """Test MCP server can be initialized in Docker environment."""
    print("🧪 Test 1: MCP Server Initialization")
    print("=" * 60)
    
    try:
        from server import WhisperMCPServer
        from presentation.composition_root import CompositionRoot
        
        # Initialize server
        server = WhisperMCPServer()
        
        # Verify composition root
        assert server.composition_root is not None, "CompositionRoot not initialized"
        assert server.mcp_handler is not None, "MCPHandler not initialized"
        
        print("✅ MCP Server initialized successfully")
        print(f"   - CompositionRoot: OK")
        print(f"   - MCPHandler: OK")
        print(f"   - Server instance: {type(server).__name__}")
        
        return server
        
    except Exception as e:
        print(f"❌ Server initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_mcp_tools_listing(server):
    """Test MCP tools can be listed."""
    print("\n🧪 Test 2: MCP Tools Listing")
    print("=" * 60)
    
    try:
        handler = server.mcp_handler
        tools = handler.get_tools()
        
        print(f"✅ Found {len(tools)} MCP tools:")
        
        expected_tools = {
            "whisper-transcribe": "Basic audio transcription",
            "whisper-transcribe-timestamps": "Transcription with timestamps",
            "whisper-transcribe-file-content": "Transcribe base64 file content",
            "whisper-detect-language": "Language detection",
            "whisper-batch-transcribe": "Batch transcription",
            "whisper-convert-audio": "Audio format conversion",
            "whisper-model-info": "Model information",
            "whisper-get-config": "Configuration details",
            "whisper-audio-info": "Audio file metadata",
        }
        
        found_tools = {}
        for tool in tools:
            found_tools[tool.name] = tool.description
            status = "✅" if tool.name in expected_tools else "⚠️"
            print(f"   {status} {tool.name}")
            print(f"      Description: {tool.description[:60]}...")
        
        # Check for missing tools
        missing = set(expected_tools.keys()) - set(found_tools.keys())
        if missing:
            print(f"\n⚠️  Missing expected tools: {missing}")
        
        # Check for extra tools
        extra = set(found_tools.keys()) - set(expected_tools.keys())
        if extra:
            print(f"\n📌 Extra tools found: {extra}")
        
        return tools
        
    except Exception as e:
        print(f"❌ Tools listing failed: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_mcp_tool_schemas(tools):
    """Test MCP tool input schemas are valid."""
    print("\n🧪 Test 3: MCP Tool Schemas")
    print("=" * 60)
    
    try:
        for tool in tools:
            schema = tool.inputSchema
            
            # Verify schema structure
            assert "type" in schema, f"Missing 'type' in {tool.name} schema"
            assert schema["type"] == "object", f"Invalid type in {tool.name} schema"
            
            if "properties" in schema:
                prop_count = len(schema["properties"])
                required_count = len(schema.get("required", []))
                print(f"✅ {tool.name}")
                print(f"   - Properties: {prop_count}")
                print(f"   - Required: {required_count}")
            else:
                print(f"⚠️  {tool.name} has no properties defined")
        
        print(f"\n✅ All {len(tools)} tool schemas are valid")
        return True
        
    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mcp_model_info_tool(server):
    """Test the model info MCP tool."""
    print("\n🧪 Test 4: MCP Tool - whisper-model-info")
    print("=" * 60)
    
    try:
        handler = server.mcp_handler
        
        # Call the model info tool
        result = await handler.call_tool("whisper-model-info", {})
        
        assert len(result) > 0, "No result returned"
        assert result[0].type == "text", "Result is not text type"
        
        text = result[0].text
        print("✅ Model info retrieved:")
        
        # Parse response (expecting JSON or formatted text)
        if "Model:" in text or "model" in text.lower():
            lines = text.split('\n')
            for line in lines[:10]:  # Show first 10 lines
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"   {text[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Model info tool failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mcp_config_tool(server):
    """Test the configuration MCP tool."""
    print("\n🧪 Test 5: MCP Tool - whisper-get-config")
    print("=" * 60)
    
    try:
        handler = server.mcp_handler
        
        # Call the config tool
        result = await handler.call_tool("whisper-get-config", {})
        
        assert len(result) > 0, "No result returned"
        assert result[0].type == "text", "Result is not text type"
        
        text = result[0].text
        print("✅ Configuration retrieved:")
        
        # Check for key config elements
        config_keys = ["whisper", "server", "segmentation", "conversion"]
        for key in config_keys:
            if key in text.lower():
                print(f"   ✅ Contains '{key}' configuration")
        
        return True
        
    except Exception as e:
        print(f"❌ Config tool failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mcp_audio_conversion_tool(server):
    """Test the audio conversion MCP tool (without actual file)."""
    print("\n🧪 Test 6: MCP Tool - whisper-convert-audio (schema test)")
    print("=" * 60)
    
    try:
        handler = server.mcp_handler
        
        # Find the convert tool
        tools = handler.get_tools()
        convert_tool = next(
            (t for t in tools if t.name == "whisper-convert-audio"),
            None
        )
        
        if not convert_tool:
            print("⚠️  Convert audio tool not found")
            return False
        
        # Verify schema
        schema = convert_tool.inputSchema
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        
        print(f"✅ Tool schema verified:")
        print(f"   - Required parameters: {required}")
        print(f"   - Available parameters: {list(properties.keys())}")
        
        # Expected parameters
        expected_params = ["input_file", "output_format"]
        for param in expected_params:
            if param in properties:
                print(f"   ✅ Parameter '{param}' defined")
            else:
                print(f"   ⚠️  Parameter '{param}' missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Audio conversion schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_docker_environment():
    """Test Docker-specific environment variables and setup."""
    print("\n🧪 Test 7: Docker Environment")
    print("=" * 60)
    
    env_vars = {
        "USE_GPU": os.getenv("USE_GPU", "Not set"),
        "CUDA_VISIBLE_DEVICES": os.getenv("CUDA_VISIBLE_DEVICES", "Not set"),
        "HF_HOME": os.getenv("HF_HOME", "Not set"),
        "HUGGINGFACE_TOKEN": "***" if os.getenv("HUGGINGFACE_TOKEN") else "Not set",
        "HF_TOKEN": "***" if os.getenv("HF_TOKEN") else "Not set",
        "ENABLE_PARALLEL_PROCESSING": os.getenv("ENABLE_PARALLEL_PROCESSING", "Not set"),
        "MAX_CONCURRENT_TRANSCRIPTIONS": os.getenv("MAX_CONCURRENT_TRANSCRIPTIONS", "Not set"),
    }
    
    print("Environment variables:")
    for key, value in env_vars.items():
        status = "✅" if value != "Not set" else "⚠️"
        print(f"   {status} {key}: {value}")
    
    # Check CUDA availability
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "N/A"
            print(f"\n✅ CUDA Status:")
            print(f"   - Available: {cuda_available}")
            print(f"   - Device count: {device_count}")
            print(f"   - Device name: {device_name}")
        else:
            print(f"\n⚠️  CUDA not available (CPU mode)")
    except ImportError:
        print("\n⚠️  PyTorch not available - cannot check CUDA")
    
    return True


async def test_composition_root_in_docker(server):
    """Test CompositionRoot works correctly in Docker."""
    print("\n🧪 Test 8: CompositionRoot in Docker")
    print("=" * 60)
    
    try:
        root = server.composition_root
        
        # Test all use cases are available
        use_cases = [
            "transcribe_audio",
            "transcribe_with_timestamps",
            "transcribe_file_content",
            "batch_transcribe",
            "detect_language",
            "convert_audio",
        ]
        
        print("Use cases availability:")
        for use_case in use_cases:
            available = hasattr(root, use_case)
            status = "✅" if available else "❌"
            print(f"   {status} {use_case}")
            
            if not available:
                print(f"      ERROR: Use case '{use_case}' not found!")
                return False
        
        # Test adapters are available
        adapters = {
            "get_whisper_model": root.get_whisper_model(),
            "get_configuration": root.get_configuration(),
        }
        
        print("\nAdapters availability:")
        for name, adapter in adapters.items():
            status = "✅" if adapter is not None else "❌"
            adapter_type = type(adapter).__name__ if adapter else "None"
            print(f"   {status} {name}: {adapter_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ CompositionRoot test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Docker MCP tests."""
    print("\n" + "=" * 60)
    print("🐳 WHISPER MCP SERVER - DOCKER TESTS")
    print("=" * 60)
    print(f"Running in: {Path.cwd()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Server initialization
    server = await test_mcp_server_initialization()
    results["initialization"] = server is not None
    
    if not server:
        print("\n❌ Cannot continue - server initialization failed")
        return False
    
    # Test 2: Tools listing
    tools = await test_mcp_tools_listing(server)
    results["tools_listing"] = len(tools) > 0
    
    # Test 3: Tool schemas
    if tools:
        results["tool_schemas"] = await test_mcp_tool_schemas(tools)
    
    # Test 4: Model info tool
    results["model_info"] = await test_mcp_model_info_tool(server)
    
    # Test 5: Config tool
    results["config_tool"] = await test_mcp_config_tool(server)
    
    # Test 6: Audio conversion schema
    results["conversion_schema"] = await test_mcp_audio_conversion_tool(server)
    
    # Test 7: Docker environment
    results["docker_env"] = await test_docker_environment()
    
    # Test 8: CompositionRoot
    results["composition_root"] = await test_composition_root_in_docker(server)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ MCP server is ready for Docker deployment")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        print("❌ Some issues need to be resolved")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
