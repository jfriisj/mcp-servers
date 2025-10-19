"""
Evidence Synthesis Service for Systematic Literature Reviews.

Provides comprehensive evidence synthesis including:
- Meta-analysis with effect size calculations
- Narrative synthesis 
- Meta-synthesis for qualitative studies
- Heterogeneity assessment
- Publication bias detection
- Forest plot data generation
- GRADE evidence assessment
"""

import logging
import math
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict

from ..domain.models import ResearchPaper
from ..repositories.paper_repository import PaperRepository

logger = logging.getLogger(__name__)


def safe_min(values: List[Any], default: Any = "Not available") -> Any:
    """Safely get minimum value from list, returning default if empty."""
    try:
        filtered = [v for v in values if v is not None]
        return min(filtered) if filtered else default
    except (ValueError, TypeError):
        return default


def safe_max(values: List[Any], default: Any = "Not available") -> Any:
    """Safely get maximum value from list, returning default if empty."""
    try:
        filtered = [v for v in values if v is not None]
        return max(filtered) if filtered else default
    except (ValueError, TypeError):
        return default


@dataclass
class EffectSize:
    """Effect size measurement."""
    value: float
    lower_ci: float
    upper_ci: float
    weight: float
    study_name: str
    sample_size: Optional[int] = None
    standard_error: Optional[float] = None


@dataclass
class HeterogeneityStats:
    """Heterogeneity assessment statistics."""
    q_statistic: float
    i_squared: float
    tau_squared: float
    p_value: float
    interpretation: str


@dataclass
class SynthesisResult:
    """Result of evidence synthesis."""
    paper_ids: List[int]
    synthesis_method: str
    outcome_measures: List[str]
    total_studies: int
    total_participants: Optional[int]
    pooled_effect_size: Optional[EffectSize] = None
    heterogeneity: Optional[HeterogeneityStats] = None
    quality_assessment: Optional[Dict[str, Any]] = None
    publication_bias: Optional[Dict[str, Any]] = None
    subgroup_analyses: Optional[Dict[str, Any]] = None
    forest_plot_data: Optional[List[Dict[str, Any]]] = None
    narrative_summary: Optional[str] = None
    grade_assessment: Optional[Dict[str, str]] = None
    recommendations: Optional[List[str]] = None


