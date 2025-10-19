"""
Systematic Literature Review (SLR) MCP Server - Main Entry Point.

This module provides the main MCP server implementation for conducting
systematic literature reviews using the mcp library and Clean Architecture
principles with proper dependency injection.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions

if TYPE_CHECKING:
    from .container import Container

# Handle imports for both module and direct execution
try:
    from .container import initialize_application  # type: ignore
    from .handlers.mcp_handler import SLRMCPHandler  # type: ignore
except ImportError:
    # Fallback for direct execution
    sys.path.append(str(Path(__file__).parent))
    from container import initialize_application  # type: ignore[no-redef,assignment]
    from handlers.mcp_handler import SLRMCPHandler  # type: ignore[no-redef]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SLRMCPServer:
    """
    Systematic Literature Review MCP Server implementation.

    This class provides the main MCP server using Clean Architecture principles:
    - Dependency injection via Container
    - Business logic separation via services
    - MCP protocol handling via SLRMCPHandler
    - Proper error handling and logging
    """

    def __init__(self, connection_string: Optional[str] = None, project_root: Optional[Path] = None):
        """
        Initialize SLR MCP Server.

        Args:
            connection_string: Optional database connection string (SQLite path or PostgreSQL URL)
            project_root: Optional path to project root for document storage
        """
        self.connection_string = connection_string
        self.project_root = project_root or Path.cwd()
        self.container: Optional['Container'] = None
        self.mcp_handler: Optional[SLRMCPHandler] = None

        # Create MCP server instance
        logger.info("Creating SLR MCP server instance...")
        self.server = Server("slr-mcp-server")
        logger.info("SLR MCP server instance created")

        # Setup MCP server handlers
        logger.info("Registering MCP handlers...")
        self._register_handlers()
        logger.info("MCP handlers registered successfully")

    def _register_handlers(self) -> None:
        """Register all MCP server handlers."""
        
        logger.info("Starting SLR MCP handler registration...")

        # Native MCP Tool Registration
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """Handle MCP list_tools request for systematic literature review tools."""
            try:
                return [
                    # Research Document Management Tools
                    types.Tool(
                        name="upload_paper",
                        description="Upload and parse academic research paper (PDF, DOCX)",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string", "description": "Path to research paper file"},
                                "title": {"type": "string", "description": "Optional paper title override"},
                                "authors": {"type": "array", "items": {"type": "string"}, "description": "Paper authors"},
                                "publication_year": {"type": "integer", "description": "Year of publication"},
                                "doi": {"type": "string", "description": "DOI identifier"},
                                "tags": {"type": "array", "items": {"type": "string"}, "description": "Research tags"}
                            },
                            "required": ["file_path"]
                        }
                    ),
                    types.Tool(
                        name="upload_bibliography_batch",
                        description="Upload and parse bibliography file containing multiple papers (BibTeX, RIS)",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string", "description": "Path to bibliography file (.bib or .ris)"},
                                "tags": {"type": "array", "items": {"type": "string"}, "description": "Research tags to apply to all papers"},
                                "auto_extract_metadata": {"type": "boolean", "default": True, "description": "Whether to extract metadata automatically"}
                            },
                            "required": ["file_path"]
                        }
                    ),
                    types.Tool(
                        name="detect_remove_duplicates",
                        description="Detect and optionally remove duplicate papers from the corpus using title similarity and DOI matching",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "similarity_threshold": {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.85, "description": "Title similarity threshold for duplicate detection (0.0-1.0)"},
                                "dry_run": {"type": "boolean", "default": True, "description": "If true, only detect duplicates without removing them"}
                            }
                        }
                    ),
                    types.Tool(
                        name="get_paper",
                        description="Retrieve research paper information by ID",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "paper_id": {"type": "integer", "description": "Paper ID to retrieve"}
                            },
                            "required": ["paper_id"]
                        }
                    ),
                    types.Tool(
                        name="list_papers",
                        description="List research papers with optional filters",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "filters": {
                                    "type": "object",
                                    "properties": {
                                        "authors": {"type": "array", "items": {"type": "string"}},
                                        "publication_year": {"type": "integer"},
                                        "tags": {"type": "array", "items": {"type": "string"}},
                                        "quality_score_min": {"type": "number"}
                                    }
                                },
                                "limit": {"type": "integer", "default": 20},
                                "offset": {"type": "integer", "default": 0}
                            }
                        }
                    ),
                    types.Tool(
                        name="search_papers",
                        description="Full-text search across research papers and chunks",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Search query"},
                                "search_type": {"type": "string", "enum": ["semantic", "keyword", "citation"], "default": "semantic"},
                                "filters": {"type": "object", "description": "Optional search filters"},
                                "limit": {"type": "integer", "default": 20}
                            },
                            "required": ["query"]
                        }
                    ),

                    # Quality Assessment Tools
                    types.Tool(
                        name="assess_quality",
                        description="Perform systematic quality assessment using PRISMA guidelines",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "paper_id": {"type": "integer", "description": "Paper ID to assess"},
                                "assessment_framework": {"type": "string", "enum": ["PRISMA", "CASP", "JBI"], "default": "PRISMA"},
                                "reviewer_id": {"type": "string", "description": "Reviewer identifier"},
                                "criteria": {"type": "object", "description": "Custom assessment criteria"}
                            },
                            "required": ["paper_id"]
                        }
                    ),
                    types.Tool(
                        name="get_quality_assessment",
                        description="Retrieve quality assessment for a paper",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "paper_id": {"type": "integer", "description": "Paper ID"},
                                "reviewer_id": {"type": "string", "description": "Optional reviewer filter"}
                            },
                            "required": ["paper_id"]
                        }
                    ),
                    types.Tool(
                        name="calculate_inter_rater_reliability",
                        description="Calculate inter-rater reliability for quality assessments",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "paper_ids": {"type": "array", "items": {"type": "integer"}, "description": "Papers to analyze"},
                                "reviewer_ids": {"type": "array", "items": {"type": "string"}, "description": "Reviewers to compare"}
                            },
                            "required": ["paper_ids", "reviewer_ids"]
                        }
                    ),

                    # Citation Analysis Tools
                    types.Tool(
                        name="analyze_citations",
                        description="Analyze citation networks and reference patterns",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "paper_id": {"type": "integer", "description": "Paper ID to analyze"},
                                "analysis_type": {"type": "string", "enum": ["forward", "backward", "network"], "default": "network"},
                                "depth": {"type": "integer", "default": 2, "description": "Citation depth to analyze"}
                            },
                            "required": ["paper_id"]
                        }
                    ),
                    types.Tool(
                        name="detect_citation_patterns",
                        description="Detect patterns and trends in citation data",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "corpus_filter": {"type": "object", "description": "Filter for paper corpus"},
                                "pattern_type": {"type": "string", "enum": ["temporal", "thematic", "collaboration"], "default": "temporal"}
                            }
                        }
                    ),

                    # Research Question and Hypothesis Tools
                    types.Tool(
                        name="validate_research_question",
                        description="Validate research questions using PICO/SPIDER frameworks",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "research_question": {"type": "string", "description": "Research question to validate"},
                                "framework": {"type": "string", "enum": ["PICO", "SPIDER"], "default": "PICO"},
                                "domain": {"type": "string", "description": "Research domain"}
                            },
                            "required": ["research_question"]
                        }
                    ),
                    types.Tool(
                        name="analyze_hypotheses",
                        description="Extract and analyze hypotheses from research papers",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "paper_id": {"type": "integer", "description": "Paper ID to analyze"},
                                "hypothesis_type": {"type": "string", "enum": ["explicit", "implicit", "all"], "default": "all"}
                            },
                            "required": ["paper_id"]
                        }
                    ),
                    types.Tool(
                        name="synthesize_evidence",
                        description="Synthesize evidence across multiple papers using meta-analysis",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "paper_ids": {"type": "array", "items": {"type": "integer"}, "description": "Papers to synthesize"},
                                "synthesis_method": {"type": "string", "enum": ["narrative", "meta-analysis", "meta-synthesis"], "default": "narrative"},
                                "outcome_measures": {"type": "array", "items": {"type": "string"}, "description": "Outcome measures to focus on"}
                            },
                            "required": ["paper_ids"]
                        }
                    ),

                    # Academic Indexing and Enhancement Tools
                    types.Tool(
                        name="index_paper",
                        description="Create intelligent academic chunks from research paper content",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "paper_id": {"type": "integer", "description": "Paper ID to index"},
                                "strategy": {"type": "string", "enum": ["academic_section", "citation_aware", "topic_based"], "default": "academic_section"},
                                "force": {"type": "boolean", "default": False, "description": "Force re-indexing"}
                            },
                            "required": ["paper_id"]
                        }
                    ),
                    types.Tool(
                        name="get_paper_structure",
                        description="Get academic paper structure (sections, subsections, etc.)",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "paper_id": {"type": "integer", "description": "Paper ID"}
                            },
                            "required": ["paper_id"]
                        }
                    ),
                    types.Tool(
                        name="get_chunk_content",
                        description="Retrieve full text content of a specific academic chunk",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "chunk_id": {"type": "integer", "description": "Chunk ID"}
                            },
                            "required": ["chunk_id"]
                        }
                    ),

                    # Export and Reporting Tools
                    types.Tool(
                        name="generate_slr_report",
                        description="Generate comprehensive systematic literature review report",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "paper_ids": {"type": "array", "items": {"type": "integer"}, "description": "Papers to include"},
                                "report_format": {"type": "string", "enum": ["markdown", "latex", "docx"], "default": "markdown"},
                                "include_quality_assessment": {"type": "boolean", "default": True},
                                "include_citation_analysis": {"type": "boolean", "default": True},
                                "output_path": {"type": "string", "description": "Output file path"}
                            },
                            "required": ["paper_ids", "output_path"]
                        }
                    ),
                    types.Tool(
                        name="export_citation_network",
                        description="Export citation network for visualization",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "paper_ids": {"type": "array", "items": {"type": "integer"}, "description": "Papers to include"},
                                "format": {"type": "string", "enum": ["gephi", "cytoscape", "json"], "default": "json"},
                                "output_path": {"type": "string", "description": "Output file path"}
                            },
                            "required": ["paper_ids", "output_path"]
                        }
                    ),

                    # SLR Workflow Guidance Tools
                    types.Tool(
                        name="create_slr_project",
                        description="Initialize new SLR project from description file (PDF/Markdown) or manually",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "project_name": {"type": "string", "description": "Project name in slug format (e.g., 'software-designs')"},
                                "description": {"type": "string", "description": "Project description (optional)"},
                                "file_path": {"type": "string", "description": "Path to PDF or Markdown file for metadata extraction (optional)"},
                                "research_questions": {"type": "array", "items": {"type": "string"}, "description": "List of research questions (optional)"},
                                "extract_metadata": {"type": "boolean", "default": True, "description": "Whether to extract metadata from file (default: True)"}
                            },
                            "required": ["project_name"]
                        }
                    ),
                    types.Tool(
                        name="get_slr_progress",
                        description="Get comprehensive progress dashboard for SLR project",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "project_id": {"type": "integer", "description": "SLR project ID"}
                            },
                            "required": ["project_id"]
                        }
                    ),
                    types.Tool(
                        name="get_next_steps",
                        description="Get AI-powered recommendations for next actions in SLR workflow",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "project_id": {"type": "integer", "description": "SLR project ID"},
                                "current_phase": {"type": "string", "enum": ["planning", "search", "screening", "quality_assessment", "data_extraction", "analysis", "reporting"], "description": "Current project phase"}
                            },
                            "required": ["project_id"]
                        }
                    ),
                    types.Tool(
                        name="create_screening_workflow",
                        description="Setup multi-stage screening process for study selection",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "project_id": {"type": "integer", "description": "SLR project ID"},
                                "inclusion_criteria": {"type": "array", "items": {"type": "string"}, "description": "Inclusion criteria"},
                                "exclusion_criteria": {"type": "array", "items": {"type": "string"}, "description": "Exclusion criteria"},
                                "reviewers": {"type": "array", "items": {"type": "string"}, "description": "Reviewer IDs"},
                                "screening_stages": {"type": "array", "items": {"type": "string"}, "enum": ["title_abstract", "full_text", "final_selection"], "description": "Screening stages"}
                            },
                            "required": ["project_id", "inclusion_criteria", "exclusion_criteria", "reviewers"]
                        }
                    ),
                    types.Tool(
                        name="screen_paper",
                        description="Record screening decision with rationale for study selection",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "project_id": {"type": "integer", "description": "SLR project ID"},
                                "paper_id": {"type": "integer", "description": "Paper ID to screen"},
                                "reviewer_id": {"type": "string", "description": "Reviewer identifier"},
                                "stage": {"type": "string", "enum": ["title_abstract", "full_text", "final_selection"], "description": "Screening stage"},
                                "decision": {"type": "string", "enum": ["include", "exclude", "uncertain"], "description": "Screening decision"},
                                "reason": {"type": "string", "description": "Reason for decision"},
                                "confidence_level": {"type": "number", "minimum": 0.0, "maximum": 1.0, "description": "Confidence in decision (0-1)"},
                                "exclusion_criteria": {"type": "array", "items": {"type": "string"}, "description": "Applicable exclusion criteria"}
                            },
                            "required": ["project_id", "paper_id", "reviewer_id", "stage", "decision"]
                        }
                    ),
                    types.Tool(
                        name="get_slr_guide",
                        description="Interactive methodology guidance and best practices for SLR",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "topic": {"type": "string", "description": "SLR methodology topic"},
                                "experience_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"], "default": "beginner"},
                                "current_phase": {"type": "string", "enum": ["planning", "search", "screening", "quality_assessment", "data_extraction", "analysis", "reporting"], "description": "Current SLR phase"}
                            },
                            "required": ["topic"]
                        }
                    )
                ]
            except Exception as e:
                logger.error(f"Error listing SLR tools: {e}")
                return []

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> List[types.TextContent]:
            """Handle MCP tool calls for systematic literature review operations."""
            try:
                # Ensure MCP handler is initialized
                if self.mcp_handler is None:
                    await self._initialize_dependencies()

                # Map tool names to handler method names
                handler_method_name = f"handle_{name}" if not hasattr(self.mcp_handler, name) else name
                handler_method = getattr(self.mcp_handler, handler_method_name, None)
                
                if handler_method is None:
                    # Check if it's a workflow tool (these don't have handle_ prefix)
                    workflow_tools = ['create_slr_project', 'get_slr_progress', 'get_next_steps', 
                                    'create_screening_workflow', 'screen_paper', 'get_slr_guide']
                    if name in workflow_tools:
                        handler_method = getattr(self.mcp_handler, name, None)
                    
                if handler_method is None:
                    raise ValueError(f"Unknown SLR tool: {name}")

                # Debug logging
                logger.debug(f"SLR tool {name} -> {handler_method_name} handler type: {type(handler_method)}")
                
                if not callable(handler_method):
                    raise ValueError(f"SLR tool {name} is not callable: {type(handler_method)}")

                # Call the handler (handle async properly)
                if arguments is None:
                    arguments = {}

                if asyncio.iscoroutinefunction(handler_method):
                    result = await handler_method(arguments)
                else:
                    result = handler_method(arguments)

                # Debug logging
                logger.debug(f"SLR handler {name} returned: {type(result)} - {result}")

                # Handle different result types
                if hasattr(result, 'content') and hasattr(result, 'isError'):
                    # CallToolResult object
                    if getattr(result, 'isError', False):
                        content = result.content[0].text if result.content else "Unknown error"
                        return [types.TextContent(type="text", text=f"❌ Error: {name}\n\n{content}")]
                    else:
                        content = result.content[0].text if result.content else "Success"
                        return [types.TextContent(type="text", text=f"✅ Success: {name}\n\n{content}")]
                elif isinstance(result, dict):
                    # Dictionary result (workflow tools)
                    if result.get("success", False):
                        content = f"✅ Success: {name}\n\n"
                        for key, value in result.items():
                            if key != "success":
                                content += f"**{key}**: {value}\n"
                        return [types.TextContent(type="text", text=content)]
                    else:
                        error_msg = result.get("error", "Unknown error")
                        return [types.TextContent(type="text", text=f"❌ Error: {name}\n\n{error_msg}")]
                else:
                    logger.error(f"SLR handler {name} returned unexpected type: {type(result)}")
                    return [types.TextContent(
                        type="text", 
                        text=f"❌ Error: {name} handler returned {type(result)} instead of expected format"
                    )]

            except Exception as e:
                logger.error(f"Error calling SLR tool {name}: {e}", exc_info=True)
                return [types.TextContent(
                    type="text",
                    text=f"❌ Error executing {name}: {str(e)}"
                )]

    async def _initialize_dependencies(self) -> None:
        """Initialize application dependencies."""
        try:
            # Initialize application with container
            self.container = await initialize_application(self.connection_string, self.project_root)

            # Get MCP handler from container
            self.mcp_handler = self.container.get_mcp_handler()

            logger.info("SLR MCP Server dependencies initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize SLR dependencies: {e}")
            raise

    async def run(self) -> None:
        """Run the SLR MCP server."""
        try:
            logger.info("Starting SLR MCP server initialization...")
            
            # Initialize dependencies
            await self._initialize_dependencies()
            logger.info("SLR dependencies initialized successfully")

            # Run MCP server with stdio transport
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                logger.info("Starting Systematic Literature Review MCP Server...")
                
                try:
                    # Create initialization options
                    logger.info("Creating SLR initialization options...")
                    init_options = InitializationOptions(
                        server_name="slr-mcp-server",
                        server_version="1.0.0",
                        capabilities=types.ServerCapabilities(
                            tools=types.ToolsCapability()
                        )
                    )
                    logger.info("SLR initialization options created successfully")
                    
                    logger.info("Starting SLR server.run()...")
                    await self.server.run(
                        read_stream,
                        write_stream,
                        init_options
                    )
                    logger.info("SLR server.run() completed successfully")
                    
                except Exception as e:
                    logger.error(f"Error in SLR server.run(): {e}", exc_info=True)
                    raise

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down SLR server...")
        except Exception as e:
            logger.error(f"SLR server error: {e}", exc_info=True)
            raise
        finally:
            await self._cleanup()

    async def _cleanup(self) -> None:
        """Clean up resources on shutdown."""
        try:
            if self.container:
                self.container.close()
            logger.info("SLR MCP Server shut down gracefully")
        except Exception as e:
            logger.error(f"Error during SLR cleanup: {e}")


async def main() -> None:
    """Main entry point for SLR MCP Server."""
    # Import database configuration system
    try:
        from .database.config import DatabaseConfig, get_database_path  # type: ignore
    except ImportError:
        # Fallback for direct execution
        sys.path.append(str(Path(__file__).parent))
        from database.config import DatabaseConfig, get_database_path  # type: ignore[no-redef]
    
    # Log database configuration and get database path
    DatabaseConfig.log_configuration()
    database_path = get_database_path()
    
    # Get project root from environment
    project_root_env = os.getenv("PROJECT_ROOT") or os.getenv("SLR_PROJECT_ROOT")
    project_root = Path(project_root_env) if project_root_env else None

    # Create and run server
    server = SLRMCPServer(database_path, project_root)
    await server.run()


if __name__ == "__main__":
    # Run the server
    asyncio.run(main())