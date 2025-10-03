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
        # Test mode - run some basic analysis
        print("🔍 Running SOLID Principles MCP Server in test mode...")
        print(f"📁 Project root: {project_root}")
        
        # Import components for testing
        from solid_analyzer import SolidBatchAnalyzer
        
        analyzer = SolidBatchAnalyzer()
        
        # Find some Python files to analyze
        python_files = list(project_root.rglob("*.py"))[:5]  # Limit to 5 files
        
        if not python_files:
            print("❌ No Python files found in project root")
            return
        
        print(f"📊 Analyzing {len(python_files)} Python files...")
        
        for py_file in python_files:
            try:
                report = analyzer.analyzer.analyze_file(py_file)
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
        
        # Generate summary
        try:
            reports = analyzer.analyze_directory(project_root)
            summary = analyzer.generate_summary_report(reports)
            
            print(f"\n📈 Overall Project Analysis:")
            print(f"   Average Score: {summary['average_score']:.1f}/100")
            print(f"   Files analyzed: {summary['total_files']}")
            print(f"   Total violations: {summary['total_violations']}")
            print(f"   Most common violations:")
            
            for principle, count in summary['violations_by_principle'].items():
                if count > 0:
                    print(f"   - {principle}: {count}")
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
        
        print("\n✅ Test completed successfully!")
        print("💡 To use with MCP clients, run without --test flag")
        
    else:
        # Normal MCP server mode
        try:
            print("🚀 Starting SOLID Principles MCP Server...")
            print(f"📁 Project root: {project_root}")
            
            server = SolidMCPServer(project_root)
            await server.serve()
            
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
        except Exception as e:
            print(f"❌ Server error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())