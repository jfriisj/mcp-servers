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
            
            result = document_service.process_document(
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
    
    async def handle_upload_bibliography_batch(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle batch bibliography upload MCP tool call."""
        try:
            document_service = self.container.get_document_service()
            
            # Use the new batch upload method - now returns detailed report
            result = document_service.upload_bibliography_batch(
                file_path=arguments["file_path"],
                tags=arguments.get("tags", []),
                auto_extract_metadata=arguments.get("auto_extract_metadata", True)
            )
            
            # Extract data from result
            created_papers = result['created_papers']
            skipped_entries = result['skipped_entries']
            summary = result['summary']
            
            # Format results with detailed information
            titles = [paper.title for paper in created_papers[:5]]  # Show first 5 titles
            if len(created_papers) > 5:
                titles.append(f"... and {len(created_papers) - 5} more papers")
            
            result_lines = [summary]
            result_lines.append("\n📚 Sample of successfully created papers:")
            result_lines.extend([f"• {title}" for title in titles])
            
            # If there were failures, show details
            if skipped_entries:
                result_lines.append("\n⚠️ Failed entries details:")
                for entry in skipped_entries[:10]:  # Show first 10 failures
                    result_lines.append(f"  Entry {entry['entry_num']}: {entry['reason']}")
                    if 'detail' in entry and entry['detail']:
                        result_lines.append(f"    Error: {entry['detail'][:100]}")
                
                if len(skipped_entries) > 10:
                    result_lines.append(f"  ... and {len(skipped_entries) - 10} more failures")
            
            result_text = "\n".join(result_lines)
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=result_text
                )]
            )
            
        except Exception as e:
            logger.error(f"Error uploading bibliography batch: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Error uploading bibliography batch: {str(e)}"
                )],
                isError=True
            )
    
    async def handle_get_paper(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get paper MCP tool call."""
        try:
            paper_repository = self.container.get_paper_repository()
            
            paper = paper_repository.get_by_id(arguments["paper_id"])
            if not paper:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Paper with ID {arguments['paper_id']} not found"
                    )],
                    isError=True
                )
            
            # Format authors properly
            authors_str = ', '.join([author.name for author in paper.authors]) if paper.authors else 'None'
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Paper: {paper.title}\nAuthors: {authors_str}\nYear: {paper.publication_year}\nDOI: {paper.doi}"
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
            
            papers = paper_repository.list_papers(
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
                    text=f"Quality assessment completed. Overall rating: {assessment.overall_rating.value}\nFramework: {assessment.framework.value}"
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
    
    async def handle_get_quality_assessment(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get quality assessment MCP tool call."""
        try:
            # Get the quality assessment service
            quality_service = self.container.get_quality_service()
            
            # Get paper repository to find assessments
            paper_repo = self.container.get_paper_repository()
            
            paper_id = arguments["paper_id"]
            reviewer_id = arguments.get("reviewer_id")
            
            # For now, return a simple message since the quality service
            # doesn't have a direct get_assessment method yet
            paper = paper_repo.get_by_id(paper_id)
            if not paper:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"❌ Paper with ID {paper_id} not found"
                    )],
                    isError=True
                )
            
            # Check if paper has been quality assessed
            if not paper.quality_assessed:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"📝 Paper '{paper.title}' has not been quality assessed yet.\nUse assess_quality tool first."
                    )]
                )
            
            # Return basic quality assessment info
            assessment_info = f"""✅ Quality Assessment for Paper ID {paper_id}

📄 **Paper:** {paper.title}
👥 **Authors:** {', '.join(paper.author_names) if paper.author_names else 'Unknown'}
📅 **Year:** {paper.publication_year or 'Unknown'}

🔍 **Assessment Status:** Quality Assessed ✓
📊 **Review Status:** {paper.review_status}

💡 **Assessment Details:**
• Paper has been quality assessed
• Included in review: {'Yes' if paper.included_in_review else 'No' if paper.included_in_review is False else 'Pending'}
• Exclusion reason: {paper.exclusion_reason or 'N/A'}

📝 **Notes:** {paper.notes or 'No additional notes'}
"""
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=assessment_info
                )]
            )
            
        except Exception as e:
            logger.error(f"Error retrieving quality assessment: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Error retrieving quality assessment: {str(e)}"
                )],
                isError=True
            )
    
    async def handle_search_papers(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle paper search MCP tool call."""
        try:
            document_service = self.container.get_document_service()
            
            results = document_service.search_documents(
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

    async def handle_index_paper(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle paper indexing MCP tool call."""
        try:
            paper_id = arguments["paper_id"]
            strategy_name = arguments.get("strategy", "academic_section")
            force = arguments.get("force", False)
            
            # Map strategy names to enum values
            from ..services.academic_chunking_service import IndexingStrategy
            strategy_map = {
                "academic_section": IndexingStrategy.SECTION_BASED,
                "citation_aware": IndexingStrategy.CITATION_AWARE,
                "topic_based": IndexingStrategy.SEMANTIC,
                "hybrid": IndexingStrategy.HYBRID,
                "full_text": IndexingStrategy.FULL_TEXT
            }
            
            strategy = strategy_map.get(strategy_name, IndexingStrategy.HYBRID)
            
            # Get the academic chunking service
            chunking_service = self.container.get_chunking_service()
            
            # If force is True, clear existing chunks first
            if force:
                chunk_repository = self.container.get_chunk_repository()
                existing_chunks = chunk_repository.get_by_paper_id(paper_id)
                if existing_chunks:
                    for chunk in existing_chunks:
                        if chunk.id is not None:
                            chunk_repository.delete(chunk.id)
                    logger.info(f"Cleared {len(existing_chunks)} existing chunks for paper {paper_id}")
            
            # Index the paper
            chunks = chunking_service.index_paper(paper_id, strategy)
            
            # Format the response
            result_text = f"✅ Successfully indexed paper {paper_id} using {strategy_name} strategy.\n\n"
            result_text += f"📊 Generated {len(chunks)} academic chunks:\n\n"
            
            for i, chunk in enumerate(chunks[:10]):  # Show first 10 chunks
                section_emoji = {"abstract": "📝", "introduction": "🚀", "methods": "🔬", 
                               "results": "📈", "discussion": "💭", "conclusion": "🎯"}.get(chunk.section_type, "📄")
                result_text += f"{section_emoji} {chunk.section_type.title()}: {chunk.title or 'Untitled'} ({chunk.word_count} words)\n"
            
            if len(chunks) > 10:
                result_text += f"\n... and {len(chunks) - 10} more chunks"
            
            # Add summary statistics
            total_words = sum(chunk.word_count or 0 for chunk in chunks)
            avg_words = total_words / len(chunks) if chunks else 0
            citations = sum(chunk.citation_count or 0 for chunk in chunks)
            
            result_text += f"\n\n📊 Summary:\n"
            result_text += f"• Total words: {total_words:,}\n"
            result_text += f"• Average chunk size: {avg_words:.0f} words\n"
            result_text += f"• Total citations: {citations}\n"
            result_text += f"• Section types: {len(set(chunk.section_type for chunk in chunks))}"
            
            return CallToolResult(
                content=[TextContent(
                    type="text", 
                    text=result_text
                )]
            )
            
        except Exception as e:
            logger.error(f"Error indexing paper: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Error indexing paper: {str(e)}"
                )],
                isError=True
            )

    async def handle_get_paper_structure(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get paper structure MCP tool call."""
        try:
            paper_id = arguments["paper_id"]
            
            # Get the research document service  
            document_service = self.container.get_document_service()
            
            # Get paper structure
            structure = document_service.get_paper_structure(paper_id)
            
            # Format the structure response
            result_text = f"📄 Paper Structure for ID {paper_id}:\n\n"
            
            if structure.get("error"):
                result_text += f"❌ Error: {structure['error']}\n"
                return CallToolResult(
                    content=[TextContent(type="text", text=result_text)],
                    isError=True
                )
            
            # Add basic paper info
            if structure.get("title"):
                result_text += f"📝 **Title:** {structure['title']}\n"
            if structure.get("authors"):
                result_text += f"👥 **Authors:** {', '.join(structure['authors'])}\n"
            if structure.get("total_pages"):
                result_text += f"📄 **Pages:** {structure['total_pages']}\n"
            if structure.get("total_words"):
                result_text += f"📊 **Words:** {structure['total_words']:,}\n"
            result_text += "\n"
            
            # Add section structure
            sections = structure.get("sections", [])
            if sections:
                result_text += "📑 **Document Structure:**\n\n"
                for i, section in enumerate(sections, 1):
                    section_emoji = {"abstract": "📝", "introduction": "🚀", "methods": "🔬", 
                                   "results": "📈", "discussion": "💭", "conclusion": "🎯",
                                   "references": "📚"}.get(section.get("type", "").lower(), "📄")
                    
                    result_text += f"{i}. {section_emoji} **{section.get('title', 'Unknown')}**"
                    if section.get("type"):
                        result_text += f" ({section['type']})"
                    if section.get("word_count"):
                        result_text += f" - {section['word_count']} words"
                    if section.get("page"):
                        result_text += f" - Page {section['page']}"
                    result_text += "\n"
                    
                    # Add subsections if available
                    if section.get("subsections"):
                        for subsection in section["subsections"]:
                            result_text += f"   • {subsection.get('title', 'Unknown subsection')}"
                            if subsection.get("word_count"):
                                result_text += f" ({subsection['word_count']} words)"
                            result_text += "\n"
                result_text += "\n"
            
            # Add content analysis if available
            if structure.get("analysis"):
                analysis = structure["analysis"]
                result_text += "🔍 **Content Analysis:**\n"
                if analysis.get("citation_count"):
                    result_text += f"• Citations found: {analysis['citation_count']}\n"
                if analysis.get("figure_count"):
                    result_text += f"• Figures referenced: {analysis['figure_count']}\n"
                if analysis.get("table_count"):
                    result_text += f"• Tables referenced: {analysis['table_count']}\n"
                if analysis.get("complexity_score"):
                    result_text += f"• Content complexity: {analysis['complexity_score']:.2f}/1.0\n"
                if analysis.get("academic_features"):
                    features = analysis["academic_features"]
                    result_text += f"• Academic sections detected: {len(features.get('sections', []))}\n"
                    if features.get("has_methodology"):
                        result_text += f"• Methodology section: ✅\n"
                    if features.get("has_results"):
                        result_text += f"• Results section: ✅\n"
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=result_text
                )]
            )
            
        except Exception as e:
            logger.error(f"Error getting paper structure: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Error getting paper structure: {str(e)}"
                )],
                isError=True
            )

    async def handle_analyze_citations(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle citation analysis MCP tool call."""
        try:
            paper_id = arguments["paper_id"]
            analysis_type = arguments.get("analysis_type", "network")
            depth = arguments.get("depth", 2)
            
            # Get citation analysis service
            citation_service = self.container.get_citation_service()
            
            # Perform citation analysis
            result = await citation_service.analyze_citations(paper_id, analysis_type, depth)
            
            # Format results
            result_text = f"🔗 Citation Analysis for Paper {paper_id}\n\n"
            result_text += f"**Analysis Type:** {result.analysis_type}\n"
            result_text += f"**Depth:** {result.depth}\n\n"
            
            result_text += "📊 **Citation Overview:**\n"
            result_text += f"• Total citations: {result.total_citations}\n"
            result_text += f"• Unique citations: {result.unique_citations}\n"
            result_text += f"• Citation density: {result.citation_density:.2f} per 1000 words\n\n"
            
            if result.citation_types:
                result_text += "**Citation Types:**\n"
                for cit_type, count in result.citation_types.items():
                    result_text += f"• {cit_type}: {count}\n"
                result_text += "\n"
            
            if result.key_citations:
                result_text += f"🎯 **Key Citations** (top {len(result.key_citations)}):\n"
                for i, citation in enumerate(result.key_citations[:5], 1):
                    result_text += f"{i}. {citation.text}"
                    if citation.year:
                        result_text += f" ({citation.year})"
                    result_text += "\n"
                result_text += "\n"
            
            if result.temporal_trends:
                trends = result.temporal_trends
                result_text += "📈 **Temporal Trends:**\n"
                if trends.get("earliest_citation"):
                    result_text += f"• Citation span: {trends['earliest_citation']} - {trends['latest_citation']}\n"
                if trends.get("recent_citations_ratio"):
                    recent_pct = trends["recent_citations_ratio"] * 100
                    result_text += f"• Recent citations (2020+): {recent_pct:.1f}%\n"
                result_text += "\n"
            
            if result.patterns:
                result_text += f"🔍 **Citation Patterns:** {', '.join(result.patterns)}\n\n"
            
            if result.citation_network:
                network = result.citation_network
                result_text += "🕸️ **Network Analysis:**\n"
                result_text += f"• Network density: {network.get('network_density', 0):.3f}\n"
                result_text += f"• Total nodes: {network.get('total_nodes', 0)}\n"
                result_text += f"• Total edges: {network.get('total_edges', 0)}\n"
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=result_text
                )]
            )
            
        except Exception as e:
            logger.error(f"Error analyzing citations: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error analyzing citations: {str(e)}"
                )],
                isError=True
            )

    async def handle_synthesize_evidence(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle evidence synthesis MCP tool call."""
        try:
            paper_ids = arguments["paper_ids"]
            synthesis_method = arguments.get("synthesis_method", "narrative")
            outcome_measures = arguments.get("outcome_measures", [])
            
            # Get evidence synthesis service
            evidence_service = self.container.get_evidence_service()
            
            # Perform evidence synthesis
            result = await evidence_service.synthesize_evidence(paper_ids, synthesis_method, outcome_measures)
            
            # Format results
            result_text = f"🔬 Evidence Synthesis Results\n\n"
            result_text += f"**Method:** {result.synthesis_method}\n"
            result_text += f"**Studies:** {result.total_studies}\n"
            if result.total_participants:
                result_text += f"**Total Participants:** {result.total_participants}\n"
            result_text += "\n"
            
            # Meta-analysis specific results
            if result.synthesis_method == "meta-analysis" and result.pooled_effect_size:
                pooled = result.pooled_effect_size
                result_text += "📊 **Meta-Analysis Results:**\n"
                result_text += f"• Pooled effect size: {pooled.value:.3f} (95% CI: {pooled.lower_ci:.3f} to {pooled.upper_ci:.3f})\n"
                
                if result.heterogeneity:
                    het = result.heterogeneity
                    result_text += f"• Heterogeneity: I² = {het.i_squared:.1f}% ({het.interpretation})\n"
                    result_text += f"• Q-statistic: {het.q_statistic:.2f}\n"
                
                if result.publication_bias:
                    bias = result.publication_bias
                    result_text += f"• Publication bias risk: {bias.get('risk_level', 'Unknown')}\n"
                
                if result.grade_assessment:
                    grade = result.grade_assessment
                    result_text += f"• GRADE quality: {grade.get('overall_quality', 'Not assessed')}\n"
                
                result_text += "\n"
            
            # Forest plot data
            if result.forest_plot_data:
                result_text += "🌲 **Forest Plot Data:**\n"
                for i, study in enumerate(result.forest_plot_data[:5], 1):  # Show first 5 studies
                    if study.get("is_pooled"):
                        result_text += f"**POOLED:** {study['effect_size']:.3f} [{study['lower_ci']:.3f}, {study['upper_ci']:.3f}]\n"
                    else:
                        result_text += f"{i}. {study['study'][:30]}...: {study['effect_size']:.3f} [{study['lower_ci']:.3f}, {study['upper_ci']:.3f}]\n"
                result_text += "\n"
            
            # Narrative summary
            if result.narrative_summary:
                result_text += "📝 **Synthesis Summary:**\n"
                # Truncate long narrative for display
                narrative = result.narrative_summary
                if len(narrative) > 500:
                    narrative = narrative[:500] + "...\n[Truncated - full summary available in detailed report]"
                result_text += narrative + "\n"
            
            # Recommendations
            if result.recommendations:
                result_text += "💡 **Recommendations:**\n"
                for i, rec in enumerate(result.recommendations, 1):
                    result_text += f"{i}. {rec}\n"
                result_text += "\n"
            
            # Quality assessment
            if result.quality_assessment:
                qa = result.quality_assessment
                result_text += "🔍 **Quality Assessment:**\n"
                result_text += f"• Overall strength: {qa.get('overall_strength', 'Not assessed')}\n"
                if qa.get('publication_span'):
                    span = qa['publication_span']
                    result_text += f"• Publication span: {span.get('earliest', 'Unknown')} - {span.get('latest', 'Unknown')}\n"
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=result_text
                )]
            )
            
        except Exception as e:
            logger.error(f"Error synthesizing evidence: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error synthesizing evidence: {str(e)}"
                )],
                isError=True
            )

    async def handle_generate_slr_report(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle SLR report generation MCP tool call."""
        try:
            paper_ids = arguments["paper_ids"]
            output_path = arguments["output_path"]
            report_format = arguments.get("report_format", "markdown")
            include_quality = arguments.get("include_quality_assessment", True)
            include_citations = arguments.get("include_citation_analysis", True)
            
            # Get report generator service
            report_generator = self.container.get_report_generator()
            
            # Generate comprehensive SLR report
            result = await report_generator.generate_slr_report(
                paper_ids=paper_ids,
                output_path=output_path,
                report_format=report_format,
                include_quality_assessment=include_quality,
                include_citation_analysis=include_citations
            )
            
            # Format results
            result_text = f"📋 SLR Report Generated Successfully!\n\n"
            
            result_text += f"📄 **Report Details:**\n"
            result_text += f"• Papers included: {result.total_papers}\n"
            result_text += f"• Format: {result.report_format.upper()}\n"
            result_text += f"• Output file: {result.output_path}\n"
            result_text += f"• Quality assessment: {'✅' if result.includes_quality_assessment else '❌'}\n"
            result_text += f"• Citation analysis: {'✅' if result.includes_citation_analysis else '❌'}\n"
            result_text += f"• PRISMA compliant: {'✅' if result.prisma_compliant else '❌'}\n\n"
            
            if result.file_size:
                file_size_kb = result.file_size / 1024
                result_text += f"📊 **File Statistics:**\n"
                result_text += f"• File size: {file_size_kb:.1f} KB\n"
                if result.generation_time:
                    result_text += f"• Generation time: {result.generation_time:.2f} seconds\n"
                result_text += "\n"
            
            result_text += f"📋 **Report Sections Generated:**\n"
            for i, section in enumerate(result.sections_generated, 1):
                result_text += f"{i}. {section}\n"
            result_text += "\n"
            
            result_text += f"📖 **Report Contents Include:**\n"
            result_text += f"• PRISMA-compliant structure\n"
            result_text += f"• Executive summary and abstract\n"
            result_text += f"• Comprehensive methodology section\n"
            result_text += f"• Detailed study characteristics\n"
            result_text += f"• Results and findings synthesis\n"
            
            if result.includes_quality_assessment:
                result_text += f"• Quality assessment and risk of bias\n"
            
            if result.includes_citation_analysis:
                result_text += f"• Citation network analysis\n"
            
            result_text += f"• Discussion and implications\n"
            result_text += f"• Evidence-based conclusions\n"
            result_text += f"• Complete reference list\n"
            result_text += f"• Detailed appendices\n\n"
            
            result_text += f"✨ **Ready for Use:**\n"
            result_text += f"The generated report follows systematic review best practices and is ready for:\n"
            result_text += f"• Academic submission\n"
            result_text += f"• Peer review\n"
            result_text += f"• Policy development\n"
            result_text += f"• Clinical guideline development\n"
            result_text += f"• Further analysis and reporting\n"
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=result_text
                )]
            )
            
        except Exception as e:
            logger.error(f"Error generating SLR report: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error generating SLR report: {str(e)}"
                )],
                isError=True
            )
    

    

    
    async def create_slr_project(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle create SLR project tool call."""
        return await self.handle_create_slr_project(arguments)
    
    async def get_slr_progress(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get SLR progress tool call."""
        return await self.workflow_handler.handle_get_slr_progress(arguments)
    
    async def get_next_steps(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get next steps tool call."""
        return await self.workflow_handler.handle_get_next_steps(arguments)
    
    async def create_screening_workflow(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle create screening workflow tool call."""
        return await self.workflow_handler.handle_create_screening_workflow(arguments)
    
    async def screen_paper(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle screen paper tool call."""
        return await self.workflow_handler.handle_screen_paper(arguments)
    
    async def get_slr_guide(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get SLR guide tool call."""
        return await self.workflow_handler.handle_get_slr_guide(arguments)

    async def validate_research_question(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle validate research question tool call."""
        try:
            from ..services.research_question_service import QuestionFramework, ResearchQuestionService
            
            # Extract parameters from arguments
            question_text = arguments.get("research_question")
            if not question_text:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="❌ Error: Missing required parameter: research_question"
                    )],
                    isError=True
                )
            
            framework_str = arguments.get("framework", "PICO").lower()
            framework_enum = QuestionFramework(framework_str)
            
            # Get research question service from container
            research_question_service = ResearchQuestionService()
            
            validation = research_question_service.validate_research_question(
                question_text, framework_enum
            )
            
            result_text = f"""✅ Research Question Validation Complete

📊 **Overall Score**: {validation.overall_score:.2f}
🎯 **Validation Level**: {validation.validation_level.value.title()}
📝 **Framework**: {framework_enum.value.upper()}

💪 **Strengths**:
{chr(10).join(f"• {strength}" for strength in validation.strengths)}

⚠️ **Areas for Improvement**:
{chr(10).join(f"• {weakness}" for weakness in validation.weaknesses)}

🔧 **Suggestions**:
{chr(10).join(f"• {suggestion}" for suggestion in validation.improvement_suggestions)}

🔍 **Searchability Score**: {validation.searchability_score:.2f}

🧩 **Component Analysis**:
{chr(10).join(f"• {comp.component.value}: {'✓' if comp.present else '✗'} (Clarity: {comp.clarity_score:.2f}, Specificity: {comp.specificity_score:.2f})" for comp in validation.component_analyses)}
"""
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=result_text
                )]
            )
            
        except Exception as e:
            logger.error(f"Error validating research question: {e}", exc_info=True)
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Error validating research question: {str(e)}"
                )],
                isError=True
            )

    async def handle_detect_remove_duplicates(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle duplicate detection and removal MCP tool call."""
        try:
            document_service = self.container.get_document_service()
            
            result = document_service.detect_and_remove_duplicates(
                similarity_threshold=arguments.get("similarity_threshold", 0.85),
                dry_run=arguments.get("dry_run", True)
            )
            
            # Format the result for display
            duplicates_found = result.get("duplicates_found", 0)
            removed_count = result.get("papers_removed", 0)
            remaining_count = result.get("total_papers_after", 0)
            
            if result.get("dry_run", True):
                result_text = f"🔍 **Duplicate Detection Analysis (Dry Run)**\n\n"
                result_text += f"• **Duplicates Found**: {duplicates_found}\n"
                result_text += f"• **Total Papers**: {result.get('total_papers_before', 0)}\n"
                result_text += f"• **Unique Papers**: {result.get('total_papers_before', 0) - duplicates_found}\n"
                if duplicates_found > 0:
                    result_text += f"\n**Duplicate Groups Found**: {result.get('duplicate_groups', 0)}\n"
                    result_text += "⚠️  Run with dry_run=false to remove duplicates"
            else:
                result_text = f"✅ **Duplicate Removal Completed**\n\n"
                result_text += f"• **Duplicates Removed**: {removed_count}\n"
                result_text += f"• **Papers Remaining**: {remaining_count}\n"
                if result.get('total_papers_before', 0) > 0:
                    reduction = (removed_count / result.get('total_papers_before', 1)) * 100
                    result_text += f"• **Reduction**: {reduction:.1f}%"
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=result_text
                )]
            )
            
        except Exception as e:
            logger.error(f"Error detecting/removing duplicates: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Error detecting/removing duplicates: {str(e)}"
                )],
                isError=True
            )
    
    async def handle_create_slr_project(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle SLR project creation MCP tool call."""
        try:
            project_service = self.container.get_project_service()
            
            project_name = arguments["project_name"]
            description = arguments.get("description", "No description provided")
            file_path = arguments.get("file_path")
            research_questions = arguments.get("research_questions", [])
            extract_metadata = arguments.get("extract_metadata", True)
            
            if file_path:
                # Create from file (PDF or Markdown)
                project = project_service.create_project_from_file(
                    project_name=project_name,
                    file_path=file_path,
                    description=description,
                    extract_metadata=extract_metadata
                )
            else:
                # Create manually
                display_name = project_name.replace("-", " ").replace("_", " ").title()
                project = project_service.create_project_manual(
                    project_name=project_name,
                    display_name=display_name,
                    description=description,
                    research_questions=research_questions
                )
            
            # Format success response
            result_text = f"✅ **SLR Project Created Successfully**\n\n"
            result_text += f"• **Project Name**: {project.name}\n"
            result_text += f"• **Display Name**: {project.display_name}\n"
            result_text += f"• **Description**: {project.description}\n"
            result_text += f"• **Status**: {project.status}\n"
            result_text += f"• **Phase**: {project.current_phase}\n"
            result_text += f"• **Folder Path**: {project.folder_path}\n"
            
            if project.research_questions:
                result_text += f"\n**Research Questions** ({len(project.research_questions)}):\n"
                for i, rq in enumerate(project.research_questions[:5], 1):
                    result_text += f"{i}. {rq}\n"
                if len(project.research_questions) > 5:
                    result_text += f"... and {len(project.research_questions) - 5} more\n"
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=result_text
                )]
            )
            
        except Exception as e:
            logger.error(f"Error creating SLR project: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Error creating SLR project: {str(e)}"
                )],
                isError=True
            )

    def _convert_call_result_to_dict(self, call_result: CallToolResult) -> dict:
        """Convert CallToolResult to dict format expected by main server."""
        if call_result.isError:
            content_text = "Unknown error"
            if call_result.content and isinstance(call_result.content[0], TextContent):
                content_text = call_result.content[0].text
            return {
                "success": False,
                "error": content_text
            }
        else:
            content_text = "Success"
            if call_result.content and isinstance(call_result.content[0], TextContent):
                content_text = call_result.content[0].text
            return {
                "success": True,
                "message": content_text
            }
