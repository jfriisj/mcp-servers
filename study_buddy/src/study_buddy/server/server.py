"""
Study Buddy MCP Server - Main Entry Point.

This module provides the main MCP server implementation using the mcp library
and Clean Architecture principles with proper dependency injection.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Handle imports for both module and direct execution
try:
    from .container import initialize_application
    from .handlers.mcp_handler import MCPHandler
except ImportError:
    # Fallback for direct execution
    from study_buddy.server.container import initialize_application
    from study_buddy.server.handlers.mcp_handler import MCPHandler

# Configure logging - Debug: force VS Code reconnect
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StudyBuddyMCPServer:
    """
    Study Buddy MCP Server implementation.

    This class provides the main MCP server using Clean Architecture principles:
    - Dependency injection via Container
    - Business logic separation via services
    - MCP protocol handling via MCPHandler
    - Proper error handling and logging
    """

    def __init__(self, database_path: Optional[str] = None):
        """
        Initialize Study Buddy MCP Server.

        Args:
            database_path: Optional path to SQLite database file
        """
        self.database_path = database_path
        self.container = None
        self.mcp_handler: Optional[MCPHandler] = None

        # Create MCP server instance
        logger.info("DEBUG: Creating MCP server instance...")
        self.server = Server("study-buddy")
        logger.info("DEBUG: MCP server instance created")

        # Setup MCP server handlers
        logger.info("DEBUG: About to register handlers...")
        self._register_handlers()
        logger.info("DEBUG: Handlers registered successfully")

    def _register_handlers(self) -> None:
        """Register all MCP server handlers."""
        
        logger.info("DEBUG: Starting handler registration...")

        # Native MCP Prompt Handlers
        @self.server.list_prompts()
        async def handle_list_prompts() -> List[types.Prompt]:
            """List available native MCP prompts for Study Buddy workflows."""
            return [
                types.Prompt(
                    name="analyze_document",
                    description="Analyze a document comprehensively using Study Buddy tools",
                    arguments=[
                        types.PromptArgument(
                            name="document_id",
                            description="ID of the document to analyze",
                            required=True
                        ),
                        types.PromptArgument(
                            name="focus_area",
                            description="Specific focus: 'overview', 'key_concepts', 'methodology', 'conclusions', or 'critical_analysis'",
                            required=False
                        )
                    ]
                ),
                types.Prompt(
                    name="create_study_plan",
                    description="Create a structured study plan for one or more documents",
                    arguments=[
                        types.PromptArgument(
                            name="document_ids",
                            description="Comma-separated document IDs (e.g., '1,2,3')",
                            required=True
                        ),
                        types.PromptArgument(
                            name="time_available",
                            description="Study timeframe (e.g., '2 weeks', '1 month', '3 days')",
                            required=True
                        ),
                        types.PromptArgument(
                            name="learning_goals",
                            description="Specific learning objectives or exam preparation goals",
                            required=False
                        )
                    ]
                ),
                types.Prompt(
                    name="summarize_chapter",
                    description="Create a focused summary of a specific chapter or document section",
                    arguments=[
                        types.PromptArgument(
                            name="chunk_id",
                            description="ID of the chunk/chapter to summarize",
                            required=True
                        ),
                        types.PromptArgument(
                            name="summary_style",
                            description="Summary style: 'brief' (150 words), 'standard' (300 words), or 'detailed' (500+ words)",
                            required=False
                        ),
                        types.PromptArgument(
                            name="save_result",
                            description="Whether to save summary to database (true/false)",
                            required=False
                        )
                    ]
                ),
                types.Prompt(
                    name="compare_documents",
                    description="Compare and contrast multiple documents on specific criteria",
                    arguments=[
                        types.PromptArgument(
                            name="document_ids",
                            description="Comma-separated document IDs to compare (e.g., '1,2')",
                            required=True
                        ),
                        types.PromptArgument(
                            name="comparison_criteria",
                            description="What to compare: 'methodology', 'conclusions', 'approach', 'evidence', or 'arguments'",
                            required=False
                        )
                    ]
                ),
                types.Prompt(
                    name="extract_key_concepts",
                    description="Extract and define key concepts, terms, and definitions from a document",
                    arguments=[
                        types.PromptArgument(
                            name="document_id",
                            description="Document ID to extract concepts from",
                            required=True
                        ),
                        types.PromptArgument(
                            name="concept_type",
                            description="Type of concepts: 'definitions', 'theories', 'methods', 'formulas', or 'all'",
                            required=False
                        )
                    ]
                ),
                types.Prompt(
                    name="research_questions",
                    description="Generate research questions and discussion points from document content",
                    arguments=[
                        types.PromptArgument(
                            name="document_id",
                            description="Document ID to generate questions from",
                            required=True
                        ),
                        types.PromptArgument(
                            name="question_level",
                            description="Question complexity: 'basic', 'intermediate', 'advanced', or 'critical_thinking'",
                            required=False
                        )
                    ]
                ),
                types.Prompt(
                    name="export_to_markdown",
                    description="Export summaries, analyses, or document structures to markdown files for user download",
                    arguments=[
                        types.PromptArgument(
                            name="export_type",
                            description="What to export: 'summary', 'document_structure', 'analysis', or 'custom'",
                            required=True
                        ),
                        types.PromptArgument(
                            name="target_id",
                            description="ID of the target (summary_id, document_id, or chunk_id depending on export_type)",
                            required=True
                        ),
                        types.PromptArgument(
                            name="file_path",
                            description="Desired output path (e.g., 'C:/Users/Documents/export.md')",
                            required=True
                        ),
                        types.PromptArgument(
                            name="include_metadata",
                            description="Include metadata in YAML frontmatter: 'true' or 'false'",
                            required=False
                        )
                    ]
                )
            ]

        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: Dict[str, str] | None = None) -> types.GetPromptResult:
            """Generate specific prompt content with Study Buddy tool instructions."""
            
            if arguments is None:
                arguments = {}

            if name == "analyze_document":
                return self._get_analyze_document_prompt(arguments)
            elif name == "create_study_plan":
                return self._get_create_study_plan_prompt(arguments)
            elif name == "summarize_chapter":
                return self._get_summarize_chapter_prompt(arguments)
            elif name == "compare_documents":
                return self._get_compare_documents_prompt(arguments)
            elif name == "extract_key_concepts":
                return self._get_extract_concepts_prompt(arguments)
            elif name == "research_questions":
                return self._get_research_questions_prompt(arguments)
            elif name == "export_to_markdown":
                return self._get_export_to_markdown_prompt(arguments)
            else:
                raise ValueError(f"Unknown prompt: {name}")

        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """Handle MCP list_tools request."""
            try:
                return [
                    # Document Management Tools
                    types.Tool(
                        name="upload_document",
                        description="Upload and parse a document file (PDF, DOCX, PPTX, Markdown)",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string", "description": "Path to document file"},
                                "title": {"type": "string", "description": "Optional custom title"},
                                "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags"}
                            },
                            "required": ["file_path"]
                        }
                    ),
                    types.Tool(
                        name="get_document",
                        description="Retrieve document information by ID",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "document_id": {"type": "integer", "description": "Document ID to retrieve"}
                            },
                            "required": ["document_id"]
                        }
                    ),
                    types.Tool(
                        name="list_documents",
                        description="List all documents with optional filters",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "filters": {
                                    "type": "object",
                                    "properties": {
                                        "file_type": {"type": "string", "description": "Filter by file type"},
                                        "indexed": {"type": "boolean", "description": "Filter by indexing status"},
                                        "tags": {"type": "array", "items": {"type": "string"}}
                                    }
                                },
                                "limit": {"type": "integer", "default": 20},
                                "offset": {"type": "integer", "default": 0}
                            }
                        }
                    ),
                    types.Tool(
                        name="delete_document",
                        description="Delete document and all related data",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "document_id": {"type": "integer", "description": "Document ID to delete"}
                            },
                            "required": ["document_id"]
                        }
                    ),
                    types.Tool(
                        name="search_documents",
                        description="Full-text search across documents and chunks",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Search query"},
                                "filters": {"type": "object", "description": "Optional search filters"},
                                "limit": {"type": "integer", "default": 20}
                            },
                            "required": ["query"]
                        }
                    ),

                    # Indexing and Chunking Tools
                    types.Tool(
                        name="index_document",
                        description="Create intelligent chunks from document content",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "document_id": {"type": "integer", "description": "Document ID to index"},
                                "strategy": {
                                    "type": "string",
                                    "enum": ["auto", "chapter", "section", "heading", "slide", "fixed"],
                                    "default": "auto",
                                    "description": "Chunking strategy to use"
                                },
                                "force": {"type": "boolean", "default": False, "description": "Force re-indexing"}
                            },
                            "required": ["document_id"]
                        }
                    ),
                    types.Tool(
                        name="get_document_structure",
                        description="Get document structure (list of chunks/chapters)",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "document_id": {"type": "integer", "description": "Document ID"}
                            },
                            "required": ["document_id"]
                        }
                    ),
                    types.Tool(
                        name="get_chunk_content",
                        description="Retrieve full text content of a specific chunk",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "chunk_id": {"type": "integer", "description": "Chunk ID"}
                            },
                            "required": ["chunk_id"]
                        }
                    ),
                    types.Tool(
                        name="list_chunks",
                        description="List chunks with optional filters",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "filters": {
                                    "type": "object",
                                    "properties": {
                                        "document_id": {"type": "integer"},
                                        "chunk_type": {"type": "string"}
                                    }
                                },
                                "limit": {"type": "integer", "default": 50},
                                "offset": {"type": "integer", "default": 0}
                            }
                        }
                    ),

                    # Summary Management Tools
                    types.Tool(
                        name="save_summary",
                        description="Save AI-generated summary for chunk or document with export-ready metadata",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "chunk_id": {"type": "integer", "description": "Chunk ID (for chunk summary)"},
                                "document_id": {"type": "integer", "description": "Document ID (for document summary)"},
                                "summary_type": {
                                    "type": "string",
                                    "enum": ["brief", "standard", "detailed", "custom"],
                                    "description": "Type of summary"
                                },
                                "summary_content": {"type": "string", "description": "Summary markdown content"},
                                "model_name": {"type": "string", "description": "AI model used (e.g., 'gpt-4', 'claude-3', 'human-guided')"},
                                "metadata": {
                                    "type": "object",
                                    "description": "Export-ready metadata for better organization and searchability",
                                    "properties": {
                                        "focus_areas": {"type": "array", "items": {"type": "string"}, "description": "Main focus areas covered"},
                                        "summary_approach": {"type": "string", "description": "Approach used: 'comprehensive', 'focused', 'analytical'"},
                                        "content_highlights": {"type": "array", "items": {"type": "string"}, "description": "Types of content emphasized"},
                                        "difficulty_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"], "description": "Content difficulty level"},
                                        "learning_objectives": {"type": "array", "items": {"type": "string"}, "description": "Learning goals addressed"},
                                        "export_tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for organization and search"},
                                        "source_info": {"type": "object", "description": "Source document/chapter information"}
                                    }
                                }
                            },
                            "required": ["summary_type", "summary_content"]
                        }
                    ),
                    types.Tool(
                        name="get_summary",
                        description="Retrieve specific summary by type",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "chunk_id": {"type": "integer", "description": "Chunk ID"},
                                "document_id": {"type": "integer", "description": "Document ID"},
                                "summary_type": {"type": "string", "description": "Summary type"}
                            },
                            "required": ["summary_type"]
                        }
                    ),
                    types.Tool(
                        name="get_summaries_for_chunk",
                        description="Get all summaries for a specific chunk",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "chunk_id": {"type": "integer", "description": "Chunk ID"}
                            },
                            "required": ["chunk_id"]
                        }
                    ),
                    types.Tool(
                        name="get_summaries_for_document",
                        description="Get all summaries for a specific document",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "document_id": {"type": "integer", "description": "Document ID"}
                            },
                            "required": ["document_id"]
                        }
                    ),
                    types.Tool(
                        name="list_summaries",
                        description="List summaries with optional filters",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "filters": {
                                    "type": "object",
                                    "properties": {
                                        "summary_type": {"type": "string"},
                                        "model_name": {"type": "string"},
                                        "document_id": {"type": "integer"}
                                    }
                                },
                                "sort_by": {
                                    "type": "string",
                                    "enum": ["generation_date", "word_count", "summary_type"],
                                    "default": "generation_date"
                                },
                                "sort_order": {
                                    "type": "string",
                                    "enum": ["asc", "desc"],
                                    "default": "desc"
                                },
                                "limit": {"type": "integer", "default": 20},
                                "offset": {"type": "integer", "default": 0}
                            }
                        }
                    ),
                    types.Tool(
                        name="get_summary_statistics",
                        description="Get summary statistics (global or for specific document)",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "document_id": {"type": "integer", "description": "Optional document ID"}
                            }
                        }
                    ),

                    # File Export Tools
                    types.Tool(
                        name="create_markdown_file",
                        description="Create a markdown file with provided content for user download/export",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "content": {"type": "string", "description": "Markdown content to write to file"},
                                "file_path": {"type": "string", "description": "Output file path (must end with .md)"},
                                "title": {"type": "string", "description": "Optional title to add as H1 header"},
                                "metadata": {
                                    "type": "object",
                                    "description": "Optional YAML frontmatter metadata",
                                    "additionalProperties": True
                                },
                                "overwrite": {"type": "boolean", "default": False, "description": "Whether to overwrite existing file"}
                            },
                            "required": ["content", "file_path"]
                        }
                    ),
                    types.Tool(
                        name="export_summary_to_file",
                        description="Export existing summary to a standalone markdown file",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "summary_id": {"type": "integer", "description": "Summary ID to export"},
                                "file_path": {"type": "string", "description": "Output file path (must end with .md)"},
                                "include_metadata": {"type": "boolean", "default": True, "description": "Include summary metadata in frontmatter"},
                                "include_source_info": {"type": "boolean", "default": True, "description": "Include source document/chunk information"},
                                "overwrite": {"type": "boolean", "default": False, "description": "Whether to overwrite existing file"}
                            },
                            "required": ["summary_id", "file_path"]
                        }
                    ),
                    types.Tool(
                        name="export_document_structure_to_file",
                        description="Export document structure (table of contents) to markdown file",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "document_id": {"type": "integer", "description": "Document ID to export structure for"},
                                "file_path": {"type": "string", "description": "Output file path (must end with .md)"},
                                "include_word_counts": {"type": "boolean", "default": True, "description": "Include word counts for each chunk"},
                                "include_metadata": {"type": "boolean", "default": True, "description": "Include document metadata"},
                                "overwrite": {"type": "boolean", "default": False, "description": "Whether to overwrite existing file"}
                            },
                            "required": ["document_id", "file_path"]
                        }
                    )
                ]
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                return []

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> List[types.TextContent]:
            """Handle MCP tool calls."""
            try:
                # Ensure MCP handler is initialized
                if self.mcp_handler is None:
                    await self._initialize_dependencies()

                # Get the handler method - check if it's actually a method
                handler_method = getattr(self.mcp_handler, name, None)
                if handler_method is None:
                    raise ValueError(f"Unknown tool: {name}")

                # Debug: Check if we got a method or something else
                logger.debug(f"Tool {name} handler type: {type(handler_method)}")
                
                if not callable(handler_method):
                    raise ValueError(f"Tool {name} is not callable: {type(handler_method)}")

                # Call the handler
                if arguments is None:
                    arguments = {}

                result = handler_method(**arguments)

                # Debug logging to identify the issue
                logger.debug(f"Handler {name} returned: {type(result)} - {result}")

                # Ensure result is a dictionary
                if not isinstance(result, dict):
                    logger.error(f"Handler {name} returned non-dict: {type(result)}")
                    return [types.TextContent(
                        type="text", 
                        text=f"❌ Error: {name} handler returned {type(result)} instead of dict"
                    )]

                # Format response as MCP TextContent
                if result.get("success", False):
                    content = f"✅ Success: {name}\n\n"

                    # Add result data
                    for key, value in result.items():
                        if key != "success":
                            content += f"**{key}**: {value}\n"

                    return [types.TextContent(type="text", text=content)]
                else:
                    # Error response
                    error_msg = result.get("error", "Unknown error")
                    content = f"❌ Error: {name}\n\n{error_msg}"
                    return [types.TextContent(type="text", text=content)]

            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}", exc_info=True)
                return [types.TextContent(
                    type="text",
                    text=f"❌ Error executing {name}: {str(e)}"
                )]

    def _get_analyze_document_prompt(self, arguments: Dict[str, str]) -> types.GetPromptResult:
        """Generate prompt for comprehensive document analysis."""
        document_id = arguments.get("document_id", "")
        focus_area = arguments.get("focus_area", "comprehensive analysis")
        
        return types.GetPromptResult(
            description=f"Comprehensive document analysis focusing on {focus_area}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Please analyze document {document_id} with focus on {focus_area}.

**Analysis Workflow:**

**Step 1: Document Overview**
- Use `get_document` tool with document_id: {document_id}
- Review title, metadata, total pages/words, and basic information

**Step 2: Document Structure**  
- Use `get_document_structure` tool to see available chapters/sections
- Identify key sections relevant to the {focus_area} focus

**Step 3: Content Analysis**
- Use `get_chunk_content` for relevant sections
- Extract key information based on focus area

**Step 4: Comprehensive Analysis**
Provide detailed analysis covering:

{self._get_analysis_framework(focus_area)}

**Step 5: Conclusions & Optional Export**
- Synthesize findings
- Highlight most important insights
- Suggest areas for further exploration

**Step 6: Save Analysis (Optional)**
If creating a comprehensive analysis summary, use `save_summary` with rich metadata:
- summary_type: "detailed" (for comprehensive analysis)
- metadata: Include analysis-specific information:
  {{
    "focus_areas": ["{focus_area}"],
    "summary_approach": "analytical",
    "content_highlights": ["key findings", "methodology", "implications"],
    "analysis_type": "document_analysis",
    "export_tags": ["analysis", "{focus_area.replace(' ', '-')}"],
    "created_by": "AI Assistant"
  }}

Start by retrieving the document information and structure."""
                    )
                )
            ]
        )

    def _get_create_study_plan_prompt(self, arguments: Dict[str, str]) -> types.GetPromptResult:
        """Generate prompt for creating structured study plans."""
        document_ids = arguments.get("document_ids", "")
        time_available = arguments.get("time_available", "flexible timeline")
        learning_goals = arguments.get("learning_goals", "comprehensive understanding")
        
        return types.GetPromptResult(
            description="Structured study plan creation using Study Buddy tools",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Create a comprehensive study plan for documents: {document_ids}

**Time Available:** {time_available}
**Learning Goals:** {learning_goals}

**Study Plan Creation Workflow:**

**Step 1: Document Assessment**
- Use `list_documents` to see all available materials
- For each document ID ({document_ids}):
  - Use `get_document` to understand scope, length, and complexity
  - Use `get_document_structure` to see chapters/sections

**Step 2: Content Prioritization**
- Identify most important sections for {learning_goals}
- Estimate reading time based on word counts
- Determine prerequisite knowledge requirements

**Step 3: Timeline Planning**
Create structured schedule for {time_available}:
- Daily/weekly reading assignments
- Key concepts to master each period
- Review and practice sessions
- Progress checkpoints

**Step 4: Study Methods**
Recommend specific techniques:
- Active reading strategies
- Note-taking approaches  
- Self-testing methods
- Spaced repetition schedule

**Step 5: Assessment Plan**
- Knowledge check questions
- Practice exercises
- Progress milestones
- Final review strategy

Optimize the plan for {learning_goals} within the {time_available} timeframe."""
                    )
                )
            ]
        )

    def _get_summarize_chapter_prompt(self, arguments: Dict[str, str]) -> types.GetPromptResult:
        """Generate prompt for chapter summarization with optional saving."""
        chunk_id = arguments.get("chunk_id", "")
        summary_style = arguments.get("summary_style", "standard")
        save_result = arguments.get("save_result", "false").lower() == "true"
        
        word_counts = {
            "brief": "100-150 words",
            "standard": "250-350 words", 
            "detailed": "500-750 words"
        }
        
        return types.GetPromptResult(
            description=f"Create {summary_style} summary of chapter/chunk {chunk_id}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Create a {summary_style} summary of chunk {chunk_id}.

**Summarization Workflow:**

**Step 1: Content Retrieval**
- Use `get_chunk_content` with chunk_id: {chunk_id}
- Review the full text and identify main themes

**Step 2: Summary Creation**
Generate {summary_style} summary ({word_counts.get(summary_style, "appropriate length")}):

{self._get_summary_guidelines(summary_style)}

**Step 3: Quality Check**
Ensure summary includes:
- Clear main points and key arguments
- Important definitions or concepts
- Relevant examples or evidence
- Logical flow and coherence

{self._get_save_instructions(save_result, chunk_id, summary_style) if save_result else ""}

Focus on accuracy and clarity while maintaining the {summary_style} style."""
                    )
                )
            ]
        )

    def _get_compare_documents_prompt(self, arguments: Dict[str, str]) -> types.GetPromptResult:
        """Generate prompt for document comparison analysis."""
        document_ids = arguments.get("document_ids", "")
        criteria = arguments.get("comparison_criteria", "overall approach and findings")
        
        return types.GetPromptResult(
            description=f"Compare documents {document_ids} on {criteria}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Compare documents {document_ids} focusing on {criteria}.

**Comparison Analysis Workflow:**

**Step 1: Document Overview**
For each document ID in {document_ids}:
- Use `get_document` to understand basic information
- Use `get_document_structure` to see organization and scope
- Note publication context, length, and intended audience

**Step 2: Focused Content Analysis**
- Use `get_chunk_content` for sections relevant to {criteria}
- Extract key information related to comparison focus
- Identify unique approaches or perspectives

**Step 3: Comparative Analysis**
Create systematic comparison:

**Similarities in {criteria}:**
- Common themes or approaches
- Shared conclusions or findings
- Overlapping methodologies

**Key Differences in {criteria}:**
- Contrasting viewpoints or methods
- Different emphasis or focus areas
- Varying conclusions or recommendations

**Strengths and Limitations:**
- What each document does well
- Potential weaknesses or gaps
- Credibility and evidence quality

**Step 4: Synthesis**
- Integration of insights across documents
- Implications of differences found
- Recommendations based on comparison

Focus specifically on {criteria} throughout the analysis."""
                    )
                )
            ]
        )

    def _get_extract_concepts_prompt(self, arguments: Dict[str, str]) -> types.GetPromptResult:
        """Generate prompt for key concept extraction."""
        document_id = arguments.get("document_id", "")
        concept_type = arguments.get("concept_type", "all")
        
        return types.GetPromptResult(
            description=f"Extract {concept_type} concepts from document {document_id}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Extract key {concept_type} from document {document_id}.

**Concept Extraction Workflow:**

**Step 1: Document Analysis**
- Use `get_document` with document_id: {document_id}
- Use `get_document_structure` to identify relevant sections
- Focus on sections likely to contain {concept_type}

**Step 2: Content Review**
- Use `get_chunk_content` for relevant chapters/sections
- Scan for {self._get_concept_indicators(concept_type)}

**Step 3: Concept Organization**
Create structured list of {concept_type}:

{self._get_concept_template(concept_type)}

**Step 4: Quality Assurance**
- Ensure accuracy of definitions
- Verify concept relationships
- Check for completeness within scope

Focus on extracting the most important {concept_type} that readers need to understand."""
                    )
                )
            ]
        )

    def _get_research_questions_prompt(self, arguments: Dict[str, str]) -> types.GetPromptResult:
        """Generate prompt for creating research questions and discussion points."""
        document_id = arguments.get("document_id", "")
        question_level = arguments.get("question_level", "intermediate")
        
        return types.GetPromptResult(
            description=f"Generate {question_level} research questions from document {document_id}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Generate {question_level} research questions from document {document_id}.

**Question Generation Workflow:**

**Step 1: Content Analysis**
- Use `get_document` with document_id: {document_id}
- Use `get_document_structure` to understand organization
- Use `get_chunk_content` for key sections

**Step 2: Question Development**
Create questions at {question_level} level:

{self._get_question_guidelines(question_level)}

**Step 3: Question Categories**
Organize questions by type:

**Comprehension Questions:**
- Test understanding of main concepts
- Check recall of key information

**Analysis Questions:**
- Examine relationships and patterns
- Explore cause and effect

**Evaluation Questions:**
- Assess arguments and evidence
- Judge quality and credibility

**Synthesis Questions:**
- Connect ideas across sections
- Relate to broader concepts

**Step 4: Discussion Prompts**
Add open-ended discussion points for:
- Classroom or study group discussion
- Personal reflection and critical thinking
- Real-world applications

Ensure questions match {question_level} cognitive complexity."""
                    )
                )
            ]
        )

    def _get_analysis_framework(self, focus_area: str) -> str:
        """Get analysis framework based on focus area."""
        frameworks = {
            "overview": """- Document purpose and main themes
- Target audience and context
- Key arguments or findings
- Overall structure and organization
- Significance and contributions""",
            
            "key_concepts": """- Core concepts and definitions
- Theoretical frameworks used
- Important terminology
- Concept relationships and hierarchies
- Applications and examples""",
            
            "methodology": """- Research methods employed
- Data collection and analysis
- Experimental design or approach
- Validity and reliability considerations
- Limitations and constraints""",
            
            "conclusions": """- Main findings and results
- Evidence supporting conclusions
- Implications and significance
- Limitations of findings
- Future research directions""",
            
            "critical_analysis": """- Strengths and weaknesses of arguments
- Quality and credibility of evidence
- Logical consistency and coherence
- Bias or perspective considerations
- Alternative interpretations"""
        }
        
        return frameworks.get(focus_area, frameworks["overview"])

    def _get_summary_guidelines(self, summary_style: str) -> str:
        """Get guidelines for different summary styles."""
        guidelines = {
            "brief": """- Focus on 2-3 most important points
- Use bullet points or short paragraphs
- Emphasize key takeaways
- Avoid detailed examples""",
            
            "standard": """- Cover main themes with supporting details
- Include key examples or evidence
- Use clear paragraph structure
- Balance breadth with depth""",
            
            "detailed": """- Comprehensive coverage of all major points
- Include relevant examples and case studies
- Explain complex concepts thoroughly
- Maintain logical flow throughout"""
        }
        
        return guidelines.get(summary_style, guidelines["standard"])

    def _get_save_instructions(self, save_result: bool, chunk_id: str, summary_style: str) -> str:
        """Get instructions for saving summary if requested."""
        if not save_result:
            return ""
        
        return f"""
**Step 4: Save Summary with Export-Ready Metadata**
- Use `save_summary` tool with:
  - chunk_id: {chunk_id}
  - summary_type: "{summary_style}"
  - summary_content: [your generated summary text]
  - model_name: "human-guided" or your model identifier (e.g., "gpt-4", "claude-3")
  - metadata: Include export-relevant information:
    {{
      "focus_areas": ["key_concepts", "methodology", "conclusions"],
      "summary_approach": "comprehensive" or "focused" or "analytical",
      "content_highlights": ["main theories", "case studies", "formulas"],
      "difficulty_level": "beginner", "intermediate", "advanced",
      "learning_objectives": ["understand X", "analyze Y", "apply Z"],
      "source_info": {{
        "chapter_title": "[chapter title]",
        "page_range": "pp. 45-67",
        "section_topics": ["topic1", "topic2"]
      }},
      "export_tags": ["study-notes", "exam-prep", "reference"],
      "created_by": "AI Assistant",
      "review_status": "generated"
    }}

**Step 5: Export to File (Recommended)**
After saving, create a markdown file for the user:
- Use `export_summary_to_file` with the returned summary_id and desired file_path (e.g., "C:/Users/Documents/{summary_style}_summary.md")
- This will include all metadata in YAML frontmatter for better organization
- Or use `create_markdown_file` for custom formatting with metadata integration

**Export Benefits:**
- YAML frontmatter preserves all metadata for future reference
- Portable format for note-taking apps, documentation systems
- Searchable and organizable with metadata tags
- Professional appearance with structured information"""

    def _get_concept_indicators(self, concept_type: str) -> str:
        """Get indicators to look for based on concept type."""
        indicators = {
            "definitions": "terms in bold/italics, glossary entries, 'defined as', 'refers to'",
            "theories": "theoretical frameworks, models, paradigms, 'theory of'",
            "methods": "procedures, techniques, approaches, step-by-step processes",
            "formulas": "mathematical expressions, equations, calculations",
            "all": "key terms, theories, methods, formulas, and important concepts"
        }
        
        return indicators.get(concept_type, indicators["all"])

    def _get_concept_template(self, concept_type: str) -> str:
        """Get template for organizing extracted concepts."""
        templates = {
            "definitions": """**Key Terms and Definitions:**
- **Term 1:** Clear definition with context
- **Term 2:** Clear definition with context
[Continue for all important terms]""",
            
            "theories": """**Theoretical Frameworks:**
- **Theory 1:** Description and key principles
- **Theory 2:** Description and applications
[Continue for all theories mentioned]""",
            
            "methods": """**Methods and Procedures:**
- **Method 1:** Steps and applications
- **Method 2:** Process and use cases
[Continue for all methods described]""",
            
            "formulas": """**Formulas and Equations:**
- **Formula 1:** Mathematical expression and variables
- **Formula 2:** Equation and applications
[Continue for all formulas presented]""",
            
            "all": """**Comprehensive Concept List:**
- **Definitions:** Key terms with clear explanations
- **Theories:** Frameworks and models discussed
- **Methods:** Procedures and techniques
- **Formulas:** Mathematical expressions (if any)
- **Other Key Concepts:** Additional important ideas"""
        }
        
        return templates.get(concept_type, templates["all"])

    def _get_question_guidelines(self, question_level: str) -> str:
        """Get guidelines for question complexity levels."""
        guidelines = {
            "basic": """- Focus on recall and comprehension
- "What is...?", "Who said...?", "When did...?"
- Test understanding of key facts and concepts
- Straightforward, factual questions""",
            
            "intermediate": """- Analysis and application questions
- "How does...?", "Why is...?", "What would happen if...?"
- Connect concepts and explore relationships
- Moderate complexity requiring explanation""",
            
            "advanced": """- Synthesis and evaluation questions
- "Compare and contrast...", "Analyze the effectiveness..."
- Multi-step reasoning and critical thinking
- Complex scenarios and problem-solving""",
            
            "critical_thinking": """- High-level analysis and judgment questions
- "Evaluate the argument that...", "What are the implications..."
- Challenge assumptions and explore alternatives
- Open-ended questions requiring original thinking"""
        }
        
        return guidelines.get(question_level, guidelines["intermediate"])

    def _get_export_to_markdown_prompt(self, arguments: Dict[str, str]) -> types.GetPromptResult:
        """Generate prompt for exporting content to markdown files."""
        export_type = arguments.get("export_type", "summary")
        target_id = arguments.get("target_id", "")
        file_path = arguments.get("file_path", "C:/Users/Documents/export.md")
        include_metadata = arguments.get("include_metadata", "true").lower() == "true"
        
        export_instructions = {
            "summary": f"""**Export Existing Summary:**
- Use `export_summary_to_file` with:
  - summary_id: {target_id}
  - file_path: "{file_path}"
  - include_metadata: {include_metadata}
  - include_source_info: true
- This will create a standalone markdown file with the summary content""",
            
            "document_structure": f"""**Export Document Structure:**
- Use `export_document_structure_to_file` with:
  - document_id: {target_id}
  - file_path: "{file_path}"
  - include_word_counts: true
  - include_metadata: {include_metadata}
- This will create a table of contents with all chunks/chapters""",
            
            "analysis": f"""**Export Custom Analysis:**
First, create your analysis content, then:
- Use `create_markdown_file` with:
  - content: [your analysis text in markdown format]
  - file_path: "{file_path}"
  - title: "Document Analysis"
  - metadata: {{"analysis_type": "comprehensive", "target_id": "{target_id}"}}""",
            
            "custom": f"""**Create Custom Markdown File:**
- Use `create_markdown_file` with:
  - content: [your custom content in markdown format]
  - file_path: "{file_path}"
  - title: [optional title]
  - metadata: [optional metadata object]
  - overwrite: false (set true to replace existing files)"""
        }
        
        return types.GetPromptResult(
            description=f"Export {export_type} (ID: {target_id}) to markdown file",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Export content to a markdown file for user download.

**Export Workflow:**

**Step 1: Understand Request**
- Export Type: {export_type}
- Target ID: {target_id}
- Output Path: {file_path}
- Include Metadata: {include_metadata}

**Step 2: Execute Export**
{export_instructions.get(export_type, export_instructions["custom"])}

**Step 3: Confirm Success**
- Verify the file was created successfully
- Report the file location and size
- Mention any metadata included

**Available Export Tools:**
- `export_summary_to_file` - Export existing summaries with metadata
- `export_document_structure_to_file` - Export document table of contents  
- `create_markdown_file` - Create custom markdown files with any content

**File Features:**
- YAML frontmatter for metadata
- UTF-8 encoding for international characters
- Automatic directory creation
- Overwrite protection (specify overwrite=true if needed)

The exported file will be ready for use in documentation systems, note-taking apps, or any markdown-compatible tool."""
                    )
                )
            ]
        )

    async def _initialize_dependencies(self) -> None:
        """Initialize application dependencies."""
        try:
            # Initialize application with container
            self.container = initialize_application(self.database_path)

            # Get MCP handler from container
            self.mcp_handler = self.container.get_mcp_handler()

            logger.info("Study Buddy MCP Server dependencies initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize dependencies: {e}")
            raise

    async def run(self) -> None:
        """Run the MCP server."""
        try:
            logger.info("DEBUG: Starting MCP server initialization...")
            
            # Initialize dependencies
            await self._initialize_dependencies()
            logger.info("DEBUG: Dependencies initialized successfully")

            # Run MCP server with stdio transport
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                logger.info("Starting Study Buddy MCP Server...")
                
                try:
                    # Create initialization options properly
                    logger.info("DEBUG: Creating initialization options...")
                    init_options = InitializationOptions(
                        server_name="study-buddy",
                        server_version="1.0.0",
                        capabilities=types.ServerCapabilities(
                            tools=types.ToolsCapability(),
                            prompts=types.PromptsCapability()
                        )
                    )
                    logger.info("DEBUG: Initialization options created successfully")
                    
                    logger.info("DEBUG: About to call server.run()...")
                    await self.server.run(
                        read_stream,
                        write_stream,
                        init_options
                    )
                    logger.info("DEBUG: server.run() completed successfully")
                    
                except Exception as e:
                    logger.error(f"DEBUG: Error in server.run(): {e}", exc_info=True)
                    raise

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            raise
        finally:
            await self._cleanup()

    async def _cleanup(self) -> None:
        """Clean up resources on shutdown."""
        try:
            if self.container:
                self.container.close()
            logger.info("Study Buddy MCP Server shut down gracefully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main() -> None:
    """Main entry point for Study Buddy MCP Server."""
    # Get database path from environment or use default
    database_path = os.getenv("STUDY_BUDDY_DB_PATH")

    # Create and run server
    server = StudyBuddyMCPServer(database_path)
    await server.run()


if __name__ == "__main__":
    # Run the server
    asyncio.run(main())
