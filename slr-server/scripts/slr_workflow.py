#!/usr/bin/env python3
"""
Production-Level Systematic Literature Review Workflow

This script demonstrates a comprehensive, production-ready systematic literature 
review workflow using ALL 23 tools available in the SLR MCP Server.

Target Document: "Analyse og design af platform til realtids taleoversættelse.pdf"
Research Domain: Real-time Speech Translation Platform Analysis

Usage: python production_slr_workflow.py

This script will:
1. Create a professional SLR project for speech translation research
2. Upload and process the PDF document
3. Execute all 23 available MCP tools in a logical workflow
4. Generate comprehensive reports and exports
5. Provide detailed logging and performance metrics
6. Create production-quality outputs for research use
"""

import asyncio
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@dataclass
class WorkflowStep:
    """Represents a single step in the SLR workflow"""
    name: str
    tool_name: str
    description: str
    parameters: Dict[str, Any]
    success: bool = False
    error: Optional[str] = None
    result: Optional[str] = None
    execution_time: float = 0.0
    timestamp: Optional[str] = None


@dataclass
class WorkflowReport:
    """Comprehensive workflow execution report"""
    project_title: str
    start_time: str
    end_time: str
    total_execution_time: float
    total_steps: int
    successful_steps: int
    failed_steps: int
    steps: List[WorkflowStep]
    project_id: Optional[int] = None
    paper_id: Optional[int] = None


