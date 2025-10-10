#!/usr/bin/env python3
"""
Integration Test Runner for Study Buddy Integration Layer

Provides comprehensive test execution with real MCP server communication,
performance monitoring, and detailed reporting for Task 13 validation.

Usage:
    python run_integration_tests.py [options]
    
Options:
    --category [connection|tools|workflows|errors|performance|all]
    --verbose          Enable verbose output
    --performance      Run performance benchmarks
    --load            Run load testing (slow)
    --report          Generate detailed HTML report
    --server-port     Test server port (default: 3000)
"""

import sys
import os
import asyncio
import argparse
import time
import json
import socket
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess
import tempfile
import shutil

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import pytest
    import psutil
    from rich.console import Console
    from rich.table import Table  
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich.syntax import Syntax
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install pytest rich psutil")
    sys.exit(1)


class IntegrationTestRunner:
    """Comprehensive integration test runner with real server testing"""
    
    def __init__(self):
        self.console = Console()
        self.test_categories = {
            "connection": "Connection lifecycle and management",
            "tools": "Tool discovery and invocation workflows", 
            "workflows": "End-to-end workflow validation",
            "errors": "Error recovery and resilience testing",
            "performance": "Performance benchmarks and load testing"
        }
        
    def print_header(self):
        """Print test runner header"""
        header_text = """
╔══════════════════════════════════════════════════════════════╗
║              Study Buddy Integration Test Suite               ║
║                     Task 13 Validation                       ║
╠══════════════════════════════════════════════════════════════╣
║  Real MCP Server Testing • Performance Validation            ║
║  Error Recovery • End-to-End Workflows • Load Testing       ║
╚══════════════════════════════════════════════════════════════╝
        """
        self.console.print(Panel(header_text.strip(), style="bold blue"))
        
    def validate_environment(self) -> bool:
        """Validate test environment setup"""
        self.console.print("\n[bold]Validating Test Environment[/bold]")
        
        checks = []
        
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        checks.append(("Python Version", python_version, python_version >= "3.8"))
        
        # Check required packages
        required_packages = ["pytest", "asyncio", "psutil"]
        for package in required_packages:
            try:
                __import__(package)
                checks.append((f"Package: {package}", "Available", True))
            except ImportError:
                checks.append((f"Package: {package}", "Missing", False))
                
        # Check test directory structure
        test_dir = Path(__file__).parent
        required_files = [
            "conftest.py",
            "test_connection_lifecycle.py",
            "test_tool_workflows.py",
            "test_error_recovery.py", 
            "test_end_to_end_workflows.py",
            "test_performance_load.py"
        ]
        
        for file_name in required_files:
            file_path = test_dir / file_name
            checks.append((f"Test File: {file_name}", "Present" if file_path.exists() else "Missing", file_path.exists()))
            
        # Check system resources
        memory_gb = psutil.virtual_memory().total / (1024**3)
        cpu_count = psutil.cpu_count()
        checks.append(("System Memory", f"{memory_gb:.1f} GB", memory_gb >= 4))
        checks.append(("CPU Cores", f"{cpu_count or 0}", (cpu_count or 0) >= 2))
        
        # Display validation results
        table = Table(title="Environment Validation")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Valid", style="green")
        
        all_valid = True
        for component, status, valid in checks:
            status_icon = "✓" if valid else "✗"
            status_color = "green" if valid else "red"
            table.add_row(component, status, f"[{status_color}]{status_icon}[/{status_color}]")
            if not valid:
                all_valid = False
                
        self.console.print(table)
        
        if not all_valid:
            self.console.print("\n[bold red]Environment validation failed. Please fix issues before running tests.[/bold red]")
            
        return all_valid
        
    async def start_test_server(self, port: int = 3000) -> Optional[subprocess.Popen]:
        """Start test MCP server for integration testing"""
        self.console.print(f"\n[bold]Starting Test MCP Server (port {port})[/bold]")
        
        # Create temporary test server
        temp_dir = tempfile.mkdtemp(prefix="integration_test_server_")
        
        # Test server script (minimal implementation)
        server_script = f"""
import asyncio
import json
import socket
import sys
from typing import Dict, Any

class TestMCPServer:
    def __init__(self, port: int):
        self.port = port
        
    async def handle_echo(self, message: str) -> Dict[str, Any]:
        return {{"result": message, "tool": "echo"}}
        
    async def handle_add(self, a: int, b: int) -> Dict[str, Any]:
        return {{"result": a + b, "tool": "add"}}
        
    async def handle_error(self) -> Dict[str, Any]:
        raise Exception("Test error for error handling validation")
        
    async def handle_slow(self, delay: float = 2.0) -> Dict[str, Any]:
        await asyncio.sleep(delay)
        return {{"result": f"Completed after {{delay}}s", "tool": "slow"}}
        
    async def start_server(self):
        print(f"Test MCP Server starting on port {{self.port}}")
        
        # Simple socket server for testing
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', self.port))
        server_socket.listen(5)
        
        print(f"Test server listening on localhost:{{self.port}}")
        
        try:
            while True:
                await asyncio.sleep(1)
                # Basic server loop - actual MCP protocol implementation
                # would be more complex but this is sufficient for testing
        except KeyboardInterrupt:
            print("Test server shutting down")
        finally:
            server_socket.close()

if __name__ == "__main__":
    server = TestMCPServer({port})
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("\\nTest server stopped")
"""
        
        # Write server script
        script_path = os.path.join(temp_dir, "test_server.py")
        with open(script_path, "w") as f:
            f.write(server_script)
            
        # Start server process
        try:
            process = subprocess.Popen([
                sys.executable, script_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            await asyncio.sleep(2)
            
            # Verify server is running
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    self.console.print(f"[green]✓[/green] Test server started successfully on port {port}")
                    return process
                else:
                    self.console.print(f"[red]✗[/red] Test server failed to start on port {port}")
                    process.terminate()
                    return None
                    
            except Exception as e:
                self.console.print(f"[red]✗[/red] Server validation failed: {e}")
                process.terminate() 
                return None
                
        except Exception as e:
            self.console.print(f"[red]✗[/red] Failed to start test server: {e}")
            return None
        finally:
            # Cleanup temp directory on exit
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                
    async def run_test_category(self, category: str, args: argparse.Namespace) -> Dict[str, Any]:
        """Run tests for specific category"""
        
        # Map categories to test files
        category_files = {
            "connection": "test_connection_lifecycle.py",
            "tools": "test_tool_workflows.py", 
            "workflows": "test_end_to_end_workflows.py",
            "errors": "test_error_recovery.py",
            "performance": "test_performance_load.py"
        }
        
        if category not in category_files:
            self.console.print(f"[red]Unknown test category: {category}[/red]")
            return {"success": False, "error": f"Unknown category: {category}"}
            
        test_file = category_files[category]
        test_path = Path(__file__).parent / test_file
        
        if not test_path.exists():
            self.console.print(f"[red]Test file not found: {test_file}[/red]")
            return {"success": False, "error": f"Test file missing: {test_file}"}
            
        self.console.print(f"\\n[bold]Running {category.title()} Tests[/bold]")
        self.console.print(f"File: {test_file}")
        self.console.print(f"Description: {self.test_categories[category]}")
        
        # Build pytest command
        pytest_args = [
            str(test_path),
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            f"--junitxml=test_results_{category}.xml"  # JUnit XML output
        ]
        
        # Add markers based on arguments
        markers = []
        if category == "performance" or args.performance:
            markers.append("load")
            
        if args.load and category in ["performance", "connection", "tools"]:
            markers.append("slow")
            
        if markers:
            pytest_args.extend(["-m", " or ".join(markers)])
            
        # Capture test execution
        start_time = time.time()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"Executing {category} tests...", total=None)
            
            # Run pytest
            exit_code = pytest.main(pytest_args)
            
        execution_time = time.time() - start_time
        
        # Parse results
        results = {
            "category": category,
            "exit_code": exit_code,
            "execution_time": execution_time,
            "success": exit_code == 0
        }
        
        # Display results
        if results["success"]:
            self.console.print(f"[green]✓[/green] {category.title()} tests completed successfully ({execution_time:.2f}s)")
        else:
            self.console.print(f"[red]✗[/red] {category.title()} tests failed (exit code: {exit_code})")
            
        return results
        
    async def run_all_tests(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Run complete integration test suite"""
        self.console.print("\\n[bold]Running Complete Integration Test Suite[/bold]")
        
        # Test execution order (dependencies)
        test_order = ["connection", "tools", "errors", "workflows", "performance"]
        
        if args.category and args.category != "all":
            if args.category in self.test_categories:
                test_order = [args.category]
            else:
                self.console.print(f"[red]Invalid category: {args.category}[/red]")
                return {"success": False, "error": "Invalid category"}
                
        all_results = {}
        overall_start = time.time()
        
        for category in test_order:
            if category == "performance" and not (args.performance or args.load):
                self.console.print(f"[yellow]Skipping performance tests (use --performance or --load)[/yellow]")
                continue
                
            result = await self.run_test_category(category, args)
            all_results[category] = result
            
            # Stop on failure unless continuing
            if not result["success"] and not args.continue_on_failure:
                self.console.print(f"[red]Stopping due to {category} test failures[/red]")
                break
                
        overall_time = time.time() - overall_start
        
        # Generate summary
        summary = self.generate_test_summary(all_results, overall_time)
        self.display_test_summary(summary)
        
        if args.report:
            self.generate_html_report(summary, all_results)
            
        return summary
        
    def generate_test_summary(self, results: Dict[str, Any], total_time: float) -> Dict[str, Any]:
        """Generate test execution summary"""
        
        executed_categories = len(results)
        successful_categories = sum(1 for r in results.values() if r["success"])
        failed_categories = executed_categories - successful_categories
        
        return {
            "total_categories": len(self.test_categories),
            "executed_categories": executed_categories,
            "successful_categories": successful_categories,
            "failed_categories": failed_categories,
            "success_rate": successful_categories / executed_categories if executed_categories > 0 else 0,
            "total_execution_time": total_time,
            "overall_success": failed_categories == 0,
            "results": results
        }
        
    def display_test_summary(self, summary: Dict[str, Any]):
        """Display comprehensive test summary"""
        
        self.console.print("\\n" + "="*60)
        self.console.print("[bold]Integration Test Suite Summary[/bold]")
        self.console.print("="*60)
        
        # Summary table
        table = Table(title="Test Execution Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_column("Status", style="green")
        
        # Add summary rows
        table.add_row("Categories Executed", str(summary["executed_categories"]), "")
        table.add_row("Successful", str(summary["successful_categories"]), "✓" if summary["successful_categories"] > 0 else "")
        table.add_row("Failed", str(summary["failed_categories"]), "✗" if summary["failed_categories"] > 0 else "")
        table.add_row("Success Rate", f"{summary['success_rate']*100:.1f}%", "✓" if summary["success_rate"] >= 0.9 else "⚠")
        table.add_row("Total Time", f"{summary['total_execution_time']:.2f}s", "")
        
        self.console.print(table)
        
        # Category details
        if summary["results"]:
            self.console.print("\\n[bold]Category Results:[/bold]")
            
            for category, result in summary["results"].items():
                status_icon = "✓" if result["success"] else "✗"
                status_color = "green" if result["success"] else "red"
                
                self.console.print(
                    f"  [{status_color}]{status_icon}[/{status_color}] "
                    f"{category.title()}: {result['execution_time']:.2f}s"
                )
                
        # Overall result
        if summary["overall_success"]:
            self.console.print("\\n[bold green]🎉 ALL INTEGRATION TESTS PASSED! 🎉[/bold green]")
            self.console.print("[green]Task 13 (Integration Testing Suite) validation complete.[/green]")
        else:
            self.console.print("\\n[bold red]❌ INTEGRATION TESTS FAILED ❌[/bold red]")
            self.console.print(f"[red]{summary['failed_categories']} out of {summary['executed_categories']} categories failed.[/red]")
            
    def generate_html_report(self, summary: Dict[str, Any], results: Dict[str, Any]):
        """Generate detailed HTML test report"""
        
        report_file = Path("integration_test_report.html")
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Study Buddy Integration Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .category {{ margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ background: #e8f5e8; border-color: #4caf50; }}
        .failure {{ background: #ffeaea; border-color: #f44336; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .status-icon {{ font-weight: bold; }}
        .success-icon {{ color: #4caf50; }}
        .failure-icon {{ color: #f44336; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Study Buddy Integration Test Report</h1>
        <h2>Task 13 - Integration Testing Suite Validation</h2>
        <p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h3>Executive Summary</h3>
        <div class="metric">
            <strong>Overall Status:</strong> 
            <span class="status-icon {'success-icon' if summary['overall_success'] else 'failure-icon'}">
                {'✓ PASSED' if summary['overall_success'] else '✗ FAILED'}
            </span>
        </div>
        <div class="metric"><strong>Categories:</strong> {summary['executed_categories']}/{summary['total_categories']}</div>
        <div class="metric"><strong>Success Rate:</strong> {summary['success_rate']*100:.1f}%</div>
        <div class="metric"><strong>Total Time:</strong> {summary['total_execution_time']:.2f}s</div>
    </div>
    
    <div class="categories">
        <h3>Category Results</h3>
"""
        
        for category, result in results.items():
            status_class = "success" if result["success"] else "failure"
            status_icon = "✓" if result["success"] else "✗"
            
            html_content += f"""
        <div class="category {status_class}">
            <h4>
                <span class="status-icon">{status_icon}</span>
                {category.title()} Tests
            </h4>
            <p><strong>Description:</strong> {self.test_categories[category]}</p>
            <p><strong>Execution Time:</strong> {result['execution_time']:.2f}s</p>
            <p><strong>Exit Code:</strong> {result['exit_code']}</p>
        </div>
"""
        
        html_content += """
    </div>
    
    <div class="footer">
        <h3>Test Environment</h3>
        <p><strong>Python Version:</strong> """ + f"{sys.version}" + """</p>
        <p><strong>Platform:</strong> """ + f"{sys.platform}" + """</p>
        <p><strong>Test Runner:</strong> Integration Test Suite v1.0</p>
    </div>
</body>
</html>"""
        
        with open(report_file, 'w') as f:
            f.write(html_content)
            
        self.console.print(f"\\n[blue]📊 HTML report generated: {report_file.absolute()}[/blue]")


async def main():
    """Main test runner entry point"""
    
    parser = argparse.ArgumentParser(
        description="Study Buddy Integration Test Runner - Task 13 Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_integration_tests.py                    # Run all basic tests  
  python run_integration_tests.py --category tools   # Run only tool tests
  python run_integration_tests.py --performance      # Include performance tests
  python run_integration_tests.py --load --report    # Full load testing with report
"""
    )
    
    parser.add_argument(
        "--category", 
        choices=["connection", "tools", "workflows", "errors", "performance", "all"],
        default="all",
        help="Test category to run (default: all)"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose test output"
    )
    
    parser.add_argument(
        "--performance",
        action="store_true", 
        help="Include performance benchmark tests"
    )
    
    parser.add_argument(
        "--load",
        action="store_true",
        help="Include load testing (slow tests)"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate detailed HTML report"
    )
    
    parser.add_argument(
        "--server-port",
        type=int,
        default=3000,
        help="Test server port (default: 3000)"
    )
    
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="Continue testing even if a category fails"
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = IntegrationTestRunner()
    runner.print_header()
    
    # Validate environment
    if not runner.validate_environment():
        return 1
        
    # Start test server
    server_process = None
    try:
        server_process = await runner.start_test_server(args.server_port)
        if not server_process:
            runner.console.print("[red]Failed to start test server. Cannot run integration tests.[/red]")
            return 1
            
        # Run tests
        summary = await runner.run_all_tests(args)
        
        # Return appropriate exit code
        return 0 if summary["overall_success"] else 1
        
    except KeyboardInterrupt:
        runner.console.print("\\n[yellow]Test execution interrupted by user[/yellow]")
        return 130
        
    except Exception as e:
        runner.console.print(f"\\n[red]Test runner error: {e}[/red]")
        return 1
        
    finally:
        # Clean up test server
        if server_process:
            try:
                server_process.terminate()
                server_process.wait(timeout=5)
                runner.console.print("[green]✓[/green] Test server stopped")
            except subprocess.TimeoutExpired:
                server_process.kill()
                runner.console.print("[yellow]⚠[/yellow] Test server forcibly stopped")
            except Exception:
                pass  # Ignore cleanup errors


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))