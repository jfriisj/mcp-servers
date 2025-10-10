"""
Performance and Load Testing Integration Tests

Tests for performance characteristics and load handling
of the MCP integration layer under various conditions.

Test Coverage:
- Baseline performance measurements
- Load testing with increasing concurrent operations
- Memory usage and resource consumption testing
- Latency and throughput optimization validation
- Performance regression detection
- Scalability limit identification
"""

import pytest
import asyncio
import time
import psutil
import statistics
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import gc

from . import PERFORMANCE_TESTS, LOAD_TEST, REQUIRES_SERVER, INTEGRATION_TEST
from .conftest import IntegrationTestBase, measure_performance


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.load  
@pytest.mark.requires_server
class TestPerformanceBaseline(IntegrationTestBase):
    """Baseline performance measurement tests"""
    
    @measure_performance
    async def test_single_operation_latency(self, mcp_client):
        """Measure baseline single operation latency"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Warm-up operations (JIT, connection establishment, etc.)
        for _ in range(5):
            await mcp_client.call_tool("echo", {"message": "warmup"})
            
        # Measure baseline latency
        latencies = []
        
        for i in range(100):  # 100 samples for statistical validity
            start_time = time.perf_counter()
            result = await mcp_client.call_tool("echo", {"message": f"latency_test_{i}"})
            end_time = time.perf_counter()
            
            assert result is not None, f"Operation {i} should succeed"
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            latencies.append(latency)
            
        # Calculate statistics
        mean_latency = statistics.mean(latencies)
        median_latency = statistics.median(latencies)
        p95_latency = sorted(latencies)[int(0.95 * len(latencies))]
        p99_latency = sorted(latencies)[int(0.99 * len(latencies))]
        std_dev = statistics.stdev(latencies)
        
        print(f"\nSingle Operation Latency Baseline:")
        print(f"  Mean: {mean_latency:.2f}ms")
        print(f"  Median: {median_latency:.2f}ms")
        print(f"  P95: {p95_latency:.2f}ms")
        print(f"  P99: {p99_latency:.2f}ms")
        print(f"  Std Dev: {std_dev:.2f}ms")
        
        # Performance requirements validation
        assert mean_latency < 100, f"Mean latency too high: {mean_latency:.2f}ms"
        assert p95_latency < 200, f"P95 latency too high: {p95_latency:.2f}ms"
        assert p99_latency < 500, f"P99 latency too high: {p99_latency:.2f}ms"
        
        return {
            "mean_latency": mean_latency,
            "p95_latency": p95_latency,
            "p99_latency": p99_latency,
            "std_dev": std_dev
        }
        
    @measure_performance
    async def test_throughput_baseline(self, mcp_client, performance_config):
        """Measure baseline throughput capacity"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Throughput test configuration
        test_duration = 30  # seconds
        batch_size = 10
        target_ops = performance_config["target_ops_per_second"]
        
        total_operations = 0
        successful_operations = 0
        start_time = time.time()
        
        throughput_samples = []
        last_sample_time = start_time
        last_sample_ops = 0
        
        while time.time() - start_time < test_duration:
            # Execute batch of operations
            batch_tasks = []
            
            for i in range(batch_size):
                task = asyncio.create_task(
                    mcp_client.call_tool("echo", {"message": f"throughput_{total_operations + i}"})
                )
                batch_tasks.append(task)
                
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Update counters
            total_operations += len(batch_results)
            batch_successful = sum(1 for r in batch_results if not isinstance(r, Exception))
            successful_operations += batch_successful
            
            # Sample throughput every 5 seconds
            current_time = time.time()
            if current_time - last_sample_time >= 5.0:
                sample_duration = current_time - last_sample_time
                sample_ops = successful_operations - last_sample_ops
                sample_throughput = sample_ops / sample_duration
                
                throughput_samples.append(sample_throughput)
                
                print(f"Throughput sample: {sample_throughput:.1f} ops/sec")
                
                last_sample_time = current_time
                last_sample_ops = successful_operations
                
        # Final throughput calculation
        total_duration = time.time() - start_time
        overall_throughput = successful_operations / total_duration
        success_rate = successful_operations / total_operations
        
        # Throughput statistics
        if throughput_samples:
            mean_throughput = statistics.mean(throughput_samples)
            min_throughput = min(throughput_samples)
            max_throughput = max(throughput_samples)
            throughput_std_dev = statistics.stdev(throughput_samples) if len(throughput_samples) > 1 else 0
        else:
            mean_throughput = overall_throughput
            min_throughput = max_throughput = overall_throughput
            throughput_std_dev = 0
            
        print(f"\nThroughput Baseline Results:")
        print(f"  Overall: {overall_throughput:.1f} ops/sec")
        print(f"  Mean sample: {mean_throughput:.1f} ops/sec")
        print(f"  Min sample: {min_throughput:.1f} ops/sec")
        print(f"  Max sample: {max_throughput:.1f} ops/sec")
        print(f"  Success rate: {success_rate*100:.1f}%")
        print(f"  Std dev: {throughput_std_dev:.1f}")
        
        # Performance validation
        assert success_rate >= 0.98, f"Success rate too low: {success_rate*100:.1f}%"
        assert overall_throughput >= target_ops * 0.3, \
            f"Throughput below minimum: {overall_throughput:.1f} < {target_ops * 0.3:.1f} ops/sec"
            
        return {
            "overall_throughput": overall_throughput,
            "mean_throughput": mean_throughput,
            "success_rate": success_rate,
            "std_dev": throughput_std_dev
        }
        
    @measure_performance
    async def test_memory_usage_baseline(self, mcp_client):
        """Measure baseline memory usage patterns"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        process = psutil.Process()
        
        # Baseline memory measurement
        gc.collect()  # Force garbage collection
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_samples = [baseline_memory]
        operation_counts = [0]
        
        # Execute operations while monitoring memory
        operations_per_sample = 100
        num_samples = 10
        
        for sample in range(num_samples):
            # Execute batch of operations
            for i in range(operations_per_sample):
                result = await mcp_client.call_tool("echo", {
                    "message": f"memory_test_{sample}_{i}"
                })
                assert result is not None, f"Operation should succeed"
                
            # Sample memory usage
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
            operation_counts.append((sample + 1) * operations_per_sample)
            
            print(f"Memory after {operation_counts[-1]} ops: {current_memory:.2f}MB")
            
        # Analyze memory usage patterns
        memory_growth = memory_samples[-1] - baseline_memory
        peak_memory = max(memory_samples)
        memory_per_operation = memory_growth / operation_counts[-1] if operation_counts[-1] > 0 else 0
        
        print(f"\nMemory Usage Baseline:")
        print(f"  Baseline: {baseline_memory:.2f}MB")
        print(f"  Peak: {peak_memory:.2f}MB")
        print(f"  Growth: {memory_growth:.2f}MB")
        print(f"  Per operation: {memory_per_operation*1000:.3f}KB")
        
        # Memory requirements validation
        assert peak_memory < 100, f"Peak memory too high: {peak_memory:.2f}MB"
        assert memory_per_operation < 0.01, f"Memory per operation too high: {memory_per_operation*1000:.3f}KB"
        
        return {
            "baseline_memory": baseline_memory,
            "peak_memory": peak_memory,
            "memory_growth": memory_growth,
            "memory_per_operation": memory_per_operation
        }


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.load
@pytest.mark.slow
class TestLoadPerformance(IntegrationTestBase):
    """Load testing and scalability tests"""
    
    @measure_performance
    async def test_concurrent_load_scaling(self, server_config, performance_config):
        """Test performance under increasing concurrent load"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        # Load scaling test configuration
        max_concurrent = performance_config["concurrent_connections"]
        load_levels = [1, 2, 5, 10, max_concurrent, max_concurrent * 2]
        operations_per_client = 20
        
        scaling_results = {}
        
        for concurrent_clients in load_levels:
            if concurrent_clients > max_concurrent * 2:
                continue  # Skip extreme loads
                
            print(f"\nTesting concurrent load: {concurrent_clients} clients")
            
            clients = []
            try:
                # Create concurrent clients
                for i in range(concurrent_clients):
                    config = server_config.copy()
                    config["client_id"] = f"load_client_{i}"
                    
                    client = MCPClient(config)
                    await client.connect()
                    clients.append(client)
                    
                # Execute concurrent workload
                start_time = time.time()
                
                async def client_workload(client_idx: int, client) -> Tuple[int, int, float]:
                    """Execute workload for single client"""
                    successful_ops = 0
                    total_ops = 0
                    workload_start = time.time()
                    
                    if hasattr(client, 'call_tool'):
                        for op in range(operations_per_client):
                            try:
                                result = await client.call_tool("echo", {
                                    "message": f"load_test_c{client_idx}_op{op}"
                                })
                                if result is not None:
                                    successful_ops += 1
                                total_ops += 1
                            except Exception:
                                total_ops += 1  # Count failed operations
                                
                    workload_duration = time.time() - workload_start
                    return successful_ops, total_ops, workload_duration
                
                # Execute all client workloads concurrently
                workload_tasks = [
                    client_workload(i, client) 
                    for i, client in enumerate(clients)
                ]
                
                workload_results = await asyncio.gather(*workload_tasks)
                
                total_duration = time.time() - start_time
                
                # Aggregate results
                total_successful = sum(r[0] for r in workload_results)
                total_operations = sum(r[1] for r in workload_results)
                success_rate = total_successful / total_operations if total_operations > 0 else 0
                overall_throughput = total_successful / total_duration
                
                # Individual client performance
                client_throughputs = [r[0] / r[2] for r in workload_results if r[2] > 0]
                avg_client_throughput = statistics.mean(client_throughputs) if client_throughputs else 0
                
                scaling_results[concurrent_clients] = {
                    "total_operations": total_operations,
                    "successful_operations": total_successful,
                    "success_rate": success_rate,
                    "overall_throughput": overall_throughput,
                    "avg_client_throughput": avg_client_throughput,
                    "duration": total_duration
                }
                
                print(f"  Results: {total_successful}/{total_operations} ops successful")
                print(f"  Success rate: {success_rate*100:.1f}%")
                print(f"  Overall throughput: {overall_throughput:.1f} ops/sec")
                print(f"  Avg client throughput: {avg_client_throughput:.1f} ops/sec")
                
            finally:
                # Clean up clients
                for client in clients:
                    try:
                        await client.disconnect()
                    except:
                        pass
                        
        # Analyze scaling characteristics
        print(f"\nConcurrent Load Scaling Analysis:")
        
        for concurrent, results in scaling_results.items():
            efficiency = results["success_rate"] * 100
            print(f"  {concurrent} clients: {efficiency:.1f}% efficiency, {results['overall_throughput']:.1f} ops/sec")
            
        # Validate scaling requirements
        baseline_results = scaling_results.get(1, {})
        max_load_results = scaling_results.get(max_concurrent, {})
        
        if baseline_results and max_load_results:
            efficiency_degradation = baseline_results["success_rate"] - max_load_results["success_rate"]
            assert efficiency_degradation < 0.2, \
                f"Efficiency degradation too high: {efficiency_degradation*100:.1f}%"
                
        return scaling_results
        
    @measure_performance
    async def test_sustained_load_performance(self, mcp_client, performance_config):
        """Test performance under sustained load over time"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Sustained load configuration
        test_duration = 300  # 5 minutes
        target_rate = performance_config["target_ops_per_second"] * 0.5  # 50% of max
        sample_interval = 30  # Sample every 30 seconds
        
        performance_samples = []
        start_time = time.time()
        last_sample_time = start_time
        operations_count = 0
        
        print(f"Starting sustained load test ({test_duration}s at {target_rate:.1f} ops/sec target)")
        
        async def sustain_load():
            """Maintain target operation rate"""
            nonlocal operations_count
            
            while time.time() - start_time < test_duration:
                operation_start = time.time()
                
                try:
                    result = await mcp_client.call_tool("echo", {
                        "message": f"sustained_load_{operations_count}"
                    })
                    if result is not None:
                        operations_count += 1
                except Exception as e:
                    print(f"Operation failed: {e}")
                    
                # Rate limiting to maintain target rate
                operation_duration = time.time() - operation_start
                target_interval = 1.0 / target_rate
                
                if operation_duration < target_interval:
                    await asyncio.sleep(target_interval - operation_duration)
                    
        # Monitor performance during sustained load
        async def monitor_performance():
            nonlocal last_sample_time
            
            while time.time() - start_time < test_duration:
                await asyncio.sleep(sample_interval)
                
                current_time = time.time()
                sample_duration = current_time - last_sample_time
                current_rate = operations_count / (current_time - start_time)
                
                # Memory usage
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                sample = {
                    "timestamp": current_time - start_time,
                    "operations": operations_count,
                    "rate": current_rate,
                    "memory_mb": memory_mb,
                    "connection_stable": mcp_client.is_connected()
                }
                
                performance_samples.append(sample)
                
                print(f"Sustained load sample: {current_rate:.1f} ops/sec, "
                      f"{memory_mb:.1f}MB memory, "
                      f"connected: {sample['connection_stable']}")
                
                last_sample_time = current_time
                
        # Run sustained load and monitoring concurrently
        await asyncio.gather(
            sustain_load(),
            monitor_performance()
        )
        
        # Analyze sustained load performance
        if performance_samples:
            rates = [s["rate"] for s in performance_samples]
            memories = [s["memory_mb"] for s in performance_samples]
            
            avg_rate = statistics.mean(rates)
            min_rate = min(rates)
            max_rate = max(rates)
            rate_stability = statistics.stdev(rates) if len(rates) > 1 else 0
            
            avg_memory = statistics.mean(memories)
            max_memory = max(memories)
            memory_growth = max_memory - memories[0] if memories else 0
            
            connection_stability = sum(1 for s in performance_samples if s["connection_stable"]) / len(performance_samples)
            
            print(f"\nSustained Load Performance Results:")
            print(f"  Target rate: {target_rate:.1f} ops/sec")
            print(f"  Achieved rate: {avg_rate:.1f} ops/sec (avg)")
            print(f"  Rate range: {min_rate:.1f} - {max_rate:.1f} ops/sec")
            print(f"  Rate stability (std dev): {rate_stability:.1f}")
            print(f"  Memory usage: {avg_memory:.1f}MB (avg), {max_memory:.1f}MB (peak)")
            print(f"  Memory growth: {memory_growth:.1f}MB")
            print(f"  Connection stability: {connection_stability*100:.1f}%")
            
            # Performance validation
            rate_efficiency = avg_rate / target_rate
            assert rate_efficiency >= 0.8, f"Rate efficiency too low: {rate_efficiency*100:.1f}%"
            assert connection_stability >= 0.99, f"Connection stability too low: {connection_stability*100:.1f}%"
            assert memory_growth < 50, f"Memory growth too high: {memory_growth:.1f}MB"
            
            return {
                "target_rate": target_rate,
                "achieved_rate": avg_rate,
                "rate_stability": rate_stability,
                "memory_growth": memory_growth,
                "connection_stability": connection_stability
            }
            
    @measure_performance
    async def test_burst_load_handling(self, mcp_client, performance_config):
        """Test handling of sudden load bursts"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Burst load configuration
        baseline_rate = 5  # ops/sec
        burst_rate = performance_config["target_ops_per_second"] * 2  # 200% of target
        burst_duration = 10  # seconds
        recovery_duration = 20  # seconds
        
        performance_timeline = []
        
        async def execute_load_phase(phase_name: str, rate: float, duration: float):
            """Execute load phase at specified rate"""
            phase_start = time.time()
            operations_in_phase = 0
            
            print(f"Starting {phase_name}: {rate:.1f} ops/sec for {duration}s")
            
            while time.time() - phase_start < duration:
                operation_start = time.time()
                
                try:
                    result = await mcp_client.call_tool("echo", {
                        "message": f"{phase_name}_op_{operations_in_phase}"
                    })
                    if result is not None:
                        operations_in_phase += 1
                except Exception as e:
                    print(f"Operation failed in {phase_name}: {e}")
                    
                # Rate control
                operation_duration = time.time() - operation_start
                target_interval = 1.0 / rate
                
                if operation_duration < target_interval:
                    await asyncio.sleep(target_interval - operation_duration)
                    
            phase_duration = time.time() - phase_start
            actual_rate = operations_in_phase / phase_duration
            
            performance_timeline.append({
                "phase": phase_name,
                "target_rate": rate,
                "actual_rate": actual_rate,
                "operations": operations_in_phase,
                "duration": phase_duration,
                "connection_stable": mcp_client.is_connected()
            })
            
            print(f"Completed {phase_name}: {actual_rate:.1f} ops/sec actual")
            
        # Execute burst load test phases
        await execute_load_phase("baseline", baseline_rate, 30)
        await execute_load_phase("burst", burst_rate, burst_duration)
        await execute_load_phase("recovery", baseline_rate, recovery_duration)
        
        # Analyze burst handling
        baseline_performance = next((p for p in performance_timeline if p["phase"] == "baseline"), None)
        burst_performance = next((p for p in performance_timeline if p["phase"] == "burst"), None)
        recovery_performance = next((p for p in performance_timeline if p["phase"] == "recovery"), None)
        
        print(f"\nBurst Load Handling Analysis:")
        
        for phase_perf in performance_timeline:
            efficiency = (phase_perf["actual_rate"] / phase_perf["target_rate"]) * 100
            print(f"  {phase_perf['phase']}: {efficiency:.1f}% efficiency")
            
        # Burst handling validation
        if burst_performance:
            burst_efficiency = burst_performance["actual_rate"] / burst_performance["target_rate"]
            assert burst_efficiency >= 0.3, f"Burst handling too poor: {burst_efficiency*100:.1f}% efficiency"
            
        if recovery_performance and baseline_performance:
            recovery_efficiency = recovery_performance["actual_rate"] / baseline_performance["actual_rate"]
            assert recovery_efficiency >= 0.9, f"Recovery incomplete: {recovery_efficiency*100:.1f}% of baseline"
            
        # Connection stability during burst
        connection_stability = all(p["connection_stable"] for p in performance_timeline)
        assert connection_stability, "Connection should remain stable during burst load"
        
        return performance_timeline


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.load
@pytest.mark.slow  
class TestPerformanceRegression(IntegrationTestBase):
    """Performance regression and optimization tests"""
    
    @measure_performance
    async def test_performance_regression_suite(self, mcp_client, performance_config):
        """Comprehensive performance regression test suite"""
        if not hasattr(mcp_client, 'call_tool'):
            pytest.skip("Tool invocation not yet implemented")
            
        # Performance benchmarks (baseline expectations)
        benchmarks = {
            "single_op_latency_ms": 100,      # Max latency for single operation
            "throughput_ops_per_sec": performance_config["target_ops_per_second"] * 0.5,
            "memory_growth_mb_per_1k_ops": 5,  # Max memory growth per 1000 operations
            "connection_stability_percent": 99.9,
            "error_rate_percent": 1.0
        }
        
        regression_results = {}
        
        # Test 1: Latency regression
        latencies = []
        for i in range(50):
            start = time.perf_counter()
            await mcp_client.call_tool("echo", {"message": f"latency_regression_{i}"})
            latencies.append((time.perf_counter() - start) * 1000)
            
        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(0.95 * len(latencies))]
        
        regression_results["latency"] = {
            "avg_ms": avg_latency,
            "p95_ms": p95_latency,
            "benchmark_ms": benchmarks["single_op_latency_ms"],
            "passed": p95_latency <= benchmarks["single_op_latency_ms"]
        }
        
        # Test 2: Throughput regression
        throughput_start = time.time()
        throughput_ops = 0
        
        while time.time() - throughput_start < 10:  # 10 second test
            await mcp_client.call_tool("echo", {"message": f"throughput_regression_{throughput_ops}"})
            throughput_ops += 1
            
        throughput = throughput_ops / (time.time() - throughput_start)
        
        regression_results["throughput"] = {
            "ops_per_sec": throughput,
            "benchmark_ops_per_sec": benchmarks["throughput_ops_per_sec"],
            "passed": throughput >= benchmarks["throughput_ops_per_sec"]
        }
        
        # Test 3: Memory regression
        process = psutil.Process()
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024
        
        for i in range(1000):  # 1000 operations
            await mcp_client.call_tool("echo", {"message": f"memory_regression_{i}"})
            
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - baseline_memory
        
        regression_results["memory"] = {
            "growth_mb": memory_growth,
            "benchmark_mb": benchmarks["memory_growth_mb_per_1k_ops"],
            "passed": memory_growth <= benchmarks["memory_growth_mb_per_1k_ops"]
        }
        
        # Test 4: Stability regression
        stability_ops = 0
        stability_errors = 0
        
        for i in range(100):
            try:
                await mcp_client.call_tool("echo", {"message": f"stability_regression_{i}"})
                stability_ops += 1
            except Exception:
                stability_errors += 1
                
        error_rate = (stability_errors / (stability_ops + stability_errors)) * 100
        connection_stable = mcp_client.is_connected()
        
        regression_results["stability"] = {
            "error_rate_percent": error_rate,
            "connection_stable": connection_stable,
            "benchmark_error_rate": benchmarks["error_rate_percent"],
            "passed": error_rate <= benchmarks["error_rate_percent"] and connection_stable
        }
        
        # Summary
        print(f"\nPerformance Regression Test Results:")
        for test_name, results in regression_results.items():
            status = "PASS" if results["passed"] else "FAIL"
            print(f"  {test_name}: {status}")
            
        # Overall regression validation
        all_passed = all(r["passed"] for r in regression_results.values())
        assert all_passed, f"Performance regression detected: {regression_results}"
        
        return regression_results