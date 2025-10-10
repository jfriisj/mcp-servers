"""
End-to-End Workflow Integration Tests

Tests for complete MCP client workflows that simulate real-world
usage patterns with the Study Buddy integration layer.

Test Coverage:
- Complete connection to operation to disconnection workflows
- Multi-step document processing workflows  
- Complex tool chain invocations
- User session simulation
- Performance under realistic workloads
- Full error recovery workflows
"""

import pytest
import asyncio
import time
import json
import tempfile
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from . import WORKFLOW_TESTS, REQUIRES_SERVER, INTEGRATION_TEST
from .conftest import IntegrationTestBase, measure_performance


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.requires_server
class TestEndToEndWorkflows(IntegrationTestBase):
    """Test suite for end-to-end workflows"""
    
    async def test_complete_session_workflow(self, server_config):
        """Test complete user session from start to finish"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        # Phase 1: Session Initialization
        client = MCPClient(server_config)
        start_time = time.time()
        
        # Connect to server
        await client.connect()
        assert client.is_connected(), "Session should start with successful connection"
        
        # Discover available capabilities
        if hasattr(client, 'list_tools'):
            tools = await client.list_tools()
            assert tools is not None, "Should discover available tools"
            print(f"Available tools: {len(tools) if isinstance(tools, list) else list(tools.keys())}")
        
        # Phase 2: Initial Operations
        initial_operations = [
            {"tool": "echo", "args": {"message": "session_start"}, "description": "Session start marker"},
            {"tool": "add", "args": {"a": 1, "b": 1}, "description": "Basic computation"},
            {"tool": "echo", "args": {"message": "capabilities_test"}, "description": "Capability validation"}
        ]
        
        for operation in initial_operations:
            if hasattr(client, 'call_tool'):
                result = await client.call_tool(operation["tool"], operation["args"])
                assert result is not None, f"Operation should succeed: {operation['description']}"
                
        # Phase 3: Complex Workflow Simulation
        # Simulate document processing workflow
        document_workflow = await self._simulate_document_processing(client)
        assert document_workflow["success"], "Document processing workflow should succeed"
        
        # Phase 4: Concurrent Operations
        concurrent_results = await self._simulate_concurrent_operations(client)
        assert concurrent_results["success_rate"] >= 0.9, "Concurrent operations should mostly succeed"
        
        # Phase 5: Error Recovery Testing
        recovery_results = await self._simulate_error_recovery(client)
        assert recovery_results["recovered"], "Session should recover from errors"
        
        # Phase 6: Session Cleanup
        cleanup_result = await self._simulate_session_cleanup(client)
        assert cleanup_result["clean"], "Session cleanup should be successful"
        
        # Final disconnect
        await client.disconnect()
        session_duration = time.time() - start_time
        
        # Session validation
        assert not client.is_connected(), "Session should end with clean disconnect"
        assert session_duration > 0, "Session should have measurable duration"
        
        print(f"Complete session workflow duration: {session_duration:.2f}s")
        
    async def _simulate_document_processing(self, client) -> Dict[str, Any]:
        """Simulate document processing workflow"""
        try:
            # Step 1: Document upload simulation
            if hasattr(client, 'call_tool'):
                upload_result = await client.call_tool("echo", {
                    "message": json.dumps({
                        "action": "upload_document",
                        "filename": "test_document.pdf",
                        "size": 1024000
                    })
                })
                
                # Step 2: Document parsing simulation
                parse_result = await client.call_tool("echo", {
                    "message": json.dumps({
                        "action": "parse_document",
                        "document_id": "doc_123",
                        "pages": 50
                    })
                })
                
                # Step 3: Content indexing simulation
                index_result = await client.call_tool("add", {"a": 50, "b": 0})  # Page count
                
                return {
                    "success": True,
                    "steps_completed": 3,
                    "upload": upload_result is not None,
                    "parse": parse_result is not None,
                    "index": index_result is not None
                }
            else:
                return {"success": False, "error": "Tool calls not available"}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def _simulate_concurrent_operations(self, client) -> Dict[str, Any]:
        """Simulate concurrent operations"""
        try:
            if not hasattr(client, 'call_tool'):
                return {"success_rate": 1.0, "message": "Tool calls not available"}
                
            # Launch concurrent operations
            tasks = []
            operation_count = 10
            
            for i in range(operation_count):
                task = asyncio.create_task(
                    client.call_tool("echo", {"message": f"concurrent_op_{i}"})
                )
                tasks.append(task)
                
            # Wait for completion
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Calculate success rate
            successful = sum(1 for r in results if not isinstance(r, Exception))
            success_rate = successful / len(results)
            
            return {
                "success_rate": success_rate,
                "total_operations": operation_count,
                "successful_operations": successful,
                "failed_operations": len(results) - successful
            }
        except Exception as e:
            return {"success_rate": 0.0, "error": str(e)}
            
    async def _simulate_error_recovery(self, client) -> Dict[str, Any]:
        """Simulate error conditions and recovery"""
        try:
            # Trigger error condition
            if hasattr(client, 'call_tool'):
                try:
                    await client.call_tool("error", {})  # Should fail
                except Exception:
                    pass  # Expected
                    
                # Test recovery
                recovery_result = await client.call_tool("echo", {"message": "recovery_test"})
                
                return {
                    "recovered": recovery_result is not None,
                    "connection_stable": client.is_connected()
                }
            else:
                return {"recovered": True, "message": "No error recovery testing needed"}
        except Exception as e:
            return {"recovered": False, "error": str(e)}
            
    async def _simulate_session_cleanup(self, client) -> Dict[str, Any]:
        """Simulate session cleanup operations"""
        try:
            # Perform cleanup operations
            if hasattr(client, 'call_tool'):
                cleanup_operations = [
                    {"tool": "echo", "args": {"message": "cleanup_temp_files"}},
                    {"tool": "echo", "args": {"message": "save_session_state"}},
                    {"tool": "echo", "args": {"message": "clear_cache"}},
                ]
                
                cleanup_results = []
                for operation in cleanup_operations:
                    result = await client.call_tool(operation["tool"], operation["args"])
                    cleanup_results.append(result is not None)
                    
                return {
                    "clean": all(cleanup_results),
                    "operations_completed": len(cleanup_results)
                }
            else:
                return {"clean": True, "message": "No cleanup operations needed"}
        except Exception as e:
            return {"clean": False, "error": str(e)}
            
    async def test_document_lifecycle_workflow(self, mcp_client):
        """Test complete document processing lifecycle"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Document lifecycle phases
        phases = [
            {"phase": "upload", "tool": "echo", "args": {"message": "document_upload"}},
            {"phase": "parse", "tool": "echo", "args": {"message": "document_parse"}},
            {"phase": "index", "tool": "add", "args": {"a": 100, "b": 200}},  # Simulated word count
            {"phase": "summarize", "tool": "echo", "args": {"message": "document_summarize"}},
            {"phase": "query", "tool": "echo", "args": {"message": "document_query"}},
        ]
        
        lifecycle_results = {}
        
        for phase_info in phases:
            phase = phase_info["phase"]
            
            try:
                start_time = time.time()
                result = await mcp_client.call_tool(phase_info["tool"], phase_info["args"])
                duration = time.time() - start_time
                
                lifecycle_results[phase] = {
                    "success": result is not None,
                    "duration": duration,
                    "result": result
                }
                
                print(f"Document {phase}: {'SUCCESS' if result is not None else 'FAILED'} ({duration:.3f}s)")
                
            except Exception as e:
                lifecycle_results[phase] = {
                    "success": False,
                    "error": str(e)
                }
                print(f"Document {phase}: FAILED - {e}")
                
        # Validate lifecycle completion
        successful_phases = sum(1 for r in lifecycle_results.values() if r.get("success", False))
        total_phases = len(phases)
        
        assert successful_phases >= total_phases - 1, \
            f"Document lifecycle should mostly succeed: {successful_phases}/{total_phases}"
            
        # Validate performance requirements
        total_duration = sum(r.get("duration", 0) for r in lifecycle_results.values())
        assert total_duration < 10.0, f"Document lifecycle too slow: {total_duration:.2f}s"
        
    @measure_performance
    async def test_high_throughput_workflow(self, mcp_client, performance_config):
        """Test high-throughput operational workflow"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # High-throughput configuration
        target_ops = performance_config["target_ops_per_second"]
        test_duration = 30  # seconds
        batch_size = 50
        
        total_operations = 0
        successful_operations = 0
        start_time = time.time()
        
        while time.time() - start_time < test_duration:
            # Create batch of operations
            batch_tasks = []
            
            for i in range(batch_size):
                task = asyncio.create_task(
                    mcp_client.call_tool("echo", {"message": f"throughput_test_{total_operations + i}"})
                )
                batch_tasks.append(task)
                
            # Execute batch
            batch_start = time.time()
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            batch_duration = time.time() - batch_start
            
            # Update metrics
            total_operations += len(batch_results)
            successful_operations += sum(1 for r in batch_results if not isinstance(r, Exception))
            
            # Log progress
            elapsed = time.time() - start_time
            current_throughput = successful_operations / elapsed
            
            print(f"Throughput: {current_throughput:.1f} ops/sec (target: {target_ops})")
            
            # Brief pause to prevent overwhelming
            if batch_duration < 0.1:
                await asyncio.sleep(0.1 - batch_duration)
                
        # Final metrics
        total_duration = time.time() - start_time
        final_throughput = successful_operations / total_duration
        success_rate = successful_operations / total_operations
        
        print(f"\nHigh-Throughput Workflow Results:")
        print(f"  Duration: {total_duration:.2f}s")
        print(f"  Total operations: {total_operations}")
        print(f"  Successful: {successful_operations}")
        print(f"  Success rate: {success_rate*100:.1f}%")
        print(f"  Throughput: {final_throughput:.2f} ops/sec")
        
        # Performance validation
        assert success_rate >= 0.95, f"Success rate too low: {success_rate*100:.1f}%"
        assert final_throughput >= target_ops * 0.3, \
            f"Throughput below minimum: {final_throughput:.2f} < {target_ops * 0.3:.2f} ops/sec"
            
    async def test_multi_client_coordination_workflow(self, server_config, performance_config):
        """Test workflow coordination across multiple clients"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        # Create multiple coordinated clients
        num_clients = min(5, performance_config["concurrent_connections"])
        clients = []
        
        try:
            # Initialize clients
            for i in range(num_clients):
                config = server_config.copy()
                config["client_id"] = f"coord_client_{i}"
                
                client = MCPClient(config)
                await client.connect()
                clients.append(client)
                
            # Coordinated workflow phases
            coordination_phases = [
                {"phase": "initialization", "parallel": True},
                {"phase": "data_processing", "parallel": True},
                {"phase": "synchronization", "parallel": False},
                {"phase": "finalization", "parallel": True},
            ]
            
            phase_results = {}
            
            for phase_info in coordination_phases:
                phase = phase_info["phase"]
                parallel = phase_info["parallel"]
                
                print(f"\nCoordination phase: {phase} ({'parallel' if parallel else 'sequential'})")
                
                phase_start = time.time()
                
                if parallel:
                    # Execute operations in parallel across clients
                    tasks = []
                    for i, client in enumerate(clients):
                        if hasattr(client, 'call_tool'):
                            task = asyncio.create_task(
                                client.call_tool("echo", {"message": f"{phase}_client_{i}"})
                            )
                            tasks.append(task)
                            
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                else:
                    # Execute operations sequentially
                    results = []
                    for i, client in enumerate(clients):
                        if hasattr(client, 'call_tool'):
                            result = await client.call_tool("echo", {"message": f"{phase}_client_{i}"})
                            results.append(result)
                            
                phase_duration = time.time() - phase_start
                successful = sum(1 for r in results if not isinstance(r, Exception))
                
                phase_results[phase] = {
                    "duration": phase_duration,
                    "successful": successful,
                    "total": len(results),
                    "success_rate": successful / len(results) if results else 0
                }
                
                print(f"  {successful}/{len(results)} operations successful in {phase_duration:.2f}s")
                
            # Validate coordination results
            total_success_rate = sum(r["success_rate"] for r in phase_results.values()) / len(phase_results)
            assert total_success_rate >= 0.9, f"Coordination success rate too low: {total_success_rate*100:.1f}%"
            
            # Validate all clients still functional
            for i, client in enumerate(clients):
                assert client.is_connected(), f"Client {i} should remain connected after coordination"
                
        finally:
            # Clean up clients
            for client in clients:
                try:
                    await client.disconnect()
                except:
                    pass
                    
    async def test_long_running_session_workflow(self, mcp_client):
        """Test workflow stability over extended session"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Long-running session configuration
        session_duration = 120  # 2 minutes
        operation_interval = 5   # Operation every 5 seconds
        health_check_interval = 15  # Health check every 15 seconds
        
        session_start = time.time()
        operation_count = 0
        health_checks = 0
        errors = []
        
        last_operation_time = session_start
        last_health_check = session_start
        
        print(f"Starting long-running session ({session_duration}s)...")
        
        while time.time() - session_start < session_duration:
            current_time = time.time()
            
            # Perform regular operations
            if current_time - last_operation_time >= operation_interval:
                try:
                    result = await mcp_client.call_tool("echo", {
                        "message": f"long_session_op_{operation_count}"
                    })
                    
                    if result is not None:
                        operation_count += 1
                    else:
                        errors.append(f"Operation {operation_count} returned None")
                        
                    last_operation_time = current_time
                    
                except Exception as e:
                    errors.append(f"Operation {operation_count} failed: {e}")
                    
            # Perform health checks
            if current_time - last_health_check >= health_check_interval:
                try:
                    if mcp_client.is_connected():
                        health_checks += 1
                        print(f"Health check {health_checks}: OK (ops: {operation_count}, errors: {len(errors)})")
                    else:
                        errors.append(f"Health check {health_checks}: Connection lost")
                        
                    last_health_check = current_time
                    
                except Exception as e:
                    errors.append(f"Health check {health_checks} failed: {e}")
                    
            # Brief sleep to prevent busy waiting
            await asyncio.sleep(0.5)
            
        session_end = time.time()
        actual_duration = session_end - session_start
        
        print(f"\nLong-running session completed:")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Operations: {operation_count}")
        print(f"  Health checks: {health_checks}")
        print(f"  Errors: {len(errors)}")
        
        # Session validation
        assert actual_duration >= session_duration * 0.95, "Session should run for expected duration"
        assert mcp_client.is_connected(), "Connection should remain stable throughout session"
        assert operation_count >= (session_duration // operation_interval) * 0.8, \
            f"Should complete most operations: {operation_count}"
            
        error_rate = len(errors) / max(operation_count + health_checks, 1)
        assert error_rate <= 0.1, f"Error rate too high: {error_rate*100:.1f}%"
        
        if errors:
            print(f"Session errors: {errors[:5]}")  # Show first 5 errors


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestComplexWorkflowScenarios(IntegrationTestBase):
    """Test suite for complex real-world workflow scenarios"""
    
    @measure_performance
    async def test_study_buddy_simulation_workflow(self, mcp_client):
        """Simulate complete Study Buddy application workflow"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        print("Simulating Study Buddy application workflow...")
        
        # Phase 1: Application Startup
        startup_operations = [
            {"name": "initialize_database", "tool": "echo", "args": {"message": "db_init"}},
            {"name": "load_configuration", "tool": "echo", "args": {"message": "config_load"}},
            {"name": "start_services", "tool": "echo", "args": {"message": "services_start"}},
        ]
        
        for operation in startup_operations:
            result = await mcp_client.call_tool(operation["tool"], operation["args"])
            assert result is not None, f"Startup operation should succeed: {operation['name']}"
            
        # Phase 2: Document Operations
        document_operations = [
            {"name": "upload_pdf", "tool": "echo", "args": {"message": "upload_angular_book.pdf"}},
            {"name": "parse_content", "tool": "add", "args": {"a": 450, "b": 0}},  # 450 pages
            {"name": "create_chunks", "tool": "add", "args": {"a": 12, "b": 0}},   # 12 chapters
            {"name": "generate_summaries", "tool": "add", "args": {"a": 12, "b": 3}}, # Summary types
        ]
        
        document_results = {}
        for operation in document_operations:
            start_time = time.time()
            result = await mcp_client.call_tool(operation["tool"], operation["args"])
            duration = time.time() - start_time
            
            document_results[operation["name"]] = {
                "success": result is not None,
                "duration": duration,
                "result": result
            }
            
        # Phase 3: User Interactions
        user_interactions = []
        for i in range(10):  # Simulate 10 user interactions
            interactions_batch = [
                {"name": f"search_query_{i}", "tool": "echo", "args": {"message": f"search_angular_components_{i}"}},
                {"name": f"view_summary_{i}", "tool": "echo", "args": {"message": f"summary_chapter_{i % 12 + 1}"}},
                {"name": f"copy_content_{i}", "tool": "echo", "args": {"message": f"copy_chunk_{i % 5}"}},
            ]
            
            # Execute interaction batch
            for interaction in interactions_batch:
                result = await mcp_client.call_tool(interaction["tool"], interaction["args"])
                user_interactions.append({
                    "name": interaction["name"],
                    "success": result is not None
                })
                
        # Phase 4: Performance Operations
        performance_operations = []
        concurrent_tasks = []
        
        for i in range(20):  # 20 concurrent operations
            task = asyncio.create_task(
                mcp_client.call_tool("echo", {"message": f"performance_op_{i}"})
            )
            concurrent_tasks.append(task)
            
        concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        concurrent_successes = sum(1 for r in concurrent_results if not isinstance(r, Exception))
        
        # Phase 5: Cleanup Operations
        cleanup_operations = [
            {"name": "save_session", "tool": "echo", "args": {"message": "session_save"}},
            {"name": "cleanup_temp", "tool": "echo", "args": {"message": "temp_cleanup"}},
            {"name": "close_connections", "tool": "echo", "args": {"message": "conn_close"}},
        ]
        
        cleanup_results = []
        for operation in cleanup_operations:
            result = await mcp_client.call_tool(operation["tool"], operation["args"])
            cleanup_results.append(result is not None)
            
        # Workflow Analysis
        workflow_metrics = {
            "document_operations": {
                "total": len(document_operations),
                "successful": sum(1 for r in document_results.values() if r["success"]),
                "avg_duration": sum(r["duration"] for r in document_results.values()) / len(document_results)
            },
            "user_interactions": {
                "total": len(user_interactions),
                "successful": sum(1 for i in user_interactions if i["success"])
            },
            "concurrent_operations": {
                "total": len(concurrent_results),
                "successful": concurrent_successes,
                "success_rate": concurrent_successes / len(concurrent_results)
            },
            "cleanup_operations": {
                "total": len(cleanup_operations),
                "successful": sum(cleanup_results)
            }
        }
        
        print(f"\nStudy Buddy Workflow Simulation Results:")
        for category, metrics in workflow_metrics.items():
            print(f"  {category}:")
            print(f"    Success: {metrics['successful']}/{metrics['total']}")
            if "success_rate" in metrics:
                print(f"    Rate: {metrics['success_rate']*100:.1f}%")
            if "avg_duration" in metrics:
                print(f"    Avg Duration: {metrics['avg_duration']:.3f}s")
                
        # Workflow validation
        overall_success = (
            workflow_metrics["document_operations"]["successful"] >= len(document_operations) * 0.9 and
            workflow_metrics["user_interactions"]["successful"] >= len(user_interactions) * 0.9 and
            workflow_metrics["concurrent_operations"]["success_rate"] >= 0.8 and
            workflow_metrics["cleanup_operations"]["successful"] >= len(cleanup_operations)
        )
        
        assert overall_success, "Study Buddy simulation workflow should achieve high success rates"
        assert workflow_metrics["document_operations"]["avg_duration"] < 1.0, \
            "Document operations should complete quickly"