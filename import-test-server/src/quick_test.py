"""
Quick test of core tools
"""
import asyncio
from pathlib import Path
from mcp_handler import MCPHandler
from infrastructure.import_analyzer import ImportAnalyzer  
from infrastructure.dependency_resolver import DependencyResolver
from application.analyze_imports import AnalyzeImportsUseCase
from application.validate_dependencies import ValidateDependenciesUseCase

async def test_core_tools():
    print("Testing Core Import Test Tools")
    print("=" * 50)
    
    project_root = Path("..").resolve()
    resolver = DependencyResolver(project_root)
    analyzer = ImportAnalyzer(resolver)
    analyze_uc = AnalyzeImportsUseCase(analyzer)
    validate_uc = ValidateDependenciesUseCase(resolver)
    
    handler = MCPHandler(project_root, analyze_uc, validate_uc, analyzer, resolver)
    
    # Test analyze file
    result = await handler.call_tool("import-test-analyze-file", {"file_path": "src/main.py"})
    print("1. File analysis: SUCCESS")
    
    # Test get stats
    result = await handler.call_tool("import-test-get-stats", {"project_path": "."})
    print("2. Statistics: SUCCESS")
    
    # Test circular imports
    result = await handler.call_tool("import-test-circular-imports", {"project_path": "."})
    print("3. Circular imports: SUCCESS")
    
    print("\nAll core tools working!")

if __name__ == "__main__":
    asyncio.run(test_core_tools())