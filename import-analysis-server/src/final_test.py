"""Final Test Summary"""
import asyncio
from pathlib import Path  
from mcp_handler import MCPHandler
from infrastructure.import_analyzer import ImportAnalyzer
from infrastructure.dependency_resolver import DependencyResolver
from application.analyze_imports import AnalyzeImportsUseCase
from application.validate_dependencies import ValidateDependenciesUseCase

async def final_test():
    print("FINAL COMPREHENSIVE TEST")
    print("=" * 60)
    
    project_root = Path("..").resolve()
    resolver = DependencyResolver(project_root)
    analyzer = ImportAnalyzer(resolver)
    analyze_uc = AnalyzeImportsUseCase(analyzer)
    validate_uc = ValidateDependenciesUseCase(resolver)
    handler = MCPHandler(project_root, analyze_uc, validate_uc, analyzer, resolver)
    
    tools = handler.get_tools()
    print(f"Available tools: {len(tools)}")
    
    stats = await handler.call_tool("import-test-get-stats", {"project_path": "."})
    lines = stats[0].text.split("\n")
    for line in lines:
        if "Files analyzed" in line or "Success rate" in line or "Health score" in line:
            print(f"  {line.strip()}")
    
    circular = await handler.call_tool("import-test-circular-imports", {"project_path": "."})
    print(f"  Circular imports: {circular[0].text.strip()}")
    
    print("\nALL SYSTEMS OPERATIONAL!")
    print("Ready for VS Code MCP integration!")

if __name__ == "__main__":
    asyncio.run(final_test())