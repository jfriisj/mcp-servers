"""
Systematic Literature Review MCP Server.

Provides MCP-compliant tools for academic research workflows including
document management, quality assessment, research question validation,
hypothesis testing, and evidence synthesis.
"""

import logging
from typing import Any, Dict, List, Optional

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .handlers.mcp_handler import SLRMCPHandler
from .services import (
    ResearchDocumentService, QualityAssessmentService,
    ResearchQuestionService, HypothesisAnalysisService,
    AcademicChunkingService
)
from .repositories import PaperRepository
from .database import Database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server
app = Server("slr-mcp-server")

# Global handler instance (will be initialized with dependencies)
handler: Optional[SLRMCPHandler] = None


def initialize_dependencies():
    """Initialize service dependencies and handler."""
    global handler
    
    # Initialize database
    database = Database("slr_database.db")
    
    # Initialize repositories
    paper_repository = PaperRepository(database)
    
    # Initialize services
    research_document_service = ResearchDocumentService(paper_repository)
    quality_assessment_service = QualityAssessmentService(paper_repository)
    research_question_service = ResearchQuestionService()
    hypothesis_analysis_service = HypothesisAnalysisService(paper_repository)
    academic_chunking_service = AcademicChunkingService(paper_repository)
    
    # Initialize MCP handler
    handler = SLRMCPHandler(
        research_document_service=research_document_service,
        quality_assessment_service=quality_assessment_service,
        research_question_service=research_question_service,
        hypothesis_analysis_service=hypothesis_analysis_service,
        academic_chunking_service=academic_chunking_service
    )
    logger.info("SLR MCP Server dependencies initialized")


