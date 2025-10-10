#!/usr/bin/env python3
"""
Batch Operations and Workflow Examples

This module demonstrates advanced patterns for batch operations, workflow management,
and error recovery in GUI applications using the Study Buddy MCP integration layer.

Key Patterns Demonstrated:
1. Batch Upload with Progress Tracking
2. Document Processing Workflows  
3. Parallel Operations Management
4. Error Recovery and Retry Logic
5. Progress Aggregation and Reporting
6. Workflow State Management
7. Resource Management and Cleanup

These examples show how to handle real-world scenarios where GUI applications
need to process multiple documents, coordinate complex workflows, and provide
robust error handling with user-friendly feedback.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Tuple
import json


# Import MCP integration layer
try:
    from gui.integration import (
        MCPClient, 
        ConfigManager, 
        MCPConnectionError,
        ConnectionState,
        OperationProgress
    )
    from gui.integration.examples.integration_manager_pattern import (
        StudyBuddyIntegrationManager,
        OperationType,
        OperationStatus
    )
except ImportError as e:
    print(f"❌ Failed to import MCP integration layer: {e}")
    print("💡 This is a template example - imports will work when integration layer is implemented")


class WorkflowStatus(Enum):
    """Status of a workflow"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep(Enum):
    """Steps in document processing workflow"""
    UPLOAD = "upload"
    INDEX = "index"
    SUMMARIZE = "summarize"
    VALIDATE = "validate"
    COMPLETE = "complete"


@dataclass
class BatchProgress:
    """Progress tracking for batch operations"""
    total_items: int
    completed_items: int = 0
    failed_items: int = 0
    current_item: Optional[str] = None
    current_step: str = "Starting..."
    start_time: datetime = field(default_factory=datetime.now)
    estimated_completion: Optional[datetime] = None
    
    @property
    def progress_percent(self) -> float:
        """Calculate overall progress percentage"""
        if self.total_items == 0:
            return 0.0
        return (self.completed_items / self.total_items) * 100
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        processed = self.completed_items + self.failed_items
        if processed == 0:
            return 0.0
        return (self.completed_items / processed) * 100
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def estimate_completion(self):
        """Estimate completion time based on current progress"""
        if self.completed_items > 0 and self.progress_percent > 0:
            total_estimated_time = self.elapsed_time * (100 / self.progress_percent)
            remaining_time = total_estimated_time - self.elapsed_time
            self.estimated_completion = datetime.now() + timedelta(seconds=remaining_time)


