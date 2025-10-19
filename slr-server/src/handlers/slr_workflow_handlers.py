"""
MCP Handlers for SLR Workflow Guidance and Project Management.

This module provides MCP tool handlers for systematic literature review
workflow management, progress tracking, and user guidance.
"""

import logging
from typing import Any, Dict

from mcp.types import CallToolResult, TextContent

from ..container import Container
from ..automation.screening_documentation import ScreeningDecision

logger = logging.getLogger(__name__)


class SLRWorkflowMCPHandler:
    """
    MCP Handler for SLR workflow guidance and project management operations.
    
    This class handles MCP tool calls for project creation, progress tracking,
    next steps recommendations, screening workflows, and methodology guidance.
    """
    
    def __init__(self, container: Container):
        self.container = container
        logger.info("SLR Workflow MCP Handler initialized")
    
    async def handle_create_slr_project(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle create SLR project MCP tool call."""
        try:
            workflow_service = self.container.get_slr_workflow_service()
            
            result = await workflow_service.create_slr_project(
                title=arguments["title"],
                research_domain=arguments["research_domain"],
                description=arguments.get("description"),
                team_lead=arguments.get("team_lead"),
                team_members=arguments.get("team_members", []),
                research_question=arguments.get("research_question"),
                estimated_timeline_weeks=arguments.get("estimated_timeline_weeks")
            )
            
            if result["success"]:
                response_text = f"""
✅ SLR Project Created Successfully!

📋 Project Details:
• Title: {result['project']['title']}
• Domain: {result['project']['research_domain']}
• Status: {result['project']['status']}
• Team Lead: {result['project'].get('team_lead', 'Not specified')}
• Timeline: {result['project'].get('estimated_timeline_weeks', 'Not specified')} weeks

📝 Initial Tasks Generated: {len(result['initial_tasks'])} tasks in planning phase

🎯 Next Steps:
{chr(10).join(f"• {step}" for step in result['next_steps'])}

🏁 Current Milestones:
{chr(10).join(f"• {milestone}" for milestone in result['progress']['next_milestones'])}
                """
            else:
                response_text = f"❌ Failed to create SLR project: {result.get('error', 'Unknown error')}"
            
            return CallToolResult(
                content=[TextContent(type="text", text=response_text.strip())]
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
    
    async def handle_get_slr_progress(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get SLR progress MCP tool call."""
        try:
            workflow_service = self.container.get_slr_workflow_service()
            
            result = await workflow_service.get_slr_progress(
                project_id=arguments["project_id"]
            )
            
            if result["success"]:
                progress = result["progress"]
                
                response_text = f"""
📊 SLR Project Progress Dashboard

📈 Overall Progress: {progress.get('overall_completion_percentage', 0):.1f}%
🔄 Current Phase: {progress['current_phase']} ({progress.get('phase_completion_percentage', 0):.1f}% complete)

📚 Paper Progress:
• Total Papers: {progress.get('total_papers', 0)}
• Screened: {progress.get('screened_papers', 0)}
• Included: {progress.get('included_papers', 0)}
• Quality Assessed: {progress.get('assessed_papers', 0)}
• Data Extracted: {progress.get('extracted_papers', 0)}

✅ Task Progress: {progress.get('completed_tasks', 0)}/{progress.get('total_tasks', 0)}

📅 Timeline:
• Estimated Days Remaining: {progress.get('estimated_days_remaining', 'Unknown')}
• Timeline Status: {result['timeline_health']['status'].upper()}

🎯 Next Milestones:
{chr(10).join(f"• {milestone}" for milestone in progress.get('next_milestones', []))}

🔍 Current Phase Details:
{result['phase_status']['description']}
Key Activities: {result['phase_status']['key_activities']}

💡 Recommendations:
{chr(10).join(f"• {rec}" for rec in result.get('recommendations', []))}
                """
                
                if progress.get('bottlenecks'):
                    response_text += f"""
🚫 Bottlenecks:
{chr(10).join(f"• {bottleneck}" for bottleneck in progress['bottlenecks'])}
                    """
            else:
                response_text = f"❌ Failed to get progress: {result.get('error', 'Unknown error')}"
            
            return CallToolResult(
                content=[TextContent(type="text", text=response_text.strip())]
            )
            
        except Exception as e:
            logger.error(f"Error getting SLR progress: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Error getting SLR progress: {str(e)}"
                )],
                isError=True
            )
    
    async def handle_get_next_steps(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get next steps MCP tool call."""
        try:
            workflow_service = self.container.get_slr_workflow_service()
            
            result = await workflow_service.get_next_steps(
                project_id=arguments["project_id"],
                current_phase=arguments.get("current_phase")
            )
            
            if result["success"]:
                response_text = f"""
🎯 Next Steps for SLR Project

📍 Current Phase: {result['current_phase'].replace('_', ' ').title()}

🚀 Recommended Actions:
{chr(10).join(f"• {step['action']} [{step['priority'].upper()}]" for step in result['next_steps'])}

⚡ Task Priorities:
• Urgent: {', '.join(result['priorities']['urgent'])}
• High: {', '.join(result['priorities']['high'])}
• Medium: {', '.join(result['priorities']['medium'])}
• Low: {', '.join(result['priorities']['low'])}

📖 Methodology Guidance:
{chr(10).join(f"• {guide}" for guide in result['methodology_guidance'])}

⏱️ Time Estimation:
• Duration: {result['estimated_time']['weeks']} weeks
• Effort Level: {result['estimated_time']['effort']}
• Dependencies: {result['estimated_time']['dependencies']}

⚠️ Common Pitfalls to Avoid:
{chr(10).join(f"• {pitfall}" for pitfall in result['common_pitfalls'])}
                """
            else:
                response_text = f"❌ Failed to get next steps: {result.get('error', 'Unknown error')}"
            
            return CallToolResult(
                content=[TextContent(type="text", text=response_text.strip())]
            )
            
        except Exception as e:
            logger.error(f"Error getting next steps: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Error getting next steps: {str(e)}"
                )],
                isError=True
            )
    
    async def handle_create_screening_workflow(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle create screening workflow MCP tool call."""
        try:
            # Extract parameters
            project_id = arguments.get("project_id", 1)
            inclusion_criteria = arguments.get("inclusion_criteria", [])
            exclusion_criteria = arguments.get("exclusion_criteria", [])
            reviewers = arguments.get("reviewers", ["reviewer_1", "reviewer_2"])
            screening_stages = arguments.get("screening_stages", ["title_abstract", "full_text"])
            
            # Create screening workflow using service
            workflow_service = self.container.get_slr_workflow_service()
            workflow_result = await workflow_service.create_screening_workflow(
                project_id=project_id,
                inclusion_criteria=inclusion_criteria,
                exclusion_criteria=exclusion_criteria,
                reviewers=reviewers,
                screening_stages=screening_stages
            )
            
            response_text = f"""
📋 Screening Workflow Created Successfully

🆔 Workflow ID: {workflow_result['workflow_id']}
📊 Status: {workflow_result['status'].title()}

🔄 Screening Stages:
{chr(10).join(f"• Stage {i+1}: {stage.replace('_', ' ').title()}" for i, stage in enumerate(screening_stages))}

👥 Assigned Reviewers:
{chr(10).join(f"• {reviewer}" for reviewer in reviewers)}

📋 Inclusion Criteria:
{chr(10).join(f"• {criterion}" for criterion in inclusion_criteria) if inclusion_criteria else "• No specific criteria defined"}

❌ Exclusion Criteria:
{chr(10).join(f"• {criterion}" for criterion in exclusion_criteria) if exclusion_criteria else "• No specific criteria defined"}

🎯 Next Actions:
{chr(10).join(f"• {action}" for action in workflow_result['next_actions'])}

👥 Setup Instructions:
• Assign at least 2 reviewers per stage
• Define clear inclusion/exclusion criteria
• Set up conflict resolution process
• Configure inter-reviewer agreement tracking

📝 Next Actions:
• Upload your search results
• Begin pilot screening with 10-20 papers
• Calculate initial inter-reviewer agreement
• Proceed with full screening once agreement is satisfactory (κ > 0.6)

✅ Workflow is ready for use!
            """
            
            return CallToolResult(
                content=[TextContent(type="text", text=response_text.strip())]
            )
            
        except Exception as e:
            logger.error(f"Error creating screening workflow: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Error creating screening workflow: {str(e)}"
                )],
                isError=True
            )
    
    async def handle_screen_paper(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle individual paper screening MCP tool call."""
        try:
            # Extract parameters
            project_id = arguments.get("project_id", 1)
            paper_id = arguments["paper_id"]
            decision = arguments["decision"]
            stage = arguments.get("stage", "title_abstract")
            reviewer_id = arguments.get("reviewer_id", "reviewer_1")
            reason = arguments.get("reason")
            exclusion_criteria = arguments.get("exclusion_criteria", [])
            confidence_level = arguments.get("confidence_level")
            
            # Record screening decision using service
            workflow_service = self.container.get_slr_workflow_service()
            screening_result = await workflow_service.screen_paper(
                project_id=project_id,
                paper_id=paper_id,
                reviewer_id=reviewer_id,
                stage=stage,
                decision=decision,
                reason=reason,
                exclusion_criteria=exclusion_criteria,
                confidence_level=confidence_level
            )
            
            # Trigger auto-documentation of screening decision
            try:
                doc_system = self.container.get_screening_documentation_system()
                
                # Get paper details for documentation
                paper_repo = self.container.get_paper_repository()
                paper = paper_repo.get_by_id(paper_id)
                
                # Create screening decision object
                screening_decision = ScreeningDecision(
                    paper_id=paper_id,
                    reviewer_id=reviewer_id,
                    decision=decision,
                    confidence_level=confidence_level or 0.5,
                    reason=reason or "No reason provided",
                    exclusion_criteria=exclusion_criteria or [],
                    stage=stage
                )
                
                # Log decision and auto-generate documentation
                doc_system.log_paper_decision(
                    decision=screening_decision,
                    paper_title=paper.title if paper else f"Paper {paper_id}",
                    paper_year=paper.publication_year or 0 if paper else 0
                )
                
                logger.info(f"✅ Auto-documentation generated for paper {paper_id}")
            except Exception as doc_error:
                logger.warning(f"⚠️ Auto-documentation generation issue: {str(doc_error)}")
                # Don't fail the screening just because documentation had an issue
            
            decision_emoji = "✅" if decision == "include" else "❌"
            
            response_text = f"""
{decision_emoji} Paper Screening Recorded

🆔 Screening ID: {screening_result['screening_id']}
� Status: {screening_result['status'].title()}

�📄 Paper ID: {paper_id}
👤 Reviewer: {reviewer_id}
🔍 Stage: {stage.replace('_', ' ').title()}
🎯 Decision: {decision.upper()}
"""
            
            # Add reason if provided
            if reason:
                response_text += f"""
📝 Reason: {reason}
"""
            
            # Add exclusion criteria if provided
            if exclusion_criteria:
                response_text += f"""
❌ Exclusion Criteria:
{chr(10).join(f"• {criterion}" for criterion in exclusion_criteria)}
"""
            
            # Add confidence level if provided
            if confidence_level:
                response_text += f"""
🎯 Confidence Level: {confidence_level:.2f}
"""
            
            # Add statistics
            if screening_result['statistics']['agreement_score'] is not None:
                response_text += f"""
📊 Agreement Score: {screening_result['statistics']['agreement_score']:.2f}
"""
            
            if screening_result['statistics']['conflict_detected']:
                response_text += """
⚠️ Conflict detected with other reviewer!
"""
            
            # Add next actions
            response_text += f"""
🎯 Next Actions:
{chr(10).join(f"• {action}" for action in screening_result['next_actions'])}

✅ Screening decision saved successfully!
• Ensure second reviewer completes screening for this paper
• Check for conflicts if decisions differ
• Update overall screening progress

📄 Auto-Documentation:
• Decision JSON log created in logs/
• Progress tracker updated in screening_progress.csv
• Master log updated in screening_log.json
• Files auto-saved to projects/real-time-translation-platform/
            """
            
            return CallToolResult(
                content=[TextContent(type="text", text=response_text.strip())]
            )
            
        except Exception as e:
            logger.error(f"Error screening paper: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Error screening paper: {str(e)}"
                )],
                isError=True
            )
    
    async def handle_get_slr_guide(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get SLR guide MCP tool call."""
        try:
            workflow_service = self.container.get_slr_workflow_service()
            
            result = await workflow_service.get_slr_guide(
                topic=arguments["topic"],
                experience_level=arguments.get("experience_level", "beginner"),
                current_phase=arguments.get("current_phase")
            )
            
            if result["success"]:
                response_text = f"""
📖 SLR Guide: {result['topic'].title()}

👤 Experience Level: {result['experience_level'].title()}
📍 Current Phase: {result.get('current_phase', 'N/A')}

🎯 Guidance:
{result['guidance']}

📋 Step-by-Step Process:
{chr(10).join(result['step_by_step'])}

🔍 Practical Examples:
{chr(10).join(f"• {example}" for example in result['examples'])}

✅ Completion Checklist:
{chr(10).join(result['checklist'])}

⚠️ Common Mistakes to Avoid:
{chr(10).join(f"• {mistake}" for mistake in result['common_mistakes'])}

📚 Learning Resources:
{chr(10).join(f"• {res['title']} ({res['type']}): {res['description']}" for res in result['resources'])}
                """
            else:
                response_text = f"❌ Failed to generate guide: {result.get('error', 'Unknown error')}"
            
            return CallToolResult(
                content=[TextContent(type="text", text=response_text.strip())]
            )
            
        except Exception as e:
            logger.error(f"Error generating SLR guide: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Error generating SLR guide: {str(e)}"
                )],
                isError=True
            )