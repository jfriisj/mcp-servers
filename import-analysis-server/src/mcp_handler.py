"""
MCP Handler for Import Testing
=============================

Handles MCP protocol tool calls for import analysis and validation.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

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
            self._tool_dependency_tree(),
            self._tool_service_dependencies(),
            self._tool_architecture_analysis(),
        ]
    
    def _tool_analyze_file_imports(self) -> Tool:
        """Tool for analyzing imports in a single file"""
        return Tool(
            name="import-analysis-analyze-file",
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
            name="import-analysis-analyze-project",
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
            name="import-analysis-circular-imports",
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
            name="import-analysis-validate-dependencies",
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
            name="import-analysis-unused-imports",
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
            name="import-analysis-check-style",
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
            name="import-analysis-resolve-import",
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
            name="import-analysis-get-stats",
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
    
    def _tool_dependency_tree(self) -> Tool:
        """Tool for generating dependency tree structure"""
        return Tool(
            name="import-analysis-dependency-tree",
            description="Generate a tree structure diagram of import dependencies",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory to analyze"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["text", "ascii", "mermaid", "json"],
                        "description": "Output format for the dependency tree",
                        "default": "text"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth of dependency tree to show",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10
                    },
                    "include_external": {
                        "type": "boolean",
                        "description": "Include external library dependencies",
                        "default": False
                    },
                    "root_module": {
                        "type": "string",
                        "description": "Start tree from specific module (optional)"
                    }
                },
                "required": ["project_path"]
            }
        )
    
    def _tool_service_dependencies(self) -> Tool:
        """Tool for analyzing service-to-service dependencies"""
        return Tool(
            name="import-analysis-service-dependencies",
            description="Analyze cross-service dependencies and usage patterns between different layers/services",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory to analyze"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["text", "mermaid", "json", "matrix"],
                        "description": "Output format for service dependency analysis",
                        "default": "text"
                    },
                    "group_by": {
                        "type": "string",
                        "enum": ["layer", "package", "service"],
                        "description": "How to group services/modules",
                        "default": "layer"
                    },
                    "show_details": {
                        "type": "boolean", 
                        "description": "Show detailed usage information",
                        "default": False
                    }
                },
                "required": ["project_path"]
            }
        )
    
    def _tool_architecture_analysis(self) -> Tool:
        """Tool for analyzing overall architecture patterns"""
        return Tool(
            name="import-analysis-architecture-analysis",
            description="Analyze architectural patterns, layer violations, and design principles adherence",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory to analyze"
                    },
                    "architecture_type": {
                        "type": "string",
                        "enum": ["clean", "layered", "hexagonal", "auto"],
                        "description": "Expected architecture pattern",
                        "default": "auto"
                    },
                    "check_violations": {
                        "type": "boolean",
                        "description": "Check for architectural violations",
                        "default": True
                    },
                    "format": {
                        "type": "string",
                        "enum": ["text", "mermaid", "json"],
                        "description": "Output format",
                        "default": "text"
                    }
                },
                "required": ["project_path"]
            }
        )
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls"""
        try:
            if name == "import-analysis-analyze-file":
                return await self._analyze_file_imports(arguments)
            elif name == "import-analysis-analyze-project":
                return await self._analyze_project_imports(arguments)
            elif name == "import-analysis-circular-imports":
                return await self._check_circular_imports(arguments)
            elif name == "import-analysis-validate-dependencies":
                return await self._validate_dependencies(arguments)
            elif name == "import-analysis-unused-imports":
                return await self._find_unused_imports(arguments)
            elif name == "import-analysis-check-style":
                return await self._check_import_style(arguments)
            elif name == "import-analysis-resolve-import":
                return await self._resolve_import(arguments)
            elif name == "import-analysis-get-stats":
                return await self._get_import_stats(arguments)
            elif name == "import-analysis-dependency-tree":
                return await self._generate_dependency_tree(arguments)
            elif name == "import-analysis-service-dependencies":
                return await self._analyze_service_dependencies(arguments)
            elif name == "import-analysis-architecture-analysis":
                return await self._analyze_architecture(arguments)
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
        path = Path(args["path"])
        if not path.is_absolute():
            path = self.project_root / path
        
        if not path.exists():
            return [TextContent(type="text", text=f"❌ Path not found: {path}")]
        
        try:
            style_guide = args.get("style_guide", "pep8")
            style_issues = []
            files_checked = 0
            
            # Get Python files to check
            if path.is_file():
                if path.suffix == ".py":
                    python_files = [path]
                else:
                    return [TextContent(type="text", text=f"❌ Only Python files are supported: {path}")]
            else:
                python_files = list(path.rglob("*.py"))
                python_files = [f for f in python_files if "__pycache__" not in str(f)]
            
            # Check each file for style issues
            for file_path in python_files[:50]:  # Limit to 50 files
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    file_issues = self._check_file_import_style(file_path, content, style_guide)
                    if file_issues:
                        style_issues.extend(file_issues)
                    files_checked += 1
                    
                except Exception as e:
                    # Skip files that can't be read
                    continue
            
            # Format results
            if not style_issues:
                return [TextContent(type="text", text=f"✅ No import style issues found in {files_checked} file(s)!")]
            
            output = f"� Import Style Issues ({style_guide.upper()} guide)\n"
            output += f"{'=' * 60}\n\n"
            output += f"📊 Summary: {len(style_issues)} issue(s) in {files_checked} file(s)\n\n"
            
            # Group issues by file
            issues_by_file = {}
            for issue in style_issues:
                file_name = issue["file"]
                if file_name not in issues_by_file:
                    issues_by_file[file_name] = []
                issues_by_file[file_name].append(issue)
            
            # Display issues
            for file_name, file_issues in list(issues_by_file.items())[:10]:  # Show first 10 files
                rel_path = Path(file_name).relative_to(path) if path.is_dir() else Path(file_name).name
                output += f"📄 {rel_path} ({len(file_issues)} issue(s)):\n"
                
                for issue in file_issues[:5]:  # Show first 5 issues per file
                    severity_emoji = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(issue["severity"], "⚪")
                    output += f"  {severity_emoji} Line {issue['line']}: {issue['message']}\n"
                    if issue.get("suggestion"):
                        output += f"     💡 {issue['suggestion']}\n"
                
                if len(file_issues) > 5:
                    output += f"  ... and {len(file_issues) - 5} more issues\n"
                output += "\n"
            
            if len(issues_by_file) > 10:
                output += f"... and {len(issues_by_file) - 10} more files with issues\n"
            
            return [TextContent(type="text", text=output.strip())]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Style check failed: {str(e)}")]
    
    def _check_file_import_style(self, file_path: Path, content: str, style_guide: str) -> List[Dict]:
        """Check import style in a single file"""
        import ast
        import re
        
        issues = []
        lines = content.split('\n')
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []  # Skip files with syntax errors
        
        # Find all import statements
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'name': alias.asname or alias.name,
                        'line': node.lineno,
                        'full_line': lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append({
                        'type': 'from',
                        'module': module,
                        'name': alias.name,
                        'asname': alias.asname,
                        'line': node.lineno,
                        'level': node.level,  # For relative imports
                        'full_line': lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                    })
        
        if not imports:
            return []
        
        # Apply style checks based on guide
        if style_guide == "pep8":
            issues.extend(self._check_pep8_import_style(file_path, imports, lines))
        elif style_guide == "google":
            issues.extend(self._check_google_import_style(file_path, imports, lines))
        else:  # custom
            issues.extend(self._check_custom_import_style(file_path, imports, lines))
        
        return issues
    
    def _check_pep8_import_style(self, file_path: Path, imports: List[Dict], lines: List[str]) -> List[Dict]:
        """Check PEP 8 import style compliance"""
        issues = []
        
        # Group imports by type
        stdlib_imports = []
        thirdparty_imports = []
        local_imports = []
        
        stdlib_modules = {
            'os', 'sys', 'json', 'datetime', 'pathlib', 'typing', 'collections',
            'itertools', 'functools', 'asyncio', 'threading', 'multiprocessing',
            'unittest', 'logging', 'argparse', 'configparser', 're', 'ast'
        }
        
        for imp in imports:
            # Classify import type
            if imp['module'].split('.')[0] in stdlib_modules:
                stdlib_imports.append(imp)
            elif imp['module'].startswith('.') or imp.get('level', 0) > 0:
                local_imports.append(imp)
            else:
                thirdparty_imports.append(imp)
        
        # Check import ordering (PEP 8: stdlib, third-party, local)
        all_imports = stdlib_imports + thirdparty_imports + local_imports
        current_imports = sorted(imports, key=lambda x: x['line'])
        
        # Check if imports are properly grouped and separated
        prev_group = None
        blank_line_expected = False
        
        for i, imp in enumerate(current_imports):
            # Determine current group
            if imp in stdlib_imports:
                current_group = 'stdlib'
            elif imp in thirdparty_imports:
                current_group = 'thirdparty'
            else:
                current_group = 'local'
            
            # Check for proper grouping
            if prev_group and current_group != prev_group:
                # Should have blank line between groups
                line_before = imp['line'] - 2  # -1 for 0-based, -1 for line before
                if (line_before >= 0 and line_before < len(lines) and 
                    lines[line_before].strip() != ""):
                    issues.append({
                        'file': str(file_path),
                        'line': imp['line'],
                        'severity': 'warning',
                        'message': f"Missing blank line between {prev_group} and {current_group} imports",
                        'suggestion': f"Add blank line before this {current_group} import"
                    })
            
            # Check for wildcard imports
            if imp.get('name') == '*':
                issues.append({
                    'file': str(file_path),
                    'line': imp['line'],
                    'severity': 'warning',
                    'message': "Wildcard import should be avoided",
                    'suggestion': "Import specific names instead of using '*'"
                })
            
            # Check for multiple imports on same line (for 'import' statements)
            if imp['type'] == 'import' and ',' in imp['full_line']:
                issues.append({
                    'file': str(file_path),
                    'line': imp['line'],
                    'severity': 'info',
                    'message': "Multiple imports on same line",
                    'suggestion': "Put each import on separate lines"
                })
            
            prev_group = current_group
        
        # Check alphabetical ordering within groups
        for group_name, group_imports in [
            ('stdlib', stdlib_imports),
            ('third-party', thirdparty_imports),
            ('local', local_imports)
        ]:
            if len(group_imports) > 1:
                sorted_group = sorted(group_imports, key=lambda x: x['module'])
                if [imp['module'] for imp in group_imports] != [imp['module'] for imp in sorted_group]:
                    # Find first out-of-order import
                    for i, imp in enumerate(group_imports):
                        if i > 0 and imp['module'] < group_imports[i-1]['module']:
                            issues.append({
                                'file': str(file_path),
                                'line': imp['line'],
                                'severity': 'info',
                                'message': f"Imports within {group_name} group should be alphabetically sorted",
                                'suggestion': f"Move '{imp['module']}' to correct alphabetical position"
                            })
                            break
        
        return issues
    
    def _check_google_import_style(self, file_path: Path, imports: List[Dict], lines: List[str]) -> List[Dict]:
        """Check Google Python style guide compliance"""
        issues = []
        
        # Google style is similar to PEP 8 but with some differences
        # For now, use PEP 8 as base and add Google-specific rules
        pep8_issues = self._check_pep8_import_style(file_path, imports, lines)
        issues.extend(pep8_issues)
        
        # Google-specific rules can be added here
        for imp in imports:
            # Google prefers 'from x import y' for single items
            if imp['type'] == 'import' and '.' not in imp['module']:
                # This is a simple module import - OK
                pass
        
        return issues
    
    def _check_custom_import_style(self, file_path: Path, imports: List[Dict], lines: List[str]) -> List[Dict]:
        """Check custom import style rules"""
        issues = []
        
        # Basic custom rules - can be extended
        for imp in imports:
            # Check for unused imports (basic check)
            if imp.get('name') and imp['name'].startswith('_'):
                issues.append({
                    'file': str(file_path),
                    'line': imp['line'],
                    'severity': 'info',
                    'message': f"Import '{imp['name']}' starts with underscore (may be internal)",
                    'suggestion': "Consider if this internal import is necessary"
                })
        
        return issues
    
    async def _resolve_import(self, args: Dict[str, Any]) -> List[TextContent]:
        """Resolve a specific import"""
        import_statement = args["import_statement"]
        from_file = Path(args["from_file"])
        
        if not from_file.is_absolute():
            from_file = self.project_root / from_file
        
        if not from_file.exists():
            return [TextContent(type="text", text=f"❌ Source file not found: {from_file}")]
        
        try:
            # Parse the import statement
            import_info = self._parse_import_statement(import_statement)
            if not import_info:
                return [TextContent(type="text", text=f"❌ Invalid import statement: {import_statement}")]
            
            # Try to resolve the import
            resolution_result = self._attempt_import_resolution(import_info, from_file)
            
            # Format the result
            output = f"🔍 Import Resolution: {import_statement}\n"
            output += f"{'=' * 60}\n\n"
            
            output += f"📄 Source File: {from_file.name}\n"
            output += f"� Import Type: {import_info['type']}\n"
            output += f"🎯 Target Module: {import_info['module']}\n"
            
            if import_info.get('names'):
                output += f"📋 Imported Names: {', '.join(import_info['names'])}\n"
            
            output += f"\n🔎 Resolution Status: "
            
            if resolution_result['success']:
                output += f"✅ RESOLVED\n"
                output += f"📍 Resolved to: {resolution_result['resolved_path']}\n"
                
                if resolution_result.get('module_type'):
                    output += f"🏷️  Module Type: {resolution_result['module_type']}\n"
                
                if resolution_result.get('available_names'):
                    available = resolution_result['available_names'][:10]  # Show first 10
                    output += f"📚 Available Names: {', '.join(available)}\n"
                    if len(resolution_result['available_names']) > 10:
                        output += f"    ... and {len(resolution_result['available_names']) - 10} more\n"
                
                # Check if imported names are actually available
                if import_info.get('names'):
                    unavailable = []
                    available_set = set(resolution_result.get('available_names', []))
                    
                    for name in import_info['names']:
                        if name != '*' and name not in available_set:
                            unavailable.append(name)
                    
                    if unavailable:
                        output += f"\n⚠️  Unavailable Names: {', '.join(unavailable)}\n"
                        output += f"💡 These names are imported but not found in the target module\n"
                
            else:
                output += f"❌ FAILED\n"
                output += f"💔 Reason: {resolution_result['error']}\n"
                
                if resolution_result.get('suggestions'):
                    output += f"\n💡 Suggestions:\n"
                    for suggestion in resolution_result['suggestions']:
                        output += f"  • {suggestion}\n"
            
            # Additional context
            if resolution_result.get('is_relative'):
                output += f"\n🔗 Relative Import: {'Yes' if resolution_result['is_relative'] else 'No'}\n"
            
            if resolution_result.get('search_paths'):
                output += f"\n🛣️  Search Paths Checked:\n"
                for path in resolution_result['search_paths'][:5]:  # Show first 5
                    output += f"  • {path}\n"
                if len(resolution_result['search_paths']) > 5:
                    output += f"  • ... and {len(resolution_result['search_paths']) - 5} more\n"
            
            return [TextContent(type="text", text=output.strip())]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Import resolution failed: {str(e)}")]
    
    def _parse_import_statement(self, import_statement: str) -> Optional[Dict]:
        """Parse an import statement into its components"""
        import ast
        import re
        
        # Clean up the statement
        statement = import_statement.strip()
        if not statement:
            return None
        
        try:
            # Try to parse as Python code
            tree = ast.parse(statement)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # Handle: import module [as alias]
                    if node.names:
                        alias = node.names[0]  # Take first one
                        return {
                            'type': 'import',
                            'module': alias.name,
                            'alias': alias.asname,
                            'names': []
                        }
                
                elif isinstance(node, ast.ImportFrom):
                    # Handle: from module import name [as alias]
                    module = node.module or ""
                    names = []
                    
                    for alias in node.names:
                        names.append(alias.name)
                    
                    return {
                        'type': 'from',
                        'module': module,
                        'names': names,
                        'level': node.level  # For relative imports
                    }
        
        except SyntaxError:
            # If AST parsing fails, try regex parsing
            pass
        
        # Fallback regex parsing
        # Match: from module import name1, name2
        from_match = re.match(r'from\s+([\w.]+)\s+import\s+(.+)', statement)
        if from_match:
            module = from_match.group(1)
            imports_str = from_match.group(2)
            names = [name.strip() for name in imports_str.split(',')]
            return {
                'type': 'from',
                'module': module,
                'names': names,
                'level': 0
            }
        
        # Match: import module
        import_match = re.match(r'import\s+([\w.]+)(?:\s+as\s+([\w.]+))?', statement)
        if import_match:
            module = import_match.group(1)
            alias = import_match.group(2)
            return {
                'type': 'import',
                'module': module,
                'alias': alias,
                'names': []
            }
        
        return None
    
    def _attempt_import_resolution(self, import_info: Dict, from_file: Path) -> Dict:
        """Attempt to resolve an import and return detailed results"""
        import sys
        import os
        import importlib.util
        from importlib import import_module
        
        result = {
            'success': False,
            'error': None,
            'resolved_path': None,
            'module_type': None,
            'available_names': [],
            'is_relative': False,
            'search_paths': [],
            'suggestions': []
        }
        
        module_name = import_info['module']
        is_relative = import_info.get('level', 0) > 0 or module_name.startswith('.')
        result['is_relative'] = is_relative
        
        # Build search paths
        search_paths = []
        
        # Add directory of source file
        source_dir = from_file.parent
        search_paths.append(str(source_dir))
        
        # Add project root
        search_paths.append(str(self.project_root))
        
        # Add parent directories for relative imports
        if is_relative:
            current_dir = source_dir
            for _ in range(import_info.get('level', 1)):
                current_dir = current_dir.parent
                search_paths.append(str(current_dir))
        
        # Add Python sys.path
        search_paths.extend(sys.path)
        
        result['search_paths'] = search_paths
        
        # Try different resolution strategies
        resolved_path = None
        
        # Strategy 1: Direct file/directory check
        for search_path in search_paths[:5]:  # Check first 5 paths
            try:
                search_dir = Path(search_path)
                if not search_dir.exists():
                    continue
                
                # Convert module name to file path
                module_parts = module_name.strip('.').split('.')
                
                # Try as file
                potential_file = search_dir
                for part in module_parts:
                    potential_file = potential_file / part
                
                # Check .py file
                py_file = potential_file.with_suffix('.py')
                if py_file.exists():
                    resolved_path = py_file
                    result['module_type'] = 'file'
                    break
                
                # Check as package (__init__.py)
                init_file = potential_file / '__init__.py'
                if init_file.exists():
                    resolved_path = init_file
                    result['module_type'] = 'package'
                    break
                    
            except Exception:
                continue
        
        # Strategy 2: Try importlib (for installed packages)
        if not resolved_path:
            try:
                spec = importlib.util.find_spec(module_name)
                if spec and spec.origin:
                    resolved_path = Path(spec.origin)
                    result['module_type'] = 'installed_package'
            except (ImportError, ModuleNotFoundError, ValueError):
                pass
        
        # If resolved, try to extract available names
        if resolved_path:
            result['success'] = True
            result['resolved_path'] = str(resolved_path)
            
            # Try to get available names
            try:
                available_names = self._extract_module_names(resolved_path)
                result['available_names'] = available_names
            except Exception:
                result['available_names'] = []
        
        else:
            # Resolution failed - provide helpful error and suggestions
            result['success'] = False
            result['error'] = f"Module '{module_name}' could not be resolved"
            
            # Generate suggestions
            suggestions = []
            
            # Check for similar names in search paths
            similar_modules = self._find_similar_modules(module_name, search_paths[:3])
            if similar_modules:
                suggestions.append(f"Similar modules found: {', '.join(similar_modules[:3])}")
            
            # Check if it might be an installed package
            try:
                import pkg_resources
                installed_packages = [pkg.project_name for pkg in pkg_resources.working_set]
                similar_packages = [pkg for pkg in installed_packages if module_name.lower() in pkg.lower()][:3]
                if similar_packages:
                    suggestions.append(f"Similar installed packages: {', '.join(similar_packages)}")
            except Exception:
                pass
            
            # General suggestions
            if is_relative:
                suggestions.append("For relative imports, ensure the module structure is correct")
            else:
                suggestions.append("Check if the module is installed or in the Python path")
                suggestions.append("Verify the module name spelling")
            
            result['suggestions'] = suggestions
        
        return result
    
    def _extract_module_names(self, module_path: Path) -> List[str]:
        """Extract available names from a Python module"""
        import ast
        
        names = []
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Functions
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):  # Skip private functions
                        names.append(node.name)
                
                # Classes
                elif isinstance(node, ast.ClassDef):
                    if not node.name.startswith('_'):
                        names.append(node.name)
                
                # Variables/Constants (assignments at module level)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if not target.id.startswith('_'):
                                names.append(target.id)
                
                # Imports (re-exported)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname or alias.name
                        if not name.startswith('_'):
                            names.append(name)
                
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name != '*':
                            name = alias.asname or alias.name
                            if not name.startswith('_'):
                                names.append(name)
        
        except Exception:
            # If parsing fails, return empty list
            pass
        
        return sorted(list(set(names)))  # Remove duplicates and sort
    
    def _find_similar_modules(self, target_module: str, search_paths: List[str]) -> List[str]:
        """Find modules with similar names"""
        import difflib
        
        found_modules = []
        
        for search_path in search_paths:
            try:
                search_dir = Path(search_path)
                if not search_dir.exists():
                    continue
                
                # Find Python files and packages
                for item in search_dir.iterdir():
                    if item.is_file() and item.suffix == '.py':
                        module_name = item.stem
                        found_modules.append(module_name)
                    elif item.is_dir() and (item / '__init__.py').exists():
                        found_modules.append(item.name)
                        
            except Exception:
                continue
        
        # Find similar names using difflib
        similar = difflib.get_close_matches(target_module, found_modules, n=5, cutoff=0.6)
        return similar
    
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
    
    async def _generate_dependency_tree(self, args: Dict[str, Any]) -> List[TextContent]:
        """Generate dependency tree structure diagram"""
        project_path = Path(args["project_path"])
        if not project_path.is_absolute():
            project_path = self.project_root / project_path
        
        if not project_path.exists():
            return [TextContent(type="text", text=f"❌ Project path not found: {project_path}")]
        
        try:
            format_type = args.get("format", "text")
            max_depth = args.get("max_depth", 5)
            include_external = args.get("include_external", False)
            root_module = args.get("root_module")
            
            # Build dependency tree
            dependency_tree = self._build_dependency_tree(
                project_path, 
                max_depth, 
                include_external, 
                root_module
            )
            
            # Format based on requested type
            if format_type == "mermaid":
                output = self._format_tree_mermaid(dependency_tree)
            elif format_type == "json":
                import json
                output = json.dumps(dependency_tree, indent=2, default=str)
            elif format_type == "ascii":
                output = self._format_tree_ascii(dependency_tree)
            else:  # text format
                output = self._format_tree_text(dependency_tree)
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Dependency tree generation failed: {str(e)}")]
    
    def _build_dependency_tree(self, project_path: Path, max_depth: int, include_external: bool, root_module: Optional[str] = None) -> Dict:
        """Build dependency tree structure"""
        # Find all Python files
        python_files = list(project_path.rglob("*.py"))
        python_files = [f for f in python_files if "__pycache__" not in str(f)]
        
        # Build import map
        import_map = {}
        all_modules = set()
        
        for file_path in python_files:
            try:
                analysis = self.analyze_imports_uc.execute(file_path)
                
                # Convert file path to module name
                rel_path = file_path.relative_to(project_path)
                if rel_path.name == "__init__.py":
                    module_name = str(rel_path.parent).replace("/", ".").replace("\\", ".")
                    if module_name == ".":
                        continue
                else:
                    module_name = str(rel_path.with_suffix("")).replace("/", ".").replace("\\", ".")
                
                all_modules.add(module_name)
                import_map[module_name] = {
                    "file_path": file_path,
                    "imports": [],
                    "external_imports": []
                }
                
                for imp in analysis.imports:
                    if imp.is_valid:
                        # Determine if import is internal or external
                        is_internal = self._is_internal_import(imp.module, all_modules, project_path)
                        
                        if is_internal:
                            import_map[module_name]["imports"].append(imp.module)
                        elif include_external:
                            import_map[module_name]["external_imports"].append(imp.module)
                            
            except Exception:
                continue  # Skip files with analysis errors
        
        # Build tree structure
        if root_module and root_module in import_map:
            tree = self._build_tree_node(root_module, import_map, set(), max_depth, 0)
        else:
            # Find entry points (modules not imported by others)
            imported_modules = set()
            for module_data in import_map.values():
                imported_modules.update(module_data["imports"])
            
            entry_points = [mod for mod in import_map.keys() if mod not in imported_modules]
            
            if not entry_points:
                entry_points = list(import_map.keys())[:5]  # Take first 5 if no clear entry points
            
            tree = {
                "name": project_path.name,
                "type": "project",
                "children": [self._build_tree_node(ep, import_map, set(), max_depth, 0) for ep in entry_points[:5]]
            }
        
        return tree
    
    def _is_internal_import(self, import_name: str, all_modules: set, project_path: Path) -> bool:
        """Check if import is internal to the project"""
        # Direct match
        if import_name in all_modules:
            return True
        
        # Check if it's a submodule of any known module
        for module in all_modules:
            if import_name.startswith(module + "."):
                return True
            if module.startswith(import_name + "."):
                return True
        
        # Check if corresponding file exists in project
        potential_paths = [
            project_path / f"{import_name.replace('.', '/')}.py",
            project_path / f"{import_name.replace('.', '/')}/__init__.py"
        ]
        
        return any(p.exists() for p in potential_paths)
    
    def _build_tree_node(self, module_name: str, import_map: Dict, visited: set, max_depth: int, current_depth: int) -> Dict:
        """Build a single tree node with its dependencies"""
        if current_depth >= max_depth or module_name in visited:
            return {
                "name": module_name,
                "type": "module",
                "children": [],
                "truncated": current_depth >= max_depth,
                "circular": module_name in visited
            }
        
        visited.add(module_name)
        node = {
            "name": module_name,
            "type": "module",
            "children": [],
            "truncated": False,
            "circular": False
        }
        
        if module_name in import_map:
            module_data = import_map[module_name]
            
            # Add internal dependencies
            for dep in module_data["imports"]:
                child_node = self._build_tree_node(dep, import_map, visited.copy(), max_depth, current_depth + 1)
                node["children"].append(child_node)
            
            # Add external dependencies if they exist
            for ext_dep in module_data.get("external_imports", []):
                node["children"].append({
                    "name": ext_dep,
                    "type": "external",
                    "children": [],
                    "truncated": False,
                    "circular": False
                })
        
        return node
    
    def _format_tree_text(self, tree: Dict, indent: str = "", is_last: bool = True) -> str:
        """Format dependency tree as text with tree characters"""
        if isinstance(tree, dict):
            name = tree.get("name", "unknown")
            node_type = tree.get("type", "unknown")
            
            # Choose appropriate symbol
            if node_type == "project":
                symbol = "📁"
            elif node_type == "external":
                symbol = "📦"
            elif tree.get("circular"):
                symbol = "🔄"
            elif tree.get("truncated"):
                symbol = "📄..."
            else:
                symbol = "📄"
            
            # Format current node
            prefix = "└── " if is_last else "├── "
            output = f"{indent}{prefix}{symbol} {name}\n"
            
            # Format children
            children = tree.get("children", [])
            if children:
                new_indent = indent + ("    " if is_last else "│   ")
                for i, child in enumerate(children):
                    child_is_last = i == len(children) - 1
                    output += self._format_tree_text(child, new_indent, child_is_last)
            
            return output
        
        return ""
    
    def _format_tree_ascii(self, tree: Dict) -> str:
        """Format dependency tree with ASCII art"""
        output = "🌳 Dependency Tree\n"
        output += "=" * 50 + "\n\n"
        output += self._format_tree_text(tree)
        return output.strip()
    
    def _format_tree_mermaid(self, tree: Dict) -> str:
        """Format dependency tree as Mermaid diagram"""
        output = "```mermaid\ngraph TD\n"
        node_counter = [0]  # Use list for mutable reference
        
        def add_mermaid_node(node: Dict, parent_id: Optional[str] = None):
            node_counter[0] += 1
            node_id = f"node{node_counter[0]}"
            name = node.get("name", "unknown")
            node_type = node.get("type", "unknown")
            
            # Format node based on type
            if node_type == "project":
                output_line = f"    {node_id}[\"{name}\"]\n"
            elif node_type == "external":
                output_line = f"    {node_id}({name})\n"
            elif node.get("circular"):
                output_line = f"    {node_id}[(\"{name} (circular)\")]\n"
            else:
                output_line = f"    {node_id}[\"{name}\"]\n"
            
            nonlocal output
            output += output_line
            
            # Add connection from parent
            if parent_id:
                output += f"    {parent_id} --> {node_id}\n"
            
            # Process children
            for child in node.get("children", []):
                add_mermaid_node(child, node_id)
            
            return node_id
        
        add_mermaid_node(tree)
        output += "```"
        return output
    
    async def _analyze_service_dependencies(self, args: Dict[str, Any]) -> List[TextContent]:
        """Analyze service-to-service dependencies"""
        project_path = Path(args["project_path"])
        if not project_path.is_absolute():
            project_path = self.project_root / project_path
        
        if not project_path.exists():
            return [TextContent(type="text", text=f"❌ Project path not found: {project_path}")]
        
        try:
            format_type = args.get("format", "text")
            group_by = args.get("group_by", "layer")
            show_details = args.get("show_details", False)
            
            # Analyze service dependencies
            service_deps = self._analyze_cross_service_usage(project_path, group_by)
            
            # Format output based on requested type
            if format_type == "mermaid":
                output = self._format_service_deps_mermaid(service_deps, group_by)
            elif format_type == "json":
                import json
                output = json.dumps(service_deps, indent=2, default=str)
            elif format_type == "matrix":
                output = self._format_service_deps_matrix(service_deps, group_by)
            else:  # text format
                output = self._format_service_deps_text(service_deps, group_by, show_details)
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Service dependency analysis failed: {str(e)}")]
    
    async def _analyze_architecture(self, args: Dict[str, Any]) -> List[TextContent]:
        """Analyze architectural patterns and violations"""
        project_path = Path(args["project_path"])
        if not project_path.is_absolute():
            project_path = self.project_root / project_path
        
        if not project_path.exists():
            return [TextContent(type="text", text=f"❌ Project path not found: {project_path}")]
        
        try:
            architecture_type = args.get("architecture_type", "auto")
            check_violations = args.get("check_violations", True)
            format_type = args.get("format", "text")
            
            # Analyze architectural patterns
            arch_analysis = self._perform_architecture_analysis(
                project_path, 
                architecture_type, 
                check_violations
            )
            
            # Format output
            if format_type == "mermaid":
                output = self._format_architecture_mermaid(arch_analysis)
            elif format_type == "json":
                import json
                output = json.dumps(arch_analysis, indent=2, default=str)
            else:  # text format
                output = self._format_architecture_text(arch_analysis)
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Architecture analysis failed: {str(e)}")]
    
    def _analyze_cross_service_usage(self, project_path: Path, group_by: str) -> Dict:
        """Analyze cross-service import usage patterns"""
        python_files = list(project_path.rglob("*.py"))
        python_files = [f for f in python_files if "__pycache__" not in str(f)]
        
        # Service/layer mapping
        services = {}
        usage_matrix = {}
        
        for file_path in python_files:
            try:
                analysis = self.analyze_imports_uc.execute(file_path)
                
                # Determine service/layer for this file
                rel_path = file_path.relative_to(project_path)
                service = self._classify_service(rel_path, group_by)
                
                if service not in services:
                    services[service] = {
                        "files": [],
                        "imports_from": {},
                        "provides_to": {}
                    }
                
                services[service]["files"].append(str(rel_path))
                
                # Analyze what this service imports from others
                for imp in analysis.imports:
                    if imp.is_valid:
                        target_service = self._classify_import_target(imp.module, project_path, group_by)
                        if target_service and target_service != service:
                            if target_service not in services[service]["imports_from"]:
                                services[service]["imports_from"][target_service] = []
                            services[service]["imports_from"][target_service].append({
                                "import": imp.full_name,
                                "file": str(rel_path),
                                "line": imp.line_number
                            })
                            
                            # Update usage matrix
                            matrix_key = f"{service} -> {target_service}"
                            if matrix_key not in usage_matrix:
                                usage_matrix[matrix_key] = 0
                            usage_matrix[matrix_key] += 1
                            
            except Exception:
                continue  # Skip files with analysis errors
        
        return {
            "services": services,
            "usage_matrix": usage_matrix,
            "summary": {
                "total_services": len(services),
                "total_cross_dependencies": len(usage_matrix),
                "group_by": group_by
            }
        }
    
    def _classify_service(self, rel_path: Path, group_by: str) -> str:
        """Classify a file into a service/layer category"""
        parts = rel_path.parts
        
        if group_by == "layer":
            # Clean architecture layers
            if "domain" in parts:
                return "Domain"
            elif "application" in parts or "use_cases" in parts:
                return "Application" 
            elif "infrastructure" in parts:
                return "Infrastructure"
            elif "presentation" in parts or "api" in parts or "web" in parts:
                return "Presentation"
            elif "tests" in parts or "test" in parts:
                return "Tests"
            else:
                return "Core"
        
        elif group_by == "package":
            # Top-level package
            return parts[0] if parts else "Root"
            
        elif group_by == "service":
            # Service-based (second level)
            if len(parts) >= 2:
                return f"{parts[0]}.{parts[1]}"
            elif len(parts) == 1:
                return parts[0]
            else:
                return "Root"
        
        return "Unknown"
    
    def _classify_import_target(self, import_name: str, project_path: Path, group_by: str) -> Optional[str]:
        """Classify what service/layer an import targets"""
        # Check if it's an internal import
        if not self._is_internal_import(import_name, set(), project_path):
            return None  # External import
        
        parts = import_name.split('.')
        
        if group_by == "layer":
            if "domain" in parts:
                return "Domain"
            elif "application" in parts or "use_cases" in parts:
                return "Application"
            elif "infrastructure" in parts:
                return "Infrastructure"
            elif "presentation" in parts or "api" in parts:
                return "Presentation"
            else:
                return "Core"
        
        elif group_by == "package":
            return parts[0] if parts else "Root"
            
        elif group_by == "service":
            if len(parts) >= 2:
                return f"{parts[0]}.{parts[1]}"
            elif len(parts) == 1:
                return parts[0]
            else:
                return "Root"
        
        return None
    
    def _format_service_deps_text(self, service_deps: Dict, group_by: str, show_details: bool) -> str:
        """Format service dependencies as text"""
        output = f"🏗️  Service Dependencies Analysis ({group_by} grouping)\n"
        output += "=" * 70 + "\n\n"
        
        services = service_deps["services"]
        summary = service_deps["summary"]
        
        output += f"📊 Summary:\n"
        output += f"  Services/Layers: {summary['total_services']}\n"
        output += f"  Cross-dependencies: {summary['total_cross_dependencies']}\n\n"
        
        # Service overview
        output += f"🔧 Services Overview:\n"
        for service_name, service_info in services.items():
            imports_count = sum(len(imports) for imports in service_info["imports_from"].values())
            output += f"  📦 {service_name}: {len(service_info['files'])} files, {imports_count} cross-imports\n"
        
        output += "\n"
        
        # Dependencies matrix
        output += f"🔗 Cross-Service Dependencies:\n"
        for service_name, service_info in services.items():
            if service_info["imports_from"]:
                output += f"\n  📦 {service_name} imports from:\n"
                for target_service, imports in service_info["imports_from"].items():
                    output += f"    └─ {target_service}: {len(imports)} import(s)\n"
                    
                    if show_details:
                        for imp_info in imports[:3]:  # Show first 3 imports
                            output += f"      • {imp_info['import']} (in {imp_info['file']})\n"
                        if len(imports) > 3:
                            output += f"      • ... and {len(imports) - 3} more\n"
        
        return output.strip()
    
    def _format_service_deps_matrix(self, service_deps: Dict, group_by: str) -> str:
        """Format service dependencies as a matrix"""
        services = list(service_deps["services"].keys())
        usage_matrix = service_deps["usage_matrix"]
        
        output = f"📊 Service Dependency Matrix ({group_by} grouping)\n"
        output += "=" * 70 + "\n\n"
        
        # Create matrix header
        output += f"{'':15}"
        for service in services:
            output += f"{service[:12]:>12} "
        output += "\n"
        
        # Create matrix rows
        for from_service in services:
            output += f"{from_service[:15]:15}"
            for to_service in services:
                if from_service == to_service:
                    output += f"{'─':>12} "
                else:
                    key = f"{from_service} -> {to_service}"
                    count = usage_matrix.get(key, 0)
                    output += f"{count:>12} " if count > 0 else f"{'·':>12} "
            output += "\n"
        
        output += f"\n📝 Legend: Numbers show import count, ─ = self, · = no imports\n"
        
        return output
    
    def _format_service_deps_mermaid(self, service_deps: Dict, group_by: str) -> str:
        """Format service dependencies as Mermaid diagram"""
        output = f"```mermaid\ngraph TD\n"
        
        services = service_deps["services"]
        node_id_map = {}
        node_counter = 0
        
        # Create nodes
        for service_name in services.keys():
            node_counter += 1
            node_id = f"S{node_counter}"
            node_id_map[service_name] = node_id
            
            # Style based on layer type
            if "Domain" in service_name:
                output += f"    {node_id}[\"{service_name}\"]:::domain\n"
            elif "Application" in service_name:
                output += f"    {node_id}[\"{service_name}\"]:::application\n"
            elif "Infrastructure" in service_name:
                output += f"    {node_id}[\"{service_name}\"]:::infrastructure\n"
            elif "Presentation" in service_name:
                output += f"    {node_id}[\"{service_name}\"]:::presentation\n"
            else:
                output += f"    {node_id}[\"{service_name}\"]\n"
        
        # Create edges
        for service_name, service_info in services.items():
            from_node = node_id_map[service_name]
            for target_service, imports in service_info["imports_from"].items():
                if target_service in node_id_map:
                    to_node = node_id_map[target_service]
                    count = len(imports)
                    output += f"    {from_node} -->|{count}| {to_node}\n"
        
        # Add styling
        output += "\n    classDef domain fill:#e1f5fe\n"
        output += "    classDef application fill:#f3e5f5\n"
        output += "    classDef infrastructure fill:#e8f5e8\n"
        output += "    classDef presentation fill:#fff3e0\n"
        
        output += "```"
        return output
    
    def _perform_architecture_analysis(self, project_path: Path, architecture_type: str, check_violations: bool) -> Dict:
        """Perform comprehensive architecture analysis"""
        python_files = list(project_path.rglob("*.py"))
        python_files = [f for f in python_files if "__pycache__" not in str(f)]
        
        # Detect architecture type if auto
        if architecture_type == "auto":
            architecture_type = self._detect_architecture_type(project_path)
        
        layers = {}
        violations = []
        metrics = {
            "total_files": len(python_files),
            "layers_found": 0,
            "cross_layer_imports": 0,
            "violation_count": 0
        }
        
        # Analyze each file for layer classification and imports
        for file_path in python_files:
            try:
                analysis = self.analyze_imports_uc.execute(file_path)
                rel_path = file_path.relative_to(project_path)
                
                layer = self._classify_service(rel_path, "layer")
                
                if layer not in layers:
                    layers[layer] = {
                        "files": [],
                        "outgoing_imports": {},
                        "incoming_imports": {}
                    }
                
                layers[layer]["files"].append(str(rel_path))
                
                # Check imports for violations
                for imp in analysis.imports:
                    if imp.is_valid:
                        target_layer = self._classify_import_target(imp.module, project_path, "layer")
                        if target_layer and target_layer != layer:
                            # Record cross-layer import
                            if target_layer not in layers[layer]["outgoing_imports"]:
                                layers[layer]["outgoing_imports"][target_layer] = 0
                            layers[layer]["outgoing_imports"][target_layer] += 1
                            
                            metrics["cross_layer_imports"] += 1
                            
                            # Check for architectural violations
                            if check_violations:
                                violation = self._check_architecture_violation(
                                    layer, target_layer, architecture_type, imp, file_path
                                )
                                if violation:
                                    violations.append(violation)
                                    metrics["violation_count"] += 1
                            
            except Exception:
                continue
        
        metrics["layers_found"] = len(layers)
        
        return {
            "architecture_type": architecture_type,
            "layers": layers,
            "violations": violations,
            "metrics": metrics,
            "recommendations": self._generate_architecture_recommendations(layers, violations, architecture_type)
        }
    
    def _detect_architecture_type(self, project_path: Path) -> str:
        """Auto-detect the architecture type based on folder structure"""
        folders = set()
        for item in project_path.rglob("*"):
            if item.is_dir():
                folders.add(item.name.lower())
        
        # Clean/Hexagonal architecture indicators
        if "domain" in folders and "application" in folders and "infrastructure" in folders:
            return "clean"
        
        # Layered architecture indicators
        if any(layer in folders for layer in ["models", "views", "controllers"]):
            return "layered"
            
        # Default to clean architecture
        return "clean"
    
    def _check_architecture_violation(self, from_layer: str, to_layer: str, architecture_type: str, 
                                     import_stmt, file_path: Path) -> Optional[Dict]:
        """Check if an import violates architectural principles"""
        violations = {
            "clean": {
                # Clean architecture dependency rules
                "Domain": [],  # Domain should not depend on anything
                "Application": ["Domain"],  # Application can only depend on Domain
                "Infrastructure": ["Domain", "Application"],  # Infrastructure can depend on Domain and Application
                "Presentation": ["Domain", "Application"]  # Presentation can depend on Domain and Application
            },
            "layered": {
                # Traditional layered architecture
                "Presentation": ["Application", "Domain"],
                "Application": ["Domain"],
                "Domain": [],
                "Infrastructure": ["Domain"]
            }
        }
        
        rules = violations.get(architecture_type, violations["clean"])
        allowed_dependencies = rules.get(from_layer, [])
        
        if to_layer not in allowed_dependencies and to_layer != from_layer:
            return {
                "type": "layer_violation",
                "severity": "error",
                "from_layer": from_layer,
                "to_layer": to_layer,
                "file": str(file_path),
                "import": import_stmt.full_name,
                "line": import_stmt.line_number,
                "message": f"{from_layer} layer should not import from {to_layer} layer in {architecture_type} architecture"
            }
        
        return None
    
    def _generate_architecture_recommendations(self, layers: Dict, violations: List, architecture_type: str) -> List[str]:
        """Generate architecture improvement recommendations"""
        recommendations = []
        
        if violations:
            recommendations.append(f"🚨 Found {len(violations)} architectural violations - review layer dependencies")
        
        # Check for missing layers
        expected_layers = ["Domain", "Application", "Infrastructure", "Presentation"]
        missing_layers = [layer for layer in expected_layers if layer not in layers]
        
        if missing_layers:
            recommendations.append(f"📂 Consider adding missing layers: {', '.join(missing_layers)}")
        
        # Check layer sizes
        layer_sizes = {layer: len(info["files"]) for layer, info in layers.items()}
        if layer_sizes and max(layer_sizes.values()) > 20:
            largest_layer = max(layer_sizes.keys(), key=lambda x: layer_sizes[x])
            recommendations.append(f"📏 {largest_layer} layer is quite large ({layer_sizes[largest_layer]} files) - consider splitting")
        
        # Check for god layers (layers that import from everything)
        for layer, info in layers.items():
            if len(info["outgoing_imports"]) >= 3:
                recommendations.append(f"🔗 {layer} layer has many dependencies - review if it violates single responsibility")
        
        if not recommendations:
            recommendations.append("✅ Architecture looks good! No major issues detected.")
        
        return recommendations
    
    def _format_architecture_text(self, arch_analysis: Dict) -> str:
        """Format architecture analysis as text"""
        output = f"🏛️  Architecture Analysis\n"
        output += "=" * 70 + "\n\n"
        
        output += f"📊 Overview:\n"
        output += f"  Architecture Type: {arch_analysis['architecture_type'].title()}\n"
        output += f"  Total Files: {arch_analysis['metrics']['total_files']}\n"
        output += f"  Layers Found: {arch_analysis['metrics']['layers_found']}\n"
        output += f"  Cross-layer Imports: {arch_analysis['metrics']['cross_layer_imports']}\n"
        output += f"  Violations: {arch_analysis['metrics']['violation_count']}\n\n"
        
        # Layer breakdown
        output += f"🏗️  Layer Breakdown:\n"
        for layer_name, layer_info in arch_analysis['layers'].items():
            output += f"  📦 {layer_name}: {len(layer_info['files'])} files\n"
            if layer_info['outgoing_imports']:
                deps = ", ".join(f"{target}({count})" for target, count in layer_info['outgoing_imports'].items())
                output += f"    └─ Dependencies: {deps}\n"
        
        output += "\n"
        
        # Violations
        if arch_analysis['violations']:
            output += f"⚠️  Architectural Violations:\n"
            for violation in arch_analysis['violations'][:5]:  # Show first 5
                output += f"  🔴 {violation['message']}\n"
                output += f"     File: {violation['file']}:{violation['line']}\n"
                output += f"     Import: {violation['import']}\n\n"
            
            if len(arch_analysis['violations']) > 5:
                output += f"  ... and {len(arch_analysis['violations']) - 5} more violations\n\n"
        
        # Recommendations
        output += f"💡 Recommendations:\n"
        for rec in arch_analysis['recommendations']:
            output += f"  • {rec}\n"
        
        return output.strip()
    
    def _format_architecture_mermaid(self, arch_analysis: Dict) -> str:
        """Format architecture analysis as Mermaid diagram"""
        output = f"```mermaid\ngraph TB\n"
        
        layers = arch_analysis['layers']
        node_counter = 0
        node_map = {}
        
        # Create layer nodes
        for layer_name, layer_info in layers.items():
            node_counter += 1
            node_id = f"L{node_counter}"
            node_map[layer_name] = node_id
            
            file_count = len(layer_info['files'])
            output += f"    {node_id}[\"{layer_name}\\n({file_count} files)\"]\n"
        
        # Add dependencies
        for layer_name, layer_info in layers.items():
            from_node = node_map[layer_name]
            for target_layer, count in layer_info['outgoing_imports'].items():
                if target_layer in node_map:
                    to_node = node_map[target_layer]
                    output += f"    {from_node} -->|{count}| {to_node}\n"
        
        output += "```"
        return output