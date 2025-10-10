"""
Tool Invocation Workflow Integration Tests

Tests for MCP tool discovery, invocation, and result handling
with real MCP servers.

Test Coverage:
- Tool discovery and listing
- Tool invocation with various parameter types
- Result processing and validation
- Concurrent tool invocations
- Tool streaming and long-running operations
- Error handling and validation
"""

import pytest
import asyncio
import time
import json
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

from . import TOOL_TESTS, REQUIRES_SERVER, INTEGRATION_TEST
from .conftest import IntegrationTestBase, measure_performance


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.requires_server  
class TestToolInvocation(IntegrationTestBase):
    """Test suite for tool invocation workflows"""
    
    async def test_tool_discovery(self, mcp_client):
        """Test discovering available tools from server"""
        if not hasattr(mcp_client, 'list_tools'):
            pytest.skip("Tool listing not yet implemented")
            
        # Get available tools
        tools = await mcp_client.list_tools()
        
        # Verify tools response format
        assert isinstance(tools, (list, dict)), "Tools should be list or dict"
        
        if isinstance(tools, list):
            assert len(tools) > 0, "Server should provide at least one tool"
            for tool in tools:
                assert "name" in tool, "Tool should have name"
                assert isinstance(tool["name"], str), "Tool name should be string"
        else:
            assert len(tools) > 0, "Tools dict should not be empty"
            
    async def test_basic_tool_invocation(self, mcp_client):
        """Test basic tool invocation with simple parameters"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Test echo tool (should be available on test server)
        result = await mcp_client.call_tool("echo", {"message": "test message"})
        
        # Verify result structure
        assert result is not None, "Tool should return result"
        assert isinstance(result, dict), "Result should be dict"
        
        if "result" in result:
            assert result["result"] == "test message", "Echo should return input message"
        elif "content" in result:
            assert "test message" in str(result["content"]), "Result should contain input message"
            
    async def test_mathematical_tool_invocation(self, mcp_client):
        """Test tool invocation with numerical parameters"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Test add tool
        result = await mcp_client.call_tool("add", {"a": 5, "b": 3})
        
        # Verify mathematical result
        assert result is not None, "Add tool should return result"
        
        if isinstance(result, dict) and "result" in result:
            assert result["result"] == 8, "5 + 3 should equal 8"
        elif isinstance(result, (int, float)):
            assert result == 8, "Direct result should equal 8"
            
    async def test_concurrent_tool_invocations(self, mcp_client, sample_tool_calls):
        """Test multiple concurrent tool invocations"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Launch concurrent tool calls
        tasks = []
        for tool_call in sample_tool_calls:
            task = asyncio.create_task(
                mcp_client.call_tool(tool_call["tool"], tool_call["args"])
            )
            tasks.append((task, tool_call))
            
        # Wait for all tasks to complete
        start_time = time.time()
        results = await asyncio.gather(*[task for task, _ in tasks], return_exceptions=True)
        elapsed_time = time.time() - start_time
        
        # Verify all calls completed within reasonable time
        assert elapsed_time < 10.0, f"Concurrent calls took too long: {elapsed_time}s"
        
        # Verify results
        for i, (result, (_, tool_call)) in enumerate(zip(results, tasks)):
            if isinstance(result, Exception):
                # Some tools might not be available, skip those
                if "not found" in str(result) or "unknown" in str(result).lower():
                    continue
                pytest.fail(f"Tool call {i} failed: {result}")
            else:
                assert result is not None, f"Tool call {i} should return result"
                
    @measure_performance
    async def test_tool_invocation_performance(self, mcp_client, performance_config):
        """Test tool invocation performance metrics"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Measure single invocation performance
        invocation_times = []
        
        for i in range(20):
            start_time = time.time()
            result = await mcp_client.call_tool("echo", {"message": f"performance_test_{i}"})
            elapsed = time.time() - start_time
            invocation_times.append(elapsed)
            
            # Verify result
            assert result is not None, f"Invocation {i} should succeed"
            
        # Calculate performance metrics
        avg_time = sum(invocation_times) / len(invocation_times)
        max_time = max(invocation_times)
        min_time = min(invocation_times)
        
        print(f"\nTool Invocation Performance:")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  Min: {min_time*1000:.2f}ms") 
        print(f"  Max: {max_time*1000:.2f}ms")
        
        # Verify performance requirements
        assert avg_time < 0.1, f"Average invocation time too high: {avg_time*1000:.2f}ms"
        assert max_time < 0.5, f"Max invocation time too high: {max_time*1000:.2f}ms"
        
    async def test_tool_parameter_validation(self, mcp_client):
        """Test tool parameter validation and error handling"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Test invalid parameters
        test_cases = [
            # Missing required parameter
            {"tool": "add", "args": {"a": 5}, "expect_error": True},
            # Invalid parameter type
            {"tool": "add", "args": {"a": "not_a_number", "b": 3}, "expect_error": True},
            # Extra parameters (should be ignored or cause error)
            {"tool": "echo", "args": {"message": "test", "extra": "param"}, "expect_error": False},
            # Empty parameters for parameter-required tool
            {"tool": "add", "args": {}, "expect_error": True}
        ]
        
        for test_case in test_cases:
            try:
                result = await mcp_client.call_tool(test_case["tool"], test_case["args"])
                
                if test_case["expect_error"]:
                    pytest.fail(f"Expected error for {test_case} but got result: {result}")
                else:
                    assert result is not None, f"Valid call should return result: {test_case}"
                    
            except Exception as e:
                if not test_case["expect_error"]:
                    pytest.fail(f"Unexpected error for {test_case}: {e}")
                # Expected error, continue
                
    async def test_nonexistent_tool_handling(self, mcp_client):
        """Test calling non-existent tools"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Try to call non-existent tool
        with pytest.raises(Exception) as exc_info:
            await mcp_client.call_tool("nonexistent_tool", {})
            
        # Verify appropriate error type
        error_msg = str(exc_info.value).lower()
        assert any(phrase in error_msg for phrase in ["not found", "unknown", "invalid", "does not exist"]), \
            f"Error should indicate tool not found: {exc_info.value}"
            
    async def test_tool_timeout_handling(self, mcp_client):
        """Test timeout handling for slow tools"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Test with configurable timeout
        original_timeout = getattr(mcp_client, 'timeout', None)
        
        try:
            # Set short timeout
            if hasattr(mcp_client, 'set_timeout'):
                await mcp_client.set_timeout(2.0)  # 2 second timeout
                
            # Call slow tool that takes longer than timeout
            start_time = time.time()
            
            with pytest.raises((TimeoutError, asyncio.TimeoutError)) as exc_info:
                await mcp_client.call_tool("slow", {"delay": 5.0})  # 5 second delay
                
            elapsed = time.time() - start_time
            
            # Verify timeout was respected
            assert elapsed < 3.0, f"Timeout took too long: {elapsed}s"
            
        finally:
            # Restore original timeout
            if original_timeout and hasattr(mcp_client, 'set_timeout'):
                await mcp_client.set_timeout(original_timeout)
                
    async def test_large_parameter_handling(self, mcp_client):
        """Test handling of large parameters"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Create large message (1MB)
        large_message = "x" * (1024 * 1024)
        
        try:
            result = await mcp_client.call_tool("echo", {"message": large_message})
            
            # Verify large data handling
            assert result is not None, "Should handle large parameters"
            
            # Verify result contains expected data (might be truncated)
            if isinstance(result, dict) and "result" in result:
                returned_message = result["result"]
                assert isinstance(returned_message, str), "Result should be string"
                assert len(returned_message) > 0, "Result should not be empty"
                
        except Exception as e:
            # Large parameters might not be supported
            error_msg = str(e).lower()
            if any(phrase in error_msg for phrase in ["too large", "size limit", "payload"]):
                pytest.skip(f"Large parameters not supported: {e}")
            else:
                raise  # Unexpected error
                
    async def test_special_character_handling(self, mcp_client):
        """Test handling of special characters in parameters"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Test various special characters
        special_messages = [
            "Hello, 世界!",  # Unicode
            '{"json": "value"}',  # JSON-like content
            "<xml>content</xml>",  # XML-like content
            "Line 1\nLine 2\tTabbed",  # Newlines and tabs
            "Quotes 'single' \"double\"",  # Quotes
            "Symbols !@#$%^&*()",  # Special symbols
            "",  # Empty string
            "   ",  # Whitespace only
        ]
        
        for message in special_messages:
            try:
                result = await mcp_client.call_tool("echo", {"message": message})
                assert result is not None, f"Should handle special characters: {message!r}"
                
                # Verify message integrity
                if isinstance(result, dict) and "result" in result:
                    returned = result["result"]
                    assert returned == message, f"Message should be preserved: {message!r} != {returned!r}"
                    
            except Exception as e:
                pytest.fail(f"Failed to handle special characters {message!r}: {e}")


@pytest.mark.asyncio
@pytest.mark.integration  
@pytest.mark.load
class TestToolWorkflowPerformance(IntegrationTestBase):
    """Performance-focused tool workflow tests"""
    
    @measure_performance
    async def test_bulk_tool_invocations(self, mcp_client, performance_config):
        """Test performance with bulk tool invocations"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        num_operations = performance_config["operations_per_connection"]
        
        # Prepare bulk operations
        operations = []
        for i in range(num_operations):
            operations.append(("echo", {"message": f"bulk_test_{i}"}))
            
        # Execute bulk operations
        start_time = time.time()
        
        tasks = []
        for tool, args in operations:
            task = asyncio.create_task(mcp_client.call_tool(tool, args))
            tasks.append(task)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed_time = time.time() - start_time
        
        # Analyze results
        successful_ops = sum(1 for r in results if not isinstance(r, Exception))
        failed_ops = len(results) - successful_ops
        ops_per_second = successful_ops / elapsed_time
        
        print(f"\nBulk Operations Performance:")
        print(f"  Total ops: {len(operations)}")
        print(f"  Successful: {successful_ops}")
        print(f"  Failed: {failed_ops}")
        print(f"  Duration: {elapsed_time:.2f}s")
        print(f"  Ops/sec: {ops_per_second:.2f}")
        
        # Performance requirements
        assert successful_ops >= num_operations * 0.95, f"Too many failures: {failed_ops}/{len(operations)}"
        assert ops_per_second >= performance_config["target_ops_per_second"] * 0.3, \
            f"Performance too low: {ops_per_second} ops/sec"
            
    @measure_performance  
    async def test_mixed_workload_performance(self, mcp_client, sample_tool_calls, performance_config):
        """Test performance with mixed tool workloads"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Create mixed workload pattern
        workload = []
        for _ in range(performance_config["operations_per_connection"] // len(sample_tool_calls)):
            workload.extend(sample_tool_calls)
            
        # Execute mixed workload
        start_time = time.time()
        
        results = []
        for tool_call in workload:
            try:
                result = await mcp_client.call_tool(tool_call["tool"], tool_call["args"])
                results.append(("success", result))
            except Exception as e:
                results.append(("error", e))
                
        elapsed_time = time.time() - start_time
        
        # Analyze mixed workload performance
        successful = sum(1 for status, _ in results if status == "success")
        error_rate = (len(results) - successful) / len(results)
        avg_time_per_op = elapsed_time / len(results)
        
        print(f"\nMixed Workload Performance:")
        print(f"  Operations: {len(results)}")
        print(f"  Success rate: {(successful/len(results))*100:.1f}%")
        print(f"  Error rate: {error_rate*100:.1f}%")
        print(f"  Avg time/op: {avg_time_per_op*1000:.2f}ms")
        
        # Performance validation
        assert error_rate < 0.1, f"Error rate too high: {error_rate*100:.1f}%"
        assert avg_time_per_op < 0.2, f"Average operation time too high: {avg_time_per_op*1000:.2f}ms"
        
    async def test_stress_tool_invocation(self, mcp_client, performance_config):
        """Test tool invocation under stress conditions"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Stress test configuration  
        concurrent_batches = 5
        ops_per_batch = performance_config["operations_per_connection"] // concurrent_batches
        
        async def run_batch(batch_id: int) -> Dict[str, Any]:
            """Run a batch of operations"""
            batch_results = []
            start_time = time.time()
            
            for i in range(ops_per_batch):
                try:
                    result = await mcp_client.call_tool("echo", {
                        "message": f"stress_batch_{batch_id}_op_{i}"
                    })
                    batch_results.append(("success", result))
                except Exception as e:
                    batch_results.append(("error", e))
                    
            elapsed = time.time() - start_time
            
            return {
                "batch_id": batch_id,
                "operations": len(batch_results),
                "successful": sum(1 for status, _ in batch_results if status == "success"),
                "duration": elapsed,
                "results": batch_results
            }
            
        # Run concurrent batches
        batch_tasks = [run_batch(i) for i in range(concurrent_batches)]
        batch_results = await asyncio.gather(*batch_tasks)
        
        # Aggregate stress test results
        total_ops = sum(batch["operations"] for batch in batch_results)
        total_successful = sum(batch["successful"] for batch in batch_results)
        total_duration = max(batch["duration"] for batch in batch_results)
        
        success_rate = total_successful / total_ops
        throughput = total_successful / total_duration
        
        print(f"\nStress Test Results:")
        print(f"  Concurrent batches: {concurrent_batches}")
        print(f"  Total operations: {total_ops}")
        print(f"  Success rate: {success_rate*100:.1f}%")
        print(f"  Total duration: {total_duration:.2f}s")
        print(f"  Throughput: {throughput:.2f} ops/sec")
        
        # Stress test validation
        assert success_rate >= 0.9, f"Success rate under stress too low: {success_rate*100:.1f}%"
        assert throughput >= performance_config["target_ops_per_second"] * 0.2, \
            f"Throughput under stress too low: {throughput:.2f} ops/sec"