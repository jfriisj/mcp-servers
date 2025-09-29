"""
Entry point for Whisper MCP Server and FastAPI
===============================================
Main application entry point with support for both MCP and FastAPI modes.
"""

import asyncio
import sys
import uvicorn
from pathlib import Path


async def main():
    """Main entry point for the Whisper server."""
    try:
        # Parse command line arguments
        args = sys.argv[1:]
        mode = "mcp"  # Default mode
        host = "0.0.0.0"
        port = 8000
        project_root = Path.cwd()

        i = 0
        while i < len(args):
            if args[i] == "--mode":
                if i + 1 < len(args):
                    mode = args[i + 1]
                    i += 2
                else:
                    i += 1
            elif args[i] == "--host":
                if i + 1 < len(args):
                    host = args[i + 1]
                    i += 2
                else:
                    i += 1
            elif args[i] == "--port":
                if i + 1 < len(args):
                    port = int(args[i + 1])
                    i += 2
                else:
                    i += 1
            elif args[i] == "--root-folder":
                if i + 1 < len(args):
                    project_root = Path(args[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                # Assume it's a project root path
                project_root = Path(args[i])
                i += 1

        if mode == "api":
            # Run FastAPI server
            print("🚀 Starting Whisper FastAPI server...")
            from api import create_app

            app = create_app(project_root)
            config = uvicorn.Config(app, host=host, port=port)
            server = uvicorn.Server(config)
            await server.serve()

        elif mode == "mcp":
            # Run MCP server (default)
            print("🎯 Starting Whisper MCP server...")
            from server import WhisperMCPServer

            service = WhisperMCPServer(project_root)
            await service.serve()

        else:
            print(f"[ERROR] Unknown mode: {mode}. Use 'mcp' or 'api'")
            sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Whisper server failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