@dataclass  
class WorkflowState:
    """State management for document processing workflows"""
    workflow_id: str
    documents: List[Dict[str, Any]]
    current_step: WorkflowStep = WorkflowStep.UPLOAD
    status: WorkflowStatus = WorkflowStatus.PENDING
    progress: BatchProgress = field(default_factory=lambda: BatchProgress(0))
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        self.progress.total_items = len(self.documents)
    
    def add_error(self, document_path: str, step: WorkflowStep, error: str):
        """Add an error to the workflow"""
        self.errors.append({
            "document": document_path,
            "step": step.value,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def update_progress(self, current_document: str = None, step_description: str = None):
        """Update workflow progress"""
        if current_document:
            self.progress.current_item = current_document
        if step_description:
            self.progress.current_step = step_description
        
        self.progress.estimate_completion()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow state to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "current_step": self.current_step.value,
            "status": self.status.value,
            "progress": {
                "total_items": self.progress.total_items,
                "completed_items": self.progress.completed_items,
                "failed_items": self.progress.failed_items,
                "progress_percent": self.progress.progress_percent,
                "success_rate": self.progress.success_rate,
                "elapsed_time": self.progress.elapsed_time,
                "current_item": self.progress.current_item,
                "current_step": self.progress.current_step,
                "estimated_completion": self.progress.estimated_completion.isoformat() if self.progress.estimated_completion else None
            },
            "results_count": len(self.results),
            "errors_count": len(self.errors),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class BatchOperationManager:
    """
    Manager for batch operations with progress tracking and error recovery.
    
    Provides high-level interface for common batch operations like:
    - Batch document upload with progress tracking
    - Parallel document processing
    - Workflow orchestration
    - Error recovery and retry logic
    """
    
    def __init__(self, integration_manager: StudyBuddyIntegrationManager):
        self.integration_manager = integration_manager
        self.logger = logging.getLogger("BatchOperationManager")
        
        # Active workflows
        self.active_workflows: Dict[str, WorkflowState] = {}
        self.workflow_counter = 0
        
        # Configuration
        self.max_parallel_operations = 3
        self.retry_delays = [1, 2, 5, 10]  # Exponential backoff delays
        
    # === Batch Upload Operations ===
    
    async def batch_upload_documents(
        self,
        file_paths: List[str],
        progress_callback: Optional[Callable[[BatchProgress], None]] = None,
        max_parallel: int = 3,
        validate_files: bool = True
    ) -> Dict[str, Any]:
        """
        Upload multiple documents in parallel with progress tracking.
        
        Args:
            file_paths: List of file paths to upload
            progress_callback: Callback for progress updates
            max_parallel: Maximum parallel uploads
            validate_files: Whether to validate files before upload
            
        Returns:
            Dict containing upload results and statistics
        """
        self.logger.info(f"Starting batch upload of {len(file_paths)} documents")
        
        # Initialize progress tracking
        progress = BatchProgress(total_items=len(file_paths))
        
        # Validate files if requested
        if validate_files:
            file_paths = await self._validate_files(file_paths, progress, progress_callback)
        
        # Results tracking
        results = {
            "successful_uploads": [],
            "failed_uploads": [],
            "total_files": len(file_paths),
            "processed_files": 0
        }
        
        # Create semaphore to limit parallel operations
        semaphore = asyncio.Semaphore(max_parallel)
        
        # Upload tasks
        tasks = []
        for i, file_path in enumerate(file_paths):
            task = self._upload_single_document(
                file_path, semaphore, progress, progress_callback, results, i
            )
            tasks.append(task)
        
        # Execute all uploads
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Final progress update
        progress.current_step = "Upload batch completed"
        if progress_callback:
            progress_callback(progress)
        
        # Calculate final statistics
        results["success_rate"] = (
            len(results["successful_uploads"]) / len(file_paths) * 100 
            if file_paths else 0
        )
        results["total_time_seconds"] = progress.elapsed_time
        
        self.logger.info(f"Batch upload completed: {len(results['successful_uploads'])} successful, {len(results['failed_uploads'])} failed")
        
        return results
    
    async def _validate_files(
        self, 
        file_paths: List[str], 
        progress: BatchProgress,
        progress_callback: Optional[Callable] = None
    ) -> List[str]:
        """Validate files before processing"""
        progress.current_step = "Validating files..."
        if progress_callback:
            progress_callback(progress)
        
        valid_files = []
        supported_extensions = {'.pdf', '.docx', '.md', '.pptx', '.txt'}
        
        for file_path in file_paths:
            path = Path(file_path)
            
            # Check file exists
            if not path.exists():
                self.logger.warning(f"File not found: {file_path}")
                continue
            
            # Check file extension
            if path.suffix.lower() not in supported_extensions:
                self.logger.warning(f"Unsupported file type: {file_path}")
                continue
            
            # Check file size (max 100MB)
            file_size = path.stat().st_size
            if file_size > 100 * 1024 * 1024:
                self.logger.warning(f"File too large: {file_path} ({file_size / 1024 / 1024:.1f}MB)")
                continue
            
            valid_files.append(file_path)
        
        self.logger.info(f"Validated {len(valid_files)} of {len(file_paths)} files")
        return valid_files
    
    async def _upload_single_document(
        self,
        file_path: str,
        semaphore: asyncio.Semaphore,
        progress: BatchProgress,
        progress_callback: Optional[Callable],
        results: Dict[str, Any],
        index: int
    ):
        """Upload a single document with error handling"""
        async with semaphore:
            try:
                # Update progress
                progress.current_item = Path(file_path).name
                progress.current_step = f"Uploading {Path(file_path).name}..."
                if progress_callback:
                    progress_callback(progress)
                
                # Perform upload
                result = await self.integration_manager.upload_document(file_path)
                
                if result.get("success"):
                    # Upload successful
                    upload_info = {
                        "file_path": file_path,
                        "document_id": result["data"]["document_id"],
                        "title": result["data"]["title"],
                        "index": index
                    }
                    results["successful_uploads"].append(upload_info)
                    progress.completed_items += 1
                    
                    self.logger.info(f"✅ Uploaded: {Path(file_path).name}")
                else:
                    # Upload failed
                    error_info = {
                        "file_path": file_path,
                        "error": result.get("error", "Unknown error"),
                        "index": index
                    }
                    results["failed_uploads"].append(error_info)
                    progress.failed_items += 1
                    
                    self.logger.error(f"❌ Failed to upload: {Path(file_path).name} - {result.get('error')}")
                
            except Exception as e:
                # Exception during upload
                error_info = {
                    "file_path": file_path,
                    "error": str(e),
                    "index": index
                }
                results["failed_uploads"].append(error_info)
                progress.failed_items += 1
                
                self.logger.error(f"❌ Exception uploading {Path(file_path).name}: {e}")
            
            finally:
                # Update processed count
                results["processed_files"] += 1
                
                # Update progress
                if progress_callback:
                    progress_callback(progress)
    
    # === Document Processing Workflows ===
    
    async def create_document_processing_workflow(
        self,
        file_paths: List[str],
        workflow_config: Dict[str, Any] = None,
        progress_callback: Optional[Callable[[WorkflowState], None]] = None
    ) -> str:
        """
        Create a comprehensive document processing workflow.
        
        The workflow includes:
        1. Document upload
        2. Document indexing (chunking)
        3. Summary generation (via AI agent integration)
        4. Validation and quality checks
        
        Args:
            file_paths: List of documents to process
            workflow_config: Configuration options
            progress_callback: Callback for workflow updates
            
        Returns:
            str: Workflow ID
        """
        # Generate workflow ID
        self.workflow_counter += 1
        workflow_id = f"workflow_{self.workflow_counter}_{int(time.time())}"
        
        # Default configuration
        config = {
            "auto_index": True,
            "indexing_strategy": "auto",
            "generate_summaries": True,
            "summary_types": ["brief", "standard"],
            "validate_results": True,
            "max_retries": 3,
            "parallel_operations": 2
        }
        
        if workflow_config:
            config.update(workflow_config)
        
        # Create workflow state
        documents = [{"file_path": path, "status": "pending"} for path in file_paths]
        workflow = WorkflowState(
            workflow_id=workflow_id,
            documents=documents
        )
        
        # Store workflow
        self.active_workflows[workflow_id] = workflow
        
        self.logger.info(f"Created workflow {workflow_id} with {len(file_paths)} documents")
        
        # Start workflow execution in background
        asyncio.create_task(self._execute_workflow(workflow, config, progress_callback))
        
        return workflow_id
    
    async def _execute_workflow(
        self,
        workflow: WorkflowState,
        config: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ):
        """Execute document processing workflow"""
        try:
            workflow.status = WorkflowStatus.RUNNING
            self.logger.info(f"Starting execution of workflow {workflow.workflow_id}")
            
            # Step 1: Upload Documents
            await self._workflow_step_upload(workflow, config, progress_callback)
            
            # Step 2: Index Documents  
            if config.get("auto_index", True):
                await self._workflow_step_index(workflow, config, progress_callback)
            
            # Step 3: Generate Summaries
            if config.get("generate_summaries", False):
                await self._workflow_step_summarize(workflow, config, progress_callback)
            
            # Step 4: Validate Results
            if config.get("validate_results", True):
                await self._workflow_step_validate(workflow, config, progress_callback)
            
            # Workflow completed
            workflow.status = WorkflowStatus.COMPLETED
            workflow.current_step = WorkflowStep.COMPLETE
            workflow.update_progress(step_description="Workflow completed successfully")
            
            if progress_callback:
                progress_callback(workflow)
            
            self.logger.info(f"✅ Workflow {workflow.workflow_id} completed successfully")
            
        except Exception as e:
            # Workflow failed
            workflow.status = WorkflowStatus.FAILED
            workflow.add_error("workflow", WorkflowStep.COMPLETE, str(e))
            
            if progress_callback:
                progress_callback(workflow)
            
            self.logger.error(f"❌ Workflow {workflow.workflow_id} failed: {e}")
    
    async def _workflow_step_upload(
        self,
        workflow: WorkflowState,
        config: Dict[str, Any],
        progress_callback: Optional[Callable]
    ):
        """Execute upload step of workflow"""
        workflow.current_step = WorkflowStep.UPLOAD
        workflow.update_progress(step_description="Uploading documents...")
        
        if progress_callback:
            progress_callback(workflow)
        
        # Extract file paths
        file_paths = [doc["file_path"] for doc in workflow.documents]
        
        # Batch upload with progress tracking
        def upload_progress(batch_progress: BatchProgress):
            workflow.progress.completed_items = batch_progress.completed_items
            workflow.progress.failed_items = batch_progress.failed_items
            workflow.progress.current_item = batch_progress.current_item
            workflow.progress.current_step = f"Upload: {batch_progress.current_step}"
            
            if progress_callback:
                progress_callback(workflow)
        
        # Execute batch upload
        upload_results = await self.batch_upload_documents(
            file_paths,
            progress_callback=upload_progress,
            max_parallel=config.get("parallel_operations", 2)
        )
        
        # Update workflow with upload results
        successful_uploads = {
            item["file_path"]: item["document_id"] 
            for item in upload_results["successful_uploads"]
        }
        
        for doc in workflow.documents:
            file_path = doc["file_path"]
            if file_path in successful_uploads:
                doc["document_id"] = successful_uploads[file_path]
                doc["status"] = "uploaded"
            else:
                doc["status"] = "upload_failed"
                # Find error details
                for failed_item in upload_results["failed_uploads"]:
                    if failed_item["file_path"] == file_path:
                        workflow.add_error(file_path, WorkflowStep.UPLOAD, failed_item["error"])
                        break
        
        # Store upload results
        workflow.results["upload"] = upload_results
        
        self.logger.info(f"Workflow {workflow.workflow_id}: Upload step completed - {len(successful_uploads)} successful")
    
    async def _workflow_step_index(
        self,
        workflow: WorkflowState,
        config: Dict[str, Any],
        progress_callback: Optional[Callable]
    ):
        """Execute indexing step of workflow"""
        workflow.current_step = WorkflowStep.INDEX
        workflow.update_progress(step_description="Indexing documents...")
        
        if progress_callback:
            progress_callback(workflow)
        
        # Get successfully uploaded documents
        uploaded_docs = [doc for doc in workflow.documents if doc.get("document_id")]
        indexing_results = {"successful": [], "failed": []}
        
        # Index each document
        for i, doc in enumerate(uploaded_docs):
            try:
                workflow.update_progress(
                    current_document=Path(doc["file_path"]).name,
                    step_description=f"Indexing document {i+1}/{len(uploaded_docs)}..."
                )
                
                if progress_callback:
                    progress_callback(workflow)
                
                # Perform indexing
                result = await self.integration_manager.client.index_document(
                    document_id=doc["document_id"],
                    strategy=config.get("indexing_strategy", "auto")
                )
                
                if result.get("success"):
                    doc["indexed"] = True
                    doc["chunks_created"] = result["data"].get("chunks_created", 0)
                    indexing_results["successful"].append(doc)
                    self.logger.info(f"✅ Indexed: {Path(doc['file_path']).name}")
                else:
                    doc["indexed"] = False
                    indexing_results["failed"].append(doc)
                    workflow.add_error(doc["file_path"], WorkflowStep.INDEX, result.get("error", "Indexing failed"))
                    self.logger.error(f"❌ Failed to index: {Path(doc['file_path']).name}")
                
            except Exception as e:
                doc["indexed"] = False
                indexing_results["failed"].append(doc)
                workflow.add_error(doc["file_path"], WorkflowStep.INDEX, str(e))
                self.logger.error(f"❌ Exception indexing {Path(doc['file_path']).name}: {e}")
        
        # Store indexing results
        workflow.results["indexing"] = indexing_results
        
        self.logger.info(f"Workflow {workflow.workflow_id}: Indexing step completed - {len(indexing_results['successful'])} successful")
    
    async def _workflow_step_summarize(
        self,
        workflow: WorkflowState,
        config: Dict[str, Any],
        progress_callback: Optional[Callable]
    ):
        """Execute summarization step of workflow (placeholder for AI agent integration)"""
        workflow.current_step = WorkflowStep.SUMMARIZE
        workflow.update_progress(step_description="Generating summaries...")
        
        if progress_callback:
            progress_callback(workflow)
        
        # Note: In a real implementation, this would:
        # 1. Get document structure (chunks) for each indexed document
        # 2. Generate prompts for AI agent
        # 3. Call AI agent to generate summaries
        # 4. Save summaries back to MCP server
        
        # For this example, we'll simulate the process
        indexed_docs = [doc for doc in workflow.documents if doc.get("indexed")]
        summary_results = {"successful": [], "failed": []}
        
        for i, doc in enumerate(indexed_docs):
            try:
                workflow.update_progress(
                    current_document=Path(doc["file_path"]).name,
                    step_description=f"Generating summaries for document {i+1}/{len(indexed_docs)}..."
                )
                
                if progress_callback:
                    progress_callback(workflow)
                
                # Simulate summary generation (would be actual AI agent calls)
                await asyncio.sleep(1)  # Simulate processing time
                
                # In real implementation:
                # 1. structure = await self.integration_manager.get_document_structure(doc["document_id"])
                # 2. for chunk in structure["chunks"]:
                #      chunk_content = await self.integration_manager.get_chunk_content(chunk["chunk_id"])
                #      summary = await ai_agent.generate_summary(chunk_content)
                #      await self.integration_manager.save_summary(chunk["chunk_id"], summary)
                
                doc["summarized"] = True
                doc["summary_types"] = config.get("summary_types", ["standard"])
                summary_results["successful"].append(doc)
                
                self.logger.info(f"✅ Generated summaries for: {Path(doc['file_path']).name}")
                
            except Exception as e:
                doc["summarized"] = False
                summary_results["failed"].append(doc)
                workflow.add_error(doc["file_path"], WorkflowStep.SUMMARIZE, str(e))
                self.logger.error(f"❌ Failed to generate summaries for {Path(doc['file_path']).name}: {e}")
        
        # Store summarization results
        workflow.results["summarization"] = summary_results
        
        self.logger.info(f"Workflow {workflow.workflow_id}: Summarization step completed - {len(summary_results['successful'])} successful")
    
    async def _workflow_step_validate(
        self,
        workflow: WorkflowState,
        config: Dict[str, Any],
        progress_callback: Optional[Callable]
    ):
        """Execute validation step of workflow"""
        workflow.current_step = WorkflowStep.VALIDATE
        workflow.update_progress(step_description="Validating results...")
        
        if progress_callback:
            progress_callback(workflow)
        
        # Validation checks
        validation_results = {
            "total_documents": len(workflow.documents),
            "uploaded_documents": len([doc for doc in workflow.documents if doc.get("document_id")]),
            "indexed_documents": len([doc for doc in workflow.documents if doc.get("indexed")]),
            "summarized_documents": len([doc for doc in workflow.documents if doc.get("summarized")]),
            "validation_errors": []
        }
        
        # Check for consistency issues
        for doc in workflow.documents:
            file_path = doc["file_path"]
            
            # Check upload-index consistency
            if doc.get("document_id") and not doc.get("indexed"):
                if config.get("auto_index", True):
                    validation_results["validation_errors"].append({
                        "document": file_path,
                        "error": "Document uploaded but not indexed (auto_index was enabled)"
                    })
            
            # Check index-summary consistency  
            if doc.get("indexed") and not doc.get("summarized"):
                if config.get("generate_summaries", False):
                    validation_results["validation_errors"].append({
                        "document": file_path,
                        "error": "Document indexed but not summarized (generate_summaries was enabled)"
                    })
        
        # Store validation results
        workflow.results["validation"] = validation_results
        
        # Calculate overall success rate
        successful_documents = len([
            doc for doc in workflow.documents 
            if doc.get("document_id") and (not config.get("auto_index", True) or doc.get("indexed"))
        ])
        
        workflow.results["overall_success_rate"] = (
            successful_documents / len(workflow.documents) * 100
            if workflow.documents else 0
        )
        
        self.logger.info(f"Workflow {workflow.workflow_id}: Validation completed - {successful_documents}/{len(workflow.documents)} fully successful")
    
    # === Workflow Management ===
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow"""
        workflow = self.active_workflows.get(workflow_id)
        return workflow.to_dict() if workflow else None
    
    def list_active_workflows(self) -> List[Dict[str, Any]]:
        """List all active workflows"""
        return [workflow.to_dict() for workflow in self.active_workflows.values()]
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return False
        
        if workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            return False  # Cannot cancel completed workflows
        
        workflow.status = WorkflowStatus.CANCELLED
        workflow.update_progress(step_description="Workflow cancelled by user")
        
        self.logger.info(f"Workflow {workflow_id} cancelled")
        return True
    
    def cleanup_completed_workflows(self, max_age_hours: int = 24):
        """Clean up old completed workflows"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for workflow_id, workflow in self.active_workflows.items():
            if (workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED] and
                workflow.updated_at < cutoff_time):
                to_remove.append(workflow_id)
        
        for workflow_id in to_remove:
            del self.active_workflows[workflow_id]
        
        if to_remove:
            self.logger.info(f"Cleaned up {len(to_remove)} old workflows")
    
    # === Error Recovery ===
    
    async def retry_failed_operations(
        self,
        workflow_id: str,
        retry_steps: Optional[List[WorkflowStep]] = None
    ) -> bool:
        """Retry failed operations in a workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return False
        
        if workflow.status != WorkflowStatus.FAILED:
            return False
        
        self.logger.info(f"Retrying failed operations for workflow {workflow_id}")
        
        # Default to retrying all steps
        if retry_steps is None:
            retry_steps = [WorkflowStep.UPLOAD, WorkflowStep.INDEX, WorkflowStep.SUMMARIZE]
        
        # Reset workflow status
        workflow.status = WorkflowStatus.RUNNING
        workflow.errors.clear()  # Clear previous errors
        
        # Retry based on specified steps
        try:
            if WorkflowStep.UPLOAD in retry_steps:
                # Retry failed uploads
                failed_uploads = [doc for doc in workflow.documents if not doc.get("document_id")]
                if failed_uploads:
                    await self._retry_uploads(workflow, failed_uploads)
            
            if WorkflowStep.INDEX in retry_steps:
                # Retry failed indexing
                failed_indexing = [doc for doc in workflow.documents if doc.get("document_id") and not doc.get("indexed")]
                if failed_indexing:
                    await self._retry_indexing(workflow, failed_indexing)
            
            if WorkflowStep.SUMMARIZE in retry_steps:
                # Retry failed summarization
                failed_summaries = [doc for doc in workflow.documents if doc.get("indexed") and not doc.get("summarized")]
                if failed_summaries:
                    await self._retry_summarization(workflow, failed_summaries)
            
            # Check if workflow is now successful
            successful_docs = [doc for doc in workflow.documents if doc.get("document_id")]
            if len(successful_docs) == len(workflow.documents):
                workflow.status = WorkflowStatus.COMPLETED
            else:
                workflow.status = WorkflowStatus.FAILED
            
            return workflow.status == WorkflowStatus.COMPLETED
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.add_error("retry", WorkflowStep.COMPLETE, str(e))
            self.logger.error(f"Error during retry for workflow {workflow_id}: {e}")
            return False
    
    async def _retry_uploads(self, workflow: WorkflowState, failed_docs: List[Dict[str, Any]]):
        """Retry failed uploads with exponential backoff"""
        for doc in failed_docs:
            for attempt, delay in enumerate(self.retry_delays):
                try:
                    if attempt > 0:
                        await asyncio.sleep(delay)
                    
                    result = await self.integration_manager.upload_document(doc["file_path"])
                    
                    if result.get("success"):
                        doc["document_id"] = result["data"]["document_id"]
                        doc["status"] = "uploaded"
                        self.logger.info(f"✅ Retry successful for: {Path(doc['file_path']).name}")
                        break
                    else:
                        if attempt == len(self.retry_delays) - 1:  # Last attempt
                            workflow.add_error(doc["file_path"], WorkflowStep.UPLOAD, result.get("error", "Upload failed"))
                            
                except Exception as e:
                    if attempt == len(self.retry_delays) - 1:  # Last attempt
                        workflow.add_error(doc["file_path"], WorkflowStep.UPLOAD, str(e))
    
    async def _retry_indexing(self, workflow: WorkflowState, failed_docs: List[Dict[str, Any]]):
        """Retry failed indexing operations"""
        for doc in failed_docs:
            for attempt, delay in enumerate(self.retry_delays):
                try:
                    if attempt > 0:
                        await asyncio.sleep(delay)
                    
                    result = await self.integration_manager.client.index_document(
                        document_id=doc["document_id"],
                        strategy="auto"
                    )
                    
                    if result.get("success"):
                        doc["indexed"] = True
                        doc["chunks_created"] = result["data"].get("chunks_created", 0)
                        self.logger.info(f"✅ Indexing retry successful for: {Path(doc['file_path']).name}")
                        break
                    else:
                        if attempt == len(self.retry_delays) - 1:
                            workflow.add_error(doc["file_path"], WorkflowStep.INDEX, result.get("error", "Indexing failed"))
                            
                except Exception as e:
                    if attempt == len(self.retry_delays) - 1:
                        workflow.add_error(doc["file_path"], WorkflowStep.INDEX, str(e))
    
    async def _retry_summarization(self, workflow: WorkflowState, failed_docs: List[Dict[str, Any]]):
        """Retry failed summarization operations"""
        # Similar implementation to _retry_indexing but for summarization
        # This would integrate with the AI agent system
        pass


# === Usage Examples ===

async def example_batch_upload():
    """Example: Batch document upload with progress tracking"""
    print("=== Batch Upload Example ===")
    
    # Initialize integration manager
    integration_manager = StudyBuddyIntegrationManager()
    await integration_manager.initialize()
    
    try:
        # Create batch operation manager
        batch_manager = BatchOperationManager(integration_manager)
        
        # Sample file paths (replace with actual files)
        file_paths = [
            "documents/paper1.pdf",
            "documents/book_chapter.docx", 
            "documents/notes.md",
            "documents/presentation.pptx"
        ]
        
        # Progress callback
        def on_progress(progress: BatchProgress):
            print(f"📈 Progress: {progress.progress_percent:.1f}% - {progress.current_step}")
            if progress.current_item:
                print(f"   Current: {progress.current_item}")
            print(f"   Completed: {progress.completed_items}, Failed: {progress.failed_items}")
        
        # Execute batch upload
        print(f"🚀 Starting batch upload of {len(file_paths)} documents...")
        results = await batch_manager.batch_upload_documents(
            file_paths,
            progress_callback=on_progress,
            max_parallel=2
        )
        
        # Print results
        print(f"\\n📊 Batch Upload Results:")
        print(f"   Total files: {results['total_files']}")
        print(f"   Successful: {len(results['successful_uploads'])}")
        print(f"   Failed: {len(results['failed_uploads'])}")
        print(f"   Success rate: {results['success_rate']:.1f}%")
        print(f"   Total time: {results['total_time_seconds']:.1f}s")
        
        # Print successful uploads
        for upload in results['successful_uploads']:
            print(f"   ✅ {Path(upload['file_path']).name} → Document ID {upload['document_id']}")
        
        # Print failures
        for failure in results['failed_uploads']:
            print(f"   ❌ {Path(failure['file_path']).name}: {failure['error']}")
    
    finally:
        await integration_manager.shutdown()


async def example_document_workflow():
    """Example: Complete document processing workflow"""
    print("=== Document Processing Workflow Example ===")
    
    # Initialize integration manager
    integration_manager = StudyBuddyIntegrationManager()
    await integration_manager.initialize()
    
    try:
        # Create batch operation manager
        batch_manager = BatchOperationManager(integration_manager)
        
        # Sample documents to process
        file_paths = [
            "documents/research_paper.pdf",
            "documents/textbook_chapter.docx",
            "documents/lecture_notes.md"
        ]
        
        # Workflow configuration
        workflow_config = {
            "auto_index": True,
            "indexing_strategy": "chapter",
            "generate_summaries": True,
            "summary_types": ["brief", "standard", "detailed"],
            "validate_results": True,
            "parallel_operations": 2
        }
        
        # Progress callback
        def on_workflow_progress(workflow: WorkflowState):
            status = workflow.to_dict()
            progress = status["progress"]
            
            print(f"🔄 Workflow {workflow.workflow_id}")
            print(f"   Step: {status['current_step']}")
            print(f"   Status: {status['status']}")
            print(f"   Progress: {progress['progress_percent']:.1f}%")
            print(f"   Current: {progress['current_step']}")
            if progress['current_item']:
                print(f"   Processing: {progress['current_item']}")
            print(f"   Completed: {progress['completed_items']}/{progress['total_items']}")
            print(f"   Errors: {status['errors_count']}")
            if progress['estimated_completion']:
                print(f"   ETA: {progress['estimated_completion']}")
        
        # Create and start workflow
        print(f"🚀 Starting document processing workflow for {len(file_paths)} documents...")
        workflow_id = await batch_manager.create_document_processing_workflow(
            file_paths,
            workflow_config,
            progress_callback=on_workflow_progress
        )
        
        print(f"📋 Created workflow: {workflow_id}")
        
        # Monitor workflow progress
        while True:
            status = batch_manager.get_workflow_status(workflow_id)
            if not status:
                break
            
            if status["status"] in ["completed", "failed", "cancelled"]:
                print(f"\\n🏁 Workflow {workflow_id} finished with status: {status['status']}")
                
                # Print final results
                if "overall_success_rate" in status.get("results", {}):
                    success_rate = status["results"]["overall_success_rate"]
                    print(f"📊 Overall success rate: {success_rate:.1f}%")
                
                # Print validation results
                if "validation" in status.get("results", {}):
                    validation = status["results"]["validation"]
                    print(f"📋 Validation Results:")
                    print(f"   Uploaded: {validation['uploaded_documents']}/{validation['total_documents']}")
                    print(f"   Indexed: {validation['indexed_documents']}/{validation['total_documents']}")
                    print(f"   Summarized: {validation['summarized_documents']}/{validation['total_documents']}")
                    
                    if validation['validation_errors']:
                        print(f"   Validation Errors: {len(validation['validation_errors'])}")
                        for error in validation['validation_errors']:
                            print(f"     ⚠️ {Path(error['document']).name}: {error['error']}")
                
                break
            
            await asyncio.sleep(2)  # Check every 2 seconds
    
    finally:
        await integration_manager.shutdown()


async def example_error_recovery():
    """Example: Error recovery and retry operations"""
    print("=== Error Recovery Example ===")
    
    # Initialize integration manager (with intentionally problematic config)
    integration_manager = StudyBuddyIntegrationManager()
    
    try:
        # This might fail to initialize, demonstrating error recovery
        success = await integration_manager.initialize()
        print(f"Initialization success: {success}")
        
        # Create batch operation manager
        batch_manager = BatchOperationManager(integration_manager)
        
        # Create a workflow that might have failures
        file_paths = [
            "documents/valid_document.pdf",
            "nonexistent/file.pdf",  # This will fail
            "documents/another_valid.docx",
        ]
        
        workflow_id = await batch_manager.create_document_processing_workflow(
            file_paths,
            {"auto_index": True, "validate_results": True},
            progress_callback=lambda w: print(f"Workflow progress: {w.progress.progress_percent:.1f}%")
        )
        
        # Wait for workflow to complete/fail
        while True:
            status = batch_manager.get_workflow_status(workflow_id)
            if status["status"] in ["completed", "failed"]:
                break
            await asyncio.sleep(1)
        
        print(f"Workflow completed with status: {status['status']}")
        
        # If workflow failed, try to recover
        if status["status"] == "failed":
            print("🔧 Attempting error recovery...")
            
            # Retry failed operations
            recovery_success = await batch_manager.retry_failed_operations(
                workflow_id,
                retry_steps=[WorkflowStep.UPLOAD, WorkflowStep.INDEX]
            )
            
            print(f"Recovery success: {recovery_success}")
            
            # Check final status
            final_status = batch_manager.get_workflow_status(workflow_id)
            print(f"Final workflow status: {final_status['status']}")
    
    finally:
        await integration_manager.shutdown()


if __name__ == "__main__":
    """Run examples"""
    print("Study Buddy Batch Operations and Workflow Examples")
    print("=" * 60)
    
    # Run batch upload example
    asyncio.run(example_batch_upload())
    
    print("\\n")
    
    # Run document workflow example
    asyncio.run(example_document_workflow())
    
    print("\\n")
    
    # Run error recovery example
    asyncio.run(example_error_recovery())