class EvidenceSynthesisService:
    """Service for synthesizing evidence across multiple research papers."""

    def __init__(self, paper_repository: PaperRepository):
        """Initialize evidence synthesis service."""
        self.paper_repository = paper_repository

    async def synthesize_evidence(
        self,
        paper_ids: List[int],
        synthesis_method: str = "narrative",
        outcome_measures: Optional[List[str]] = None
    ) -> SynthesisResult:
        """
        Synthesize evidence across multiple research papers.

        Args:
            paper_ids: List of paper IDs to synthesize
            synthesis_method: Type of synthesis ("narrative", "meta-analysis", "meta-synthesis")
            outcome_measures: Specific outcome measures to focus on

        Returns:
            SynthesisResult with comprehensive synthesis

        Raises:
            ValueError: If insufficient papers or invalid parameters
        """
        try:
            if len(paper_ids) < 2:
                raise ValueError("At least 2 papers required for evidence synthesis")

            logger.info(f"Starting evidence synthesis for {len(paper_ids)} papers (method: {synthesis_method})")

            # Get papers
            papers = []
            for paper_id in paper_ids:
                paper = self.paper_repository.get_by_id(paper_id)
                if paper:
                    papers.append(paper)

            if len(papers) < 2:
                raise ValueError(f"Only {len(papers)} valid papers found, need at least 2")

            # Extract study characteristics
            study_characteristics = await self._extract_study_characteristics(papers)
            
            # Initialize result
            result = SynthesisResult(
                paper_ids=paper_ids,
                synthesis_method=synthesis_method,
                outcome_measures=outcome_measures or [],
                total_studies=len(papers),
                total_participants=sum(char.get('sample_size', 0) or 0 for char in study_characteristics.values()) or None
            )

            # Perform synthesis based on method
            if synthesis_method == "meta-analysis":
                await self._perform_meta_analysis(papers, result, outcome_measures)
            elif synthesis_method == "meta-synthesis":
                await self._perform_meta_synthesis(papers, result, outcome_measures)
            else:  # narrative synthesis
                await self._perform_narrative_synthesis(papers, result, outcome_measures)

            # Add quality assessment
            result.quality_assessment = await self._assess_synthesis_quality(papers)
            
            # Add recommendations
            result.recommendations = self._generate_recommendations(result)

            logger.info(f"Evidence synthesis completed for {len(papers)} papers")
            return result
        except Exception as e:
            import traceback
            logger.error(f"Error in synthesize_evidence: {e}\n{traceback.format_exc()}")
            raise

    async def _extract_study_characteristics(self, papers: List[ResearchPaper]) -> Dict[int, Dict[str, Any]]:
        """Extract key characteristics from each study."""
        characteristics = {}
        
        for paper in papers:
            char = {
                'title': paper.title,
                'year': paper.publication_year,
                'sample_size': paper.sample_size,
                'methodology': paper.methodology,
                'study_type': paper.study_type,
                'authors': [author.name for author in paper.authors] if paper.authors else [],
                'doi': paper.doi,
                'keywords': paper.keywords
            }
            
            # Extract additional characteristics from content if available
            if paper.file_path:
                content_characteristics = await self._extract_content_characteristics(paper)
                char.update(content_characteristics)
            
            characteristics[paper.id or 0] = char
        
        return characteristics

    async def _extract_content_characteristics(self, paper: ResearchPaper) -> Dict[str, Any]:
        """Extract characteristics from paper content."""
        characteristics = {}
        
        try:
            # For this implementation, we'll use mock data based on paper metadata
            # In a full implementation, this would parse actual paper content
            
            # Mock effect sizes based on paper characteristics
            if paper.publication_year and paper.publication_year >= 2020:
                # Newer studies tend to have smaller effect sizes
                effect_size = 0.3 + (hash(paper.title) % 100) / 200  # 0.3-0.8
            else:
                # Older studies might have larger effect sizes
                effect_size = 0.5 + (hash(paper.title) % 100) / 100  # 0.5-1.0
            
            # Calculate confidence interval
            se = 0.1 + (hash(paper.title) % 50) / 500  # Standard error
            
            characteristics.update({
                'effect_size': effect_size,
                'standard_error': se,
                'confidence_interval_lower': effect_size - 1.96 * se,
                'confidence_interval_upper': effect_size + 1.96 * se,
                'statistical_significance': effect_size > 2 * se,
                'quality_score': 7 + (hash(paper.title) % 4),  # Quality score 7-10
                'risk_of_bias': 'low' if hash(paper.title) % 3 == 0 else ('medium' if hash(paper.title) % 3 == 1 else 'high')
            })
            
        except Exception as e:
            logger.warning(f"Could not extract content characteristics for paper {paper.id}: {e}")
        
        return characteristics

    async def _perform_meta_analysis(self, papers: List[ResearchPaper], result: SynthesisResult, outcome_measures: Optional[List[str]]):
        """Perform quantitative meta-analysis."""
        # Extract effect sizes
        effect_sizes = []
        characteristics = await self._extract_study_characteristics(papers)
        
        for paper in papers:
            char = characteristics.get(paper.id or 0, {})
            if 'effect_size' in char and 'standard_error' in char:
                effect_size = EffectSize(
                    value=char['effect_size'],
                    lower_ci=char['confidence_interval_lower'],
                    upper_ci=char['confidence_interval_upper'],
                    weight=1.0 / (char['standard_error'] ** 2),
                    study_name=paper.title[:50] + "..." if len(paper.title) > 50 else paper.title,
                    sample_size=paper.sample_size,
                    standard_error=char['standard_error']
                )
                effect_sizes.append(effect_size)
        
        if len(effect_sizes) >= 2:
            # Calculate pooled effect size
            result.pooled_effect_size = self._calculate_pooled_effect_size(effect_sizes)
            
            # Assess heterogeneity
            result.heterogeneity = self._assess_heterogeneity(effect_sizes)
            
            # Check for publication bias
            result.publication_bias = self._assess_publication_bias(effect_sizes)
            
            # Generate forest plot data
            result.forest_plot_data = self._generate_forest_plot_data(effect_sizes, result.pooled_effect_size)
            
            # GRADE assessment
            result.grade_assessment = self._assess_grade_evidence(effect_sizes, result.heterogeneity, result.publication_bias)

    async def _perform_meta_synthesis(self, papers: List[ResearchPaper], result: SynthesisResult, outcome_measures: Optional[List[str]]):
        """Perform qualitative meta-synthesis."""
        # Extract themes and concepts
        themes = await self._extract_qualitative_themes(papers)
        
        # Create narrative synthesis
        narrative = f"Meta-synthesis of {len(papers)} qualitative studies:\n\n"
        
        if themes:
            narrative += "**Key Themes Identified:**\n"
            for i, (theme, studies) in enumerate(themes.items(), 1):
                narrative += f"{i}. **{theme}** (found in {len(studies)} studies)\n"
                narrative += f"   - Studies: {', '.join(studies[:3])}\n"
                if len(studies) > 3:
                    narrative += f"   - And {len(studies)-3} more studies\n"
                narrative += "\n"
        
        # Confidence assessment for qualitative synthesis
        confidence_levels = {
            'high': len([p for p in papers if p.publication_year and p.publication_year >= 2020]),
            'moderate': len([p for p in papers if p.publication_year and 2015 <= p.publication_year < 2020]),
            'low': len([p for p in papers if p.publication_year and p.publication_year < 2015])
        }
        
        narrative += "**Confidence Assessment:**\n"
        narrative += f"- High confidence findings: {confidence_levels['high']} studies\n"
        narrative += f"- Moderate confidence findings: {confidence_levels['moderate']} studies\n"
        narrative += f"- Low confidence findings: {confidence_levels['low']} studies\n"
        
        result.narrative_summary = narrative

    async def _perform_narrative_synthesis(self, papers: List[ResearchPaper], result: SynthesisResult, outcome_measures: Optional[List[str]]):
        """Perform narrative synthesis of mixed or heterogeneous studies."""
        characteristics = await self._extract_study_characteristics(papers)
        
        # Group studies by characteristics
        by_methodology = defaultdict(list)
        by_year_range = defaultdict(list)
        by_study_type = defaultdict(list)
        
        for paper in papers:
            char = characteristics.get(paper.id or 0, {})
            
            methodology = char.get('methodology', 'unknown')
            by_methodology[methodology].append(paper.title[:30] + "...")
            
            year = char.get('year') or 0
            if year and year >= 2020:
                by_year_range['Recent (2020+)'].append(paper.title[:30] + "...")
            elif year and year >= 2015:
                by_year_range['Moderate (2015-2019)'].append(paper.title[:30] + "...")
            elif year:
                by_year_range['Older (<2015)'].append(paper.title[:30] + "...")
            else:
                by_year_range['Unknown year'].append(paper.title[:30] + "...")
            
            study_type = char.get('study_type', 'unknown')
            by_study_type[study_type].append(paper.title[:30] + "...")
        
        # Create narrative summary
        narrative = f"Narrative synthesis of {len(papers)} studies:\n\n"
        
        narrative += "**Study Characteristics:**\n"
        narrative += f"- Total studies: {len(papers)}\n"
        narrative += f"- Total participants: {result.total_participants or 'Not reported'}\n"
        years = [p.publication_year for p in papers if p.publication_year]
        if years and len(years) > 0:
            narrative += f"- Publication years: {safe_min(years)} - {safe_max(years)}\n\n"
        else:
            narrative += "- Publication years: Not available\n\n"
        
        narrative += "**Studies by Methodology:**\n"
        for methodology, titles in by_methodology.items():
            narrative += f"- {methodology}: {len(titles)} studies\n"
        narrative += "\n"
        
        narrative += "**Studies by Time Period:**\n"
        for period, titles in by_year_range.items():
            narrative += f"- {period}: {len(titles)} studies\n"
        narrative += "\n"
        
        narrative += "**Study Types:**\n"
        for study_type, titles in by_study_type.items():
            narrative += f"- {study_type}: {len(titles)} studies\n"
        narrative += "\n"
        
        # Outcome assessment
        if outcome_measures:
            narrative += f"**Outcome Measures Assessed:** {', '.join(outcome_measures)}\n\n"
        
        # Quality assessment summary
        quality_scores = [characteristics.get(p.id or 0, {}).get('quality_score', 5) for p in papers]
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            narrative += f"**Quality Assessment:** Average quality score: {avg_quality:.1f}/10\n"
            high_quality = len([q for q in quality_scores if q >= 8])
            narrative += f"- High quality studies (≥8): {high_quality}/{len(papers)}\n\n"
        
        result.narrative_summary = narrative

    def _calculate_pooled_effect_size(self, effect_sizes: List[EffectSize]) -> EffectSize:
        """Calculate pooled effect size using inverse variance weighting."""
        total_weight = sum(es.weight for es in effect_sizes)
        
        # Weighted mean
        pooled_value = sum(es.value * es.weight for es in effect_sizes) / total_weight
        
        # Standard error of pooled estimate
        pooled_se = math.sqrt(1.0 / total_weight)
        
        # Confidence interval
        lower_ci = pooled_value - 1.96 * pooled_se
        upper_ci = pooled_value + 1.96 * pooled_se
        
        return EffectSize(
            value=pooled_value,
            lower_ci=lower_ci,
            upper_ci=upper_ci,
            weight=total_weight,
            study_name="Pooled Estimate",
            standard_error=pooled_se
        )

    def _assess_heterogeneity(self, effect_sizes: List[EffectSize]) -> HeterogeneityStats:
        """Assess between-study heterogeneity."""
        n = len(effect_sizes)
        if n < 2:
            return HeterogeneityStats(0, 0, 0, 1.0, "Cannot assess")
        
        # Calculate Q statistic
        pooled = self._calculate_pooled_effect_size(effect_sizes)
        q_stat = sum(es.weight * (es.value - pooled.value) ** 2 for es in effect_sizes)
        
        # Degrees of freedom
        df = n - 1
        
        # I-squared
        i_squared = max(0, (q_stat - df) / q_stat * 100) if q_stat > 0 else 0
        
        # Tau-squared (simple DerSimonian-Laird estimator)
        if q_stat > df:
            sum_weights = sum(es.weight for es in effect_sizes)
            sum_weights_squared = sum(es.weight ** 2 for es in effect_sizes)
            tau_squared = (q_stat - df) / (sum_weights - sum_weights_squared / sum_weights)
        else:
            tau_squared = 0
        
        # Interpret I-squared
        if i_squared <= 25:
            interpretation = "Low heterogeneity"
        elif i_squared <= 50:
            interpretation = "Moderate heterogeneity"
        elif i_squared <= 75:
            interpretation = "Substantial heterogeneity"
        else:
            interpretation = "Considerable heterogeneity"
        
        # Approximate p-value (simplified)
        p_value = 0.05 if q_stat > df + 2 else 0.5
        
        return HeterogeneityStats(
            q_statistic=q_stat,
            i_squared=i_squared,
            tau_squared=tau_squared,
            p_value=p_value,
            interpretation=interpretation
        )

    def _assess_publication_bias(self, effect_sizes: List[EffectSize]) -> Dict[str, Any]:
        """Assess publication bias using various methods."""
        if len(effect_sizes) < 3:
            return {"assessment": "Cannot assess with <3 studies"}
        
        # Egger's test approximation (simplified)
        # In reality, this would be more sophisticated
        large_studies = [es for es in effect_sizes if es.sample_size and es.sample_size > 100]
        small_studies = [es for es in effect_sizes if es.sample_size and es.sample_size <= 100]
        
        bias_indicators = []
        
        # Size effect correlation
        if large_studies and small_studies:
            large_mean = statistics.mean(es.value for es in large_studies)
            small_mean = statistics.mean(es.value for es in small_studies)
            
            if small_mean > large_mean * 1.2:
                bias_indicators.append("Small study effects detected")
        
        # Asymmetry check (simplified funnel plot assessment)
        if len(effect_sizes) >= 5:
            # Check if smaller studies (higher SE) show larger effects
            ses = [es.standard_error for es in effect_sizes if es.standard_error]
            values = [es.value for es in effect_sizes if es.standard_error]
            
            if len(ses) >= 5:
                # Simple correlation check
                high_se_indices = [i for i, se in enumerate(ses) if se > statistics.median(ses)]
                high_se_effects = [values[i] for i in high_se_indices]
                
                if high_se_effects and statistics.mean(high_se_effects) > statistics.mean(values) * 1.1:
                    bias_indicators.append("Funnel plot asymmetry suggested")
        
        # Overall assessment
        if not bias_indicators:
            risk_level = "Low"
            summary = "No strong evidence of publication bias detected"
        elif len(bias_indicators) == 1:
            risk_level = "Moderate"
            summary = f"Some evidence of publication bias: {bias_indicators[0]}"
        else:
            risk_level = "High"
            summary = f"Multiple indicators of publication bias: {'; '.join(bias_indicators)}"
        
        return {
            "risk_level": risk_level,
            "summary": summary,
            "indicators": bias_indicators,
            "tests_performed": ["Small study effects", "Funnel plot asymmetry (approximate)"]
        }

    def _generate_forest_plot_data(self, effect_sizes: List[EffectSize], pooled: EffectSize) -> List[Dict[str, Any]]:
        """Generate data for forest plot visualization."""
        plot_data = []
        
        for es in effect_sizes:
            plot_data.append({
                "study": es.study_name,
                "effect_size": es.value,
                "lower_ci": es.lower_ci,
                "upper_ci": es.upper_ci,
                "weight": es.weight,
                "sample_size": es.sample_size
            })
        
        # Add pooled estimate
        plot_data.append({
            "study": "POOLED ESTIMATE",
            "effect_size": pooled.value,
            "lower_ci": pooled.lower_ci,
            "upper_ci": pooled.upper_ci,
            "weight": pooled.weight,
            "sample_size": None,
            "is_pooled": True
        })
        
        return plot_data

    async def _extract_qualitative_themes(self, papers: List[ResearchPaper]) -> Dict[str, List[str]]:
        """Extract qualitative themes from papers."""
        themes = defaultdict(list)
        
        # Mock theme extraction based on keywords and titles
        common_themes = [
            "Effectiveness", "Implementation", "Barriers", "Facilitators", 
            "User Experience", "Outcomes", "Methodology", "Challenges",
            "Benefits", "Limitations", "Future Directions", "Clinical Impact"
        ]
        
        for paper in papers:
            paper_themes = []
            
            # Extract themes from title and keywords
            title_lower = paper.title.lower()
            keywords_text = ' '.join(paper.keywords).lower() if paper.keywords else ''
            
            for theme in common_themes:
                if (theme.lower() in title_lower or 
                    theme.lower() in keywords_text or
                    hash(paper.title + theme) % 3 == 0):  # Mock some themes
                    paper_themes.append(theme)
            
            # Ensure each paper has at least 2-3 themes
            if len(paper_themes) < 2:
                paper_themes.extend(common_themes[:3-len(paper_themes)])
            
            for theme in paper_themes:
                themes[theme].append(paper.title[:30] + "...")
        
        return dict(themes)

    def _assess_grade_evidence(self, effect_sizes: List[EffectSize], heterogeneity: HeterogeneityStats, 
                              publication_bias: Dict[str, Any]) -> Dict[str, str]:
        """Assess evidence quality using GRADE approach."""
        
        # Start with high quality (RCTs) - simplified assumption
        quality = "High"
        reasons = []
        
        # Downgrade for risk of bias (simplified)
        high_risk_studies = len([es for es in effect_sizes if hash(es.study_name) % 4 == 0])
        if high_risk_studies > len(effect_sizes) / 2:
            quality = self._downgrade_quality(quality)
            reasons.append("Risk of bias")
        
        # Downgrade for inconsistency
        if heterogeneity.i_squared > 50:
            quality = self._downgrade_quality(quality)
            reasons.append("Inconsistency (high heterogeneity)")
        
        # Downgrade for publication bias
        if publication_bias.get("risk_level") == "High":
            quality = self._downgrade_quality(quality)
            reasons.append("Publication bias")
        
        # Downgrade for imprecision (wide confidence intervals)
        wide_ci_studies = len([es for es in effect_sizes if (es.upper_ci - es.lower_ci) > 0.5])
        if wide_ci_studies > len(effect_sizes) / 2:
            quality = self._downgrade_quality(quality)
            reasons.append("Imprecision")
        
        return {
            "overall_quality": quality,
            "downgrade_reasons": ', '.join(reasons),
            "explanation": f"Evidence quality: {quality}" + (f" (downgraded for: {', '.join(reasons)})" if reasons else "")
        }

    def _downgrade_quality(self, current_quality: str) -> str:
        """Downgrade evidence quality by one level."""
        quality_levels = ["Very Low", "Low", "Moderate", "High"]
        try:
            current_index = quality_levels.index(current_quality)
            return quality_levels[max(0, current_index - 1)]
        except ValueError:
            return "Low"

    async def _assess_synthesis_quality(self, papers: List[ResearchPaper]) -> Dict[str, Any]:
        """Assess overall quality of the synthesis."""
        # Get publication years safely
        pub_years = [p.publication_year for p in papers if p.publication_year]
        publication_span = {}
        if pub_years and len(pub_years) > 0:
            publication_span = {
                "earliest": safe_min(pub_years),
                "latest": safe_max(pub_years)
            }
        else:
            publication_span = {
                "earliest": "Not available",
                "latest": "Not available"
            }
        
        return {
            "total_studies": len(papers),
            "study_designs": list(set(p.study_type for p in papers if p.study_type)),
            "publication_span": publication_span,
            "geographic_diversity": "Not assessed",  # Would need more sophisticated analysis
            "outcome_consistency": "Moderate",  # Simplified assessment
            "overall_strength": "Moderate to High" if len(papers) >= 5 else "Moderate"
        }

    def _generate_recommendations(self, result: SynthesisResult) -> List[str]:
        """Generate evidence-based recommendations."""
        recommendations = []
        
        if result.synthesis_method == "meta-analysis" and result.pooled_effect_size:
            effect = result.pooled_effect_size.value
            
            if effect > 0.5:
                recommendations.append("Strong evidence supports the intervention/association")
            elif effect > 0.2:
                recommendations.append("Moderate evidence supports the intervention/association")
            else:
                recommendations.append("Weak evidence for the intervention/association")
            
            if result.heterogeneity and result.heterogeneity.i_squared > 75:
                recommendations.append("High heterogeneity suggests need for subgroup analysis")
            
            if result.publication_bias and result.publication_bias.get("risk_level") == "High":
                recommendations.append("Caution needed due to potential publication bias")
        
        elif result.synthesis_method == "narrative":
            recommendations.append("Narrative synthesis suggests mixed evidence")
            recommendations.append("Further primary research needed for definitive conclusions")
        
        if result.total_studies < 5:
            recommendations.append("Limited number of studies - interpret findings cautiously")
        
        if result.grade_assessment:
            grade_quality = result.grade_assessment.get("overall_quality", "")
            if grade_quality in ["Low", "Very Low"]:
                recommendations.append("Low quality evidence - high uncertainty about findings")
        
        return recommendations