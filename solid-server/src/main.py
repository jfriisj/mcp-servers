"""
Main entry point for the SOLID Principles MCP Server
====================================================
"""

import asyncio
import argparse
import sys
from pathlib import Path

from server import SolidMCPServer


async def main():
    """Main entry point for the SOLID Principles MCP server"""
    parser = argparse.ArgumentParser(description="SOLID Principles MCP Server")
    parser.add_argument(
        "--project-root", 
        type=str, 
        help="Root directory for SOLID analysis (defaults to current directory)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (non-MCP mode for debugging)"
    )
    
    args = parser.parse_args()

    # Determine project root
    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    
    if not project_root.exists():
        print(f"Error: Project root does not exist: {project_root}")
        sys.exit(1)
    
    if args.test:
        # Test mode - run some basic analysis using new architecture
        print("🔍 Running SOLID Principles MCP Server in test mode...")
        print(f"📁 Project root: {project_root}")
        
        # Use composition root to eliminate DIP violations in test mode
        from presentation.composition_root import CompositionRoot
        from application.analyze_directory import DirectoryFilters
        from application.generate_report import ReportOptions
        
        # Create composition root and get configured use cases
        composition_root = CompositionRoot(project_root)
        use_cases = composition_root._get_use_cases()
        
        # Extract use cases from the composition root
        analyze_file_uc = use_cases['analyze_file']
        analyze_dir_uc = use_cases['analyze_directory'] 
        generate_report_uc = use_cases['generate_report']
        
        # Find some Python files to analyze
        python_files = list(project_root.rglob("*.py"))[:5]  # Limit to 5 files
        
        if not python_files:
            print("❌ No Python files found in project root")
            return
        
        print(f"📊 Analyzing {len(python_files)} Python files...")
        
        for py_file in python_files:
            try:
                report = analyze_file_uc.execute(py_file)
                rel_path = py_file.relative_to(project_root)
                print(f"\n📄 {rel_path}")
                print(f"   Score: {report.score:.1f}/100")
                print(f"   Violations: {len(report.violations)}")
                
                if report.violations:
                    for v in report.violations[:3]:  # Show first 3 violations
                        print(f"   - Line {v.line_number}: [{v.principle.value}] {v.message}")
                    if len(report.violations) > 3:
                        print(f"   ... and {len(report.violations) - 3} more")
                        
            except Exception as e:
                print(f"   ❌ Error analyzing {py_file.name}: {e}")
        
        # Generate directory summary using composition root
        try:
            # Use composition root's pre-configured filters to avoid DIP violation
            filters = DirectoryFilters(
                include_patterns=["*.py"],
                exclude_patterns=["__pycache__", "test_*"]
            )
            reports = analyze_dir_uc.execute(project_root, filters)
            
            options = ReportOptions(
                include_suggestions=True,
                output_format="text", 
                severity_filter="all"
            )
            output = generate_report_uc.execute(reports, options)
            
            print("\n📈 Overall Project Analysis:")
            # Show first 15 lines of report
            for line in output.split('\n')[:15]:
                print(line)
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
        
        print("\n✅ Test completed successfully!")
        print("💡 To use with MCP clients, run without --test flag")
        
    else:
        # Normal MCP server mode
        try:
            # Don't print to stdout in MCP mode - it interferes with the protocol
            # Use stderr for any necessary logging
            import logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stderr)]
            )
            logger = logging.getLogger('solid-mcp-server')
            logger.info(f"Starting SOLID Principles MCP Server with project root: {project_root}")
            
            # Use composition root for proper dependency injection
            from presentation.composition_root import create_solid_server
            server = create_solid_server(project_root)
            await server.serve()
            
        except KeyboardInterrupt:
            # Use stderr for exit messages in MCP mode
            print("\n🛑 Server stopped by user", file=sys.stderr)
        except Exception as e:
            print(f"❌ Server error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())