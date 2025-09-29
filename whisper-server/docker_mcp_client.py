#!/usr/bin/env python3
"""
Example MCP client for testing the Whisper Docker MCP server
"""

import json
import subprocess
import sys
from typing import Dict, Any, Optional


class DockerMCPClient:
    """Simple MCP client for testing Docker MCP servers."""

    def __init__(self, docker_image: str, env_vars: Optional[Dict[str, str]] = None):
        self.docker_image = docker_image
        self.env_vars = env_vars or {}
        self.request_id = 1

    def _build_docker_command(self) -> list:
        """Build the docker run command."""
        cmd = ["docker", "run", "--rm", "-i"]

        # Add environment variables
        for key, value in self.env_vars.items():
            cmd.extend(["-e", f"{key}={value}"])

        # Add the image name
        cmd.append(self.docker_image)

        return cmd

    def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server."""
        request["jsonrpc"] = "2.0"
        request["id"] = self.request_id
        self.request_id += 1

        # Convert request to JSON
        request_json = json.dumps(request) + "\n"

        # Build docker command
        cmd = self._build_docker_command()

        # Run the command and communicate
        try:
            result = subprocess.run(
                cmd,
                input=request_json,
                text=True,
                capture_output=True,
                timeout=30
            )

            # Extract JSON response from output (skip startup logs)
            lines = result.stdout.strip().split('\n')
            json_line = None
            for line in reversed(lines):  # Start from the end
                line = line.strip()
                if line.startswith('{') and 'jsonrpc' in line:
                    json_line = line
                    break

            if json_line:
                return json.loads(json_line)
            else:
                return {"error": "No JSON-RPC response found"}

        except subprocess.TimeoutExpired:
            return {"error": "Request timed out"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response: {e}"}

    def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP connection."""
        request = {
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "docker-mcp-test-client",
                    "version": "1.0.0"
                }
            }
        }
        return self._send_request(request)

    def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        request = {
            "method": "tools/list"
        }
        return self._send_request(request)

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool."""
        request = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        return self._send_request(request)


def main():
    """Example usage of the Docker MCP client."""
    if len(sys.argv) < 2:
        print("Usage: python docker_mcp_client.py <docker_image> [huggingface_token]")
        sys.exit(1)

    docker_image = sys.argv[1]
    hf_token = sys.argv[2] if len(sys.argv) > 2 else "dummy_token"

    # Create client
    client = DockerMCPClient(
        docker_image=docker_image,
        env_vars={
            "HUGGINGFACE_TOKEN": hf_token,
            "HF_TOKEN": hf_token
        }
    )

    print("🚀 Testing Docker MCP Server...")
    print(f"📦 Image: {docker_image}")
    print()

    # Test initialization
    print("1. Testing initialization...")
    init_response = client.initialize()
    print(f"Response: {json.dumps(init_response, indent=2)}")
    print()

    # Test tools listing
    print("2. Testing tools/list...")
    tools_response = client.list_tools()
    print(f"Response: {json.dumps(tools_response, indent=2)}")
    print()

    print("✅ Docker MCP server test completed!")


if __name__ == "__main__":
    main()