#!/usr/bin/env python3
"""
Example client for connecting to the SLR MCP Server programmatically.
This demonstrates how to use the SLR server from your own applications.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    """Example usage of the SLR MCP Server"""
    
    # Configure server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.main"],
        env={
            "DATABASE_PATH": "slr_database.db",
            "LOG_LEVEL": "INFO",
            "MAX_PAPERS_PER_ANALYSIS": "100",
            "ENABLE_CACHING": "true"
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available SLR Tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Example: Upload a paper
            try:
                result = await session.call_tool(
                    name="upload-paper",
                    arguments={
                        "file_path": "./example_paper.pdf",
                        "title": "Machine Learning in Healthcare: A Review",
                        "tags": ["machine-learning", "healthcare"]
                    }
                )
                print(f"Upload result: {result}")
            except Exception as e:
                print(f"Upload failed: {e}")
            
            # Example: Validate a research question
            try:
                result = await session.call_tool(
                    name="validate-research-question",
                    arguments={
                        "question_text": "How effective are ML algorithms in improving healthcare outcomes?",
                        "framework": "pico",
                        "suggest_improvements": True
                    }
                )
                print(f"Research question validation: {result}")
            except Exception as e:
                print(f"Validation failed: {e}")
            
            # Example: Perform quality assessment
            try:
                result = await session.call_tool(
                    name="assess-quality",
                    arguments={
                        "paper_id": 1,
                        "framework": "prisma",
                        "reviewer_id": "researcher_001"
                    }
                )
                print(f"Quality assessment: {result}")
            except Exception as e:
                print(f"Assessment failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())