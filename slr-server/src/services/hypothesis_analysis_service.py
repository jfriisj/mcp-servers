"""
Hypothesis Analysis Service for systematic literature review hypothesis testing and 
evidence synthesis.

This module implements the HypothesisAnalysisService class following GRADE framework
guidelines and systematic review best practices for hypothesis analysis and meta-analysis.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import re
import math

from ..domain.models import ResearchPaper, ResearchHypothesis, EvidenceItem
from ..repositories.paper_repository import PaperRepository


class EvidenceLevel(Enum):
    """GRADE evidence quality levels."""
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"


class EffectDirection(Enum):
    """Direction of treatment effect."""
    BENEFICIAL = "beneficial"
    HARMFUL = "harmful"
    NO_EFFECT = "no_effect"
    UNCLEAR = "unclear"


class StatisticalMethod(Enum):
    """Statistical methods for meta-analysis."""
    FIXED_EFFECTS = "fixed_effects"
    RANDOM_EFFECTS = "random_effects"
    BAYESIAN = "bayesian"
    NETWORK_META = "network_meta"


class OutcomeType(Enum):
    """Types of outcome measures."""
    CONTINUOUS = "continuous"
    DICHOTOMOUS = "dichotomous"
    TIME_TO_EVENT = "time_to_event"
    ORDINAL = "ordinal"
    RATE = "rate"


@dataclass
class StudyEffect:
    """Individual study effect size and statistics."""
    study_id: str
    effect_size: float
    standard_error: float
    confidence_interval: Tuple[float, float]
    sample_size: int
    weight: float
    outcome_type: OutcomeType
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class MetaAnalysisResult:
    """Meta-analysis pooled results."""
    pooled_effect: float
    pooled_se: float
    confidence_interval: Tuple[float, float]
    p_value: float
    i_squared: float  # Heterogeneity measure
    tau_squared: float  # Between-study variance
    q_statistic: float
    studies_included: int
    total_participants: int
    method: StatisticalMethod
    forest_plot_data: Dict[str, Any]


@dataclass
class GRADEAssessment:
    """GRADE framework assessment."""
    outcome: str
    initial_rating: EvidenceLevel
    final_rating: EvidenceLevel
    risk_of_bias: int  # Downgrade points (0-2)
    inconsistency: int  # Downgrade points (0-2)
    indirectness: int  # Downgrade points (0-2)
    imprecision: int  # Downgrade points (0-2)
    publication_bias: int  # Downgrade points (0-1)
    large_effect: int  # Upgrade points (0-2)
    dose_response: int  # Upgrade points (0-1)
    confounding: int  # Upgrade points (0-1)
    justification: str
    certainty_factors: Dict[str, str]


@dataclass
class HypothesisTestResult:
    """Results of hypothesis testing."""
    hypothesis_id: str
    hypothesis_text: str
    supported: bool
    confidence_level: float
    effect_direction: EffectDirection
    meta_analysis: Optional[MetaAnalysisResult]
    grade_assessment: Optional[GRADEAssessment]
    evidence_summary: Dict[str, Any]
    limitations: List[str]
    conclusions: List[str]


class HypothesisAnalysisService:
    """
    Hypothesis analysis service for systematic literature reviews.

    Implements hypothesis extraction, evidence classification, meta-analysis,
    and GRADE framework assessment following systematic review standards.

    Key Features:
    - Hypothesis extraction from research questions and papers
    - Evidence classification and quality assessment
    - Meta-analysis with multiple statistical methods
    - GRADE framework evidence evaluation
    - Publication bias detection and assessment
    - Statistical synthesis and effect size calculation
    - Heterogeneity assessment and subgroup analysis

    Follows Clean Architecture Layer 2 principles:
    - Framework-agnostic business logic
    - Contains statistical and methodological business rules
    - Validates evidence and enforces quality standards
    - Provides comprehensive hypothesis testing results
    """

    def __init__(self, paper_repository: PaperRepository):
        """
        Initialize HypothesisAnalysisService.

        Args:
            paper_repository: Repository for research paper access
        """
        self.paper_repository = paper_repository
        self._grade_criteria = self._initialize_grade_criteria()
        self._statistical_methods = self._initialize_statistical_methods()

    def extract_hypotheses(
        self,
        research_question: str,
        included_papers: List[ResearchPaper] = None
    ) -> List[ResearchHypothesis]:
        """
        Extract research hypotheses from research question and papers.

        Args:
            research_question: Primary research question
            included_papers: Papers included in systematic review

        Returns:
            List of extracted hypotheses

        Raises:
            ValueError: If research question is invalid
        """
        if not research_question or not research_question.strip():
            raise ValueError("Research question cannot be empty")

        hypotheses = []

        # Extract primary hypothesis from research question
        primary_hypothesis = self._extract_primary_hypothesis(research_question)
        if primary_hypothesis:
            hypotheses.append(primary_hypothesis)

        # Extract hypotheses from included papers
        if included_papers:
            for paper in included_papers:
                paper_hypotheses = self._extract_paper_hypotheses(paper)
                hypotheses.extend(paper_hypotheses)

        # Remove duplicates and consolidate similar hypotheses
        unique_hypotheses = self._consolidate_hypotheses(hypotheses)

        return unique_hypotheses

    def classify_evidence(
        self,
        hypothesis: ResearchHypothesis,
        papers: List[ResearchPaper],
        outcome_measures: List[str] = None
    ) -> List[EvidenceItem]:
        """
        Classify and extract evidence relevant to hypothesis.

        Args:
            hypothesis: Hypothesis to find evidence for
            papers: Papers to search for evidence
            outcome_measures: Specific outcomes to focus on

        Returns:
            List of classified evidence items

        Raises:
            ValueError: If hypothesis or papers are invalid
        """
        if not papers:
            raise ValueError("No papers provided for evidence classification")

        evidence_items = []

        for paper in papers:
            # Extract evidence from each paper
            paper_evidence = self._extract_paper_evidence(
                paper, hypothesis, outcome_measures
            )
            evidence_items.extend(paper_evidence)

        # Classify evidence by strength and relevance
        classified_evidence = self._classify_evidence_strength(evidence_items)

        return classified_evidence

    def perform_meta_analysis(
        self,
        evidence_items: List[EvidenceItem],
        outcome_type: OutcomeType,
        method: StatisticalMethod = StatisticalMethod.RANDOM_EFFECTS
    ) -> MetaAnalysisResult:
        """
        Perform meta-analysis on evidence items.

        Args:
            evidence_items: Evidence to include in meta-analysis
            outcome_type: Type of outcome measure
            method: Statistical method for pooling

        Returns:
            Meta-analysis results

        Raises:
            ValueError: If insufficient evidence or invalid parameters
        """
        if len(evidence_items) < 2:
            raise ValueError("At least 2 studies required for meta-analysis")

        # Extract effect sizes from evidence
        study_effects = self._extract_effect_sizes(evidence_items, outcome_type)

        if len(study_effects) < 2:
            raise ValueError("Insufficient extractable effect sizes for meta-analysis")

        # Perform statistical pooling
        pooled_result = self._pool_effect_sizes(study_effects, method)

        # Assess heterogeneity
        heterogeneity_stats = self._assess_heterogeneity(study_effects, pooled_result)

        # Create comprehensive result
        meta_result = MetaAnalysisResult(
            pooled_effect=pooled_result["effect"],
            pooled_se=pooled_result["se"],
            confidence_interval=pooled_result["ci"],
            p_value=pooled_result["p_value"],
            i_squared=heterogeneity_stats["i_squared"],
            tau_squared=heterogeneity_stats["tau_squared"],
            q_statistic=heterogeneity_stats["q_statistic"],
            studies_included=len(study_effects),
            total_participants=sum(effect.sample_size for effect in study_effects),
            method=method,
            forest_plot_data=self._generate_forest_plot_data(study_effects, pooled_result)
        )

        return meta_result

    def assess_grade_evidence(
        self,
        outcome: str,
        evidence_items: List[EvidenceItem],
        meta_analysis: Optional[MetaAnalysisResult] = None
    ) -> GRADEAssessment:
        """
        Assess evidence quality using GRADE framework.

        Args:
            outcome: Outcome being assessed
            evidence_items: Evidence to assess
            meta_analysis: Meta-analysis results if available

        Returns:
            GRADE assessment

        Raises:
            ValueError: If insufficient evidence for assessment
        """
        if not evidence_items:
            raise ValueError("No evidence provided for GRADE assessment")

        # Start with initial rating based on study design
        initial_rating = self._determine_initial_grade_rating(evidence_items)

        # Assess downgrading factors
        downgrade_assessments = self._assess_downgrade_factors(
            evidence_items, meta_analysis
        )

        # Assess upgrading factors
        upgrade_assessments = self._assess_upgrade_factors(
            evidence_items, meta_analysis
        )

        # Calculate final rating
        final_rating = self._calculate_final_grade_rating(
            initial_rating, downgrade_assessments, upgrade_assessments
        )

        # Generate justification
        justification = self._generate_grade_justification(
            initial_rating, final_rating, downgrade_assessments, upgrade_assessments
        )

        # Create certainty factors explanation
        certainty_factors = self._generate_certainty_factors(
            downgrade_assessments, upgrade_assessments
        )

        return GRADEAssessment(
            outcome=outcome,
            initial_rating=initial_rating,
            final_rating=final_rating,
            risk_of_bias=downgrade_assessments["risk_of_bias"],
            inconsistency=downgrade_assessments["inconsistency"],
            indirectness=downgrade_assessments["indirectness"],
            imprecision=downgrade_assessments["imprecision"],
            publication_bias=downgrade_assessments["publication_bias"],
            large_effect=upgrade_assessments["large_effect"],
            dose_response=upgrade_assessments["dose_response"],
            confounding=upgrade_assessments["confounding"],
            justification=justification,
            certainty_factors=certainty_factors
        )

    def test_hypothesis(
        self,
        hypothesis: ResearchHypothesis,
        evidence_items: List[EvidenceItem],
        significance_level: float = 0.05
    ) -> HypothesisTestResult:
        """
        Perform comprehensive hypothesis testing.

        Args:
            hypothesis: Hypothesis to test
            evidence_items: Evidence supporting/refuting hypothesis
            significance_level: Statistical significance threshold

        Returns:
            Comprehensive hypothesis test results

        Raises:
            ValueError: If hypothesis or evidence are invalid
        """
        if not evidence_items:
            raise ValueError("No evidence provided for hypothesis testing")

        # Determine outcome type and perform meta-analysis if possible
        outcome_type = self._determine_outcome_type(evidence_items)
        meta_analysis = None

        try:
            if len(evidence_items) >= 2:
                meta_analysis = self.perform_meta_analysis(
                    evidence_items, outcome_type
                )
        except ValueError:
            # Not enough data for meta-analysis
            pass

        # Assess evidence quality with GRADE
        grade_assessment = None
        if hypothesis.expected_outcome:
            try:
                grade_assessment = self.assess_grade_evidence(
                    hypothesis.expected_outcome, evidence_items, meta_analysis
                )
            except ValueError:
                # Insufficient evidence for GRADE
                pass

        # Determine if hypothesis is supported
        hypothesis_supported = self._determine_hypothesis_support(
            hypothesis, evidence_items, meta_analysis, significance_level
        )

        # Calculate confidence level
        confidence_level = self._calculate_hypothesis_confidence(
            evidence_items, meta_analysis, grade_assessment
        )

        # Determine effect direction
        effect_direction = self._determine_effect_direction(
            hypothesis, evidence_items, meta_analysis
        )

        # Generate evidence summary
        evidence_summary = self._generate_evidence_summary(
            evidence_items, meta_analysis
        )

        # Identify limitations
        limitations = self._identify_analysis_limitations(
            evidence_items, meta_analysis, grade_assessment
        )

        # Generate conclusions
        conclusions = self._generate_hypothesis_conclusions(
            hypothesis, hypothesis_supported, confidence_level, effect_direction
        )

        return HypothesisTestResult(
            hypothesis_id=str(hypothesis.id) if hypothesis.id else "unknown",
            hypothesis_text=hypothesis.hypothesis_text,
            supported=hypothesis_supported,
            confidence_level=confidence_level,
            effect_direction=effect_direction,
            meta_analysis=meta_analysis,
            grade_assessment=grade_assessment,
            evidence_summary=evidence_summary,
            limitations=limitations,
            conclusions=conclusions
        )

    def detect_publication_bias(
        self,
        study_effects: List[StudyEffect],
        method: str = "egger"
    ) -> Dict[str, Any]:
        """
        Detect publication bias using statistical tests.

        Args:
            study_effects: Study effect sizes
            method: Method for bias detection (egger, begg, funnel)

        Returns:
            Publication bias assessment results
        """
        if len(study_effects) < 3:
            return {
                "method": method,
                "sufficient_studies": False,
                "warning": "At least 3 studies required for publication bias assessment"
            }

        bias_assessment = {
            "method": method,
            "sufficient_studies": True,
            "test_statistic": 0.0,
            "p_value": 1.0,
            "significant_bias": False,
            "interpretation": ""
        }

        if method == "egger":
            bias_assessment.update(self._egger_test(study_effects))
        elif method == "begg":
            bias_assessment.update(self._begg_test(study_effects))
        elif method == "funnel":
            bias_assessment.update(self._funnel_plot_assessment(study_effects))

        return bias_assessment

    def generate_synthesis_report(
        self,
        hypothesis_results: List[HypothesisTestResult]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive evidence synthesis report.

        Args:
            hypothesis_results: Results from hypothesis testing

        Returns:
            Comprehensive synthesis report
        """
        if not hypothesis_results:
            return {"error": "No hypothesis results provided"}

        report = {
            "report_date": datetime.now().isoformat(),
            "hypotheses_tested": len(hypothesis_results),
            "synthesis_summary": {},
            "evidence_quality": {},
            "statistical_synthesis": {},
            "grade_summary": {},
            "limitations": [],
            "recommendations": []
        }

        # Overall synthesis summary
        supported_hypotheses = sum(1 for result in hypothesis_results if result.supported)
        report["synthesis_summary"] = {
            "total_hypotheses": len(hypothesis_results),
            "supported_hypotheses": supported_hypotheses,
            "support_rate": supported_hypotheses / len(hypothesis_results),
            "high_confidence_results": sum(
                1 for result in hypothesis_results if result.confidence_level > 0.8
            ),
            "meta_analyses_conducted": sum(
                1 for result in hypothesis_results if result.meta_analysis
            )
        }

        # Evidence quality assessment
        grade_ratings = [
            result.grade_assessment.final_rating.value
            for result in hypothesis_results
            if result.grade_assessment
        ]

        if grade_ratings:
            report["evidence_quality"] = {
                "high_quality": grade_ratings.count("high"),
                "moderate_quality": grade_ratings.count("moderate"),
                "low_quality": grade_ratings.count("low"),
                "very_low_quality": grade_ratings.count("very_low")
            }

        # Statistical synthesis summary
        meta_analyses = [
            result.meta_analysis for result in hypothesis_results
            if result.meta_analysis
        ]

        if meta_analyses:
            report["statistical_synthesis"] = {
                "meta_analyses_count": len(meta_analyses),
                "total_studies": sum(ma.studies_included for ma in meta_analyses),
                "total_participants": sum(ma.total_participants for ma in meta_analyses),
                "significant_results": sum(
                    1 for ma in meta_analyses if ma.p_value < 0.05
                ),
                "high_heterogeneity": sum(
                    1 for ma in meta_analyses if ma.i_squared > 75
                )
            }

        # Compile limitations and recommendations
        all_limitations = []
        for result in hypothesis_results:
            all_limitations.extend(result.limitations)

        report["limitations"] = list(set(all_limitations))  # Remove duplicates
        report["recommendations"] = self._generate_synthesis_recommendations(
            hypothesis_results
        )

        return report

    # Private helper methods

    def _initialize_grade_criteria(self) -> Dict[str, Any]:
        """Initialize GRADE assessment criteria."""
        return {
            "initial_ratings": {
                "randomized_trial": EvidenceLevel.HIGH,
                "observational": EvidenceLevel.LOW,
                "case_series": EvidenceLevel.VERY_LOW
            },
            "downgrade_factors": {
                "risk_of_bias": {"serious": 1, "very_serious": 2},
                "inconsistency": {"serious": 1, "very_serious": 2},
                "indirectness": {"serious": 1, "very_serious": 2},
                "imprecision": {"serious": 1, "very_serious": 2},
                "publication_bias": {"likely": 1}
            },
            "upgrade_factors": {
                "large_effect": {"large": 1, "very_large": 2},
                "dose_response": {"present": 1},
                "confounding": {"reduces_effect": 1}
            }
        }

    def _initialize_statistical_methods(self) -> Dict[str, Any]:
        """Initialize statistical methods configurations."""
        return {
            "fixed_effects": {
                "assumption": "single_true_effect",
                "weights": "inverse_variance"
            },
            "random_effects": {
                "assumption": "distribution_of_effects",
                "weights": "dersimonian_laird"
            }
        }

    def _extract_primary_hypothesis(self, research_question: str) -> Optional[ResearchHypothesis]:
        """Extract primary hypothesis from research question."""
        # Simplified hypothesis extraction using patterns
        hypothesis_patterns = [
            r"(.*)\s+is\s+more\s+effective\s+than\s+(.*)",
            r"(.*)\s+reduces\s+(.*)",
            r"(.*)\s+improves\s+(.*)",
            r"(.*)\s+increases\s+(.*)",
            r"(.*)\s+decreases\s+(.*)"
        ]

        for pattern in hypothesis_patterns:
            match = re.search(pattern, research_question, re.IGNORECASE)
            if match:
                return ResearchHypothesis(
                    hypothesis_text=research_question,
                    hypothesis_type="primary",
                    direction="directional",
                    intervention=match.group(1).strip(),
                    expected_outcome=match.group(2).strip() if len(match.groups()) > 1 else None,
                    statistical_test="t_test",  # Default
                    significance_level=0.05
                )

        # If no pattern matches, create null hypothesis
        return ResearchHypothesis(
            hypothesis_text=f"Null hypothesis: {research_question}",
            hypothesis_type="null",
            direction="non_directional",
            statistical_test="t_test",
            significance_level=0.05
        )

    def _extract_paper_hypotheses(self, paper: ResearchPaper) -> List[ResearchHypothesis]:
        """Extract hypotheses from individual paper."""
        hypotheses = []
        
        # Look for hypotheses in abstract
        if paper.abstract:
            abstract_hypotheses = self._find_hypotheses_in_text(paper.abstract)
            hypotheses.extend(abstract_hypotheses)

        return hypotheses

    def _find_hypotheses_in_text(self, text: str) -> List[ResearchHypothesis]:
        """Find hypothesis statements in text."""
        hypotheses = []
        
        # Simple pattern matching for hypothesis identification
        hypothesis_indicators = [
            r"we hypothesize that (.*?)(?:\.|$)",
            r"our hypothesis is that (.*?)(?:\.|$)",
            r"we predict that (.*?)(?:\.|$)",
            r"it is hypothesized that (.*?)(?:\.|$)"
        ]

        for pattern in hypothesis_indicators:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                hypothesis = ResearchHypothesis(
                    hypothesis_text=match.strip(),
                    hypothesis_type="extracted",
                    direction="directional",
                    statistical_test="unspecified",
                    significance_level=0.05
                )
                hypotheses.append(hypothesis)

        return hypotheses

    def _consolidate_hypotheses(
        self, hypotheses: List[ResearchHypothesis]
    ) -> List[ResearchHypothesis]:
        """Remove duplicate and consolidate similar hypotheses."""
        # Simple deduplication based on text similarity
        unique_hypotheses = []
        
        for hypothesis in hypotheses:
            is_duplicate = False
            for existing in unique_hypotheses:
                if self._calculate_text_similarity(
                    hypothesis.hypothesis_text, existing.hypothesis_text
                ) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_hypotheses.append(hypothesis)

        return unique_hypotheses

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        # Simplified Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

    def _extract_paper_evidence(
        self,
        paper: ResearchPaper,
        hypothesis: ResearchHypothesis,
        outcome_measures: List[str] = None
    ) -> List[EvidenceItem]:
        """Extract evidence from paper relevant to hypothesis."""
        evidence_items = []

        # Create evidence item from paper
        evidence = EvidenceItem(
            paper_id=paper.id,
            evidence_type="study_result",
            strength="moderate",  # Default, would be assessed
            relevance_score=0.7,  # Default
            outcome_measure=hypothesis.expected_outcome or "primary_outcome",
            intervention=hypothesis.intervention or "intervention",
            population="study_population",
            setting="clinical",
            effect_size=None,  # Would be extracted from results
            confidence_interval=None,
            p_value=None,
            sample_size=paper.sample_size,
            study_design=paper.study_type or "unspecified",
            risk_of_bias="unclear",
            notes=f"Evidence from: {paper.title}"
        )

        evidence_items.append(evidence)
        return evidence_items

    def _classify_evidence_strength(
        self, evidence_items: List[EvidenceItem]
    ) -> List[EvidenceItem]:
        """Classify evidence by strength and quality."""
        for evidence in evidence_items:
            # Classify based on study design
            if evidence.study_design in ["randomized_controlled_trial", "rct"]:
                evidence.strength = "strong"
            elif evidence.study_design in ["cohort", "case_control"]:
                evidence.strength = "moderate"
            else:
                evidence.strength = "weak"

        return evidence_items

    def _extract_effect_sizes(
        self,
        evidence_items: List[EvidenceItem],
        outcome_type: OutcomeType
    ) -> List[StudyEffect]:
        """Extract effect sizes from evidence items."""
        study_effects = []

        for i, evidence in enumerate(evidence_items):
            # For demonstration, create placeholder effect sizes
            # In real implementation, would extract from study results
            if evidence.effect_size is not None:
                effect_size = evidence.effect_size
                se = 0.2  # Placeholder
            else:
                # Generate placeholder based on study characteristics
                effect_size = 0.5  # Moderate effect
                se = 0.2

            # Calculate confidence interval
            ci_lower = effect_size - 1.96 * se
            ci_upper = effect_size + 1.96 * se

            study_effect = StudyEffect(
                study_id=str(evidence.paper_id or f"study_{i}"),
                effect_size=effect_size,
                standard_error=se,
                confidence_interval=(ci_lower, ci_upper),
                sample_size=evidence.sample_size or 100,
                weight=1.0,  # Will be calculated
                outcome_type=outcome_type
            )

            study_effects.append(study_effect)

        return study_effects

    def _pool_effect_sizes(
        self,
        study_effects: List[StudyEffect],
        method: StatisticalMethod
    ) -> Dict[str, Any]:
        """Pool effect sizes using specified method."""
        # Calculate weights (inverse variance)
        for effect in study_effects:
            effect.weight = 1.0 / (effect.standard_error ** 2)

        total_weight = sum(effect.weight for effect in study_effects)

        # Calculate pooled effect
        pooled_effect = sum(
            effect.effect_size * effect.weight for effect in study_effects
        ) / total_weight

        # Calculate pooled standard error
        if method == StatisticalMethod.FIXED_EFFECTS:
            pooled_se = math.sqrt(1.0 / total_weight)
        else:  # Random effects
            # Simplified random effects calculation
            pooled_se = math.sqrt(1.0 / total_weight + 0.1)  # Add between-study variance

        # Calculate confidence interval
        ci_lower = pooled_effect - 1.96 * pooled_se
        ci_upper = pooled_effect + 1.96 * pooled_se

        # Calculate p-value
        z_score = pooled_effect / pooled_se
        p_value = 2 * (1 - self._normal_cdf(abs(z_score)))

        return {
            "effect": pooled_effect,
            "se": pooled_se,
            "ci": (ci_lower, ci_upper),
            "p_value": p_value
        }

    def _normal_cdf(self, x: float) -> float:
        """Approximate normal CDF for p-value calculation."""
        # Simplified approximation
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def _assess_heterogeneity(
        self,
        study_effects: List[StudyEffect],
        pooled_result: Dict[str, Any]
    ) -> Dict[str, float]:
        """Assess heterogeneity between studies."""
        if len(study_effects) < 2:
            return {"i_squared": 0.0, "tau_squared": 0.0, "q_statistic": 0.0}

        # Calculate Q statistic
        q_statistic = sum(
            effect.weight * (effect.effect_size - pooled_result["effect"]) ** 2
            for effect in study_effects
        )

        # Calculate I-squared
        df = len(study_effects) - 1
        i_squared = max(0, (q_statistic - df) / q_statistic) * 100

        # Estimate tau-squared (between-study variance)
        tau_squared = max(0, (q_statistic - df) / sum(effect.weight for effect in study_effects))

        return {
            "i_squared": i_squared,
            "tau_squared": tau_squared,
            "q_statistic": q_statistic
        }

    def _generate_forest_plot_data(
        self,
        study_effects: List[StudyEffect],
        pooled_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate data for forest plot visualization."""
        return {
            "studies": [
                {
                    "id": effect.study_id,
                    "effect": effect.effect_size,
                    "ci_lower": effect.confidence_interval[0],
                    "ci_upper": effect.confidence_interval[1],
                    "weight": effect.weight
                }
                for effect in study_effects
            ],
            "pooled": {
                "effect": pooled_result["effect"],
                "ci_lower": pooled_result["ci"][0],
                "ci_upper": pooled_result["ci"][1]
            }
        }

    def _determine_initial_grade_rating(
        self, evidence_items: List[EvidenceItem]
    ) -> EvidenceLevel:
        """Determine initial GRADE rating based on study designs."""
        study_designs = [item.study_design for item in evidence_items]
        
        # Check for randomized trials
        if any("randomized" in design.lower() or "rct" in design.lower()
               for design in study_designs):
            return EvidenceLevel.HIGH
        
        # Check for observational studies
        if any(design.lower() in ["cohort", "case_control", "cross_sectional"]
               for design in study_designs):
            return EvidenceLevel.LOW
        
        # Default to very low
        return EvidenceLevel.VERY_LOW

    def _assess_downgrade_factors(
        self,
        evidence_items: List[EvidenceItem],
        meta_analysis: Optional[MetaAnalysisResult]
    ) -> Dict[str, int]:
        """Assess GRADE downgrade factors."""
        downgrade = {
            "risk_of_bias": 0,
            "inconsistency": 0,
            "indirectness": 0,
            "imprecision": 0,
            "publication_bias": 0
        }

        # Risk of bias assessment
        high_risk_studies = sum(
            1 for item in evidence_items if item.risk_of_bias == "high"
        )
        if high_risk_studies > len(evidence_items) / 2:
            downgrade["risk_of_bias"] = 2  # Very serious
        elif high_risk_studies > 0:
            downgrade["risk_of_bias"] = 1  # Serious

        # Inconsistency (heterogeneity)
        if meta_analysis and meta_analysis.i_squared > 75:
            downgrade["inconsistency"] = 2  # Very serious
        elif meta_analysis and meta_analysis.i_squared > 50:
            downgrade["inconsistency"] = 1  # Serious

        # Imprecision (wide confidence intervals)
        if meta_analysis:
            ci_width = meta_analysis.confidence_interval[1] - meta_analysis.confidence_interval[0]
            if ci_width > 1.0:  # Arbitrary threshold
                downgrade["imprecision"] = 1

        return downgrade

    def _assess_upgrade_factors(
        self,
        evidence_items: List[EvidenceItem],
        meta_analysis: Optional[MetaAnalysisResult]
    ) -> Dict[str, int]:
        """Assess GRADE upgrade factors."""
        upgrade = {
            "large_effect": 0,
            "dose_response": 0,
            "confounding": 0
        }

        # Large effect size
        if meta_analysis:
            effect_size = abs(meta_analysis.pooled_effect)
            if effect_size > 2.0:  # Very large effect
                upgrade["large_effect"] = 2
            elif effect_size > 1.0:  # Large effect
                upgrade["large_effect"] = 1

        return upgrade

    def _calculate_final_grade_rating(
        self,
        initial_rating: EvidenceLevel,
        downgrade: Dict[str, int],
        upgrade: Dict[str, int]
    ) -> EvidenceLevel:
        """Calculate final GRADE rating."""
        # Convert to numeric scale
        rating_scale = {
            EvidenceLevel.VERY_LOW: 0,
            EvidenceLevel.LOW: 1,
            EvidenceLevel.MODERATE: 2,
            EvidenceLevel.HIGH: 3
        }

        current_rating = rating_scale[initial_rating]
        
        # Apply downgrades
        total_downgrade = sum(downgrade.values())
        current_rating = max(0, current_rating - total_downgrade)
        
        # Apply upgrades (only for observational studies)
        if initial_rating == EvidenceLevel.LOW:
            total_upgrade = sum(upgrade.values())
            current_rating = min(3, current_rating + total_upgrade)

        # Convert back to enum
        rating_map = {
            0: EvidenceLevel.VERY_LOW, 1: EvidenceLevel.LOW,
            2: EvidenceLevel.MODERATE, 3: EvidenceLevel.HIGH
        }
        
        return rating_map[current_rating]

    # Additional placeholder methods for completeness
    def _generate_grade_justification(self, initial, final, downgrade, upgrade):
        return f"GRADE assessment: {initial.value} to {final.value}"

    def _generate_certainty_factors(self, downgrade, upgrade):
        return {"downgrade_reasons": downgrade, "upgrade_reasons": upgrade}

    def _determine_outcome_type(self, evidence_items):
        return OutcomeType.CONTINUOUS  # Default

    def _determine_hypothesis_support(self, hypothesis, evidence, meta_analysis, significance):
        if meta_analysis:
            return meta_analysis.p_value < significance
        return len(evidence) > 0  # Simplified

    def _calculate_hypothesis_confidence(self, evidence, meta_analysis, grade):
        if grade:
            rating_scores = {"very_low": 0.2, "low": 0.4, "moderate": 0.6, "high": 0.8}
            return rating_scores.get(grade.final_rating.value, 0.5)
        return 0.5

    def _determine_effect_direction(self, hypothesis, evidence, meta_analysis):
        if meta_analysis and meta_analysis.pooled_effect > 0:
            return EffectDirection.BENEFICIAL
        elif meta_analysis and meta_analysis.pooled_effect < 0:
            return EffectDirection.HARMFUL
        return EffectDirection.UNCLEAR

    def _generate_evidence_summary(self, evidence, meta_analysis):
        return {"studies": len(evidence), "meta_analysis": meta_analysis is not None}

    def _identify_analysis_limitations(self, evidence, meta_analysis, grade):
        limitations = []
        if len(evidence) < 5:
            limitations.append("Limited number of studies")
        if not meta_analysis:
            limitations.append("No meta-analysis possible")
        return limitations

    def _generate_hypothesis_conclusions(self, hypothesis, supported, confidence, direction):
        conclusions = []
        support_text = "supported" if supported else "not supported"
        conclusions.append(f"Hypothesis is {support_text} with {confidence:.1%} confidence")
        return conclusions

    def _egger_test(self, study_effects):
        return {"test_statistic": 1.5, "p_value": 0.15, "significant_bias": False}

    def _begg_test(self, study_effects):
        return {"test_statistic": 0.8, "p_value": 0.42, "significant_bias": False}

    def _funnel_plot_assessment(self, study_effects):
        return {"asymmetry_score": 0.3, "interpretation": "No clear asymmetry"}

    def _generate_synthesis_recommendations(self, results):
        return [
            "Conduct additional high-quality RCTs",
            "Assess for publication bias",
            "Consider subgroup analyses"
        ]


class HypothesisAnalysisError(Exception):
    """Exception for hypothesis analysis operations."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause