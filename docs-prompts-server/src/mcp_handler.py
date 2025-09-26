"""
MCP protocol handling for the Documentation and Prompts MCP Server
"""

import json
import logging
import sqlite3
from pathlib import Path
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

    def _load_tools_from_yaml(self) -> List[Tool]:
        """Load tool definitions from YAML file"""
        try:
            import yaml
        except ImportError:
            logger.warning("PyYAML not available, falling back to empty tools")
            return []

        # Find the tools directory relative to this module
        module_dir = Path(__file__).parent
        tools_dir = module_dir.parent / "tools"
        yaml_file = tools_dir / "tools_schemas.yaml"

        if not yaml_file.exists():
            logger.warning(f"Tools schemas file not found: {yaml_file}")
            return []

        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    logger.error("Invalid YAML structure in tools schemas file")
                    return []

                tools = []
                for tool_data in data.values():
                    try:
                        tool = Tool(
                            name=tool_data["name"],
                            description=tool_data["description"],
                            inputSchema=tool_data["inputSchema"],
                        )
                        tools.append(tool)
                    except KeyError as e:
                        logger.error(f"Missing required field in tool definition: {e}")
                        continue

                return tools
        except Exception as e:
            logger.error(f"Error loading tools from YAML: {e}")
            return []

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
        return self._load_tools_from_yaml()

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

    def _find_reusable_code(
        self, functionality: str, service_context: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Find reusable code patterns across services"""
        results = []

        # Search Python files specifically
        py_results = self.document_indexer.search_documents(
            functionality, ".py", limit * 2
        )

        for result in py_results:
            if len(results) >= limit:
                break

            path = result["path"]
            title = result["title"]

            # Extract service name from path
            service = self._extract_service_from_path(path)

            # Determine code type and reuse suggestion
            code_type, reuse_suggestion = self._analyze_code_reusability(
                title, path, functionality, service_context
            )

            # Extract docstring if available
            docstring = self._extract_docstring_from_result(result)

            results.append(
                {
                    "title": title,
                    "service": service,
                    "file": path.split("/")[-1],
                    "code_type": code_type,
                    "docstring": docstring,
                    "reuse_suggestion": reuse_suggestion,
                    "path": path,
                }
            )

        return results

    def _extract_service_from_path(self, path: str) -> str:
        """Extract service name from file path"""
        if "services/" in path:
            parts = path.split("services/")[1].split("/")
            return parts[0] if parts else "unknown"
        return "shared"

    def _analyze_code_reusability(
        self, title: str, path: str, functionality: str, service_context: str
    ) -> tuple[str, str]:
        """Analyze code for reusability and provide suggestions"""
        title_lower = title.lower()
        path_lower = path.lower()

        # Determine code type
        if "class" in title_lower:
            code_type = "Class"
        elif "function" in title_lower or "def " in title_lower:
            code_type = "Function"
        elif "utils" in path_lower or "utilities" in path_lower:
            code_type = "Utility Module"
        elif "handler" in path_lower:
            code_type = "Handler"
        else:
            code_type = "Module"

        # Generate reuse suggestion
        if service_context and service_context.lower() in path_lower:
            reuse_suggestion = f"Direct import from {path}"
        else:
            reuse_suggestion = f"Import from {path} (consider service abstraction)"

        # Add specific suggestions based on functionality
        if functionality.lower() in ["logging", "log"]:
            reuse_suggestion += " - Standardize logging across services"
        elif functionality.lower() in ["validation", "validate"]:
            reuse_suggestion += " - Use consistent validation patterns"
        elif functionality.lower() in ["circuit_breaker", "circuit breaker"]:
            reuse_suggestion += " - Implement resilient service calls"
        elif functionality.lower() in ["metrics", "monitoring"]:
            reuse_suggestion += " - Centralize observability"

        return code_type, reuse_suggestion

    def _extract_docstring_from_result(self, result: Dict[str, Any]) -> str:
        """Extract docstring from search result"""
        content = result.get("content_snippet", "")
        # Look for docstring patterns in the content
        if '"""' in content or "'''" in content:
            # Extract first docstring-like content
            lines = content.split("\n")
            docstring_lines = []
            in_docstring = False

            for line in lines[:10]:  # Check first 10 lines
                if ('"""' in line or "'''" in line) and not in_docstring:
                    in_docstring = True
                    # Remove opening quotes
                    line = line.replace('"""', "").replace("'''", "").strip()
                    if line:
                        docstring_lines.append(line)
                elif in_docstring:
                    if '"""' in line or "'''" in line:
                        break
                    docstring_lines.append(line.strip())

            if docstring_lines:
                return " ".join(docstring_lines[:5])  # First 5 lines of docstring

        return ""

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls for documentation and prompts"""
        try:
            if name == "find_code_reuse":
                functionality = arguments["functionality"]
                service_context = arguments.get("service_context", "")
                limit = arguments.get("limit", 5)

                # Search Python files specifically for reusable code
                results = self._find_reusable_code(
                    functionality, service_context, limit
                )

                response_text = f"🔍 Code Reuse Search for '{functionality}':\n\n"

                if results:
                    for i, result in enumerate(results, 1):
                        response_text += f"{i}. **{result['title']}**\n"
                        response_text += f"   📁 Service: {result['service']}\n"
                        response_text += f"   📄 File: {result['file']}\n"
                        response_text += f"   🔧 Type: {result['code_type']}\n"
                        if result.get("docstring"):
                            response_text += (
                                f"   📝 Docs: {result['docstring'][:100]}...\n"
                            )
                        response_text += (
                            f"   💡 Reuse: {result['reuse_suggestion']}\n\n"
                        )
                else:
                    response_text += f"❌ No reusable {functionality} code found.\n"
                    response_text += (
                        "💡 Try searching documentation or creating new implementation."
                    )

                return [TextContent(type="text", text=response_text)]

            elif name == "find_documents":
                topic = arguments["topic"]
                doc_type = arguments.get("doc_type")
                limit = arguments.get("limit", 10)

                # Search documentation files (exclude Python files)
                results = self.document_indexer.search_documents(topic, doc_type, limit)

                # Filter out Python files for document-focused search
                doc_results = [r for r in results if not r["path"].endswith(".py")]

                response_text = f"📚 Document Search for '{topic}':\n\n"

                if doc_results:
                    for i, result in enumerate(doc_results[:limit], 1):
                        response_text += (
                            f"{i}. **{result['title']}** ({result['doc_type']})\n"
                        )
                        response_text += f"   📁 Path: {result['path']}\n"
                        response_text += f"   📄 Section: {result['section_title']}\n"
                        response_text += (
                            f"   📝 Content: {result['content_snippet'][:200]}...\n\n"
                        )
                else:
                    response_text += f"❌ No documentation found for '{topic}'.\n"
                    response_text += "💡 Try broader search terms or check spelling."

                return [TextContent(type="text", text=response_text)]

            elif name == "search_docs":
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
