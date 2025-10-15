"""
SLR Workflow Guidance Service for managing SLR projects and providing user guidance.

This service implements workflow management, progress tracking, and intelligent
guidance for systematic literature review projects following best practices.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone

from ..models import (
    SLRProject, SLRTask, ScreeningRecord, ProjectProgress,
    SLRPhase, ProjectStatus, TaskStatus, TaskPriority,
    ScreeningDecision, ScreeningStage
)

logger = logging.getLogger(__name__)


class SLRWorkflowService:
    """
    Service for SLR workflow management and user guidance.
    
    Provides comprehensive project management, progress tracking, and intelligent
    recommendations for systematic literature review workflows.
    """
    
    def __init__(self):
        self.logger = logger.getChild(self.__class__.__name__)
    
    async def create_slr_project(self, 
                               title: str,
                               research_domain: str,
                               description: Optional[str] = None,
                               team_lead: Optional[str] = None,
                               team_members: Optional[List[str]] = None,
                               research_question: Optional[str] = None,
                               estimated_timeline_weeks: Optional[int] = None) -> Dict[str, Any]:
        """
        Create new SLR project with structured phases and initial guidance.
        
        Args:
            title: Project title
            research_domain: Research domain/field
            description: Project description
            team_lead: Team leader name
            team_members: List of team member names
            research_question: Initial research question
            estimated_timeline_weeks: Estimated project duration
            
        Returns:
            Dictionary with project details and next steps
        """
        try:
            # Create project
            project = SLRProject(
                title=title,
                research_domain=research_domain,
                description=description,
                team_lead=team_lead,
                team_members=team_members or [],
                research_question=research_question,
                estimated_timeline_weeks=estimated_timeline_weeks,
                status=ProjectStatus.IN_PROGRESS
            )
            
            # Generate initial tasks for planning phase
            initial_tasks = self._generate_initial_tasks(project)
            
            # Create project progress tracker
            # Generate temporary project ID until saved to repository
            temp_project_id = int(datetime.utcnow().timestamp())
            
            progress = ProjectProgress(
                project_id=temp_project_id,
                current_phase=SLRPhase.PLANNING,
                total_tasks=len(initial_tasks),
                next_milestones=[
                    "Define research question using PICO/SPIDER framework",
                    "Develop inclusion/exclusion criteria", 
                    "Create search strategy",
                    "Register protocol with PROSPERO"
                ]
            )
            
            self.logger.info(f"Created new SLR project: {title}")
            
            return {
                "success": True,
                "project": project.to_dict(),
                "initial_tasks": [task.to_dict() for task in initial_tasks],
                "progress": progress.to_dict(),
                "next_steps": self._get_planning_phase_guidance(),
                "message": f"SLR project '{title}' created successfully. Starting with planning phase."
            }
            
        except Exception as e:
            self.logger.error(f"Error creating SLR project: {e}")
            return {
                "success": False,
                "error": f"Failed to create SLR project: {str(e)}"
            }
    
    def _generate_initial_tasks(self, project: SLRProject) -> List[SLRTask]:
        """Generate initial tasks for project planning phase."""
        tasks = []
        
        planning_tasks = [
            {
                "title": "Refine Research Question",
                "description": "Use PICO/SPIDER framework to structure and validate research question",
                "priority": TaskPriority.HIGH,
                "estimated_hours": 4.0
            },
            {
                "title": "Define Inclusion Criteria", 
                "description": "Establish clear criteria for study inclusion",
                "priority": TaskPriority.HIGH,
                "estimated_hours": 3.0
            },
            {
                "title": "Define Exclusion Criteria",
                "description": "Establish clear criteria for study exclusion", 
                "priority": TaskPriority.HIGH,
                "estimated_hours": 2.0
            },
            {
                "title": "Develop Search Strategy",
                "description": "Create comprehensive search terms and database strategy",
                "priority": TaskPriority.MEDIUM,
                "estimated_hours": 6.0
            },
            {
                "title": "Create Protocol Document",
                "description": "Draft PRISMA-P compliant protocol",
                "priority": TaskPriority.MEDIUM,
                "estimated_hours": 8.0
            },
            {
                "title": "Register PROSPERO",
                "description": "Submit protocol to PROSPERO registry",
                "priority": TaskPriority.LOW,
                "estimated_hours": 2.0
            }
        ]
        
        for i, task_data in enumerate(planning_tasks):
            task = SLRTask(
                project_id=project.id or int(datetime.utcnow().timestamp()),
                title=task_data["title"],
                description=task_data["description"],
                phase=SLRPhase.PLANNING,
                priority=task_data["priority"],
                estimated_hours=task_data["estimated_hours"],
                due_date=datetime.now(timezone.utc) + timedelta(days=7 * (i + 1))
            )
            tasks.append(task)
        
        return tasks
    
    def _get_planning_phase_guidance(self) -> List[str]:
        """Get step-by-step guidance for planning phase."""
        return [
            "1. Start by clearly defining your research question using the PICO framework (Population, Intervention, Comparison, Outcome)",
            "2. Establish specific inclusion and exclusion criteria that align with your research objectives",
            "3. Develop a comprehensive search strategy including key terms and database selection",
            "4. Create a detailed protocol document following PRISMA-P guidelines",
            "5. Consider registering your protocol with PROSPERO before starting the review",
            "6. Ensure all team members understand the methodology and their roles"
        ]
    
    async def get_slr_progress(self, project_id: int) -> Dict[str, Any]:
        """
        Get comprehensive progress dashboard for SLR project.
        
        Args:
            project_id: SLR project ID
            
        Returns:
            Dictionary with detailed progress information
        """
        try:
            # TODO: Fetch from repository
            # For now, return mock progress data
            progress = ProjectProgress(
                project_id=project_id,
                total_papers=150,
                screened_papers=75,
                included_papers=25,
                assessed_papers=10,
                extracted_papers=5,
                completed_tasks=8,
                total_tasks=15,
                current_phase=SLRPhase.SCREENING,
                phase_completion_percentage=50.0,
                overall_completion_percentage=35.0,
                estimated_days_remaining=45,
                bottlenecks=[
                    "Screening backlog: 75 papers pending review",
                    "Quality assessment: Need second reviewer for 5 papers"
                ],
                next_milestones=[
                    "Complete title/abstract screening (75 papers remaining)",
                    "Begin full-text screening for included papers",
                    "Finalize quality assessment framework"
                ]
            )
            
            self.logger.info(f"Generated progress report for project {project_id}")
            
            return {
                "success": True,
                "progress": progress.to_dict(),
                "recommendations": self._generate_progress_recommendations(progress),
                "phase_status": self._get_phase_status(progress.current_phase),
                "timeline_health": self._assess_timeline_health(progress)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting SLR progress: {e}")
            return {
                "success": False,
                "error": f"Failed to get progress: {str(e)}"
            }
    
    def _generate_progress_recommendations(self, progress: ProjectProgress) -> List[str]:
        """Generate intelligent recommendations based on project progress."""
        recommendations = []
        
        # Screening recommendations
        if progress.screening_completion_rate < 50 and progress.current_phase == SLRPhase.SCREENING:
            recommendations.append("🔍 Priority: Accelerate screening process - consider adding reviewers or using AI assistance")
        
        # Quality assessment recommendations  
        if progress.included_papers > 0 and progress.assessed_papers == 0:
            recommendations.append("📊 Next: Begin quality assessment of included papers using PRISMA checklist")
        
        # Timeline recommendations
        if progress.estimated_days_remaining and progress.estimated_days_remaining < 30:
            recommendations.append("⏰ Alert: Project timeline tight - consider scope adjustments or additional resources")
        
        # Bottleneck recommendations
        if progress.bottlenecks:
            recommendations.append("🚫 Address bottlenecks: Focus on resolving identified workflow blockages")
        
        return recommendations
    
    def _get_phase_status(self, phase: SLRPhase) -> Dict[str, str]:
        """Get status information for current phase."""
        phase_info = {
            SLRPhase.PLANNING: {
                "description": "Developing protocol and search strategy",
                "key_activities": "Research question refinement, criteria definition, protocol creation"
            },
            SLRPhase.SEARCH: {
                "description": "Executing search strategy across databases", 
                "key_activities": "Database searching, citation searching, grey literature"
            },
            SLRPhase.SCREENING: {
                "description": "Selecting relevant studies based on inclusion criteria",
                "key_activities": "Title/abstract screening, full-text screening, reviewer agreement"
            },
            SLRPhase.QUALITY_ASSESSMENT: {
                "description": "Assessing methodological quality of included studies",
                "key_activities": "Quality assessment, inter-rater reliability, bias assessment"
            },
            SLRPhase.DATA_EXTRACTION: {
                "description": "Extracting data from included studies",
                "key_activities": "Data extraction, verification, conflict resolution"
            },
            SLRPhase.ANALYSIS: {
                "description": "Analyzing and synthesizing extracted data",
                "key_activities": "Statistical analysis, meta-analysis, narrative synthesis"
            },
            SLRPhase.REPORTING: {
                "description": "Writing and finalizing systematic review report",
                "key_activities": "PRISMA reporting, manuscript writing, peer review"
            }
        }
        
        return phase_info.get(phase, {"description": "Unknown phase", "key_activities": ""})
    
    def _assess_timeline_health(self, progress: ProjectProgress) -> Dict[str, Any]:
        """Assess project timeline health and provide warnings."""
        health_status = "green"  # green, yellow, red
        warnings = []
        
        if progress.overall_completion_percentage < 20 and progress.estimated_days_remaining and progress.estimated_days_remaining < 60:
            health_status = "red"
            warnings.append("Project significantly behind schedule")
        elif progress.overall_completion_percentage < 50 and progress.estimated_days_remaining and progress.estimated_days_remaining < 30:
            health_status = "yellow" 
            warnings.append("Project timeline may be at risk")
        
        return {
            "status": health_status,
            "warnings": warnings,
            "completion_velocity": progress.overall_completion_percentage / max(1, (100 - (progress.estimated_days_remaining or 0)))
        }
    
    async def get_next_steps(self, project_id: int, current_phase: Optional[str] = None) -> Dict[str, Any]:
        """
        Get AI-powered recommendations for next actions in SLR workflow.
        
        Args:
            project_id: SLR project ID  
            current_phase: Current project phase
            
        Returns:
            Dictionary with prioritized recommendations and guidance
        """
        try:
            phase_enum = SLRPhase(current_phase) if current_phase else SLRPhase.PLANNING
            
            next_steps = self._get_phase_specific_next_steps(phase_enum)
            priorities = self._calculate_task_priorities(phase_enum)
            guidance = self._get_methodology_guidance(phase_enum)
            
            self.logger.info(f"Generated next steps for project {project_id}, phase {phase_enum.value}")
            
            return {
                "success": True,
                "current_phase": phase_enum.value,
                "next_steps": next_steps,
                "priorities": priorities,
                "methodology_guidance": guidance,
                "estimated_time": self._estimate_phase_time(phase_enum),
                "common_pitfalls": self._get_common_pitfalls(phase_enum)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting next steps: {e}")
            return {
                "success": False,
                "error": f"Failed to get next steps: {str(e)}"
            }
    
    def _get_phase_specific_next_steps(self, phase: SLRPhase) -> List[Dict[str, Any]]:
        """Get specific next steps for each SLR phase."""
        phase_steps = {
            SLRPhase.PLANNING: [
                {"action": "Validate research question using PICO/SPIDER framework", "priority": "high"},
                {"action": "Define specific inclusion and exclusion criteria", "priority": "high"},
                {"action": "Develop comprehensive search strategy", "priority": "medium"},
                {"action": "Create protocol document following PRISMA-P", "priority": "medium"},
                {"action": "Register protocol with PROSPERO", "priority": "low"}
            ],
            SLRPhase.SEARCH: [
                {"action": "Execute database searches with documented strategy", "priority": "high"},
                {"action": "Perform citation searching (forward/backward)", "priority": "medium"},
                {"action": "Search grey literature and repositories", "priority": "medium"},
                {"action": "Remove duplicates systematically", "priority": "high"},
                {"action": "Document search results and decisions", "priority": "medium"}
            ],
            SLRPhase.SCREENING: [
                {"action": "Conduct pilot screening to test criteria", "priority": "high"},
                {"action": "Perform title/abstract screening", "priority": "high"},
                {"action": "Calculate inter-reviewer agreement", "priority": "medium"},
                {"action": "Conduct full-text screening", "priority": "high"},
                {"action": "Resolve conflicts through discussion", "priority": "medium"}
            ],
            SLRPhase.QUALITY_ASSESSMENT: [
                {"action": "Select appropriate quality assessment tool", "priority": "high"},
                {"action": "Conduct pilot quality assessment", "priority": "medium"},
                {"action": "Assess quality of all included studies", "priority": "high"},
                {"action": "Calculate inter-rater reliability", "priority": "medium"},
                {"action": "Create quality assessment summary tables", "priority": "low"}
            ]
        }
        
        return phase_steps.get(phase, [])
    
    def _calculate_task_priorities(self, phase: SLRPhase) -> Dict[str, List[str]]:
        """Calculate task priorities for current phase."""
        return {
            "urgent": ["Complete current phase tasks before moving forward"],
            "high": ["Core methodology tasks that affect review validity"],
            "medium": ["Important documentation and quality checks"],
            "low": ["Administrative tasks and reporting preparation"]
        }
    
    def _get_methodology_guidance(self, phase: SLRPhase) -> List[str]:
        """Get methodology guidance for specific phase."""
        guidance = {
            SLRPhase.PLANNING: [
                "Follow PRISMA-P checklist for protocol development",
                "Use PICO framework for intervention studies, SPIDER for qualitative",
                "Consider registering with PROSPERO before starting",
                "Ensure research question is focused and answerable"
            ],
            SLRPhase.SEARCH: [
                "Search at least 3 major databases relevant to your topic",
                "Use both controlled vocabulary (MeSH) and free text terms", 
                "Document all search strategies with dates and results",
                "Consider searching trial registries and grey literature"
            ],
            SLRPhase.SCREENING: [
                "Use at least 2 independent reviewers for screening",
                "Conduct pilot screening to test inclusion/exclusion criteria",
                "Aim for substantial agreement (kappa > 0.6) between reviewers",
                "Document all exclusion reasons for transparency"
            ]
        }
        
        return guidance.get(phase, ["Follow established systematic review methodology"])
    
    def _estimate_phase_time(self, phase: SLRPhase) -> Dict[str, Any]:
        """Estimate time requirements for phase completion."""
        time_estimates = {
            SLRPhase.PLANNING: {"weeks": "2-4", "effort": "Medium", "dependencies": "None"},
            SLRPhase.SEARCH: {"weeks": "2-3", "effort": "Low", "dependencies": "Completed protocol"},
            SLRPhase.SCREENING: {"weeks": "4-8", "effort": "High", "dependencies": "Search results"},
            SLRPhase.QUALITY_ASSESSMENT: {"weeks": "2-4", "effort": "Medium", "dependencies": "Included studies"},
            SLRPhase.DATA_EXTRACTION: {"weeks": "3-6", "effort": "High", "dependencies": "Quality assessment"},
            SLRPhase.ANALYSIS: {"weeks": "3-5", "effort": "High", "dependencies": "Extracted data"},
            SLRPhase.REPORTING: {"weeks": "4-6", "effort": "Medium", "dependencies": "Completed analysis"}
        }
        
        return time_estimates.get(phase, {"weeks": "Variable", "effort": "Unknown", "dependencies": "Unknown"})
    
    def _get_common_pitfalls(self, phase: SLRPhase) -> List[str]:
        """Get common pitfalls and how to avoid them."""
        pitfalls = {
            SLRPhase.PLANNING: [
                "Overly broad research question - keep it focused and specific",
                "Insufficient database coverage - include discipline-specific databases",
                "Unclear inclusion/exclusion criteria - test with sample papers"
            ],
            SLRPhase.SCREENING: [
                "Low inter-reviewer agreement - improve criteria clarity", 
                "Inconsistent application of criteria - provide reviewer training",
                "Incomplete documentation - record all exclusion reasons"
            ],
            SLRPhase.QUALITY_ASSESSMENT: [
                "Wrong quality assessment tool - choose tool appropriate for study designs",
                "Insufficient reviewer training - ensure consistent assessment approach"
            ]
        }
        
        return pitfalls.get(phase, ["Follow established best practices for systematic reviews"])
    
    async def get_slr_guide(self, 
                          topic: str, 
                          experience_level: str = "beginner",
                          current_phase: Optional[str] = None) -> Dict[str, Any]:
        """
        Get interactive methodology guidance and best practices for SLR.
        
        Args:
            topic: SLR methodology topic
            experience_level: User's experience level
            current_phase: Current SLR phase
            
        Returns:
            Dictionary with comprehensive guidance and resources
        """
        try:
            guidance = self._get_topic_guidance(topic.lower())
            resources = self._get_learning_resources(topic.lower(), experience_level)
            examples = self._get_practical_examples(topic.lower())
            
            self.logger.info(f"Generated SLR guide for topic: {topic}")
            
            return {
                "success": True,
                "topic": topic,
                "experience_level": experience_level,
                "current_phase": current_phase,
                "guidance": guidance,
                "step_by_step": self._get_step_by_step_guide(topic.lower()),
                "resources": resources,
                "examples": examples,
                "checklist": self._get_topic_checklist(topic.lower()),
                "common_mistakes": self._get_topic_pitfalls(topic.lower())
            }
            
        except Exception as e:
            self.logger.error(f"Error generating SLR guide: {e}")
            return {
                "success": False,
                "error": f"Failed to generate guide: {str(e)}"
            }
    
    def _get_topic_guidance(self, topic: str) -> str:
        """Get detailed guidance for specific SLR topic."""
        topic_guides = {
            "research question": """
            A well-formulated research question is the foundation of a systematic review. Use structured frameworks:
            
            **PICO Framework** (for intervention studies):
            - P (Population): Who is the study population?
            - I (Intervention): What intervention is being studied?
            - C (Comparison): What is the comparison intervention?
            - O (Outcome): What outcome is measured?
            
            **SPIDER Framework** (for qualitative studies):
            - S (Sample): Who are the participants?
            - P (Phenomenon of Interest): What is being studied?
            - I (Design): What methodology is used?
            - D (Evaluation): What outcome is measured?
            - R (Research type): What research approach?
            """,
            
            "search strategy": """
            Develop a comprehensive search strategy:
            
            1. **Identify key concepts** from your research question
            2. **Generate synonyms** and alternative terms
            3. **Use database thesauri** (MeSH, EMTREE) for controlled vocabulary
            4. **Combine terms** using Boolean operators (AND, OR, NOT)
            5. **Test and refine** your search strategy
            6. **Document everything** for reproducibility
            
            Search at least 3 relevant databases and consider grey literature.
            """,
            
            "screening": """
            Systematic screening process:
            
            1. **Two-stage screening**: Title/abstract first, then full-text
            2. **Independent reviewers**: At least 2 reviewers for each stage
            3. **Clear criteria**: Well-defined inclusion/exclusion criteria
            4. **Pilot testing**: Test criteria on sample of papers
            5. **Conflict resolution**: Predetermined process for disagreements
            6. **Documentation**: Record all decisions and reasons
            
            Aim for substantial agreement (κ > 0.6) between reviewers.
            """,
            
            "quality assessment": """
            Assess methodological quality of included studies:
            
            1. **Choose appropriate tool**: CASP, JBI, Cochrane RoB, etc.
            2. **Multiple reviewers**: Independent assessment by 2+ reviewers
            3. **Pilot assessment**: Test tool on sample of studies
            4. **Training**: Ensure reviewers understand quality criteria
            5. **Documentation**: Record scores and justifications
            6. **Summary**: Create quality assessment summary tables
            
            Quality assessment informs evidence synthesis and confidence ratings.
            """
        }
        
        return topic_guides.get(topic, "No specific guidance available for this topic. Please refer to PRISMA guidelines.")
    
    def _get_step_by_step_guide(self, topic: str) -> List[str]:
        """Get step-by-step instructions for topic."""
        step_guides = {
            "research question": [
                "1. Identify the broad area of interest",
                "2. Review existing literature to understand gaps", 
                "3. Apply PICO/SPIDER framework to structure question",
                "4. Ensure question is focused and answerable",
                "5. Validate question with supervisors/experts",
                "6. Document final research question clearly"
            ],
            "screening": [
                "1. Import search results to reference manager",
                "2. Remove duplicates systematically",
                "3. Create screening forms with criteria",
                "4. Conduct pilot screening (10-20 papers)",
                "5. Begin title/abstract screening",
                "6. Calculate inter-reviewer agreement",
                "7. Proceed to full-text screening",
                "8. Document final included/excluded studies"
            ]
        }
        
        return step_guides.get(topic, ["Follow established systematic review methodology"])
    
    def _get_learning_resources(self, topic: str, experience_level: str) -> List[Dict[str, str]]:
        """Get learning resources based on topic and experience level."""
        return [
            {
                "title": "PRISMA Guidelines",
                "type": "Website",
                "url": "http://www.prisma-statement.org/",
                "description": "Official PRISMA reporting guidelines"
            },
            {
                "title": "Cochrane Handbook",
                "type": "Manual", 
                "url": "https://handbook-5-1.cochrane.org/",
                "description": "Comprehensive systematic review methodology"
            },
            {
                "title": "JBI Manual",
                "type": "Manual",
                "url": "https://jbi.global/critical-appraisal-tools",
                "description": "Joanna Briggs Institute methodology"
            }
        ]
    
    def _get_practical_examples(self, topic: str) -> List[str]:
        """Get practical examples for topic."""
        examples = {
            "research question": [
                "PICO Example: In adults with depression (P), is cognitive behavioral therapy (I) compared to medication (C) more effective in reducing depressive symptoms (O)?",
                "SPIDER Example: What are the experiences (P) of nurses (S) regarding workplace stress (P) in qualitative studies (D,E,R)?"
            ],
            "screening": [
                "Title screening: 'Machine learning algorithms for medical diagnosis' → Include (relevant to AI in healthcare review)",
                "Abstract screening: Study includes both intervention and control groups → Include for full-text review"
            ]
        }
        
        return examples.get(topic, ["Examples not available for this topic"])
    
    def _get_topic_checklist(self, topic: str) -> List[str]:
        """Get checklist for topic completion."""
        checklists = {
            "research question": [
                "☐ Research question uses PICO/SPIDER framework",
                "☐ Question is focused and specific", 
                "☐ Question is answerable with available literature",
                "☐ Question validated by experts/supervisors"
            ],
            "screening": [
                "☐ Inclusion/exclusion criteria clearly defined",
                "☐ Pilot screening completed successfully",
                "☐ Two independent reviewers assigned",
                "☐ Inter-reviewer agreement calculated", 
                "☐ All decisions documented with reasons"
            ]
        }
        
        return checklists.get(topic, ["Follow general systematic review checklist"])
    
    def _get_topic_pitfalls(self, topic: str) -> List[str]:
        """Get common pitfalls for topic."""
        pitfalls = {
            "research question": [
                "Question too broad - leads to unmanageable scope",
                "Missing key components of PICO/SPIDER framework",
                "Question not aligned with available evidence"
            ],
            "screening": [
                "Poorly defined criteria leading to inconsistent decisions",
                "Insufficient reviewer training",
                "Low inter-reviewer agreement not addressed"
            ]
        }
        
        return pitfalls.get(topic, ["Follow established best practices"])

    async def create_screening_workflow(self, 
                                      project_id: int, 
                                      inclusion_criteria: List[str], 
                                      exclusion_criteria: List[str], 
                                      reviewers: List[str],
                                      screening_stages: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a multi-stage screening workflow for study selection."""
        if screening_stages is None:
            screening_stages = ["title_abstract", "full_text", "final_selection"]
        
        # Create screening workflow configuration
        workflow_config = {
            "project_id": project_id,
            "created_at": datetime.utcnow().isoformat(),
            "inclusion_criteria": inclusion_criteria,
            "exclusion_criteria": exclusion_criteria,
            "reviewers": reviewers,
            "screening_stages": screening_stages,
            "required_agreement": 0.8,  # Kappa coefficient threshold
            "conflict_resolution": "consensus_meeting"
        }
        
        # Initialize screening statistics
        screening_stats = {
            "total_papers": 0,
            "papers_by_stage": {stage: {"pending": 0, "included": 0, "excluded": 0} for stage in screening_stages},
            "reviewer_agreement": {},
            "conflicts": []
        }
        
        # Generate reviewer assignments (round-robin for balance)
        reviewer_assignments = {}
        for i, reviewer in enumerate(reviewers):
            reviewer_assignments[reviewer] = {
                "stages": screening_stages,
                "workload": 0,
                "decisions": []
            }
        
        return {
            "workflow_id": f"screening_workflow_{project_id}_{int(datetime.utcnow().timestamp())}",
            "config": workflow_config,
            "statistics": screening_stats,
            "reviewer_assignments": reviewer_assignments,
            "status": "initialized",
            "next_actions": [
                "Upload papers for screening",
                "Begin title/abstract screening stage",
                "Monitor inter-reviewer agreement"
            ]
        }

    async def screen_paper(self, 
                          project_id: int,
                          paper_id: int,
                          reviewer_id: str,
                          stage: str,
                          decision: str,
                          reason: Optional[str] = None,
                          exclusion_criteria: Optional[List[str]] = None,
                          confidence_level: Optional[float] = None) -> Dict[str, Any]:
        """Record screening decision with rationale for study selection."""
        # Validate decision
        valid_decisions = ["include", "exclude", "uncertain"]
        if decision not in valid_decisions:
            raise ValueError(f"Decision must be one of: {valid_decisions}")
        
        # Validate stage
        valid_stages = ["title_abstract", "full_text", "final_selection"]
        if stage not in valid_stages:
            raise ValueError(f"Stage must be one of: {valid_stages}")
        
        # Create screening record
        screening_record = {
            "project_id": project_id,
            "paper_id": paper_id,
            "reviewer_id": reviewer_id,
            "stage": stage,
            "decision": decision,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "exclusion_criteria": exclusion_criteria or [],
            "confidence_level": confidence_level or 0.8
        }
        
        # Calculate screening statistics
        screening_stats = {
            "decision_recorded": True,
            "requires_second_reviewer": stage in ["title_abstract", "full_text"],
            "conflict_detected": False,
            "agreement_score": None
        }
        
        # Check for conflicts with other reviewers
        # (In real implementation, this would query the database)
        other_decisions = []  # Would fetch from database
        
        if other_decisions:
            agreement_score = self._calculate_reviewer_agreement(screening_record, other_decisions)
            screening_stats["agreement_score"] = agreement_score
            
            if agreement_score < 0.8:
                screening_stats["conflict_detected"] = True
                screening_stats["resolution_required"] = True
        
        # Determine next actions
        next_actions = []
        if screening_stats["requires_second_reviewer"]:
            next_actions.append("Await second reviewer decision")
        
        if screening_stats["conflict_detected"]:
            next_actions.append("Schedule conflict resolution meeting")
        
        if decision == "include" and stage == "title_abstract":
            next_actions.append("Proceed to full-text screening")
        
        return {
            "screening_id": f"screening_{project_id}_{paper_id}_{int(datetime.utcnow().timestamp())}",
            "record": screening_record,
            "statistics": screening_stats,
            "next_actions": next_actions,
            "status": "recorded"
        }

    def _calculate_reviewer_agreement(self, 
                                    current_decision: Dict[str, Any], 
                                    other_decisions: List[Dict[str, Any]]) -> float:
        """Calculate inter-reviewer agreement score."""
        if not other_decisions:
            return 1.0
        
        # Simple agreement calculation (could be enhanced with Cohen's Kappa)
        agreements = 0
        total_comparisons = len(other_decisions)
        
        for other_decision in other_decisions:
            if current_decision["decision"] == other_decision["decision"]:
                agreements += 1
        
        return agreements / total_comparisons if total_comparisons > 0 else 1.0