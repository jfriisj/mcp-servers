#!/usr/bin/env python3
"""
Test script for Whisp        proc = subprocess.Popen(
            docker_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent
        )r    try:
        # Start the Docker process
        print("🐳 Starting Docker container...")
        proc = subprocess.Popen(
            docker_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent
        )ontainer with base64 audio
"""

import json
import subprocess
import sys
import base64
from pathlib import Path


def create_test_audio_base64():
    """Create base64 encoded audio from test1.mp3 file."""
    audio_path = Path(__file__).parent / "audio" / "test1.mp3"
    
    if not audio_path.exists():
        raise FileNotFoundError(f"Test audio file not found: {audio_path}")
    
    with open(audio_path, "rb") as f:
        audio_data = f.read()
    
    return base64.b64encode(audio_data).decode('utf-8')


def test_mcp_docker():
    """Test the Whisper MCP server running in Docker."""

    print("🎵 Testing Whisper MCP Server with Docker...")

    # Create test base64 audio
    test_audio_b64 = create_test_audio_base64()
    print(f"📄 Created test audio (length: {len(test_audio_b64)} chars)")

    # Docker command to run the container using docker-compose
    docker_cmd = [
        "docker-compose", "run", "--rm", "-T", "whisper-server"
    ]

    try:
        # Start the Docker process
        print("🐳 Starting Docker container...")
        proc = subprocess.Popen(
            docker_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent
        )

        if proc is None or proc.stdin is None or proc.stdout is None:
            print("❌ Failed to start Docker process")
            return False

        # Test 1: Initialize
        print("🔧 Sending initialize request...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }

        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        # Read initialize response
        init_line = proc.stdout.readline().strip()
        print(f"📥 Raw init response: '{init_line}'")
        if not init_line:
            print("❌ No response from container")
            return False
        init_response = json.loads(init_line)
        result = init_response.get('result', {})
        server_info = result.get('serverInfo', {})
        server_name = server_info.get('name', 'unknown')
        print(f"✅ Initialize response: {server_name}")

        # Send initialized notification
        print("🔧 Sending initialized notification...")
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }

        proc.stdin.write(json.dumps(initialized_notification) + "\n")
        proc.stdin.flush()

        # Test 2: List tools
        print("📋 Requesting tools list...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        proc.stdin.write(json.dumps(tools_request) + "\n")
        proc.stdin.flush()

        # Read tools response
        tools_response = json.loads(proc.stdout.readline().strip())
        tools = tools_response.get('result', {}).get('tools', [])
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description'][:60]}...")

        # Test 3: Transcribe file content
        print("🎤 Testing base64 audio transcription...")
        transcribe_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "whisper-transcribe-file-content",
                "arguments": {
                    "file_content": test_audio_b64,
                    "language": "en",
                    "response_format": "verbose_json"  # Enable timestamps
                }
            }
        }

        proc.stdin.write(json.dumps(transcribe_request) + "\n")
        proc.stdin.flush()

        # Read transcription response (with timeout handling)
        print("⏳ Waiting for transcription response...")
        import time
        start_time = time.time()
        transcribe_line = None
        
        while time.time() - start_time < 60:  # Wait up to 60 seconds
            if proc.poll() is not None:  # Process finished
                break
            try:
                line = proc.stdout.readline().strip()
                if line:
                    print(f"📥 Raw transcription response: '{line[:100]}...'")
                    transcribe_line = line
                    break
            except (OSError, IOError):
                time.sleep(0.1)
        
        if not transcribe_line:
            print("❌ No transcription response received within timeout")
            return False
            
        transcribe_response = json.loads(transcribe_line)
        result = transcribe_response.get('result', {})
        content_list = result.get('content', [{}])
        content = content_list[0] if content_list else {}
        text = content.get('text', 'No text found')

        print(f"✅ Transcription result: {text}")

        # Close stdin to end the process
        proc.stdin.close()

        # Check for any errors
        if proc.stderr:
            stderr_output = proc.stderr.read()
            if stderr_output:
                print(f"⚠️  Stderr: {stderr_output}")

        # Wait for process to finish
        proc.wait()

        print("🎉 All tests completed successfully!")
        return True

    except (subprocess.SubprocessError, json.JSONDecodeError, OSError) as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_mcp_docker()
    sys.exit(0 if success else 1)
