#!/usr/bin/env python3
"""
Quick test for dependency tree in Docker
"""

import json
import subprocess
import sys

def test_dependency_tree_docker():
    """Test dependency tree tool via Docker"""
    
    print("🌳 Testing Dependency Tree Tool in Docker")
    print("=" * 60)
    
    # Prepare MCP call for dependency tree
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "import-test-dependency-tree",
            "arguments": {
                "project_path": "/workspace",
                "format": "text",
                "max_depth": 3,
                "include_external": False
            }
        }
    }
    
    try:
        # Run Docker container with MCP input
        result = subprocess.run([
            'docker', 'run', '--rm', '-i',
            '-v', 'C:/github/mcp-servers/solid-server:/workspace',
            'import-test-server'
        ], 
        input=json.dumps(mcp_request), 
        text=True, 
        capture_output=True,
        timeout=30
        )
        
        print(f"✅ Docker command completed (exit code: {result.returncode})")
        print(f"\n📤 STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"\n📥 STDERR:\n{result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Docker command timed out")
    except Exception as e:
        print(f"❌ Docker command failed: {e}")

    # Test 2: Mermaid format
    print("\n" + "="*60)
    print("Testing Mermaid Format")
    print("="*60)
    
    mcp_request["params"]["arguments"]["format"] = "mermaid"
    mcp_request["params"]["arguments"]["max_depth"] = 2
    
    try:
        result = subprocess.run([
            'docker', 'run', '--rm', '-i',
            '-v', 'C:/github/mcp-servers/solid-server:/workspace',
            'import-test-server'
        ], 
        input=json.dumps(mcp_request), 
        text=True, 
        capture_output=True,
        timeout=30
        )
        
        print(f"✅ Mermaid test completed (exit code: {result.returncode})")
        if result.stdout:
            print(f"\n📤 STDOUT (first 500 chars):\n{result.stdout[:500]}...")
            
    except Exception as e:
        print(f"❌ Mermaid test failed: {e}")

if __name__ == "__main__":
    test_dependency_tree_docker()