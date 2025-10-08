"""
MCP Handler for Import Testing
=============================

Handles MCP protocol tool calls for import analysis and validation.
"""

from pathlib import Path
from typing import Any, Dict, List

# Try to import MCP types with fallback
try:
    from mcp.types import TextContent, Tool
except ImportError:
    # Fallback for development
    class TextContent:
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text
    
    class Tool:
        def __init__(self, name: str, description: str, inputSchema: dict):
            self.name = name
            self.description = description
            self.inputSchema = inputSchema

from domain.models import ImportAnalysisOptions
from application.analyze_imports import AnalyzeImportsUseCase
from application.validate_dependencies import ValidateDependenciesUseCase
from infrastructure.import_analyzer import ImportAnalyzer
from infrastructure.dependency_resolver import DependencyResolver


class MCPHandler:
    """MCP protocol handler for import testing tools"""
    
    def __init__(
        self,
        project_root: Path,
        analyze_imports_uc: AnalyzeImportsUseCase,
        validate_deps_uc: ValidateDependenciesUseCase,
        import_analyzer: ImportAnalyzer,
        dependency_resolver: DependencyResolver
    ):
        self.project_root = project_root
        self.analyze_imports_uc = analyze_imports_uc
        self.validate_deps_uc = validate_deps_uc
        self.import_analyzer = import_analyzer
        self.dependency_resolver = dependency_resolver
    
    def get_tools(self) -> List[Tool]:
        """Return list of available import testing tools"""
        return [
            self._tool_analyze_file_imports(),
            self._tool_analyze_project_imports(),
            self._tool_check_circular_imports(),
            self._tool_validate_dependencies(),
            self._tool_find_unused_imports(),
            self._tool_check_import_style(),
            self._tool_resolve_import(),
            self._tool_get_import_stats(),
        ]
    
    def _tool_analyze_file_imports(self) -> Tool:
        """Tool for analyzing imports in a single file"""
        return Tool(
            name="import-test-analyze-file",
            description="Analyze imports in a single Python file to check validity and find issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the Python file to analyze"
                    },
                    "check_unused": {
                        "type": "boolean",
                        "description": "Check for unused imports",
                        "default": True
                    },
                    "check_style": {
                        "type": "boolean", 
                        "description": "Check import style and ordering",
                        "default": True
                    }
                },
                "required": ["file_path"]
            }
        )
    
    def _tool_analyze_project_imports(self) -> Tool:
        """Tool for analyzing imports across entire project"""
        return Tool(
            name="import-test-analyze-project",
            description="Analyze imports across all Python files in a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory to analyze"
                    },
                    "include_test_files": {
                        "type": "boolean",
                        "description": "Include test files in analysis",
                        "default": True
                    },
                    "max_files": {
                        "type": "integer",
                        "description": "Maximum number of files to analyze",
                        "default": 100
                    },
                    "exclude_patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Patterns to exclude from analysis",
                        "default": ["__pycache__", "*.pyc", ".git", ".venv"]
                    }
                },
                "required": ["project_path"]
            }
        )
    
    def _tool_check_circular_imports(self) -> Tool:
        """Tool for detecting circular imports"""
        return Tool(
            name="import-test-circular-imports",
            description="Detect circular import dependencies in a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory to check"
                    }
                },
                "required": ["project_path"]
            }
        )
    
    def _tool_validate_dependencies(self) -> Tool:
        """Tool for validating project dependencies"""
        return Tool(
            name="import-test-validate-dependencies",
            description="Validate project dependencies and find missing/unused packages",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory"
                    },
                    "check_missing": {
                        "type": "boolean",
                        "description": "Check for missing dependencies",
                        "default": True
                    },
                    "check_unused": {
                        "type": "boolean",
                        "description": "Check for unused dependencies",
                        "default": True
                    }
                },
                "required": ["project_path"]
            }
        )
    
    def _tool_find_unused_imports(self) -> Tool:
        """Tool for finding unused imports"""
        return Tool(
            name="import-test-unused-imports",
            description="Find unused imports in Python files",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file or directory to check"
                    }
                },
                "required": ["path"]
            }
        )
    
    def _tool_check_import_style(self) -> Tool:
        """Tool for checking import style consistency"""
        return Tool(
            name="import-test-check-style",
            description="Check import style consistency and ordering",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file or directory to check"
                    },
                    "style_guide": {
                        "type": "string",
                        "enum": ["pep8", "google", "custom"],
                        "description": "Style guide to follow",
                        "default": "pep8"
                    }
                },
                "required": ["path"]
            }
        )
    
    def _tool_resolve_import(self) -> Tool:
        """Tool for resolving individual imports"""
        return Tool(
            name="import-test-resolve-import",
            description="Check if a specific import can be resolved",
            inputSchema={
                "type": "object",
                "properties": {
                    "import_statement": {
                        "type": "string",
                        "description": "Import statement to check (e.g., 'from module import name')"
                    },
                    "from_file": {
                        "type": "string",
                        "description": "File path where the import is used"
                    }
                },
                "required": ["import_statement", "from_file"]
            }
        )
    
    def _tool_get_import_stats(self) -> Tool:
        """Tool for getting import statistics"""
        return Tool(
            name="import-test-get-stats",
            description="Get comprehensive import statistics for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory"
                    }
                },
                "required": ["project_path"]
            }
        )
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls"""
        try:
            if name == "import-test-analyze-file":
                return await self._analyze_file_imports(arguments)
            elif name == "import-test-analyze-project":
                return await self._analyze_project_imports(arguments)
            elif name == "import-test-circular-imports":
                return await self._check_circular_imports(arguments)
            elif name == "import-test-validate-dependencies":
                return await self._validate_dependencies(arguments)
            elif name == "import-test-unused-imports":
                return await self._find_unused_imports(arguments)
            elif name == "import-test-check-style":
                return await self._check_import_style(arguments)
            elif name == "import-test-resolve-import":
                return await self._resolve_import(arguments)
            elif name == "import-test-get-stats":
                return await self._get_import_stats(arguments)
            else:
                return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]
                
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error executing {name}: {str(e)}")]
    
    async def _analyze_file_imports(self, args: Dict[str, Any]) -> List[TextContent]:
        """Analyze imports in a single file"""
        file_path = Path(args["file_path"])
        if not file_path.is_absolute():
            file_path = self.project_root / file_path
        
        if not file_path.exists():
            return [TextContent(type="text", text=f"❌ File not found: {file_path}")]
        
        if not file_path.suffix == ".py":
            return [TextContent(type="text", text=f"❌ Only Python files are supported: {file_path}")]
        
        try:
            analysis = self.analyze_imports_uc.execute(file_path)
            output = self._format_file_analysis(analysis)
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Analysis failed: {str(e)}")]
    
    async def _analyze_project_imports(self, args: Dict[str, Any]) -> List[TextContent]:
        """Analyze imports across entire project"""
        project_path = Path(args["project_path"])
        if not project_path.is_absolute():
            project_path = self.project_root / project_path
        
        if not project_path.exists():
            return [TextContent(type="text", text=f"❌ Project path not found: {project_path}")]
        
        try:
            # Set up analysis options
            options = ImportAnalysisOptions(
                include_test_files=args.get("include_test_files", True),
                max_files=args.get("max_files", 100),
                exclude_patterns=args.get("exclude_patterns", ["__pycache__", "*.pyc", ".git", ".venv"])
            )
            
            analysis = self.import_analyzer.analyze_project(project_path, options)
            output = self._format_project_analysis(analysis)
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Project analysis failed: {str(e)}")]
    
    async def _check_circular_imports(self, args: Dict[str, Any]) -> List[TextContent]:
        """Check for circular imports"""
        project_path = Path(args["project_path"])
        if not project_path.is_absolute():
            project_path = self.project_root / project_path
        
        try:
            # Find all Python files
            python_files = list(project_path.rglob("*.py"))
            python_files = [f for f in python_files if "__pycache__" not in str(f)]
            
            circular_imports = self.import_analyzer.find_circular_imports(python_files)
            
            if not circular_imports:
                return [TextContent(type="text", text="✅ No circular imports detected!")]
            
            output = f"⚠️  Found {len(circular_imports)} circular import(s):\n\n"
            for i, cycle in enumerate(circular_imports, 1):
                output += f"{i}. {cycle.cycle_description}\n"
            
            return [TextContent(type="text", text=output.strip())]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Circular import check failed: {str(e)}")]
    
    async def _validate_dependencies(self, args: Dict[str, Any]) -> List[TextContent]:
        """Validate project dependencies"""
        project_path = Path(args["project_path"])
        if not project_path.is_absolute():
            project_path = self.project_root / project_path
        
        try:
            installed_packages, missing_packages = self.validate_deps_uc.execute(project_path)
            
            output = f"📦 Dependency Validation Results\n"
            output += f"{'=' * 50}\n\n"
            
            output += f"📥 Installed Packages: {len(installed_packages)}\n"
            if installed_packages:
                for name, info in list(installed_packages.items())[:10]:  # Show first 10
                    output += f"  ✅ {info}\n"
                if len(installed_packages) > 10:
                    output += f"  ... and {len(installed_packages) - 10} more\n"
            
            if missing_packages:
                output += f"\n❌ Missing Packages: {len(missing_packages)}\n"
                for pkg in missing_packages:
                    output += f"  - {pkg}\n"
            else:
                output += f"\n✅ No missing packages detected\n"
            
            return [TextContent(type="text", text=output.strip())]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Dependency validation failed: {str(e)}")]
    
    async def _find_unused_imports(self, args: Dict[str, Any]) -> List[TextContent]:
        """Find unused imports"""
        path = Path(args["path"])
        if not path.is_absolute():
            path = self.project_root / path
        
        try:
            if path.is_file():
                analysis = self.analyze_imports_uc.execute(path)
                unused_issues = [issue for issue in analysis.issues 
                               if issue.issue_type.value == "unused_import"]
                
                if not unused_issues:
                    return [TextContent(type="text", text=f"✅ No unused imports found in {path.name}")]
                
                output = f"🗑️  Found {len(unused_issues)} unused import(s) in {path.name}:\n\n"
                for issue in unused_issues:
                    output += f"  Line {issue.line_number}: {issue.message}\n"
                
            else:
                # Directory analysis
                python_files = list(path.rglob("*.py"))
                python_files = [f for f in python_files if "__pycache__" not in str(f)]
                
                total_unused = 0
                files_with_unused = []
                
                for file_path in python_files[:50]:  # Limit to 50 files
                    analysis = self.analyze_imports_uc.execute(file_path)
                    unused_issues = [issue for issue in analysis.issues 
                                   if issue.issue_type.value == "unused_import"]
                    
                    if unused_issues:
                        total_unused += len(unused_issues)
                        files_with_unused.append((file_path, unused_issues))
                
                if total_unused == 0:
                    return [TextContent(type="text", text="✅ No unused imports found in project!")]
                
                output = f"🗑️  Found {total_unused} unused import(s) in {len(files_with_unused)} file(s):\n\n"
                for file_path, issues in files_with_unused:
                    rel_path = file_path.relative_to(path)
                    output += f"📄 {rel_path} ({len(issues)} unused):\n"
                    for issue in issues[:3]:  # Show first 3 per file
                        output += f"  - Line {issue.line_number}: {issue.message}\n"
                    if len(issues) > 3:
                        output += f"  ... and {len(issues) - 3} more\n"
                    output += "\n"
            
            return [TextContent(type="text", text=output.strip())]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Unused import check failed: {str(e)}")]
    
    async def _check_import_style(self, args: Dict[str, Any]) -> List[TextContent]:
        """Check import style consistency"""
        # This is a placeholder - would need more sophisticated style checking
        return [TextContent(type="text", text="🔧 Import style checking not yet implemented")]
    
    async def _resolve_import(self, args: Dict[str, Any]) -> List[TextContent]:
        """Resolve a specific import"""
        # This would need to parse the import statement and check resolution
        return [TextContent(type="text", text="🔧 Individual import resolution not yet implemented")]
    
    async def _get_import_stats(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get import statistics for project"""
        project_path = Path(args["project_path"])
        if not project_path.is_absolute():
            project_path = self.project_root / project_path
        
        try:
            options = ImportAnalysisOptions()
            analysis = self.import_analyzer.analyze_project(project_path, options)
            
            output = f"📊 Import Statistics\n"
            output += f"{'=' * 50}\n\n"
            output += f"📁 Project: {project_path.name}\n"
            output += f"📄 Files analyzed: {analysis.total_files}\n"
            output += f"📦 Total imports: {analysis.total_imports}\n"
            output += f"✅ Valid imports: {analysis.total_valid_imports}\n"
            output += f"❌ Invalid imports: {analysis.total_imports - analysis.total_valid_imports}\n"
            output += f"⚠️  Total issues: {analysis.total_issues}\n"
            output += f"🔄 Circular imports: {len(analysis.circular_imports)}\n"
            output += f"📈 Success rate: {analysis.success_rate}%\n"
            output += f"🏥 Health score: {analysis.overall_health_score}/100\n"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Statistics generation failed: {str(e)}")]
    
    def _format_file_analysis(self, analysis) -> str:
        """Format single file analysis result"""
        output = f"🔍 Import Analysis: {analysis.file_path.name}\n"
        output += f"{'=' * 60}\n\n"
        
        # Summary stats
        output += f"📊 Summary:\n"
        output += f"  Total imports: {len(analysis.imports)}\n"
        output += f"  Valid imports: {analysis.valid_imports_count}\n"
        output += f"  Invalid imports: {analysis.invalid_imports_count}\n"
        output += f"  Issues found: {len(analysis.issues)}\n"
        output += f"  Health score: {analysis.health_score}/100\n\n"
        
        # Import details
        if analysis.imports:
            output += f"📦 Imports ({len(analysis.imports)}):\n"
            for imp in analysis.imports:
                status = "✅" if imp.is_valid else "❌"
                output += f"  {status} Line {imp.line_number}: {imp.full_name} [{imp.import_type.value}]\n"
            output += "\n"
        
        # Issues
        if analysis.issues:
            output += f"⚠️  Issues ({len(analysis.issues)}):\n"
            for issue in analysis.issues:
                severity_emoji = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(issue.severity.value, "⚪")
                output += f"  {severity_emoji} Line {issue.line_number}: [{issue.issue_type.value}] {issue.message}\n"
                if issue.suggestion:
                    output += f"     💡 {issue.suggestion}\n"
        else:
            output += "✅ No issues found!\n"
        
        return output.strip()
    
    def _format_project_analysis(self, analysis) -> str:
        """Format project-wide analysis result"""
        output = f"📁 Project Import Analysis: {analysis.project_root.name}\n"
        output += f"{'=' * 60}\n\n"
        
        # Overall stats
        output += f"📊 Overall Statistics:\n"
        output += f"  Files analyzed: {analysis.total_files}\n"
        output += f"  Total imports: {analysis.total_imports}\n"
        output += f"  Valid imports: {analysis.total_valid_imports}\n"
        output += f"  Success rate: {analysis.success_rate}%\n"
        output += f"  Health score: {analysis.overall_health_score}/100\n"
        output += f"  Total issues: {analysis.total_issues}\n"
        output += f"  Circular imports: {len(analysis.circular_imports)}\n\n"
        
        # File breakdown
        if analysis.file_analyses:
            # Show worst performing files
            worst_files = sorted(analysis.file_analyses, key=lambda x: x.health_score)[:5]
            if worst_files:
                output += f"📉 Files needing attention:\n"
                for file_analysis in worst_files:
                    rel_path = file_analysis.file_path.relative_to(analysis.project_root)
                    output += f"  🔴 {rel_path}: {file_analysis.health_score}/100 ({len(file_analysis.issues)} issues)\n"
                output += "\n"
        
        # Circular imports
        if analysis.circular_imports:
            output += f"🔄 Circular Imports ({len(analysis.circular_imports)}):\n"
            for cycle in analysis.circular_imports:
                output += f"  ⚠️  {cycle.cycle_description}\n"
            output += "\n"
        
        # Dependencies
        if analysis.missing_dependencies:
            output += f"❌ Missing Dependencies ({len(analysis.missing_dependencies)}):\n"
            for dep in analysis.missing_dependencies:
                output += f"  - {dep}\n"
            output += "\n"
        
        if analysis.unused_dependencies:
            output += f"🗑️  Unused Dependencies ({len(analysis.unused_dependencies)}):\n"
            for dep in analysis.unused_dependencies:
                output += f"  - {dep}\n"
        
        return output.strip()