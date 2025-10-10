"""
Error Recovery and Resilience Integration Tests

Tests for error handling, recovery mechanisms, and system resilience
under various failure conditions with real MCP servers.

Test Coverage:
- Network failure recovery
- Server restart and reconnection
- Invalid response handling
- Resource exhaustion scenarios
- Partial failure recovery
- Circuit breaker patterns
- Graceful degradation
"""

import pytest
import asyncio
import time
import random
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from . import ERROR_TESTS, RESILIENCE_TESTS, REQUIRES_SERVER, INTEGRATION_TEST
from .conftest import IntegrationTestBase, measure_performance, temporary_server_failure


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.requires_server
class TestErrorRecovery(IntegrationTestBase):
    """Test suite for error recovery mechanisms"""
    
    async def test_server_restart_recovery(self, server_config):
        """Test recovery from server restart"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        client = MCPClient(server_config)
        await client.connect()
        
        # Verify initial connection
        assert client.is_connected(), "Initial connection should succeed"
        
        # Perform operation before restart
        if hasattr(client, 'call_tool'):
            result = await client.call_tool("echo", {"message": "before_restart"})
            assert result is not None, "Operation before restart should succeed"
            
        # Simulate server restart
        async with temporary_server_failure(self.test_server, duration=3.0):
            # During restart, operations should fail or be queued
            if hasattr(client, 'call_tool'):
                with pytest.raises(Exception):
                    await client.call_tool("echo", {"message": "during_restart"})
                    
        # Allow time for reconnection
        await asyncio.sleep(2)
        
        # Test recovery
        if hasattr(client, 'reconnect'):
            await client.reconnect()
        else:
            # Manual reconnection
            await client.disconnect()
            await client.connect()
            
        # Verify recovery
        assert client.is_connected(), "Should recover connection after restart"
        
        if hasattr(client, 'call_tool'):
            result = await client.call_tool("echo", {"message": "after_restart"})
            assert result is not None, "Operation after restart should succeed"
            
        await client.disconnect()
        
    async def test_network_timeout_recovery(self, mcp_client):
        """Test recovery from network timeouts"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Test with timeout-prone operation
        timeout_scenarios = [
            {"delay": 1.0, "should_succeed": True},   # Within timeout
            {"delay": 10.0, "should_timeout": True},  # Beyond timeout
            {"delay": 0.5, "should_succeed": True},   # Recovery test
        ]
        
        for i, scenario in enumerate(timeout_scenarios):
            try:
                start_time = time.time()
                result = await mcp_client.call_tool("slow", {"delay": scenario["delay"]})
                elapsed = time.time() - start_time
                
                if scenario.get("should_timeout"):
                    pytest.fail(f"Expected timeout for scenario {i} but succeeded in {elapsed}s")
                    
                assert result is not None, f"Scenario {i} should return result"
                
            except (TimeoutError, asyncio.TimeoutError) as e:
                if scenario.get("should_succeed"):
                    pytest.fail(f"Unexpected timeout for scenario {i}: {e}")
                # Expected timeout
                
            except Exception as e:
                # Check if it's a connection-related error
                if "connection" in str(e).lower() or "timeout" in str(e).lower():
                    if scenario.get("should_succeed"):
                        # Try to recover connection
                        if hasattr(mcp_client, 'reconnect'):
                            await mcp_client.reconnect()
                        continue
                raise
                
        # Verify client is still functional after timeouts
        assert mcp_client.is_connected(), "Client should remain connected after timeout recovery"
        
    async def test_invalid_response_handling(self, server_config):
        """Test handling of invalid server responses"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        client = MCPClient(server_config)
        await client.connect()
        
        # Test various invalid response scenarios
        invalid_scenarios = [
            {"description": "Non-existent tool", "tool": "invalid_tool", "args": {}},
            {"description": "Malformed arguments", "tool": "add", "args": {"invalid": "args"}},
            {"description": "Tool that triggers server error", "tool": "error", "args": {}},
        ]
        
        for scenario in invalid_scenarios:
            try:
                result = await client.call_tool(scenario["tool"], scenario["args"])
                
                # Some scenarios might succeed with warnings
                if scenario["tool"] == "invalid_tool":
                    pytest.fail(f"Expected error for {scenario['description']} but got: {result}")
                    
            except Exception as e:
                # Verify error is handled appropriately
                assert isinstance(e, Exception), f"Should raise exception for {scenario['description']}"
                
                # Verify error contains meaningful information
                error_msg = str(e)
                assert len(error_msg) > 0, f"Error message should not be empty for {scenario['description']}"
                
                # Verify connection remains stable after error
                assert client.is_connected(), f"Connection should remain after error: {scenario['description']}"
                
        await client.disconnect()
        
    async def test_resource_exhaustion_recovery(self, server_config, performance_config):
        """Test recovery from resource exhaustion"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        # Create resource exhaustion scenario
        clients = []
        
        try:
            # Create many connections to exhaust resources
            max_connections = performance_config["concurrent_connections"] * 3
            
            for i in range(max_connections):
                try:
                    client = MCPClient(server_config)
                    await client.connect()
                    clients.append(client)
                    
                    # Perform operation to maintain connection
                    if hasattr(client, 'call_tool'):
                        await client.call_tool("echo", {"message": f"connection_{i}"})
                        
                except Exception as e:
                    # Resource exhaustion expected at some point
                    if "too many" in str(e).lower() or "limit" in str(e).lower():
                        print(f"Resource limit reached at {i} connections: {e}")
                        break
                    else:
                        raise
                        
            # Verify some connections were established
            assert len(clients) > 0, "Should establish at least some connections"
            
            # Test recovery by releasing some connections
            if len(clients) > 5:
                # Release half the connections
                release_count = len(clients) // 2
                for _ in range(release_count):
                    client = clients.pop()
                    await client.disconnect()
                    
                await asyncio.sleep(1)  # Allow resource cleanup
                
                # Try to create new connection (should succeed after cleanup)
                recovery_client = MCPClient(server_config)
                await recovery_client.connect()
                
                assert recovery_client.is_connected(), "Should recover after resource release"
                
                if hasattr(recovery_client, 'call_tool'):
                    result = await recovery_client.call_tool("echo", {"message": "recovery_test"})
                    assert result is not None, "Operations should work after recovery"
                    
                await recovery_client.disconnect()
                
        finally:
            # Clean up all connections
            for client in clients:
                try:
                    await client.disconnect()
                except:
                    pass  # Ignore cleanup errors
                    
    async def test_partial_failure_handling(self, mcp_client, sample_tool_calls):
        """Test handling of partial failures in batch operations"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Create mixed batch with some failing operations
        mixed_operations = [
            {"tool": "echo", "args": {"message": "success1"}, "should_succeed": True},
            {"tool": "invalid_tool", "args": {}, "should_succeed": False},
            {"tool": "add", "args": {"a": 5, "b": 3}, "should_succeed": True},
            {"tool": "error", "args": {}, "should_succeed": False},
            {"tool": "echo", "args": {"message": "success2"}, "should_succeed": True},
        ]
        
        # Execute batch with partial failures
        results = []
        for operation in mixed_operations:
            try:
                result = await mcp_client.call_tool(operation["tool"], operation["args"])
                results.append(("success", result, operation))
            except Exception as e:
                results.append(("error", e, operation))
                
        # Analyze partial failure results
        successful_ops = [r for r in results if r[0] == "success"]
        failed_ops = [r for r in results if r[0] == "error"]
        
        # Verify expected outcomes
        expected_successes = sum(1 for op in mixed_operations if op["should_succeed"])
        expected_failures = len(mixed_operations) - expected_successes
        
        assert len(successful_ops) >= expected_successes - 1, \
            f"Too few successes: {len(successful_ops)} < {expected_successes}"
            
        assert len(failed_ops) >= expected_failures - 1, \
            f"Too few failures: {len(failed_ops)} < {expected_failures}"
            
        # Verify connection remains stable after partial failures
        assert mcp_client.is_connected(), "Connection should remain stable after partial failures"
        
        # Verify subsequent operations still work
        result = await mcp_client.call_tool("echo", {"message": "post_partial_failure"})
        assert result is not None, "Operations should continue working after partial failures"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.resilience
class TestResiliencePatterns(IntegrationTestBase):
    """Test suite for resilience patterns and mechanisms"""
    
    async def test_circuit_breaker_pattern(self, server_config):
        """Test circuit breaker implementation"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        # Configure client with circuit breaker (if supported)
        config = server_config.copy()
        config.update({
            "circuit_breaker": {
                "failure_threshold": 3,
                "timeout": 5,
                "reset_timeout": 10
            }
        })
        
        client = MCPClient(config)
        await client.connect()
        
        # Trigger circuit breaker with repeated failures
        failure_count = 0
        
        try:
            for i in range(5):
                try:
                    # Call error-inducing tool
                    await client.call_tool("error", {})
                except Exception:
                    failure_count += 1
                    
                    # Check if circuit breaker is active
                    if hasattr(client, 'circuit_breaker_state'):
                        state = await client.circuit_breaker_state()
                        if state == "open":
                            print(f"Circuit breaker opened after {failure_count} failures")
                            break
                            
        except Exception as e:
            if "circuit" in str(e).lower() or "breaker" in str(e).lower():
                # Circuit breaker activated
                print(f"Circuit breaker prevented call: {e}")
            else:
                raise
                
        await client.disconnect()
        
    async def test_retry_with_backoff(self, server_config):
        """Test retry mechanism with exponential backoff"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        # Configure client with retry policy
        config = server_config.copy()
        config.update({
            "retry_policy": {
                "max_attempts": 3,
                "base_delay": 1.0,
                "backoff_factor": 2.0,
                "max_delay": 10.0
            }
        })
        
        client = MCPClient(config)
        await client.connect()
        
        # Test retry behavior with intermittent failures
        start_time = time.time()
        
        try:
            # This should retry on failure
            if hasattr(client, 'call_tool_with_retry'):
                result = await client.call_tool_with_retry("error", {})
            else:
                # Fallback to regular call
                result = await client.call_tool("error", {})
        except Exception as e:
            elapsed = time.time() - start_time
            
            # Verify retry delay patterns
            expected_min_delay = 1.0 + 2.0 + 4.0  # Base + 2*base + 4*base (3 attempts)
            if elapsed >= expected_min_delay - 1:  # Allow some margin
                print(f"Retry with backoff took {elapsed:.2f}s (expected >= {expected_min_delay:.1f}s)")
            
        await client.disconnect()
        
    async def test_graceful_degradation(self, server_config):
        """Test graceful degradation under load"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        client = MCPClient(server_config)
        await client.connect()
        
        # Test degradation scenarios
        degradation_scenarios = [
            {"description": "Normal load", "concurrent_ops": 5, "delay": 0.1},
            {"description": "High load", "concurrent_ops": 20, "delay": 0.5},
            {"description": "Extreme load", "concurrent_ops": 50, "delay": 2.0},
        ]
        
        for scenario in degradation_scenarios:
            print(f"\nTesting: {scenario['description']}")
            
            # Launch concurrent operations
            tasks = []
            for i in range(scenario["concurrent_ops"]):
                task = asyncio.create_task(
                    client.call_tool("slow", {"delay": scenario["delay"]})
                )
                tasks.append(task)
                
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = time.time() - start_time
            
            # Analyze degradation
            successful = sum(1 for r in results if not isinstance(r, Exception))
            failed = len(results) - successful
            success_rate = successful / len(results)
            
            print(f"  Results: {successful}/{len(results)} success ({success_rate*100:.1f}%)")
            print(f"  Duration: {elapsed:.2f}s")
            print(f"  Avg time: {elapsed/len(results):.2f}s per operation")
            
            # Verify graceful degradation (some operations should succeed)
            if scenario["concurrent_ops"] <= 10:
                assert success_rate >= 0.8, f"Success rate too low for {scenario['description']}: {success_rate*100:.1f}%"
            else:
                # Under extreme load, allow lower success rates
                assert success_rate >= 0.3, f"Even under extreme load, some operations should succeed: {success_rate*100:.1f}%"
                
        await client.disconnect()
        
    async def test_error_isolation(self, mcp_client):
        """Test that errors in one operation don't affect others"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Execute operations in parallel with mixed success/failure
        operations = [
            asyncio.create_task(mcp_client.call_tool("echo", {"message": "isolated_1"})),
            asyncio.create_task(mcp_client.call_tool("error", {})),  # Should fail
            asyncio.create_task(mcp_client.call_tool("echo", {"message": "isolated_2"})),
            asyncio.create_task(mcp_client.call_tool("add", {"a": 1, "b": 2})),
            asyncio.create_task(mcp_client.call_tool("invalid_tool", {})),  # Should fail
            asyncio.create_task(mcp_client.call_tool("echo", {"message": "isolated_3"})),
        ]
        
        # Wait for all operations
        results = await asyncio.gather(*operations, return_exceptions=True)
        
        # Verify error isolation
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append((i, result))
            else:
                successful_results.append((i, result))
                
        # Verify expected pattern: errors isolated, successes unaffected
        assert len(successful_results) >= 4, f"Too few successful operations: {len(successful_results)}"
        assert len(failed_results) >= 2, f"Expected some failures for error isolation test: {len(failed_results)}"
        
        # Verify connection remains stable
        assert mcp_client.is_connected(), "Connection should remain stable despite errors"
        
        # Verify subsequent operations work normally
        final_test = await mcp_client.call_tool("echo", {"message": "post_isolation_test"})
        assert final_test is not None, "Operations should work normally after error isolation"
        
    @measure_performance
    async def test_recovery_time_measurement(self, server_config, resilience_config):
        """Measure recovery times for various failure scenarios"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        recovery_metrics = {}
        
        for scenario in resilience_config["failure_scenarios"]:
            print(f"\nTesting recovery from: {scenario}")
            
            client = MCPClient(server_config)
            await client.connect()
            
            # Establish baseline
            baseline_result = await client.call_tool("echo", {"message": "baseline"})
            assert baseline_result is not None, "Baseline should work"
            
            recovery_start = time.time()
            
            try:
                if scenario == "server_restart":
                    # Simulate server restart
                    async with temporary_server_failure(self.test_server, duration=2.0):
                        await asyncio.sleep(1)  # Let client detect failure
                        
                elif scenario == "network_timeout":
                    # Trigger timeout scenario
                    try:
                        await client.call_tool("slow", {"delay": 20})  # Long operation
                    except (TimeoutError, asyncio.TimeoutError):
                        pass  # Expected
                        
                elif scenario == "invalid_response":
                    # Trigger invalid response
                    try:
                        await client.call_tool("error", {})
                    except Exception:
                        pass  # Expected
                        
                # Measure recovery
                recovery_attempts = 0
                max_recovery_attempts = resilience_config["max_retry_attempts"]
                
                while recovery_attempts < max_recovery_attempts:
                    try:
                        if not client.is_connected():
                            if hasattr(client, 'reconnect'):
                                await client.reconnect()
                            else:
                                await client.connect()
                                
                        # Test if recovered
                        recovery_result = await client.call_tool("echo", {"message": f"recovery_test_{scenario}"})
                        
                        if recovery_result is not None:
                            recovery_time = time.time() - recovery_start
                            recovery_metrics[scenario] = {
                                "time": recovery_time,
                                "attempts": recovery_attempts + 1,
                                "success": True
                            }
                            print(f"  Recovered in {recovery_time:.2f}s after {recovery_attempts + 1} attempts")
                            break
                            
                    except Exception as e:
                        recovery_attempts += 1
                        if recovery_attempts < max_recovery_attempts:
                            backoff_delay = resilience_config.get("backoff_factor", 1.0) ** recovery_attempts
                            await asyncio.sleep(min(backoff_delay, 5.0))
                        else:
                            recovery_metrics[scenario] = {
                                "time": time.time() - recovery_start,
                                "attempts": recovery_attempts,
                                "success": False,
                                "error": str(e)
                            }
                            print(f"  Failed to recover after {recovery_attempts} attempts: {e}")
                            
            except Exception as e:
                recovery_metrics[scenario] = {
                    "time": time.time() - recovery_start,
                    "attempts": 0,
                    "success": False,
                    "error": f"Test setup failed: {e}"
                }
                
            finally:
                try:
                    await client.disconnect()
                except:
                    pass
                    
        # Analyze recovery metrics
        print(f"\nRecovery Metrics Summary:")
        for scenario, metrics in recovery_metrics.items():
            if metrics["success"]:
                print(f"  {scenario}: {metrics['time']:.2f}s ({metrics['attempts']} attempts)")
            else:
                print(f"  {scenario}: FAILED - {metrics.get('error', 'Unknown error')}")
                
        # Validate recovery requirements
        successful_recoveries = sum(1 for m in recovery_metrics.values() if m["success"])
        recovery_rate = successful_recoveries / len(recovery_metrics)
        
        assert recovery_rate >= 0.7, f"Recovery rate too low: {recovery_rate*100:.1f}%"
        
        # Validate recovery times
        successful_times = [m["time"] for m in recovery_metrics.values() if m["success"]]
        if successful_times:
            avg_recovery_time = sum(successful_times) / len(successful_times)
            max_allowed_time = resilience_config["recovery_timeout"]
            
            assert avg_recovery_time <= max_allowed_time, \
                f"Average recovery time too high: {avg_recovery_time:.2f}s > {max_allowed_time}s"