@app.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available MCP tools for systematic literature review."""
    return [
        types.Tool(
            name="upload-paper",
            description="Upload and process research paper with metadata extraction",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the research paper file (PDF or text)"
                    },
                    "title": {
                        "type": "string",
                        "description": "Paper title (optional, will be extracted if not provided)"
                    },
                    "authors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of author names (optional)"
                    },
                    "doi": {
                        "type": "string",
                        "description": "Digital Object Identifier (optional)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Classification tags (optional)"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="assess-quality",
            description="Assess paper quality using systematic evaluation frameworks",
            inputSchema={
                "type": "object",
                "properties": {
                    "paper_id": {
                        "type": "integer",
                        "description": "ID of the paper to assess"
                    },
                    "framework": {
                        "type": "string",
                        "enum": ["prisma", "strobe", "consort", "quadas"],
                        "default": "prisma",
                        "description": "Quality assessment framework"
                    },
                    "reviewer_id": {
                        "type": "string",
                        "default": "default",
                        "description": "Identifier for the reviewer"
                    },
                    "criterion_scores": {
                        "type": "object",
                        "description": "Manual criterion scores override (optional)"
                    }
                },
                "required": ["paper_id"]
            }
        ),
        types.Tool(
            name="validate-research-question",
            description="Validate research question using PICO or SPIDER frameworks",
            inputSchema={
                "type": "object",
                "properties": {
                    "question_text": {
                        "type": "string",
                        "description": "The research question to validate"
                    },
                    "framework": {
                        "type": "string",
                        "enum": ["pico", "spider"],
                        "default": "pico",
                        "description": "Validation framework to use"
                    }
                },
                "required": ["question_text"]
            }
        ),
        types.Tool(
            name="analyze-citations",
            description="Perform citation network analysis on research paper",
            inputSchema={
                "type": "object",
                "properties": {
                    "paper_id": {
                        "type": "integer",
                        "description": "ID of the paper to analyze"
                    }
                },
                "required": ["paper_id"]
            }
        ),
        types.Tool(
            name="test-hypothesis",
            description="Test research hypothesis against evidence from papers",
            inputSchema={
                "type": "object",
                "properties": {
                    "hypothesis_text": {
                        "type": "string",
                        "description": "The research hypothesis to test"
                    },
                    "paper_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of paper IDs containing evidence"
                    },
                    "significance_level": {
                        "type": "number",
                        "default": 0.05,
                        "description": "Statistical significance level (alpha)"
                    }
                },
                "required": ["hypothesis_text", "paper_ids"]
            }
        ),
        types.Tool(
            name="index-paper",
            description="Create intelligent academic chunks and indexes for paper",
            inputSchema={
                "type": "object",
                "properties": {
                    "paper_id": {
                        "type": "integer",
                        "description": "ID of the paper to index"
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["section_based", "semantic", "hybrid", "full_text", "citation_aware"],
                        "default": "hybrid",
                        "description": "Chunking strategy to use"
                    },
                    "optimization_level": {
                        "type": "string",
                        "enum": ["basic", "intermediate", "advanced"],
                        "default": "intermediate",
                        "description": "Optimization level for chunking"
                    },
                    "force": {
                        "type": "boolean",
                        "default": False,
                        "description": "Force reindexing even if paper is already indexed"
                    }
                },
                "required": ["paper_id"]
            }
        ),
        types.Tool(
            name="synthesize-evidence",
            description="Synthesize evidence from multiple papers for a research question",
            inputSchema={
                "type": "object",
                "properties": {
                    "research_question": {
                        "type": "string",
                        "description": "The research question to investigate"
                    },
                    "paper_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of paper IDs to analyze"
                    },
                    "include_meta_analysis": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether to include meta-analysis in synthesis"
                    }
                },
                "required": ["research_question", "paper_ids"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle MCP tool calls."""
    if handler is None:
        return [types.TextContent(
            type="text",
            text='{"success": false, "error": "Server not initialized", "error_type": "system"}'
        )]
    
    try:
        result = None
        
        if name == "upload-paper":
            result = handler.upload_paper(
                file_path=arguments["file_path"],
                title=arguments.get("title"),
                authors=arguments.get("authors"),
                doi=arguments.get("doi"),
                tags=arguments.get("tags")
            )
        elif name == "assess-quality":
            result = handler.assess_quality(
                paper_id=arguments["paper_id"],
                framework=arguments.get("framework", "prisma"),
                reviewer_id=arguments.get("reviewer_id", "default"),
                criterion_scores=arguments.get("criterion_scores")
            )
        elif name == "validate-research-question":
            result = handler.validate_research_question(
                question_text=arguments["question_text"],
                framework=arguments.get("framework", "pico")
            )
        elif name == "analyze-citations":
            result = handler.analyze_citations(
                paper_id=arguments["paper_id"]
            )
        elif name == "test-hypothesis":
            result = handler.test_hypothesis(
                hypothesis_text=arguments["hypothesis_text"],
                paper_ids=arguments["paper_ids"],
                significance_level=arguments.get("significance_level", 0.05)
            )
        elif name == "index-paper":
            result = handler.index_paper(
                paper_id=arguments["paper_id"],
                strategy=arguments.get("strategy", "hybrid"),
                optimization_level=arguments.get("optimization_level", "intermediate"),
                force=arguments.get("force", False)
            )
        elif name == "synthesize-evidence":
            result = handler.synthesize_evidence(
                research_question=arguments["research_question"],
                paper_ids=arguments["paper_ids"],
                include_meta_analysis=arguments.get("include_meta_analysis", True)
            )
        else:
            result = {"success": False, "error": f"Unknown tool: {name}", "error_type": "validation"}
        
        import json
        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
    
    except Exception as e:
        logger.error(f"Tool execution error for {name}: {str(e)}")
        import json
        return [types.TextContent(
            type="text", 
            text=json.dumps({
                "success": False, 
                "error": str(e), 
                "error_type": "execution"
            })
        )]


async def main():
    """Run the SLR MCP server."""
    initialize_dependencies()
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Starting SLR MCP Server...")
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())