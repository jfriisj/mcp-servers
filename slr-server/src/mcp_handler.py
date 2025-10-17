"""
MCP Protocol Handler for SLR MCP Server.

Implements MCP tool definitions for systematic literature review operations.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from .services import (
    ResearchDocumentService, QualityAssessmentService, 
    ResearchQuestionService, HypothesisAnalysisService,
    AcademicChunkingService
)

logger = logging.getLogger(__name__)


class SLRMCPHandler:
    """MCP Protocol Handler for Systematic Literature Review tools."""

    def __init__(
        self,
        research_document_service: ResearchDocumentService,
        quality_assessment_service: QualityAssessmentService,
        research_question_service: ResearchQuestionService,
        hypothesis_analysis_service: HypothesisAnalysisService,
        academic_chunking_service: AcademicChunkingService
    ):
        """Initialize with service dependencies."""
        self.research_document_service = research_document_service
        self.quality_assessment_service = quality_assessment_service
        self.research_question_service = research_question_service
        self.hypothesis_analysis_service = hypothesis_analysis_service
        self.academic_chunking_service = academic_chunking_service

    def _create_success_response(self, data: Any = None, message: str = None) -> Dict[str, Any]:
        """Create standardized success response."""
        response = {"success": True}
        if data is not None:
            response["data"] = data
        if message:
            response["message"] = message
        return response

    def _create_error_response(self, error_message: str, error_type: str = "system") -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "success": False,
            "error": error_message,
            "error_type": error_type
        }

    def upload_paper(
        self,
        file_path: str,
        title: Optional[str] = None,
        authors: Optional[List[str]] = None,
        doi: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Upload and process research paper."""
        try:
            paper = self.research_document_service.upload_paper(
                file_path=file_path,
                title=title,
                doi=doi,
                tags=tags
            )
            return self._create_success_response({
                "paper_id": paper.id,
                "title": paper.title,
                "authors": [author.name for author in paper.authors] if paper.authors else [],
                "doi": paper.doi
            }, "Paper uploaded successfully")
        except Exception as e:
            return self._create_error_response(str(e))

    def assess_quality(
        self,
        paper_id: int,
        framework: str = "prisma",
        reviewer_id: str = "default",
        criterion_scores: Dict[str, Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Assess paper quality using specified framework."""
        try:
            from .services.quality_assessment_service import QualityFramework
            framework_enum = QualityFramework(framework)
            
            assessment = self.quality_assessment_service.create_assessment(
                paper_id=paper_id,
                framework=framework_enum,
                reviewer_id=reviewer_id,
                criterion_scores=criterion_scores or {}
            )
            return self._create_success_response({
                "assessment_id": assessment.id if hasattr(assessment, 'id') else None,
                "overall_score": assessment.overall_score,
                "framework": assessment.framework,
                "risk_of_bias": assessment.risk_of_bias
            })
        except Exception as e:
            return self._create_error_response(str(e))

    def validate_research_question(
        self,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate research question using PICO/SPIDER framework."""
        try:
            from .services.research_question_service import QuestionFramework
            
            # Extract parameters from arguments
            question_text = arguments.get("research_question")
            if not question_text:
                return self._create_error_response("Missing required parameter: research_question")
            
            framework = arguments.get("framework", "PICO").lower()
            framework_enum = QuestionFramework(framework)
            
            validation = self.research_question_service.validate_research_question(
                question_text, framework_enum
            )
            return self._create_success_response({
                "overall_score": validation.overall_score,
                "validation_level": validation.validation_level.value,
                "strengths": validation.strengths,
                "weaknesses": validation.weaknesses,
                "suggestions": validation.improvement_suggestions
            })
        except Exception as e:
            return self._create_error_response(str(e))

    def analyze_citations(self, paper_id: int) -> Dict[str, Any]:
        """Perform citation analysis on paper."""
        try:
            analysis = self.research_document_service.analyze_citations(paper_id)
            return self._create_success_response(analysis)
        except Exception as e:
            return self._create_error_response(str(e))

    def test_hypothesis(
        self,
        hypothesis_text: str,
        paper_ids: List[int],
        significance_level: float = 0.05
    ) -> Dict[str, Any]:
        """Test research hypothesis with evidence."""
        try:
            from .domain.models import ResearchHypothesis
            hypothesis = ResearchHypothesis(
                hypothesis_text=hypothesis_text,
                hypothesis_type="primary",
                direction="directional",
                statistical_test="t_test",
                significance_level=significance_level
            )
            
            # Get evidence from papers
            evidence_items = []
            for paper_id in paper_ids:
                papers = [self.research_document_service.paper_repository.get_by_id(paper_id)]
                evidence = self.hypothesis_analysis_service.classify_evidence(
                    hypothesis, papers
                )
                evidence_items.extend(evidence)
            
            result = self.hypothesis_analysis_service.test_hypothesis(
                hypothesis, evidence_items, significance_level
            )
            
            return self._create_success_response({
                "hypothesis_text": result.hypothesis_text,
                "supported": result.supported,
                "confidence_level": result.confidence_level,
                "effect_direction": result.effect_direction.value,
                "conclusions": result.conclusions
            })
        except Exception as e:
            return self._create_error_response(str(e))

    def index_paper(
        self,
        paper_id: int,
        strategy: str = "hybrid",
        optimization_level: str = "intermediate",
        force: bool = False
    ) -> Dict[str, Any]:
        """Index paper with intelligent chunking."""
        try:
            from .services.academic_chunking_service import IndexingStrategy, OptimizationLevel
            strategy_enum = IndexingStrategy(strategy)
            optimization_enum = OptimizationLevel(optimization_level)
            
            if force:
                # Use reindex_paper method when force is True
                chunks = self.academic_chunking_service.reindex_paper(
                    paper_id, force=True, new_strategy=strategy_enum
                )
            else:
                # Use regular index_paper method
                chunks = self.academic_chunking_service.index_paper(
                    paper_id, strategy_enum, optimization_enum
                )
            
            return self._create_success_response({
                "paper_id": paper_id,
                "chunks_created": len(chunks),
                "average_chunk_size": sum(c.word_count or 0 for c in chunks) / len(chunks) if chunks else 0,
                "indexing_strategy": strategy,
                "optimization_level": optimization_level
            })
        except Exception as e:
            return self._create_error_response(str(e))

    def synthesize_evidence(
        self,
        research_question: str,
        paper_ids: List[int],
        include_meta_analysis: bool = True
    ) -> Dict[str, Any]:
        """Synthesize evidence from multiple papers."""
        try:
            # Extract hypotheses from research question
            hypotheses = self.hypothesis_analysis_service.extract_hypotheses(
                research_question
            )
            
            if not hypotheses:
                return self._create_error_response("No hypotheses extracted from research question")
            
            # Test each hypothesis
            results = []
            for hypothesis in hypotheses[:3]:  # Limit to first 3 hypotheses
                try:
                    evidence_items = []
                    for paper_id in paper_ids:
                        papers = [self.research_document_service.paper_repository.get_by_id(paper_id)]
                        if papers[0]:
                            evidence = self.hypothesis_analysis_service.classify_evidence(
                                hypothesis, papers
                            )
                            evidence_items.extend(evidence)
                    
                    if evidence_items:
                        result = self.hypothesis_analysis_service.test_hypothesis(
                            hypothesis, evidence_items
                        )
                        results.append({
                            "hypothesis": result.hypothesis_text,
                            "supported": result.supported,
                            "confidence": result.confidence_level
                        })
                except Exception:
                    continue  # Skip problematic hypotheses
            
            # Generate synthesis report
            report = self.hypothesis_analysis_service.generate_synthesis_report(
                [r for r in results if hasattr(r, 'hypothesis_text')]
            ) if results else {"error": "No valid results"}
            
            return self._create_success_response({
                "research_question": research_question,
                "papers_analyzed": len(paper_ids),
                "hypotheses_tested": len(results),
                "results": results,
                "synthesis_report": report
            })
        except Exception as e:
            return self._create_error_response(str(e))

    def detect_remove_duplicates(
        self,
        similarity_threshold: float = 0.85,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Detect and optionally remove duplicate papers from the corpus.
        
        Args:
            similarity_threshold: Title similarity threshold for duplicate detection (0.0-1.0)
            dry_run: If True, only detect duplicates without removing them
            
        Returns:
            Dictionary with duplicate detection results and actions taken
        """
        try:
            result = self.research_document_service.detect_and_remove_duplicates(
                similarity_threshold=similarity_threshold,
                dry_run=dry_run
            )
            return result
        except Exception as e:
            return self._create_error_response(str(e))