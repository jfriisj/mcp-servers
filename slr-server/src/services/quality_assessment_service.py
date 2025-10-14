"""
Quality Assessment Service for systematic literature review quality evaluation.

This module implements the QualityAssessmentService class following PRISMA
guidelines and systematic review best practices for research quality assessment.
"""

import statistics
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from ..models import ResearchPaper, QualityAssessment
from ..repositories.paper_repository import PaperRepository


class QualityFramework(Enum):
    """Quality assessment frameworks supported by the service."""
    PRISMA = "prisma"
    COCHRANE = "cochrane"
    CASP = "casp"
    JADAD = "jadad"
    NEWCASTLE_OTTAWA = "newcastle_ottawa"
    ROBINS_I = "robins_i"
    ROB_2 = "rob_2"


class QualityDomain(Enum):
    """Quality assessment domains for systematic evaluation."""
    STUDY_DESIGN = "study_design"
    PARTICIPANT_SELECTION = "participant_selection"
    INTERVENTION_IMPLEMENTATION = "intervention_implementation"
    OUTCOME_MEASUREMENT = "outcome_measurement"
    STATISTICAL_ANALYSIS = "statistical_analysis"
    REPORTING_QUALITY = "reporting_quality"
    RISK_OF_BIAS = "risk_of_bias"
    EXTERNAL_VALIDITY = "external_validity"


