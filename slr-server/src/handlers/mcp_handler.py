"""
MCP Handler for Systematic Literature Review operations.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Sequence

from mcp.types import CallToolResult, TextContent, ImageContent, EmbeddedResource

from ..container import Container
from .slr_workflow_handlers import SLRWorkflowMCPHandler

logger = logging.getLogger(__name__)


class SLRMCPHandler:
    """
    MCP Handler for systematic literature review operations.
    
    This class handles MCP tool calls and routes them to appropriate
    services through the dependency injection container.
    """
    
    def __init__(self, container: Container):
        self.container = container
        self.workflow_handler = SLRWorkflowMCPHandler(container)
        logger.info("SLR MCP Handler initialized")
    
    async def handle_upload_paper(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle paper upload MCP tool call."""
        try:
            document_service = self.container.get_document_service()
            
            result = await document_service.process_document(
                file_path=arguments["file_path"],
                title=arguments.get("title"),
                authors=arguments.get("authors", []),
                publication_year=arguments.get("publication_year"),
                doi=arguments.get("doi"),
                tags=arguments.get("tags", [])
            )
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Paper uploaded successfully. ID: {result.id}, Title: {result.title}"
                )]
            )
            
        except Exception as e:
            logger.error(f"Error uploading paper: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error uploading paper: {str(e)}"
                )],
                isError=True
            )
    
    async def handle_get_paper(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get paper MCP tool call."""
        try:
            paper_repository = self.container.get_paper_repository()
            
            paper = await paper_repository.get_by_id(arguments["paper_id"])
            if not paper:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Paper with ID {arguments['paper_id']} not found"
                    )],
                    isError=True
                )
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Paper: {paper.title}\nAuthors: {', '.join(paper.authors or [])}\nYear: {paper.publication_year}\nDOI: {paper.doi}"
                )]
            )
            
        except Exception as e:
            logger.error(f"Error retrieving paper: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error retrieving paper: {str(e)}"
                )],
                isError=True
            )
    
    async def handle_list_papers(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle list papers MCP tool call."""
        try:
            paper_repository = self.container.get_paper_repository()
            
            papers = await paper_repository.list_papers(
                filters=arguments.get("filters", {}),
                limit=arguments.get("limit", 20),
                offset=arguments.get("offset", 0)
            )
            
            if not papers:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="No papers found matching the criteria"
                    )]
                )
            
            papers_text = "\n".join([
                f"ID: {p.id}, Title: {p.title}, Year: {p.publication_year}"
                for p in papers
            ])
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Found {len(papers)} papers:\n{papers_text}"
                )]
            )
            
        except Exception as e:
            logger.error(f"Error listing papers: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error listing papers: {str(e)}"
                )],
                isError=True
            )
    
    async def handle_assess_quality(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle quality assessment MCP tool call."""
        try:
            quality_service = self.container.get_quality_service()
            
            assessment = await quality_service.assess_paper_quality(
                paper_id=arguments["paper_id"],
                framework=arguments.get("assessment_framework", "PRISMA"),
                reviewer_id=arguments.get("reviewer_id", "system"),
                custom_criteria=arguments.get("criteria")
            )
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Quality assessment completed. Overall score: {assessment.overall_score:.2f}\nFramework: {assessment.framework}"
                )]
            )
            
        except Exception as e:
            logger.error(f"Error in quality assessment: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error in quality assessment: {str(e)}"
                )],
                isError=True
            )
    
    async def handle_search_papers(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle paper search MCP tool call."""
        try:
            document_service = self.container.get_document_service()
            
            results = await document_service.search_documents(
                query=arguments["query"],
                search_type=arguments.get("search_type", "semantic"),
                filters=arguments.get("filters", {}),
                limit=arguments.get("limit", 20)
            )
            
            if not results:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"No papers found for query: {arguments['query']}"
                    )]
                )
            
            results_text = "\n".join([
                f"ID: {r.id}, Title: {r.title}, Relevance: {getattr(r, 'relevance_score', 'N/A')}"
                for r in results
            ])
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Found {len(results)} papers:\n{results_text}"
                )]
            )
            
        except Exception as e:
            logger.error(f"Error searching papers: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error searching papers: {str(e)}"
                )],
                isError=True
            )
    
    # SLR Workflow Guidance Tools - Convert CallToolResult to dict format
    def create_slr_project(self, **arguments):
        """Handle create SLR project tool call."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            call_result = loop.run_until_complete(self.workflow_handler.handle_create_slr_project(arguments))
            return self._convert_call_result_to_dict(call_result)
        finally:
            loop.close()
    
    def get_slr_progress(self, **arguments):
        """Handle get SLR progress tool call."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            call_result = loop.run_until_complete(self.workflow_handler.handle_get_slr_progress(arguments))
            return self._convert_call_result_to_dict(call_result)
        finally:
            loop.close()
    
    def get_next_steps(self, **arguments):
        """Handle get next steps tool call."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            call_result = loop.run_until_complete(self.workflow_handler.handle_get_next_steps(arguments))
            return self._convert_call_result_to_dict(call_result)
        finally:
            loop.close()
    
    def create_screening_workflow(self, **arguments):
        """Handle create screening workflow tool call."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            call_result = loop.run_until_complete(self.workflow_handler.handle_create_screening_workflow(arguments))
            return self._convert_call_result_to_dict(call_result)
        finally:
            loop.close()
    
    def screen_paper(self, **arguments):
        """Handle screen paper tool call."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            call_result = loop.run_until_complete(self.workflow_handler.handle_screen_paper(arguments))
            return self._convert_call_result_to_dict(call_result)
        finally:
            loop.close()
    
    def get_slr_guide(self, **arguments):
        """Handle get SLR guide tool call."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            call_result = loop.run_until_complete(self.workflow_handler.handle_get_slr_guide(arguments))
            return self._convert_call_result_to_dict(call_result)
        finally:
            loop.close()
    
    def _convert_call_result_to_dict(self, call_result: CallToolResult) -> dict:
        """Convert CallToolResult to dict format expected by main server."""
        if call_result.isError:
            return {
                "success": False,
                "error": call_result.content[0].text if call_result.content else "Unknown error"
            }
        else:
            return {
                "success": True,
                "message": call_result.content[0].text if call_result.content else "Success"
            }
