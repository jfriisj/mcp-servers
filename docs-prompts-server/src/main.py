"""
Main entry point for the Documentation and Prompts MCP Server
"""
import asyncio
import logging

from mcp.server import Server
from pydantic.networks import AnyUrl
from server import DocumentationPromptsServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("docs-prompts-mcp-server")

# Initialize the server
docs_prompts_server = DocumentationPromptsServer()

# Create MCP app
app = Server("docs-prompts-server")


@app.list_resources()
async def handle_list_resources():
    """List available resources"""
    return docs_prompts_server.get_resources()


@app.read_resource()
async def read_resource(uri: AnyUrl):
    """Read resource data"""
    result = docs_prompts_server.read_resource(str(uri))
    # Return the text content directly as string
    if result.contents and hasattr(result.contents[0], 'text'):
        return result.contents[0].text  # type: ignore
    return ""


@app.list_tools()
async def list_tools():
    """List available tools"""
    return docs_prompts_server.get_tools()


@app.call_tool()
async def call_tool(name: str, arguments):
    """Handle tool calls"""
    return docs_prompts_server.call_tool(name, arguments)


async def main():
    """Main entry point for the documentation and prompts MCP server"""
    try:
        from mcp.server.stdio import stdio_server

        # Auto-index documentation on startup
        try:
            logger.info("Auto-indexing documentation on startup...")
            await docs_prompts_server.index_all_documents()
        except Exception as e:
            logger.error("Error during startup indexing: %s", e)

        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    except Exception as e:  # noqa: BLE001
        logger.error("Error during server startup: %s", e)
        raise


if __name__ == "__main__":
    asyncio.run(main())



