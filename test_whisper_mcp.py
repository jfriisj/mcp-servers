#!/usr/bin/env python3
"""
Test script for Whisper MCP server
"""

import json
import subprocess
import sys
from pathlib import Path


def test_mcp_tools_list():
    """Test the tools/list MCP method"""
    print("Testing MCP tools/list...")

    # MCP tools/list request
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

    # Run the server with the request
    cmd = [
        "docker",
        "run",
        "--rm",
        "-i",
        "-e",
        "HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN}",
        "-e",
        "HF_TOKEN=${HF_TOKEN}",
        "whisper-server-whisper-server",
        "bash",
        "-c",
        "cd /app/src && python main.py",
    ]

    proc = None
    try:
        # Start the process
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent / "whisper-server",
        )

        # Send the request
        if proc.stdin:
            proc.stdin.write(json.dumps(request) + "\n")
            proc.stdin.close()

        # Read response
        stdout, stderr = proc.communicate(timeout=10)

        print("STDOUT:", stdout)
        if stderr:
            print("STDERR:", stderr)

        # Parse response
        try:
            response = json.loads(stdout.strip())
            print("✅ MCP Response received:")
            print(json.dumps(response, indent=2))

            # Check if it has the expected structure
            has_jsonrpc = "jsonrpc" in response
            has_id = "id" in response
            has_result = "result" in response
            if has_jsonrpc and has_id and has_result:
                tools = response["result"].get("tools", [])
                print(f"✅ Found {len(tools)} tools")
                for tool in tools:
                    print(f"  - {tool['name']}: {tool['description'][:50]}...")
                return True
            else:
                print("❌ Invalid MCP response structure")
                return False

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        if proc:
            proc.kill()
        return False
    except OSError as e:
        print(f"❌ OS error: {e}")
        return False


if __name__ == "__main__":
    success = test_mcp_tools_list()
    sys.exit(0 if success else 1)