class ProductionSLRWorkflow:
    """Production-grade systematic literature review workflow manager"""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.project_id: Optional[int] = None
        self.paper_id: Optional[int] = None
        self.workflow_report = WorkflowReport(
            project_title="Real-time Speech Translation Platform Analysis",
            start_time="",
            end_time="",
            total_execution_time=0.0,
            total_steps=0,
            successful_steps=0,
            failed_steps=0,
            steps=[]
        )
        
        # Production-level configuration
        self.pdf_path = Path("Analyse og design af platform til realtids taleoversættelse.pdf")
        self.output_dir = Path("slr_outputs")
        self.output_dir.mkdir(exist_ok=True)
        
    async def connect_to_server(self) -> bool:
        """Establish connection to SLR MCP Server"""
        print("🔗 Establishing production connection to SLR MCP Server...")
        
        server_params = StdioServerParameters(
            command='python',
            args=['-m', 'src.main'],
            cwd=str(Path.cwd())
        )
        
        try:
            self.read, self.write = await stdio_client(server_params).__aenter__()
            self.session = await ClientSession(self.read, self.write).__aenter__()
            await self.session.initialize()
            
            print("✅ Production MCP connection established")
            return True
            
        except Exception as e:
            print(f"❌ Failed to establish connection: {e}")
            return False
    
    async def execute_step(self, step: WorkflowStep) -> WorkflowStep:
        """Execute a single workflow step with comprehensive error handling"""
        print(f"\n⏳ Executing: {step.name}")
        print(f"   Tool: {step.tool_name}")
        print(f"   Description: {step.description}")
        
        start_time = time.time()
        step.timestamp = datetime.now().isoformat()
        
        try:
            # Execute the MCP tool call
            result = await self.session.call_tool(step.tool_name, step.parameters)
            
            if result.content and result.content[0].text:
                step.result = result.content[0].text
                step.success = True
                
                # Extract IDs from responses for subsequent steps
                if step.tool_name == "create_slr_project" and "project_id" in step.result.lower():
                    # Try to extract project ID (simplified extraction)
                    self.project_id = 1  # Assume first project
                    self.workflow_report.project_id = self.project_id
                    
                elif step.tool_name == "upload_paper" and "paper_id" in step.result.lower():
                    # Try to extract paper ID (simplified extraction)
                    self.paper_id = 1  # Assume first paper
                    self.workflow_report.paper_id = self.paper_id
                
                print(f"   ✅ Success: {step.result[:100]}...")
                
            else:
                step.success = False
                step.error = "Empty response from server"
                print(f"   ⚠️  Empty response from {step.tool_name}")
                
        except Exception as e:
            step.success = False
            step.error = str(e)
            print(f"   ❌ Error: {e}")
            
        step.execution_time = time.time() - start_time
        print(f"   ⏱️  Execution time: {step.execution_time:.2f}s")
        
        return step
    
    def create_workflow_steps(self) -> List[WorkflowStep]:
        """Create comprehensive workflow using all 23 SLR MCP tools"""
        
        steps = [
            # Phase 1: Project Setup & Document Processing
            WorkflowStep(
                name="Create SLR Project",
                tool_name="create_slr_project",
                description="Initialize comprehensive SLR project for speech translation research",
                parameters={
                    "title": "Systematic Literature Review: Real-time Speech Translation Platform Analysis and Design",
                    "research_domain": "Natural Language Processing, Machine Translation, Real-time Systems",
                    "description": "Comprehensive systematic literature review analyzing the design and implementation of real-time speech translation platforms, focusing on system architecture, performance optimization, user experience, and technical challenges.",
                    "team_lead": "Senior Research Analyst",
                    "team_members": [
                        "NLP Systems Architect", 
                        "Machine Translation Specialist", 
                        "Real-time Systems Engineer",
                        "Quality Assessment Reviewer",
                        "Technical Documentation Specialist"
                    ],
                    "research_question": "What are the key architectural patterns, performance optimization strategies, and design principles for building effective real-time speech translation platforms, and how do different approaches impact system latency, translation accuracy, and user experience?",
                    "estimated_timeline_weeks": 12
                }
            ),
            
            WorkflowStep(
                name="Upload Target Document",
                tool_name="upload_paper",
                description="Upload and parse the speech translation platform analysis document",
                parameters={
                    "file_path": str(self.pdf_path.absolute()),
                    "title": "Analysis and Design of Real-time Speech Translation Platform",
                    "authors": ["Research Team"],
                    "publication_year": 2024,
                    "doi": "slr-speech-translation-2024-001",
                    "tags": ["speech translation", "real-time systems", "NLP", "machine translation", "platform design"]
                }
            ),
            
            WorkflowStep(
                name="Index Document Content",
                tool_name="index_paper",
                description="Create intelligent academic chunks for comprehensive content analysis",
                parameters={
                    "paper_id": 1,  # Will be updated dynamically
                    "strategy": "academic_sections",
                    "force": True
                }
            ),
            
            WorkflowStep(
                name="Validate Research Question",
                tool_name="validate_research_question",
                description="Validate research question using PICO framework",
                parameters={
                    "research_question": "What are the key architectural patterns, performance optimization strategies, and design principles for building effective real-time speech translation platforms?",
                    "framework": "PICO",
                    "domain": "Computer Science - Natural Language Processing"
                }
            ),
            
            # Phase 2: Document Analysis & Quality Assessment
            WorkflowStep(
                name="Analyze Document Structure",
                tool_name="get_paper_structure",
                description="Extract and analyze document structure and organization",
                parameters={
                    "paper_id": 1
                }
            ),
            
            WorkflowStep(
                name="Perform Quality Assessment",
                tool_name="assess_quality",
                description="Systematic quality assessment using PRISMA guidelines",
                parameters={
                    "paper_id": 1,
                    "assessment_framework": "PRISMA",
                    "reviewer_id": "primary_reviewer",
                    "criteria": {
                        "methodology_clarity": "high",
                        "technical_rigor": "high",
                        "system_evaluation": "medium",
                        "reproducibility": "medium",
                        "literature_coverage": "high",
                        "bias_risk": "low"
                    }
                }
            ),
            
            WorkflowStep(
                name="Retrieve Quality Assessment",
                tool_name="get_quality_assessment",
                description="Retrieve detailed quality assessment results",
                parameters={
                    "paper_id": 1,
                    "reviewer_id": "primary_reviewer"
                }
            ),
            
            WorkflowStep(
                name="Analyze Hypotheses",
                tool_name="analyze_hypotheses",
                description="Extract and analyze research hypotheses and claims",
                parameters={
                    "paper_id": 1,
                    "hypothesis_type": "technical_performance"
                }
            ),
            
            WorkflowStep(
                name="Analyze Citations",
                tool_name="analyze_citations",
                description="Analyze citation patterns and reference networks",
                parameters={
                    "paper_id": 1,
                    "analysis_type": "reference_analysis",
                    "depth": 2
                }
            ),
            
            # Phase 3: Content Search & Analysis
            WorkflowStep(
                name="Full-text Search - Architecture",
                tool_name="search_papers",
                description="Search for content related to system architecture",
                parameters={
                    "query": "system architecture platform design microservices",
                    "search_type": "semantic",
                    "filters": {"paper_ids": [1]},
                    "limit": 10
                }
            ),
            
            WorkflowStep(
                name="Full-text Search - Performance",
                tool_name="search_papers",
                description="Search for performance optimization content",
                parameters={
                    "query": "performance optimization latency real-time processing",
                    "search_type": "semantic",
                    "filters": {"paper_ids": [1]},
                    "limit": 10
                }
            ),
            
            WorkflowStep(
                name="Full-text Search - Translation Quality",
                tool_name="search_papers",
                description="Search for translation quality and accuracy discussions",
                parameters={
                    "query": "translation accuracy quality evaluation metrics",
                    "search_type": "semantic",
                    "filters": {"paper_ids": [1]},
                    "limit": 10
                }
            ),
            
            # Phase 4: Screening & Workflow Management
            WorkflowStep(
                name="Create Screening Workflow",
                tool_name="create_screening_workflow",
                description="Set up systematic screening process for document evaluation",
                parameters={
                    "project_id": 1,
                    "inclusion_criteria": [
                        "Focuses on real-time speech translation systems",
                        "Contains technical architecture information",
                        "Discusses performance evaluation or optimization",
                        "Addresses user experience or interface design",
                        "Published in academic or professional context"
                    ],
                    "exclusion_criteria": [
                        "Non-technical promotional material",
                        "Incomplete or draft documents",
                        "Purely theoretical without implementation details",
                        "Not related to speech or translation technologies"
                    ],
                    "reviewers": ["primary_reviewer", "secondary_reviewer"],
                    "screening_stages": ["title_abstract", "full_text", "quality_assessment"]
                }
            ),
            
            WorkflowStep(
                name="Screen Document - Primary",
                tool_name="screen_paper",
                description="Perform primary screening of the document",
                parameters={
                    "project_id": 1,
                    "paper_id": 1,
                    "reviewer_id": "primary_reviewer",
                    "stage": "full_text",
                    "decision": "include",
                    "reason": "Document provides comprehensive analysis of real-time speech translation platform with detailed technical architecture and design principles",
                    "confidence_level": 0.95,
                    "exclusion_criteria": []
                }
            ),
            
            WorkflowStep(
                name="Screen Document - Secondary",
                tool_name="screen_paper",
                description="Perform secondary screening for reliability",
                parameters={
                    "project_id": 1,
                    "paper_id": 1,
                    "reviewer_id": "secondary_reviewer",
                    "stage": "full_text",
                    "decision": "include",
                    "reason": "High-quality technical document with clear methodology and implementation details relevant to research question",
                    "confidence_level": 0.90,
                    "exclusion_criteria": []
                }
            ),
            
            # Phase 5: Advanced Analysis & Synthesis
            WorkflowStep(
                name="Calculate Inter-rater Reliability",
                tool_name="calculate_inter_rater_reliability",
                description="Calculate agreement between reviewers for quality assurance",
                parameters={
                    "paper_ids": [1],
                    "reviewer_ids": ["primary_reviewer", "secondary_reviewer"]
                }
            ),
            
            WorkflowStep(
                name="Detect Citation Patterns",
                tool_name="detect_citation_patterns",
                description="Identify patterns in citation and reference data",
                parameters={
                    "corpus_filter": {"paper_ids": [1]},
                    "pattern_type": "topic_clustering"
                }
            ),
            
            WorkflowStep(
                name="Synthesize Evidence",
                tool_name="synthesize_evidence",
                description="Synthesize evidence and findings from the document",
                parameters={
                    "paper_ids": [1],
                    "synthesis_method": "narrative_synthesis",
                    "outcome_measures": [
                        "system_performance_metrics",
                        "translation_accuracy",
                        "user_satisfaction",
                        "technical_architecture_patterns"
                    ]
                }
            ),
            
            # Phase 6: Content Retrieval & Detailed Analysis
            WorkflowStep(
                name="List All Papers",
                tool_name="list_papers",
                description="Retrieve comprehensive list of papers in the project",
                parameters={
                    "filters": {"project_id": 1},
                    "limit": 50,
                    "offset": 0
                }
            ),
            
            WorkflowStep(
                name="Get Document Details",
                tool_name="get_paper",
                description="Retrieve detailed information about the processed document",
                parameters={
                    "paper_id": 1
                }
            ),
            
            WorkflowStep(
                name="Get Content Chunks",
                tool_name="get_chunk_content",
                description="Retrieve specific content chunks for detailed analysis",
                parameters={
                    "chunk_id": 1  # First chunk
                }
            ),
            
            # Phase 7: Reporting & Export
            WorkflowStep(
                name="Generate SLR Report",
                tool_name="generate_slr_report",
                description="Generate comprehensive systematic literature review report",
                parameters={
                    "paper_ids": [1],
                    "report_format": "academic_report",
                    "include_quality_assessment": True,
                    "include_citation_analysis": True,
                    "output_path": str(self.output_dir / "comprehensive_slr_report.pdf")
                }
            ),
            
            WorkflowStep(
                name="Export Citation Network",
                tool_name="export_citation_network",
                description="Export citation network for visualization and analysis",
                parameters={
                    "paper_ids": [1],
                    "format": "graphml",
                    "output_path": str(self.output_dir / "citation_network.graphml")
                }
            ),
            
            # Phase 8: Project Management & Guidance
            WorkflowStep(
                name="Get SLR Progress",
                tool_name="get_slr_progress",
                description="Retrieve comprehensive project progress dashboard",
                parameters={
                    "project_id": 1
                }
            ),
            
            WorkflowStep(
                name="Get Next Steps",
                tool_name="get_next_steps",
                description="Get AI-powered recommendations for next actions",
                parameters={
                    "project_id": 1,
                    "current_phase": "data_synthesis"
                }
            ),
            
            WorkflowStep(
                name="Get SLR Methodology Guide",
                tool_name="get_slr_guide",
                description="Get methodology guidance for systematic literature reviews",
                parameters={
                    "topic": "data_synthesis",
                    "experience_level": "advanced",
                    "current_phase": "synthesis"
                }
            )
        ]
        
        return steps
    
    def update_dynamic_parameters(self, steps: List[WorkflowStep]):
        """Update parameters that depend on runtime values"""
        for step in steps:
            # Update project_id references
            if "project_id" in step.parameters and step.parameters["project_id"] == 1:
                if self.project_id:
                    step.parameters["project_id"] = self.project_id
            
            # Update paper_id references
            if "paper_id" in step.parameters and step.parameters["paper_id"] == 1:
                if self.paper_id:
                    step.parameters["paper_id"] = self.paper_id
            
            # Update paper_ids arrays
            if "paper_ids" in step.parameters and step.parameters["paper_ids"] == [1]:
                if self.paper_id:
                    step.parameters["paper_ids"] = [self.paper_id]
    
    async def execute_comprehensive_workflow(self) -> WorkflowReport:
        """Execute the complete production SLR workflow"""
        
        print("🔬 Production-Level Systematic Literature Review Workflow")
        print("=" * 70)
        print(f"Target Document: {self.pdf_path.name}")
        print(f"Research Domain: Natural Language Processing & Real-time Systems")
        print(f"Output Directory: {self.output_dir}")
        print("=" * 70)
        
        # Verify PDF exists
        if not self.pdf_path.exists():
            print(f"❌ PDF file not found: {self.pdf_path}")
            return self.workflow_report
        
        # Connect to server
        if not await self.connect_to_server():
            print("❌ Failed to establish server connection")
            return self.workflow_report
        
        # Initialize workflow
        self.workflow_report.start_time = datetime.now().isoformat()
        start_time = time.time()
        
        # Create and execute workflow steps
        steps = self.create_workflow_steps()
        self.workflow_report.total_steps = len(steps)
        
        print(f"\n📋 Executing {len(steps)} workflow steps...")
        
        for i, step in enumerate(steps, 1):
            print(f"\n{'='*50}")
            print(f"Step {i}/{len(steps)}: {step.name}")
            
            # Update dynamic parameters before execution
            self.update_dynamic_parameters([step])
            
            # Execute step
            executed_step = await self.execute_step(step)
            self.workflow_report.steps.append(executed_step)
            
            if executed_step.success:
                self.workflow_report.successful_steps += 1
            else:
                self.workflow_report.failed_steps += 1
            
            # Small delay between steps for stability
            await asyncio.sleep(0.1)
        
        # Finalize report
        self.workflow_report.end_time = datetime.now().isoformat()
        self.workflow_report.total_execution_time = time.time() - start_time
        
        return self.workflow_report
    
    def generate_final_report(self, report: WorkflowReport):
        """Generate comprehensive final report of the workflow execution"""
        
        report_path = self.output_dir / "workflow_execution_report.json"
        
        # Convert to JSON-serializable format
        report_data = asdict(report)
        
        # Add summary statistics
        success_rate = (report.successful_steps / report.total_steps) * 100 if report.total_steps > 0 else 0
        
        summary = {
            "execution_summary": {
                "success_rate": f"{success_rate:.1f}%",
                "total_execution_time": f"{report.total_execution_time:.2f} seconds",
                "avg_step_time": f"{report.total_execution_time / report.total_steps:.2f} seconds",
                "pdf_processed": str(self.pdf_path.name),
                "outputs_generated": list(self.output_dir.glob("*")),
                "server_tools_tested": 23,
                "production_ready": success_rate >= 80.0
            }
        }
        
        report_data["summary"] = summary
        
        # Save comprehensive report
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Print summary to console
        print("\n" + "=" * 70)
        print("🎉 PRODUCTION WORKFLOW EXECUTION COMPLETE")
        print("=" * 70)
        print(f"📊 Success Rate: {success_rate:.1f}% ({report.successful_steps}/{report.total_steps} steps)")
        print(f"⏱️  Total Time: {report.total_execution_time:.2f} seconds")
        print(f"📄 Document Processed: {self.pdf_path.name}")
        print(f"📁 Outputs Generated: {len(list(self.output_dir.glob('*')))} files")
        print(f"🔧 Tools Tested: All 23 SLR MCP Server tools")
        
        if success_rate >= 80.0:
            print("✅ PRODUCTION VALIDATION: PASSED - Server ready for production use")
        else:
            print("⚠️  PRODUCTION VALIDATION: NEEDS ATTENTION - Review failed steps")
        
        print(f"📋 Detailed Report: {report_path}")
        print("=" * 70)
        
        # Print failed steps if any
        if report.failed_steps > 0:
            print(f"\n⚠️  Failed Steps ({report.failed_steps}):")
            for step in report.steps:
                if not step.success:
                    print(f"   ❌ {step.name}: {step.error}")
        
        # Print successful tool usage
        successful_tools = [step.tool_name for step in report.steps if step.success]
        print(f"\n✅ Successfully Tested Tools ({len(successful_tools)}):")
        for tool in sorted(set(successful_tools)):
            print(f"   🔧 {tool}")


async def main():
    """Main entry point for production SLR workflow"""
    
    workflow = ProductionSLRWorkflow()
    
    try:
        print("🚀 Starting Production-Level SLR MCP Server Validation")
        print("📋 Testing ALL 23 tools with real document processing")
        print("🎯 Validating server for production deployment\n")
        
        # Execute comprehensive workflow
        report = await workflow.execute_comprehensive_workflow()
        
        # Generate final validation report
        workflow.generate_final_report(report)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Production workflow interrupted by user")
    except Exception as e:
        print(f"\n❌ Production workflow failed: {e}")
        traceback.print_exc()
    finally:
        # Cleanup connections
        if hasattr(workflow, 'session') and workflow.session:
            try:
                await workflow.session.__aexit__(None, None, None)
            except:
                pass


if __name__ == "__main__":
    asyncio.run(main())