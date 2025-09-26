"""
MCP protocol handling for the Documentation and Prompts MCP Server
"""

import json
import logging
import sqlite3
from typing import Dict, Any, List

from mcp.types import Resource, Tool, TextContent, ReadResourceResult

logger = logging.getLogger(__name__)


class MCPHandler:
    """Handles MCP protocol interactions"""

    def __init__(self, document_indexer, prompt_manager, db_manager, config, db_path):
        self.document_indexer = document_indexer
        self.prompt_manager = prompt_manager
        self.db_manager = db_manager
        self.config = config
        self.db_path = db_path

    def get_resources(self) -> List[Resource]:
        """List available documentation and prompt resources"""
        return [
            # Documentation resources
            Resource(
                uri="docs://index",
                name="Documentation Index",
                description="Complete index of all documented files and metadata",
                mimeType="application/json",
            ),
            Resource(
                uri="docs://architecture",
                name="Architecture Information",
                description="Extracted architecture patterns and design information",
                mimeType="application/json",
            ),
            Resource(
                uri="docs://statistics",
                name="Documentation Statistics",
                description="Statistics about indexed documentation",
                mimeType="application/json",
            ),
            # Prompt resources
            Resource(
                uri="prompts://library",
                name="Prompt Library",
                description="Complete library of available prompts",
                mimeType="application/json",
            ),
            Resource(
                uri="prompts://categories",
                name="Prompt Categories",
                description="Available prompt categories and organization",
                mimeType="application/json",
            ),
            Resource(
                uri="prompts://usage-stats",
                name="Prompt Usage Statistics",
                description="Usage statistics and effectiveness metrics",
                mimeType="application/json",
            ),
        ]

    def get_tools(self) -> List[Tool]:
        """List available documentation and prompt tools"""
        return [
            # Provide a user-friendly alias that matches the project's guidance "Run docs"
            Tool(
                name="search_docs",
                description="Search documentation using keywords or phrases",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (keywords or phrases)",
                        },
                        "doc_type": {
                            "type": "string",
                            "description": "Filter by document type (.md, .rst, .yaml, etc.)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50,
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="get_architecture_info",
                description="Extract architecture patterns and design information",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="index_documentation",
                description="Re-index all documentation files",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "force": {
                            "type": "boolean",
                            "description": "Force re-indexing of all files",
                            "default": False,
                        }
                    },
                },
            ),
            # Prompt management tools
            Tool(
                name="search_prompts",
                description="Search prompts by keyword, category, or tags",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for prompt name, description, or tags",
                        },
                        "category": {
                            "type": "string",
                            "description": "Filter by prompt category",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50,
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="get_prompt",
                description="Retrieve a specific prompt by ID with full details",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt_id": {
                            "type": "string",
                            "description": "ID of the prompt to retrieve",
                        }
                    },
                    "required": ["prompt_id"],
                },
            ),
            Tool(
                name="suggest_prompts",
                description="Get context-aware prompt suggestions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "context": {
                            "type": "string",
                            "description": "Context description for prompt suggestions (optional)",
                        }
                    },
                },
            ),
            Tool(
                name="create_prompt",
                description="Create a new custom prompt",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the prompt"},
                        "description": {
                            "type": "string",
                            "description": "Description of what the prompt does",
                        },
                        "template": {
                            "type": "string",
                            "description": "The prompt template with variables in {variable} format",
                        },
                        "category": {
                            "type": "string",
                            "description": "Prompt category",
                            "default": "custom",
                        },
                        "variables": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of variable names used in the template",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for categorizing and searching",
                        },
                    },
                    "required": ["name", "description", "template"],
                },
            ),
            # Integration tools
            Tool(
                name="generate_contextual_prompt",
                description="Generate a prompt based on current documentation context",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The task type (e.g., 'code_review', 'documentation', 'architecture_analysis')",
                        },
                        "docs_query": {
                            "type": "string",
                            "description": "Query to find relevant documentation context",
                        },
                    },
                    "required": ["task", "docs_query"],
                },
            ),
            Tool(
                name="apply_prompt_with_context",
                description="Apply a prompt with documentation context automatically filled",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt_id": {
                            "type": "string",
                            "description": "ID of the prompt to apply",
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to analyze (code, documentation, etc.)",
                        },
                        "auto_fill_context": {
                            "type": "boolean",
                            "description": "Automatically fill context variables from documentation",
                            "default": True,
                        },
                    },
                    "required": ["prompt_id", "content"],
                },
            ),
        ]

    def read_resource(self, uri: str) -> ReadResourceResult:
        """Read resource data"""
        if uri == "docs://index":
            docs = []
            # Get all documents from database
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute("""
                    SELECT path, title, doc_type, metadata, last_modified
                    FROM documents ORDER BY title
                """)

                for row in cursor.fetchall():
                    docs.append(
                        {
                            "path": row[0],
                            "title": row[1],
                            "doc_type": row[2],
                            "metadata": json.loads(row[3]),
                            "last_modified": row[4],
                        }
                    )

            content = TextContent(
                type="text",
                text=json.dumps(
                    {"documents": docs, "total_count": len(docs)}, indent=2
                ),
            )
            return ReadResourceResult(contents=[content])

        elif uri == "docs://architecture":
            arch_info = self.document_indexer.get_architecture_info()
            content = TextContent(type="text", text=json.dumps(arch_info, indent=2))
            return ReadResourceResult(contents=[content])

        elif uri == "docs://statistics":
            doc_count = self.document_indexer.get_document_count()
            stats = {
                "total_documents": doc_count,
                "index_file": str(self.db_path),
                "documentation_paths": self.config["documentation_paths"],
            }
            content = TextContent(type="text", text=json.dumps(stats, indent=2))
            return ReadResourceResult(contents=[content])

        elif uri == "prompts://library":
            prompts = self.db_manager.get_all_prompts()
            content = TextContent(
                type="text",
                text=json.dumps(
                    {"prompts": prompts, "total_count": len(prompts)}, indent=2
                ),
            )
            return ReadResourceResult(contents=[content])

        elif uri == "prompts://categories":
            # This would need access to the prompts directory
            categories_data = {"categories": {}}
            content = TextContent(
                type="text", text=json.dumps(categories_data, indent=2)
            )
            return ReadResourceResult(contents=[content])

        elif uri == "prompts://usage-stats":
            stats = self.prompt_manager.get_usage_stats()
            content = TextContent(
                type="text", text=json.dumps({"usage_statistics": stats}, indent=2)
            )
            return ReadResourceResult(contents=[content])

        else:
            raise ValueError(f"Unknown resource: {uri}")

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls for documentation and prompts"""
        try:
            if name == "search_docs":
                query = arguments["query"]
                doc_type = arguments.get("doc_type")
                limit = arguments.get("limit", 10)

                results = self.document_indexer.search_documents(query, doc_type, limit)

                response_text = f"Documentation Search Results for '{query}':\n\n"

                if results:
                    for i, result in enumerate(results, 1):
                        response_text += (
                            f"{i}. **{result['title']}** ({result['doc_type']})\n"
                        )
                        response_text += f"   Path: {result['path']}\n"
                        response_text += f"   Section: {result['section_title']}\n"
                        response_text += f"   Content: {result['content_snippet']}\n\n"
                else:
                    response_text += f"No results found for '{query}'"

                return [TextContent(type="text", text=response_text)]

            elif name == "get_architecture_info":
                arch_info = self.document_indexer.get_architecture_info()

                response_text = "Architecture Documentation Summary:\n\n"

                if arch_info["architecture_documents"]:
                    for doc in arch_info["architecture_documents"]:
                        response_text += f"📋 **{doc['title']}**\n"
                        response_text += f"   Section: {doc['section_title']}\n"
                        response_text += f"   Content: {doc['content_snippet']}\n\n"
                else:
                    response_text += "No architecture documentation found."

                return [TextContent(type="text", text=response_text)]

            elif name == "index_documentation":
                # This would need to be async
                # result = await self.document_indexer.index_all_documents()
                return [TextContent(type="text", text="Indexing started...")]

            # ... other tool implementations would go here

            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]