class RiskLevel(Enum):
    """Risk of bias levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    UNCLEAR = "unclear"


@dataclass
class QualityCriterion:
    """Individual quality assessment criterion."""
    domain: QualityDomain
    criterion_id: str
    description: str
    weight: float
    required: bool = True
    guidance: Optional[str] = None


@dataclass
class AssessmentResult:
    """Result of a quality assessment for a single criterion."""
    criterion_id: str
    score: float
    risk_level: RiskLevel
    justification: str
    evidence: Optional[str] = None
    reviewer_id: str = ""
    assessment_date: Optional[datetime] = None


@dataclass
class InterRaterReliability:
    """Inter-rater reliability statistics."""
    kappa_score: float
    agreement_percentage: float
    disagreement_details: Dict[str, Any]
    reviewer_pairs: List[Tuple[str, str]]
    assessment_count: int


class QualityAssessmentService:
    """
    Quality assessment service for systematic literature reviews.

    Implements PRISMA-compliant quality assessment frameworks with support
    for multiple reviewers, inter-rater reliability calculation, and
    comprehensive quality scoring following academic standards.

    Key Features:
    - Multiple quality assessment frameworks
    - Multi-reviewer support and consensus building
    - Inter-rater reliability calculations
    - Risk of bias assessment
    - Quality score aggregation and reporting
    - Assessment audit trails

    Follows Clean Architecture Layer 2 principles:
    - Framework-agnostic business logic
    - Depends on repository abstractions
    - Contains systematic review business rules
    - Validates assessment input and enforces quality standards
    """

    def __init__(self, paper_repository: PaperRepository):
        """
        Initialize QualityAssessmentService.

        Args:
            paper_repository: Repository for research paper persistence
        """
        self.paper_repository = paper_repository
        self._frameworks = self._initialize_frameworks()
        self._quality_criteria = self._initialize_quality_criteria()

    def create_assessment(
        self,
        paper_id: int,
        framework: QualityFramework,
        reviewer_id: str,
        criterion_scores: Dict[str, Dict[str, Any]],
        overall_notes: Optional[str] = None
    ) -> QualityAssessment:
        """
        Create a new quality assessment for a research paper.

        Args:
            paper_id: ID of paper to assess
            framework: Quality assessment framework to use
            reviewer_id: Identifier of the reviewer
            criterion_scores: Scores for each quality criterion
            overall_notes: General notes about the assessment

        Returns:
            Created quality assessment

        Raises:
            ValueError: If paper not found or assessment data invalid
        """
        paper = self.paper_repository.get_by_id(paper_id)
        if not paper:
            raise ValueError(f"Research paper {paper_id} not found")

        # Validate framework and criteria
        if framework not in QualityFramework:
            raise ValueError(f"Unsupported quality framework: {framework}")

        framework_criteria = self._frameworks[framework]
        assessment_results = []

        # Validate and process criterion scores
        for criterion_id, score_data in criterion_scores.items():
            if criterion_id not in framework_criteria:
                raise ValueError(
                    f"Invalid criterion '{criterion_id}' for framework {framework.value}"
                )

            criterion = framework_criteria[criterion_id]
            self._validate_criterion_score(criterion, score_data)

            result = AssessmentResult(
                criterion_id=criterion_id,
                score=score_data["score"],
                risk_level=RiskLevel(score_data["risk_level"]),
                justification=score_data["justification"],
                evidence=score_data.get("evidence"),
                reviewer_id=reviewer_id,
                assessment_date=datetime.now()
            )
            assessment_results.append(result)

        # Calculate overall quality scores
        overall_score = self._calculate_overall_score(assessment_results, framework_criteria)
        risk_of_bias = self._calculate_overall_risk(assessment_results)

        # Create quality assessment
        quality_assessment = QualityAssessment(
            paper_id=paper_id,
            framework=framework.value,
            reviewer_id=reviewer_id,
            overall_score=overall_score,
            risk_of_bias=risk_of_bias.value,
            criterion_scores={r.criterion_id: {
                "score": r.score,
                "risk_level": r.risk_level.value,
                "justification": r.justification,
                "evidence": r.evidence
            } for r in assessment_results},
            assessment_date=datetime.now(),
            notes=overall_notes or "",
            validated=True
        )

        # Update paper quality assessment status
        paper.quality_assessed = True
        self.paper_repository.update(paper)

        return quality_assessment

    def calculate_inter_rater_reliability(
        self,
        assessments: List[QualityAssessment],
        criterion_id: Optional[str] = None
    ) -> InterRaterReliability:
        """
        Calculate inter-rater reliability between multiple assessments.

        Args:
            assessments: List of quality assessments to compare
            criterion_id: Specific criterion to analyze (None for overall)

        Returns:
            Inter-rater reliability statistics

        Raises:
            ValueError: If insufficient assessments or invalid data
        """
        if len(assessments) < 2:
            raise ValueError("At least two assessments required for reliability analysis")

        # Group assessments by reviewer pairs
        reviewer_pairs = []
        agreement_data = []

        for i in range(len(assessments)):
            for j in range(i + 1, len(assessments)):
                assessment_a = assessments[i]
                assessment_b = assessments[j]

                pair = (assessment_a.reviewer_id, assessment_b.reviewer_id)
                reviewer_pairs.append(pair)

                if criterion_id:
                    # Analyze specific criterion
                    score_a = assessment_a.criterion_scores.get(criterion_id, {}).get("score")
                    score_b = assessment_b.criterion_scores.get(criterion_id, {}).get("score")

                    if score_a is not None and score_b is not None:
                        agreement_data.append((score_a, score_b))
                else:
                    # Analyze overall scores
                    agreement_data.append((assessment_a.overall_score, assessment_b.overall_score))

        if not agreement_data:
            raise ValueError("No comparable assessment data found")

        # Calculate agreement statistics
        kappa_score = self._calculate_kappa(agreement_data)
        agreement_percentage = self._calculate_agreement_percentage(agreement_data)
        disagreement_details = self._analyze_disagreements(agreement_data, reviewer_pairs)

        return InterRaterReliability(
            kappa_score=kappa_score,
            agreement_percentage=agreement_percentage,
            disagreement_details=disagreement_details,
            reviewer_pairs=reviewer_pairs,
            assessment_count=len(assessments)
        )

    def create_consensus_assessment(
        self,
        assessments: List[QualityAssessment],
        consensus_method: str = "median"
    ) -> QualityAssessment:
        """
        Create consensus assessment from multiple reviewer assessments.

        Args:
            assessments: List of assessments to combine
            consensus_method: Method for consensus (median, mean, expert_adjudication)

        Returns:
            Consensus quality assessment

        Raises:
            ValueError: If assessments are incompatible or insufficient
        """
        if not assessments:
            raise ValueError("No assessments provided for consensus")

        if len(assessments) == 1:
            return assessments[0]  # Single assessment is consensus

        # Validate assessments are for same paper and framework
        paper_id = assessments[0].paper_id
        framework = assessments[0].framework

        for assessment in assessments[1:]:
            if assessment.paper_id != paper_id:
                raise ValueError("All assessments must be for the same paper")
            if assessment.framework != framework:
                raise ValueError("All assessments must use the same framework")

        # Calculate consensus scores
        consensus_scores = {}
        all_criteria = set()

        for assessment in assessments:
            all_criteria.update(assessment.criterion_scores.keys())

        for criterion_id in all_criteria:
            criterion_assessments = []
            for assessment in assessments:
                if criterion_id in assessment.criterion_scores:
                    criterion_assessments.append(assessment.criterion_scores[criterion_id])

            if criterion_assessments:
                consensus_scores[criterion_id] = self._calculate_criterion_consensus(
                    criterion_assessments, consensus_method
                )

        # Calculate consensus overall score
        overall_scores = [a.overall_score for a in assessments]
        consensus_overall_score = self._apply_consensus_method(overall_scores, consensus_method)

        # Calculate consensus risk of bias
        risk_levels = [RiskLevel(a.risk_of_bias) for a in assessments]
        consensus_risk = self._calculate_risk_consensus(risk_levels)

        # Create consensus assessment
        consensus_assessment = QualityAssessment(
            paper_id=paper_id,
            framework=framework,
            reviewer_id="consensus",
            overall_score=consensus_overall_score,
            risk_of_bias=consensus_risk.value,
            criterion_scores=consensus_scores,
            assessment_date=datetime.now(),
            notes=(
                f"Consensus assessment from {len(assessments)} reviewers "
                f"using {consensus_method} method"
            ),
            validated=True
        )

        return consensus_assessment

    def assess_quality_automatically(
        self,
        paper: ResearchPaper,
        framework: QualityFramework = QualityFramework.PRISMA
    ) -> Dict[str, Any]:
        """
        Perform automated quality assessment using heuristics and text analysis.

        Args:
            paper: Research paper to assess
            framework: Quality framework to use

        Returns:
            Automated quality assessment results with confidence scores

        Note:
            Automated assessment should be reviewed by human assessors
        """
        assessment_results = {
            "paper_id": paper.id,
            "framework": framework.value,
            "automated": True,
            "assessment_date": datetime.now().isoformat(),
            "criterion_assessments": {},
            "overall_assessment": {},
            "confidence_scores": {},
            "recommendations": []
        }

        framework_criteria = self._frameworks[framework]

        for criterion_id, criterion in framework_criteria.items():
            # Automated assessment based on available metadata
            automated_result = self._assess_criterion_automatically(paper, criterion)
            assessment_results["criterion_assessments"][criterion_id] = automated_result

        # Calculate automated overall scores
        automated_scores = [
            result["score"] for result in assessment_results["criterion_assessments"].values()
        ]

        assessment_results["overall_assessment"] = {
            "overall_score": statistics.mean(automated_scores) if automated_scores else 0.0,
            "risk_level": "unclear",  # Automated assessment typically unclear
            "confidence": "low",
            "justification": "Automated assessment based on available metadata"
        }

        # Add recommendations for manual review
        assessment_results["recommendations"] = self._generate_assessment_recommendations(
            paper, assessment_results
        )

        return assessment_results

    def validate_assessment_completeness(
        self,
        assessment: QualityAssessment,
        framework: QualityFramework
    ) -> Dict[str, Any]:
        """
        Validate completeness and quality of an assessment.

        Args:
            assessment: Quality assessment to validate
            framework: Expected quality framework

        Returns:
            Validation results with completeness and quality indicators
        """
        validation_results = {
            "complete": True,
            "valid": True,
            "errors": [],
            "warnings": [],
            "missing_criteria": [],
            "quality_indicators": {}
        }

        framework_criteria = self._frameworks[framework]

        # Check for required criteria
        for criterion_id, criterion in framework_criteria.items():
            if criterion.required and criterion_id not in assessment.criterion_scores:
                validation_results["missing_criteria"].append(criterion_id)
                validation_results["complete"] = False

        # Validate existing criterion scores
        for criterion_id, score_data in assessment.criterion_scores.items():
            try:
                self._validate_assessment_criterion(criterion_id, score_data, framework_criteria)
            except ValueError as e:
                validation_results["errors"].append(f"Criterion {criterion_id}: {str(e)}")
                validation_results["valid"] = False

        # Quality indicators
        validation_results["quality_indicators"] = {
            "justification_completeness": self._assess_justification_completeness(assessment),
            "evidence_provided": self._assess_evidence_provision(assessment),
            "internal_consistency": self._assess_internal_consistency(assessment),
            "bias_consideration": self._assess_bias_consideration(assessment)
        }

        return validation_results

    def generate_quality_report(
        self,
        assessments: List[QualityAssessment],
        include_reliability: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive quality assessment report.

        Args:
            assessments: List of quality assessments to include
            include_reliability: Whether to include inter-rater reliability analysis

        Returns:
            Comprehensive quality report
        """
        if not assessments:
            return {"error": "No assessments provided"}

        report = {
            "report_date": datetime.now().isoformat(),
            "assessment_count": len(assessments),
            "papers_assessed": len(set(a.paper_id for a in assessments)),
            "reviewers": list(set(a.reviewer_id for a in assessments)),
            "frameworks_used": list(set(a.framework for a in assessments)),
            "quality_summary": {},
            "risk_of_bias_summary": {},
            "framework_analysis": {},
        }

        # Overall quality statistics
        overall_scores = [a.overall_score for a in assessments]
        report["quality_summary"] = {
            "mean_score": statistics.mean(overall_scores),
            "median_score": statistics.median(overall_scores),
            "std_dev": statistics.stdev(overall_scores) if len(overall_scores) > 1 else 0,
            "score_distribution": self._calculate_score_distribution(overall_scores),
            "high_quality_papers": len([s for s in overall_scores if s >= 0.8]),
            "low_quality_papers": len([s for s in overall_scores if s < 0.4])
        }

        # Risk of bias analysis
        risk_levels = [a.risk_of_bias for a in assessments]
        report["risk_of_bias_summary"] = {
            "low_risk": risk_levels.count("low"),
            "moderate_risk": risk_levels.count("moderate"),
            "high_risk": risk_levels.count("high"),
            "unclear_risk": risk_levels.count("unclear")
        }

        # Framework-specific analysis
        for framework in set(a.framework for a in assessments):
            framework_assessments = [a for a in assessments if a.framework == framework]
            report["framework_analysis"][framework] = self._analyze_framework_performance(
                framework_assessments
            )

        # Inter-rater reliability if requested
        if include_reliability and len(assessments) > 1:
            try:
                reliability = self.calculate_inter_rater_reliability(assessments)
                report["inter_rater_reliability"] = {
                    "kappa_score": reliability.kappa_score,
                    "agreement_percentage": reliability.agreement_percentage,
                    "assessment_count": reliability.assessment_count,
                    "reviewer_pairs": len(reliability.reviewer_pairs)
                }
            except ValueError as e:
                report["inter_rater_reliability"] = {"error": str(e)}

        return report

    # Private helper methods

    def _initialize_frameworks(self) -> Dict[QualityFramework, Dict[str, QualityCriterion]]:
        """Initialize quality assessment frameworks and their criteria."""
        frameworks = {}

        # PRISMA framework criteria
        frameworks[QualityFramework.PRISMA] = {
            "title_abstract": QualityCriterion(
                QualityDomain.REPORTING_QUALITY, "title_abstract",
                "Title and abstract clearly describe the study", 0.1
            ),
            "introduction": QualityCriterion(
                QualityDomain.REPORTING_QUALITY, "introduction",
                "Introduction provides clear rationale and objectives", 0.1
            ),
            "methods_protocol": QualityCriterion(
                QualityDomain.STUDY_DESIGN, "methods_protocol",
                "Methods section describes protocol and registration", 0.15
            ),
            "eligibility_criteria": QualityCriterion(
                QualityDomain.PARTICIPANT_SELECTION, "eligibility_criteria",
                "Clear eligibility criteria for study selection", 0.15
            ),
            "search_strategy": QualityCriterion(
                QualityDomain.STUDY_DESIGN, "search_strategy",
                "Comprehensive and reproducible search strategy", 0.15
            ),
            "study_selection": QualityCriterion(
                QualityDomain.PARTICIPANT_SELECTION, "study_selection",
                "Study selection process clearly described", 0.1
            ),
            "data_extraction": QualityCriterion(
                QualityDomain.OUTCOME_MEASUREMENT, "data_extraction",
                "Data extraction methods clearly described", 0.1
            ),
            "risk_of_bias": QualityCriterion(
                QualityDomain.RISK_OF_BIAS, "risk_of_bias",
                "Risk of bias assessment conducted", 0.15
            )
        }

        # Additional frameworks would be added here
        # For now, we'll use PRISMA as the primary framework

        return frameworks

    def _initialize_quality_criteria(self) -> Dict[str, QualityCriterion]:
        """Initialize quality criteria database."""
        all_criteria = {}
        for framework_criteria in self._frameworks.values():
            all_criteria.update(framework_criteria)
        return all_criteria

    def _validate_criterion_score(
        self, criterion: QualityCriterion, score_data: Dict[str, Any]
    ) -> None:
        """Validate individual criterion score data."""
        required_fields = ["score", "risk_level", "justification"]
        for field in required_fields:
            if field not in score_data:
                raise ValueError(f"Missing required field: {field}")

        score = score_data["score"]
        if not isinstance(score, (int, float)) or not (0.0 <= score <= 1.0):
            raise ValueError(f"Score must be a number between 0.0 and 1.0, got: {score}")

        try:
            RiskLevel(score_data["risk_level"])
        except ValueError:
            raise ValueError(f"Invalid risk level: {score_data['risk_level']}")

        if not score_data["justification"].strip():
            raise ValueError("Justification cannot be empty")

    def _calculate_overall_score(
        self,
        assessment_results: List[AssessmentResult],
        criteria: Dict[str, QualityCriterion]
    ) -> float:
        """Calculate weighted overall quality score."""
        total_weight = sum(criteria[r.criterion_id].weight for r in assessment_results)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(
            r.score * criteria[r.criterion_id].weight
            for r in assessment_results
        )

        return weighted_sum / total_weight

    def _calculate_overall_risk(self, assessment_results: List[AssessmentResult]) -> RiskLevel:
        """Calculate overall risk of bias level."""
        risk_counts = {level: 0 for level in RiskLevel}
        for result in assessment_results:
            risk_counts[result.risk_level] += 1

        # Conservative approach: any high risk makes overall high
        if risk_counts[RiskLevel.HIGH] > 0:
            return RiskLevel.HIGH
        elif risk_counts[RiskLevel.MODERATE] > 0:
            return RiskLevel.MODERATE
        elif risk_counts[RiskLevel.UNCLEAR] > len(assessment_results) // 2:
            return RiskLevel.UNCLEAR
        else:
            return RiskLevel.LOW

    def _calculate_kappa(self, agreement_data: List[Tuple[float, float]]) -> float:
        """Calculate Cohen's kappa for inter-rater reliability."""
        # Simplified kappa calculation
        # In practice, would use a statistical library
        agreements = sum(1 for a, b in agreement_data if abs(a - b) < 0.1)
        total = len(agreement_data)
        observed_agreement = agreements / total if total > 0 else 0

        # Expected agreement (simplified)
        expected_agreement = 0.25  # Simplified assumption

        if expected_agreement == 1.0:
            return 1.0

        kappa = (observed_agreement - expected_agreement) / (1.0 - expected_agreement)
        return max(0.0, min(1.0, kappa))  # Clamp to [0, 1]

    def _calculate_agreement_percentage(
        self, agreement_data: List[Tuple[float, float]]
    ) -> float:
        """Calculate percentage agreement between raters."""
        if not agreement_data:
            return 0.0

        agreements = sum(1 for a, b in agreement_data if abs(a - b) < 0.1)
        return (agreements / len(agreement_data)) * 100

    def _analyze_disagreements(
        self,
        agreement_data: List[Tuple[float, float]],
        reviewer_pairs: List[Tuple[str, str]]
    ) -> Dict[str, Any]:
        """Analyze patterns in reviewer disagreements."""
        disagreements = []
        for (score_a, score_b), (reviewer_a, reviewer_b) in zip(agreement_data, reviewer_pairs):
            if abs(score_a - score_b) >= 0.1:  # Significant disagreement
                disagreements.append({
                    "reviewers": (reviewer_a, reviewer_b),
                    "scores": (score_a, score_b),
                    "difference": abs(score_a - score_b)
                })

        return {
            "disagreement_count": len(disagreements),
            "major_disagreements": len([d for d in disagreements if d["difference"] > 0.3]),
            "average_difference": statistics.mean([d["difference"] for d in disagreements])
            if disagreements else 0.0,
            "disagreement_details": disagreements[:10]  # Limit for readability
        }

    def _apply_consensus_method(
        self, values: List[float], method: str
    ) -> float:
        """Apply consensus method to list of values."""
        if not values:
            return 0.0

        if method == "mean":
            return statistics.mean(values)
        elif method == "median":
            return statistics.median(values)
        elif method == "expert_adjudication":
            # For now, use median as fallback
            return statistics.median(values)
        else:
            return statistics.median(values)  # Default

    def _calculate_criterion_consensus(
        self,
        criterion_assessments: List[Dict[str, Any]],
        method: str
    ) -> Dict[str, Any]:
        """Calculate consensus for a specific criterion."""
        scores = [assessment["score"] for assessment in criterion_assessments]
        consensus_score = self._apply_consensus_method(scores, method)

        # Risk level consensus (most conservative)
        risk_levels = [RiskLevel(assessment["risk_level"]) for assessment in criterion_assessments]
        consensus_risk = self._calculate_risk_consensus(risk_levels)

        # Combine justifications
        justifications = [assessment["justification"] for assessment in criterion_assessments]
        combined_justification = "; ".join(justifications)

        return {
            "score": consensus_score,
            "risk_level": consensus_risk.value,
            "justification": combined_justification,
            "evidence": "Consensus from multiple reviewers"
        }

    def _calculate_risk_consensus(self, risk_levels: List[RiskLevel]) -> RiskLevel:
        """Calculate consensus risk level (conservative approach)."""
        risk_counts = {level: risk_levels.count(level) for level in RiskLevel}

        # Conservative: any high risk makes consensus high
        if risk_counts[RiskLevel.HIGH] > 0:
            return RiskLevel.HIGH
        elif risk_counts[RiskLevel.MODERATE] > 0:
            return RiskLevel.MODERATE
        elif risk_counts[RiskLevel.UNCLEAR] >= len(risk_levels) // 2:
            return RiskLevel.UNCLEAR
        else:
            return RiskLevel.LOW

    def _assess_criterion_automatically(
        self, paper: ResearchPaper, criterion: QualityCriterion
    ) -> Dict[str, Any]:
        """Perform automated assessment of a quality criterion."""
        # Basic automated assessment based on available metadata
        score = 0.5  # Default neutral score
        confidence = "low"
        justification = "Automated assessment based on limited metadata"

        # Simple heuristics based on paper attributes
        if criterion.domain == QualityDomain.REPORTING_QUALITY:
            if paper.abstract and len(paper.abstract) > 100:
                score += 0.2
            if paper.keywords and len(paper.keywords) > 3:
                score += 0.1
            justification = "Assessment based on abstract length and keyword presence"

        elif criterion.domain == QualityDomain.STUDY_DESIGN:
            if paper.methodology:
                score += 0.2
            if paper.study_type:
                score += 0.2
            justification = "Assessment based on reported methodology and study type"

        elif criterion.domain == QualityDomain.PARTICIPANT_SELECTION:
            if paper.sample_size and paper.sample_size > 50:
                score += 0.3
            justification = "Assessment based on sample size information"

        # Clamp score to valid range
        score = max(0.0, min(1.0, score))

        return {
            "score": score,
            "risk_level": "unclear",  # Automated assessments typically unclear
            "justification": justification,
            "confidence": confidence,
            "automated": True
        }

    def _generate_assessment_recommendations(
        self, paper: ResearchPaper, assessment_results: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for manual review."""
        recommendations = []

        # Low confidence areas need manual review
        low_confidence_criteria = [
            criterion_id
            for criterion_id, result in assessment_results["criterion_assessments"].items()
            if result.get("confidence") == "low"
        ]

        if low_confidence_criteria:
            recommendations.append(
                f"Manual review recommended for criteria: {', '.join(low_confidence_criteria)}"
            )

        # Missing information recommendations
        if not paper.abstract or len(paper.abstract) < 100:
            recommendations.append("Abstract appears incomplete - verify reporting quality")

        if not paper.methodology:
            recommendations.append("Methodology not clearly identified - manual assessment needed")

        if not paper.sample_size:
            recommendations.append(
                "Sample size information missing - check participant selection quality"
            )

        return recommendations

    def _validate_assessment_criterion(
        self,
        criterion_id: str,
        score_data: Dict[str, Any],
        framework_criteria: Dict[str, QualityCriterion]
    ) -> None:
        """Validate assessment criterion data."""
        if criterion_id not in framework_criteria:
            raise ValueError(f"Unknown criterion: {criterion_id}")

        criterion = framework_criteria[criterion_id]
        self._validate_criterion_score(criterion, score_data)

    def _assess_justification_completeness(self, assessment: QualityAssessment) -> float:
        """Assess completeness of justifications in assessment."""
        justifications = [
            score_data.get("justification", "")
            for score_data in assessment.criterion_scores.values()
        ]

        if not justifications:
            return 0.0

        complete_justifications = sum(
            1 for j in justifications if j and len(j.split()) >= 10
        )

        return complete_justifications / len(justifications)

    def _assess_evidence_provision(self, assessment: QualityAssessment) -> float:
        """Assess provision of evidence in assessment."""
        evidence_counts = sum(
            1 for score_data in assessment.criterion_scores.values()
            if score_data.get("evidence")
        )

        total_criteria = len(assessment.criterion_scores)
        return evidence_counts / total_criteria if total_criteria > 0 else 0.0

    def _assess_internal_consistency(self, assessment: QualityAssessment) -> float:
        """Assess internal consistency of assessment scores."""
        scores = [
            score_data["score"] for score_data in assessment.criterion_scores.values()
            if "score" in score_data
        ]

        if len(scores) < 2:
            return 1.0

        # Simple consistency check based on standard deviation
        std_dev = statistics.stdev(scores)
        # Lower standard deviation indicates more consistency
        consistency_score = max(0.0, 1.0 - (std_dev * 2))  # Normalize roughly

        return consistency_score

    def _assess_bias_consideration(self, assessment: QualityAssessment) -> float:
        """Assess consideration of bias in assessment."""
        bias_mentions = 0
        bias_keywords = ["bias", "limitation", "confound", "validity", "reliability"]

        for score_data in assessment.criterion_scores.values():
            justification = score_data.get("justification", "").lower()
            if any(keyword in justification for keyword in bias_keywords):
                bias_mentions += 1

        total_criteria = len(assessment.criterion_scores)
        return bias_mentions / total_criteria if total_criteria > 0 else 0.0

    def _calculate_score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate distribution of quality scores."""
        distribution = {
            "excellent": 0,  # 0.8-1.0
            "good": 0,       # 0.6-0.8
            "fair": 0,       # 0.4-0.6
            "poor": 0        # 0.0-0.4
        }

        for score in scores:
            if score >= 0.8:
                distribution["excellent"] += 1
            elif score >= 0.6:
                distribution["good"] += 1
            elif score >= 0.4:
                distribution["fair"] += 1
            else:
                distribution["poor"] += 1

        return distribution

    def _analyze_framework_performance(
        self, framework_assessments: List[QualityAssessment]
    ) -> Dict[str, Any]:
        """Analyze performance metrics for a specific framework."""
        scores = [a.overall_score for a in framework_assessments]

        analysis = {
            "assessment_count": len(framework_assessments),
            "mean_score": statistics.mean(scores) if scores else 0.0,
            "median_score": statistics.median(scores) if scores else 0.0,
            "score_range": {
                "min": min(scores) if scores else 0.0,
                "max": max(scores) if scores else 0.0
            }
        }

        # Criterion-specific analysis
        criterion_analysis = {}
        all_criteria = set()
        for assessment in framework_assessments:
            all_criteria.update(assessment.criterion_scores.keys())

        for criterion_id in all_criteria:
            criterion_scores = []
            for assessment in framework_assessments:
                if criterion_id in assessment.criterion_scores:
                    score = assessment.criterion_scores[criterion_id].get("score")
                    if score is not None:
                        criterion_scores.append(score)

            if criterion_scores:
                criterion_analysis[criterion_id] = {
                    "mean_score": statistics.mean(criterion_scores),
                    "assessment_count": len(criterion_scores)
                }

        analysis["criterion_analysis"] = criterion_analysis
        return analysis


class QualityAssessmentError(Exception):
    """Exception for quality assessment operations."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause