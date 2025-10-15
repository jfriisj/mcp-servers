"""
Research Question Validation Service for systematic literature review question optimization.

This module implements the ResearchQuestionService class following PICO/SPIDER frameworks
and systematic review best practices for research question validation and optimization.
"""

import re
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass


class QuestionFramework(Enum):
    """Research question frameworks supported by the service."""
    PICO = "pico"  # Population, Intervention, Comparison, Outcome
    SPIDER = "spider"  # Sample, Phenomenon, Design, Evaluation, Research type
    PICOS = "picos"  # PICO + Study design
    PICOT = "picot"  # PICO + Time
    ECLIPSE = "eclipse"  # Expectation, Client group, Location, Impact, Professionals, Service


class QuestionComponent(Enum):
    """Components of research question frameworks."""
    # PICO components
    POPULATION = "population"
    INTERVENTION = "intervention"
    COMPARISON = "comparison"
    OUTCOME = "outcome"
    
    # SPIDER components
    SAMPLE = "sample"
    PHENOMENON = "phenomenon"
    DESIGN = "design"
    EVALUATION = "evaluation"
    RESEARCH_TYPE = "research_type"
    
    # Additional components
    STUDY_DESIGN = "study_design"
    TIMEFRAME = "timeframe"
    SETTING = "setting"


class ValidationLevel(Enum):
    """Validation result levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class ComponentAnalysis:
    """Analysis of a single research question component."""
    component: QuestionComponent
    present: bool
    clarity_score: float
    specificity_score: float
    extracted_text: str
    suggestions: List[str]
    confidence: float


@dataclass
class QuestionValidation:
    """Comprehensive research question validation results."""
    framework: QuestionFramework
    overall_score: float
    validation_level: ValidationLevel
    component_analyses: List[ComponentAnalysis]
    missing_components: List[QuestionComponent]
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]
    novelty_assessment: Dict[str, Any]
    searchability_score: float


class ResearchQuestionService:
    """
    Research question validation service for systematic literature reviews.

    Implements PICO/SPIDER framework validation with research question optimization
    following systematic review methodological standards.

    Key Features:
    - Multiple research question framework validation
    - Component-wise analysis and scoring
    - Novelty assessment and gap identification
    - Searchability optimization for database queries
    - Question refinement suggestions
    - Framework-specific validation rules

    Follows Clean Architecture Layer 2 principles:
    - Framework-agnostic business logic
    - Contains research methodology business rules
    - Validates question structure and enforces academic standards
    - Provides actionable improvement recommendations
    """

    def __init__(self):
        """Initialize ResearchQuestionService with framework definitions."""
        self._frameworks = self._initialize_frameworks()
        self._component_keywords = self._initialize_component_keywords()
        self._quality_indicators = self._initialize_quality_indicators()

    def validate_research_question(
        self,
        question_text: str,
        framework: QuestionFramework = QuestionFramework.PICO,
        context: Optional[Dict[str, Any]] = None
    ) -> QuestionValidation:
        """
        Validate research question using specified framework.

        Args:
            question_text: Research question text to validate
            framework: Framework to use for validation
            context: Additional context (domain, research type, etc.)

        Returns:
            Comprehensive validation results

        Raises:
            ValueError: If question text is invalid or framework unsupported
        """
        if not question_text or not question_text.strip():
            raise ValueError("Research question text cannot be empty")

        if framework not in QuestionFramework:
            raise ValueError(f"Unsupported framework: {framework}")

        # Analyze question components
        component_analyses = self._analyze_question_components(question_text, framework)
        
        # Calculate overall validation metrics
        overall_score = self._calculate_overall_score(component_analyses)
        validation_level = self._determine_validation_level(overall_score)
        
        # Identify missing components
        missing_components = self._identify_missing_components(component_analyses, framework)
        
        # Generate strengths and weaknesses
        strengths = self._identify_question_strengths(component_analyses, question_text)
        weaknesses = self._identify_question_weaknesses(component_analyses, missing_components)
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            component_analyses, missing_components, framework
        )
        
        # Assess novelty potential
        novelty_assessment = self._assess_question_novelty(question_text, context)
        
        # Calculate searchability score
        searchability_score = self._calculate_searchability_score(question_text, component_analyses)

        return QuestionValidation(
            framework=framework,
            overall_score=overall_score,
            validation_level=validation_level,
            component_analyses=component_analyses,
            missing_components=missing_components,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_suggestions=improvement_suggestions,
            novelty_assessment=novelty_assessment,
            searchability_score=searchability_score
        )

    def decompose_research_question(
        self,
        question_text: str,
        framework: QuestionFramework = QuestionFramework.PICO
    ) -> Dict[str, Any]:
        """
        Decompose research question into sub-questions and searchable terms.

        Args:
            question_text: Research question to decompose
            framework: Framework for decomposition structure

        Returns:
            Dictionary containing sub-questions, key terms, and search strategies
        """
        validation = self.validate_research_question(question_text, framework)
        
        decomposition = {
            "main_question": question_text,
            "framework": framework.value,
            "sub_questions": {},
            "key_terms": {},
            "search_strategies": {},
            "concept_map": {},
            "synonyms": {}
        }

        # Generate sub-questions for each component
        for analysis in validation.component_analyses:
            if analysis.present and analysis.extracted_text:
                component_name = analysis.component.value
                
                # Generate focused sub-question
                sub_question = self._generate_sub_question(
                    analysis.component, analysis.extracted_text, question_text
                )
                decomposition["sub_questions"][component_name] = sub_question
                
                # Extract key terms
                key_terms = self._extract_key_terms(analysis.extracted_text)
                decomposition["key_terms"][component_name] = key_terms
                
                # Generate search strategies
                search_strategy = self._generate_search_strategy(analysis.component, key_terms)
                decomposition["search_strategies"][component_name] = search_strategy
                
                # Generate synonyms
                synonyms = self._generate_synonyms(key_terms)
                decomposition["synonyms"][component_name] = synonyms

        # Create concept map
        decomposition["concept_map"] = self._create_concept_map(decomposition)

        return decomposition

    def optimize_for_databases(
        self,
        question_text: str,
        target_databases: List[str] = None
    ) -> Dict[str, Any]:
        """
        Optimize research question for database searching.

        Args:
            question_text: Research question to optimize
            target_databases: List of target databases (PubMed, Embase, etc.)

        Returns:
            Optimization recommendations for database searching
        """
        if target_databases is None:
            target_databases = ["pubmed", "embase", "cochrane", "web_of_science"]

        validation = self.validate_research_question(question_text)
        decomposition = self.decompose_research_question(question_text)

        optimization = {
            "original_question": question_text,
            "searchability_score": validation.searchability_score,
            "database_strategies": {},
            "mesh_terms": {},
            "boolean_queries": {},
            "search_filters": {},
            "optimization_suggestions": []
        }

        # Generate database-specific strategies
        for database in target_databases:
            database_strategy = self._generate_database_strategy(
                decomposition, database, validation
            )
            optimization["database_strategies"][database] = database_strategy
            
            # Generate MeSH terms (for medical databases)
            if database.lower() in ["pubmed", "medline"]:
                mesh_terms = self._generate_mesh_terms(decomposition)
                optimization["mesh_terms"][database] = mesh_terms
            
            # Generate boolean queries
            boolean_query = self._generate_boolean_query(decomposition, database)
            optimization["boolean_queries"][database] = boolean_query
            
            # Generate search filters
            search_filters = self._generate_search_filters(validation, database)
            optimization["search_filters"][database] = search_filters

        # Generate optimization suggestions
        optimization["optimization_suggestions"] = self._generate_optimization_suggestions(
            validation, decomposition, target_databases
        )

        return optimization

    def assess_novelty(
        self,
        question_text: str,
        existing_reviews: List[Dict[str, Any]] = None,
        domain_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assess novelty and research gap potential of research question.

        Args:
            question_text: Research question to assess
            existing_reviews: Information about existing systematic reviews
            domain_context: Research domain context

        Returns:
            Novelty assessment with gap analysis and recommendations
        """
        validation = self.validate_research_question(question_text)
        decomposition = self.decompose_research_question(question_text)

        novelty_assessment = {
            "question": question_text,
            "novelty_score": 0.0,
            "gap_analysis": {},
            "existing_coverage": {},
            "potential_contributions": [],
            "research_opportunities": [],
            "methodological_gaps": [],
            "population_gaps": [],
            "intervention_gaps": [],
            "outcome_gaps": [],
            "recommendations": []
        }

        # Analyze question components for novelty
        novelty_assessment["gap_analysis"] = self._analyze_research_gaps(
            decomposition, existing_reviews
        )
        
        # Calculate novelty score
        novelty_assessment["novelty_score"] = self._calculate_novelty_score(
            novelty_assessment["gap_analysis"], validation
        )
        
        # Identify potential contributions
        novelty_assessment["potential_contributions"] = self._identify_potential_contributions(
            decomposition, novelty_assessment["gap_analysis"]
        )
        
        # Identify research opportunities
        novelty_assessment["research_opportunities"] = self._identify_research_opportunities(
            validation, decomposition, domain_context
        )
        
        # Analyze specific gap types
        novelty_assessment.update(self._analyze_specific_gaps(decomposition, existing_reviews))
        
        # Generate recommendations
        novelty_assessment["recommendations"] = self._generate_novelty_recommendations(
            novelty_assessment, validation
        )

        return novelty_assessment

    def refine_research_question(
        self,
        question_text: str,
        improvement_priorities: List[str] = None
    ) -> Dict[str, Any]:
        """
        Provide specific refinement suggestions for research question.

        Args:
            question_text: Research question to refine
            improvement_priorities: Areas to prioritize for improvement

        Returns:
            Refinement suggestions with alternative formulations
        """
        validation = self.validate_research_question(question_text)
        
        refinement = {
            "original_question": question_text,
            "current_score": validation.overall_score,
            "target_level": ValidationLevel.EXCELLENT.value,
            "refinement_suggestions": {},
            "alternative_formulations": [],
            "component_improvements": {},
            "linguistic_improvements": [],
            "structural_improvements": [],
            "priority_actions": []
        }

        # Component-specific improvements
        for analysis in validation.component_analyses:
            if analysis.component.value in (improvement_priorities or []) or not analysis.present:
                improvements = self._generate_component_improvements(analysis, question_text)
                refinement["component_improvements"][analysis.component.value] = improvements

        # Generate alternative formulations
        refinement["alternative_formulations"] = self._generate_alternative_formulations(
            question_text, validation
        )
        
        # Linguistic improvements
        refinement["linguistic_improvements"] = self._suggest_linguistic_improvements(
            question_text, validation
        )
        
        # Structural improvements
        refinement["structural_improvements"] = self._suggest_structural_improvements(
            validation
        )
        
        # Priority actions
        refinement["priority_actions"] = self._identify_priority_actions(
            validation, improvement_priorities
        )

        return refinement

    # Private helper methods

    def _initialize_frameworks(self) -> Dict[QuestionFramework, List[QuestionComponent]]:
        """Initialize research question frameworks and their required components."""
        return {
            QuestionFramework.PICO: [
                QuestionComponent.POPULATION,
                QuestionComponent.INTERVENTION,
                QuestionComponent.COMPARISON,
                QuestionComponent.OUTCOME
            ],
            QuestionFramework.SPIDER: [
                QuestionComponent.SAMPLE,
                QuestionComponent.PHENOMENON,
                QuestionComponent.DESIGN,
                QuestionComponent.EVALUATION,
                QuestionComponent.RESEARCH_TYPE
            ],
            QuestionFramework.PICOS: [
                QuestionComponent.POPULATION,
                QuestionComponent.INTERVENTION,
                QuestionComponent.COMPARISON,
                QuestionComponent.OUTCOME,
                QuestionComponent.STUDY_DESIGN
            ],
            QuestionFramework.PICOT: [
                QuestionComponent.POPULATION,
                QuestionComponent.INTERVENTION,
                QuestionComponent.COMPARISON,
                QuestionComponent.OUTCOME,
                QuestionComponent.TIMEFRAME
            ]
        }

    def _initialize_component_keywords(self) -> Dict[QuestionComponent, List[str]]:
        """Initialize keywords for identifying question components."""
        return {
            QuestionComponent.POPULATION: [
                "patients", "participants", "adults", "children", "elderly", "people",
                "individuals", "subjects", "cohort", "population", "group"
            ],
            QuestionComponent.INTERVENTION: [
                "treatment", "intervention", "therapy", "medication", "drug", "procedure",
                "program", "training", "education", "counseling", "surgery"
            ],
            QuestionComponent.COMPARISON: [
                "compared to", "versus", "vs", "against", "control", "placebo",
                "standard care", "usual care", "alternative", "compared with"
            ],
            QuestionComponent.OUTCOME: [
                "outcome", "result", "effect", "effectiveness", "efficacy", "improvement",
                "reduction", "increase", "change", "impact", "benefit", "response"
            ],
            QuestionComponent.SAMPLE: [
                "sample", "participants", "respondents", "cases", "subjects", "informants"
            ],
            QuestionComponent.PHENOMENON: [
                "phenomenon", "experience", "perception", "attitude", "behavior",
                "practice", "knowledge", "belief", "feeling"
            ],
            QuestionComponent.DESIGN: [
                "qualitative", "quantitative", "mixed methods", "ethnography",
                "phenomenology", "grounded theory", "case study"
            ],
            QuestionComponent.EVALUATION: [
                "explore", "understand", "describe", "examine", "investigate",
                "analyze", "assess", "evaluate"
            ],
            QuestionComponent.RESEARCH_TYPE: [
                "systematic review", "meta-analysis", "primary research", "secondary analysis"
            ]
        }

    def _initialize_quality_indicators(self) -> Dict[str, List[str]]:
        """Initialize quality indicators for research questions."""
        return {
            "clarity_indicators": [
                "clear population", "specific intervention", "measurable outcome",
                "defined timeframe", "explicit comparison"
            ],
            "specificity_indicators": [
                "precise terms", "narrow scope", "well-defined concepts",
                "specific population", "detailed intervention"
            ],
            "feasibility_indicators": [
                "adequate sample size", "accessible population", "realistic timeframe",
                "available resources", "ethical considerations"
            ],
            "novelty_indicators": [
                "research gap", "new intervention", "understudied population",
                "novel outcome", "methodological innovation"
            ]
        }

    def _analyze_question_components(
        self,
        question_text: str,
        framework: QuestionFramework
    ) -> List[ComponentAnalysis]:
        """Analyze individual components of research question."""
        required_components = self._frameworks[framework]
        analyses = []

        for component in required_components:
            analysis = self._analyze_single_component(question_text, component)
            analyses.append(analysis)

        return analyses

    def _analyze_single_component(
        self,
        question_text: str,
        component: QuestionComponent
    ) -> ComponentAnalysis:
        """Analyze a single research question component."""
        keywords = self._component_keywords.get(component, [])
        
        # Simple keyword matching (would be enhanced with NLP)
        extracted_text = ""
        present = False
        confidence = 0.0

        text_lower = question_text.lower()
        matches = []

        for keyword in keywords:
            if keyword in text_lower:
                matches.append(keyword)
                present = True

        if matches:
            confidence = len(matches) / len(keywords)
            # Extract surrounding context (simplified)
            for match in matches:
                start = text_lower.find(match)
                if start != -1:
                    context_start = max(0, start - 20)
                    context_end = min(len(question_text), start + len(match) + 20)
                    extracted_text = question_text[context_start:context_end]
                    break

        # Calculate scores
        clarity_score = confidence * 0.8 + (0.2 if extracted_text else 0.0)
        specificity_score = min(1.0, len(extracted_text.split()) / 10) if extracted_text else 0.0

        # Generate suggestions
        suggestions = self._generate_component_suggestions(component, present, extracted_text)

        return ComponentAnalysis(
            component=component,
            present=present,
            clarity_score=clarity_score,
            specificity_score=specificity_score,
            extracted_text=extracted_text,
            suggestions=suggestions,
            confidence=confidence
        )

    def _generate_component_suggestions(
        self,
        component: QuestionComponent,
        present: bool,
        extracted_text: str
    ) -> List[str]:
        """Generate improvement suggestions for a component."""
        suggestions = []

        if not present:
            suggestions.append(f"Add {component.value.replace('_', ' ')} specification")
        else:
            if len(extracted_text.split()) < 3:
                suggestions.append(
                    f"Provide more specific {component.value.replace('_', ' ')} details"
                )
            if component == QuestionComponent.POPULATION and "adults" in extracted_text.lower():
                suggestions.append(
                    "Consider specifying age range, demographics, or inclusion criteria"
                )
            elif component == QuestionComponent.INTERVENTION and len(extracted_text.split()) < 5:
                suggestions.append("Specify intervention duration, frequency, or delivery method")
            elif component == QuestionComponent.OUTCOME and "improvement" in extracted_text.lower():
                suggestions.append("Define specific, measurable outcome indicators")

        return suggestions

    def _calculate_overall_score(self, component_analyses: List[ComponentAnalysis]) -> float:
        """Calculate overall validation score from component analyses."""
        if not component_analyses:
            return 0.0

        # Weighted scoring based on presence, clarity, and specificity
        total_score = 0.0
        for analysis in component_analyses:
            component_score = 0.0
            if analysis.present:
                component_score += 0.4  # Base score for presence
                component_score += analysis.clarity_score * 0.3
                component_score += analysis.specificity_score * 0.3
            total_score += component_score

        return total_score / len(component_analyses)

    def _determine_validation_level(self, overall_score: float) -> ValidationLevel:
        """Determine validation level from overall score."""
        if overall_score >= 0.8:
            return ValidationLevel.EXCELLENT
        elif overall_score >= 0.6:
            return ValidationLevel.GOOD
        elif overall_score >= 0.4:
            return ValidationLevel.FAIR
        else:
            return ValidationLevel.POOR

    def _identify_missing_components(
        self,
        component_analyses: List[ComponentAnalysis],
        framework: QuestionFramework
    ) -> List[QuestionComponent]:
        """Identify missing required components."""
        present_components = {a.component for a in component_analyses if a.present}
        required_components = set(self._frameworks[framework])
        return list(required_components - present_components)

    def _identify_question_strengths(
        self,
        component_analyses: List[ComponentAnalysis],
        question_text: str
    ) -> List[str]:
        """Identify strengths in the research question."""
        strengths = []
        
        present_count = sum(1 for a in component_analyses if a.present)
        total_count = len(component_analyses)
        
        if present_count == total_count:
            strengths.append("All framework components are present")
        elif present_count >= total_count * 0.75:
            strengths.append("Most framework components are present")

        avg_clarity = sum(a.clarity_score for a in component_analyses) / len(component_analyses)
        if avg_clarity >= 0.7:
            strengths.append("Components are clearly defined")

        if len(question_text.split()) <= 25:
            strengths.append("Question is concise and focused")

        if "?" in question_text:
            strengths.append("Proper question format with interrogative structure")

        return strengths

    def _identify_question_weaknesses(
        self,
        component_analyses: List[ComponentAnalysis],
        missing_components: List[QuestionComponent]
    ) -> List[str]:
        """Identify weaknesses in the research question."""
        weaknesses = []

        if missing_components:
            missing_names = [comp.value.replace('_', ' ') for comp in missing_components]
            weaknesses.append(f"Missing components: {', '.join(missing_names)}")

        low_clarity_components = [
            a.component.value.replace('_', ' ')
            for a in component_analyses
            if a.present and a.clarity_score < 0.5
        ]
        if low_clarity_components:
            weaknesses.append(f"Unclear components: {', '.join(low_clarity_components)}")

        low_specificity_components = [
            a.component.value.replace('_', ' ')
            for a in component_analyses
            if a.present and a.specificity_score < 0.3
        ]
        if low_specificity_components:
            weaknesses.append(f"Vague components: {', '.join(low_specificity_components)}")

        return weaknesses

    def _generate_improvement_suggestions(
        self,
        component_analyses: List[ComponentAnalysis],
        missing_components: List[QuestionComponent],
        framework: QuestionFramework
    ) -> List[str]:
        """Generate specific improvement suggestions."""
        suggestions = []

        # Add missing component suggestions
        for component in missing_components:
            component_name = component.value.replace('_', ' ')
            suggestions.append(f"Include {component_name} specification")

        # Add component-specific suggestions
        for analysis in component_analyses:
            suggestions.extend(analysis.suggestions)

        # Framework-specific suggestions
        if framework == QuestionFramework.PICO:
            suggestions.append(
                "Consider PICO structure: Population + Intervention + Comparison + Outcome"
            )
        elif framework == QuestionFramework.SPIDER:
            suggestions.append("Consider SPIDER structure for qualitative questions")

        return list(set(suggestions))  # Remove duplicates

    def _assess_question_novelty(
        self,
        question_text: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess potential novelty of research question."""
        # Simplified novelty assessment
        novelty_score = 0.5  # Default neutral score

        # Check for novel keywords
        novel_indicators = [
            "new", "novel", "innovative", "first", "emerging", "recent", "unexplored"
        ]
        text_lower = question_text.lower()
        for indicator in novel_indicators:
            if indicator in text_lower:
                novelty_score += 0.1

        novelty_score = min(1.0, novelty_score)

        return {
            "novelty_score": novelty_score,
            "novelty_indicators": [ind for ind in novel_indicators if ind in text_lower],
            "potential_gaps": self._identify_potential_gaps(question_text),
            "research_value": "medium" if novelty_score > 0.6 else "low"
        }

    def _identify_potential_gaps(self, question_text: str) -> List[str]:
        """Identify potential research gaps in question."""
        gaps = []
        text_lower = question_text.lower()

        gap_indicators = {
            "population": ["understudied", "underrepresented", "vulnerable", "specific"],
            "intervention": ["new", "novel", "innovative", "alternative"],
            "outcome": ["long-term", "quality of life", "patient-reported", "economic"],
            "methodology": ["mixed methods", "longitudinal", "multi-center"]
        }

        for gap_type, indicators in gap_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    gaps.append(f"Potential {gap_type} gap: {indicator}")

        return gaps

    def _calculate_searchability_score(
        self,
        question_text: str,
        component_analyses: List[ComponentAnalysis]
    ) -> float:
        """Calculate how searchable the research question is."""
        score = 0.0
        
        # Check for specific terms
        specific_terms = len([word for word in question_text.split() if len(word) > 3])
        score += min(0.3, specific_terms / 20)  # Up to 0.3 for specific terms

        # Check component clarity
        clarity_scores = [a.clarity_score for a in component_analyses if a.present]
        if clarity_scores:
            score += sum(clarity_scores) / len(clarity_scores) * 0.4

        # Check for searchable concepts
        searchable_concepts = ["treatment", "intervention", "outcome", "population", "condition"]
        text_lower = question_text.lower()
        concept_matches = sum(1 for concept in searchable_concepts if concept in text_lower)
        score += min(0.3, concept_matches / len(searchable_concepts) * 0.3)

        return min(1.0, score)

    def _generate_sub_question(
        self,
        component: QuestionComponent,
        extracted_text: str,
        main_question: str
    ) -> str:
        """Generate focused sub-question for a component."""
        component_name = component.value.replace('_', ' ')
        
        if component == QuestionComponent.POPULATION:
            return f"Who is the target {component_name} for this research?"
        elif component == QuestionComponent.INTERVENTION:
            return f"What specific {component_name} will be studied?"
        elif component == QuestionComponent.COMPARISON:
            return "What will the intervention be compared against?"
        elif component == QuestionComponent.OUTCOME:
            return "What outcomes will be measured?"
        else:
            return f"How is {component_name} defined in this research?"

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from component text."""
        # Simple key term extraction (would use NLP in practice)
        words = re.findall(r'\b\w{4,}\b', text.lower())
        
        # Filter common words
        common_words = {
            "that", "this", "with", "from", "they", "them", "their", "there",
            "where", "when", "what", "which", "will", "would", "should", "could"
        }
        
        key_terms = [word for word in words if word not in common_words]
        return list(set(key_terms))  # Remove duplicates

    def _generate_search_strategy(
        self,
        component: QuestionComponent,
        key_terms: List[str]
    ) -> Dict[str, Any]:
        """Generate search strategy for component."""
        return {
            "primary_terms": key_terms[:3],  # Top 3 terms
            "secondary_terms": key_terms[3:6],  # Next 3 terms
            "boolean_logic": " OR ".join(key_terms[:5]),
            "mesh_candidates": key_terms if component == QuestionComponent.INTERVENTION else [],
            "filters": self._suggest_search_filters(component)
        }

    def _suggest_search_filters(self, component: QuestionComponent) -> List[str]:
        """Suggest search filters for component."""
        filters = {
            QuestionComponent.POPULATION: ["humans", "adult", "age_groups"],
            QuestionComponent.INTERVENTION: ["therapy", "drug_therapy", "procedures"],
            QuestionComponent.OUTCOME: ["treatment_outcome", "mortality", "morbidity"],
            QuestionComponent.STUDY_DESIGN: ["randomized_controlled_trial", "systematic_review"]
        }
        return filters.get(component, [])

    def _generate_synonyms(self, key_terms: List[str]) -> Dict[str, List[str]]:
        """Generate synonyms for key terms."""
        # Simplified synonym generation (would use thesaurus/ontologies in practice)
        synonym_map = {
            "treatment": ["therapy", "intervention", "management"],
            "patient": ["participant", "subject", "individual"],
            "effectiveness": ["efficacy", "efficiency", "success"],
            "improvement": ["enhancement", "betterment", "progress"],
            "reduction": ["decrease", "decline", "diminishment"]
        }
        
        synonyms = {}
        for term in key_terms:
            synonyms[term] = synonym_map.get(term.lower(), [term])
        
        return synonyms

    def _create_concept_map(self, decomposition: Dict[str, Any]) -> Dict[str, Any]:
        """Create concept map from decomposition."""
        return {
            "main_concepts": list(decomposition["key_terms"].keys()),
            "relationships": self._identify_concept_relationships(decomposition),
            "hierarchy": self._create_concept_hierarchy(decomposition)
        }

    def _identify_concept_relationships(
        self, decomposition: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify relationships between concepts."""
        relationships = []
        components = list(decomposition["key_terms"].keys())
        
        for i, comp1 in enumerate(components):
            for comp2 in components[i+1:]:
                relationships.append({
                    "source": comp1,
                    "target": comp2,
                    "relationship": "related_to"
                })
        
        return relationships

    def _create_concept_hierarchy(self, decomposition: Dict[str, Any]) -> Dict[str, List[str]]:
        """Create hierarchical concept structure."""
        hierarchy = {
            "primary": [],
            "secondary": [],
            "tertiary": []
        }
        
        # Simplified hierarchy based on component importance
        important_components = ["population", "intervention", "outcome"]
        
        for component, terms in decomposition["key_terms"].items():
            if component in important_components:
                hierarchy["primary"].extend(terms[:2])
            else:
                hierarchy["secondary"].extend(terms[:2])
        
        return hierarchy

    # Additional helper methods would continue here...
    # For brevity, I'll add placeholder methods for the remaining functionality

    def _generate_database_strategy(self, decomposition, database, validation):
        """Generate database-specific search strategy."""
        return {"strategy": f"Optimized for {database}", "terms": []}

    def _generate_mesh_terms(self, decomposition):
        """Generate MeSH terms for medical databases."""
        return []

    def _generate_boolean_query(self, decomposition, database):
        """Generate boolean search query."""
        # Extract key components from PICO/SPIDER decomposition
        population = decomposition.get('population', [])
        intervention = decomposition.get('intervention', [])
        comparison = decomposition.get('comparison', [])
        outcome = decomposition.get('outcome', [])
        context = decomposition.get('context', [])
        
        # Build boolean query based on database type
        if database.lower() in ['pubmed', 'medline']:
            query_parts = []
            
            # Population terms
            if population:
                pop_terms = [f'"{term}"[MeSH Terms] OR "{term}"[Title/Abstract]' for term in population]
                query_parts.append(f"({' OR '.join(pop_terms)})")
            
            # Intervention terms
            if intervention:
                int_terms = [f'"{term}"[MeSH Terms] OR "{term}"[Title/Abstract]' for term in intervention]
                query_parts.append(f"({' OR '.join(int_terms)})")
            
            # Outcome terms
            if outcome:
                out_terms = [f'"{term}"[MeSH Terms] OR "{term}"[Title/Abstract]' for term in outcome]
                query_parts.append(f"({' OR '.join(out_terms)})")
            
            # Combine with AND
            boolean_query = ' AND '.join(query_parts)
            
        elif database.lower() in ['scopus', 'web of science']:
            query_parts = []
            
            # Use TITLE-ABS-KEY for Scopus
            if population:
                pop_terms = [f'TITLE-ABS-KEY("{term}")' for term in population]
                query_parts.append(f"({' OR '.join(pop_terms)})")
            
            if intervention:
                int_terms = [f'TITLE-ABS-KEY("{term}")' for term in intervention]
                query_parts.append(f"({' OR '.join(int_terms)})")
            
            if outcome:
                out_terms = [f'TITLE-ABS-KEY("{term}")' for term in outcome]
                query_parts.append(f"({' OR '.join(out_terms)})")
            
            boolean_query = ' AND '.join(query_parts)
            
        elif database.lower() in ['ieee', 'acm']:
            # Computer science databases
            query_parts = []
            
            if population:
                pop_terms = [f'"{term}"' for term in population]
                query_parts.append(f"({' OR '.join(pop_terms)})")
            
            if intervention:
                int_terms = [f'"{term}"' for term in intervention]
                query_parts.append(f"({' OR '.join(int_terms)})")
            
            if outcome:
                out_terms = [f'"{term}"' for term in outcome]
                query_parts.append(f"({' OR '.join(out_terms)})")
            
            boolean_query = ' AND '.join(query_parts)
            
        else:
            # Generic boolean query
            all_terms = population + intervention + comparison + outcome + context
            unique_terms = list(set(all_terms))
            
            if len(unique_terms) > 0:
                # Create OR groups for similar concepts, AND between different concepts
                boolean_query = ' AND '.join([f'"{term}"' for term in unique_terms[:5]])  # Limit complexity
            else:
                boolean_query = '("systematic review" OR "literature review")'
        
        # Ensure query is not empty
        if not boolean_query.strip():
            boolean_query = '("systematic review" OR "literature review")'
        
        return boolean_query

    def _generate_search_filters(self, validation, database):
        """Generate search filters."""
        return []

    def _generate_optimization_suggestions(self, validation, decomposition, databases):
        """Generate optimization suggestions."""
        return []

    def _analyze_research_gaps(self, decomposition, existing_reviews):
        """Analyze research gaps."""
        return {}

    def _calculate_novelty_score(self, gap_analysis, validation):
        """Calculate novelty score."""
        return 0.5

    def _identify_potential_contributions(self, decomposition, gap_analysis):
        """Identify potential contributions."""
        return []

    def _identify_research_opportunities(self, validation, decomposition, domain_context):
        """Identify research opportunities."""
        return []

    def _analyze_specific_gaps(self, decomposition, existing_reviews):
        """Analyze specific types of gaps."""
        return {
            "methodological_gaps": [],
            "population_gaps": [],
            "intervention_gaps": [],
            "outcome_gaps": []
        }

    def _generate_novelty_recommendations(self, novelty_assessment, validation):
        """Generate novelty-based recommendations."""
        return []

    def _generate_component_improvements(self, analysis, question_text):
        """Generate component-specific improvements."""
        return []

    def _generate_alternative_formulations(self, question_text, validation):
        """Generate alternative question formulations."""
        return []

    def _suggest_linguistic_improvements(self, question_text, validation):
        """Suggest linguistic improvements."""
        return []

    def _suggest_structural_improvements(self, validation):
        """Suggest structural improvements."""
        return []

    def _identify_priority_actions(self, validation, improvement_priorities):
        """Identify priority actions for improvement."""
        return []


class ResearchQuestionError(Exception):
    """Exception for research question operations."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause