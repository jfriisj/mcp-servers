"""
Import Test MCP Server
======================

A Model Context Protocol (MCP) server that validates Python imports, 
exports, and dependency correctness in projects.

Features:
- Validate all imports exist and are accessible
- Check for circular imports
- Analyze export completeness (__all__, __init__.py)
- Find unused imports
- Validate relative vs absolute import consistency  
- Check for missing dependencies
- Analyze import performance and organization
"""

import asyncio
import argparse
import sys
from pathlib import Path

from server import ImportTestMCPServer


async def main():
    """Main entry point for the Import Test MCP server"""
    parser = argparse.ArgumentParser(description="Import Test MCP Server")
    parser.add_argument(
        "--project-root", 
        type=str, 
        help="Root directory for import analysis (defaults to current directory)"
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
        # Test mode - run some basic import analysis
        print("🔍 Running Import Test MCP Server in test mode...")
        print(f"📁 Project root: {project_root}")
        
        # Import components
        from application.analyze_imports import AnalyzeImportsUseCase
        from application.validate_dependencies import ValidateDependenciesUseCase
        from infrastructure.import_analyzer import ImportAnalyzer
        from infrastructure.dependency_resolver import DependencyResolver
        
        # Set up dependencies
        resolver = DependencyResolver(project_root)
        analyzer = ImportAnalyzer(resolver)
        
        # Create use cases
        analyze_imports_uc = AnalyzeImportsUseCase(analyzer)
        validate_deps_uc = ValidateDependenciesUseCase(resolver)
        
        # Find Python files to analyze
        python_files = list(project_root.rglob("*.py"))[:10]  # Limit to 10 files
        
        if not python_files:
            print("❌ No Python files found in project root")
            return
        
        print(f"📊 Analyzing imports in {len(python_files)} Python files...")
        
        total_imports = 0
        valid_imports = 0
        issues_found = []
        
        for py_file in python_files:
            try:
                result = analyze_imports_uc.execute(py_file)
                rel_path = py_file.relative_to(project_root)
                
                file_imports = len(result.imports)
                file_valid = len([imp for imp in result.imports if imp.is_valid])
                
                total_imports += file_imports
                valid_imports += file_valid
                
                print(f"\n📄 {rel_path}")
                print(f"   Imports: {file_imports} total, {file_valid} valid")
                
                if result.issues:
                    print(f"   Issues: {len(result.issues)}")
                    for issue in result.issues[:3]:  # Show first 3 issues
                        print(f"   - Line {issue.line_number}: {issue.message}")
                    if len(result.issues) > 3:
                        print(f"   ... and {len(result.issues) - 3} more")
                    issues_found.extend(result.issues)
                        
            except Exception as e:
                print(f"   ❌ Error analyzing {py_file.name}: {e}")
        
        # Overall statistics
        success_rate = (valid_imports / total_imports * 100) if total_imports > 0 else 100
        print(f"\n📈 Overall Import Analysis:")
        print(f"   Total imports analyzed: {total_imports}")
        print(f"   Valid imports: {valid_imports}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Total issues found: {len(issues_found)}")
        
        # Check for circular imports
        try:
            circular_imports = analyzer.find_circular_imports(python_files)
            if circular_imports:
                print(f"\n⚠️  Circular imports detected: {len(circular_imports)}")
                for cycle in circular_imports[:3]:
                    print(f"   - {' → '.join(cycle)}")
            else:
                print(f"\n✅ No circular imports detected")
        except Exception as e:
            print(f"\n❌ Error checking circular imports: {e}")
        
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
            logger = logging.getLogger('import-test-mcp-server')
            logger.info(f"Starting Import Test MCP Server with project root: {project_root}")
            
            server = ImportTestMCPServer(project_root)
            await server.serve()
            
        except KeyboardInterrupt:
            # Use stderr for exit messages in MCP mode
            print("\n🛑 Server stopped by user", file=sys.stderr)
        except Exception as e:
            print(f"❌ Server error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())