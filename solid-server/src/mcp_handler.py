"""
MCP Handler for SOLID Principles Analysis
========================================
Handles MCP protocol tool calls for SOLID analysis.
"""

import ast
import json
from pathlib import Path
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

# Import from new architecture
from domain.models import SolidPrinciple, SolidViolation
from application.analyze_file import AnalyzeFileUseCase
from application.analyze_directory import (
    AnalyzeDirectoryUseCase, DirectoryFilters
)
from application.generate_report import (
    GenerateReportUseCase, ReportOptions
)
from application.suggest_refactoring import (
    SuggestRefactoringUseCase, RefactoringOptions
)


class MCPHandler:
    """
    MCP protocol handler for SOLID analysis tools.
    
    Follows Dependency Inversion Principle - depends on use case abstractions,
    not concrete implementations. Dependencies are injected via constructor.
    """
    
    def __init__(
        self,
        project_root: Path,
        analyze_file_uc: AnalyzeFileUseCase,
        analyze_dir_uc: AnalyzeDirectoryUseCase,
        generate_report_uc: GenerateReportUseCase,
        suggest_refactoring_uc: SuggestRefactoringUseCase
    ):
        """
        Initialize handler with injected dependencies.
        
        Args:
            project_root: Root directory for the project
            analyze_file_uc: Use case for analyzing single files
            analyze_dir_uc: Use case for analyzing directories
            generate_report_uc: Use case for generating reports
            suggest_refactoring_uc: Use case for refactoring suggestions
        """
        self.project_root = project_root
        self.analyze_file_uc = analyze_file_uc
        self.analyze_dir_uc = analyze_dir_uc
        self.generate_report_uc = generate_report_uc
        self.suggest_refactoring_uc = suggest_refactoring_uc
    
    def get_tools(self) -> List[Tool]:
        """Return list of available SOLID analysis tools"""
        return [
            self._tool_check_file(),
            self._tool_check_directory(),
            self._tool_generate_report(),
            self._tool_explain_principle(),
            self._tool_check_score(),
            self._tool_list_violations(),
            self._tool_suggest_refactoring(),
            self._tool_dependency_graph(),
            self._tool_analyze_inheritance(),
        ]
    
    def _tool_check_file(self) -> Tool:
        """Tool definition for analyzing a single file"""
        return Tool(
            name="solid-check-file",
            description="Analyze a single Python file for SOLID principles violations",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the Python file to analyze"
                    },
                    "principles": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["SRP", "OCP", "LSP", "ISP", "DIP", "ALL"]
                        },
                        "description": "Which SOLID principles to check. Use 'ALL' for all principles.",
                        "default": ["ALL"]
                    }
                },
                "required": ["file_path"]
            }
        )
    
    def _tool_check_directory(self) -> Tool:
        """Tool definition for analyzing a directory"""
        return Tool(
            name="solid-check-directory",
            description="Analyze all Python files in a directory for SOLID principles violations",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "Path to the directory to analyze"
                    },
                    "include_patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File patterns to include (e.g., ['*.py'])",
                        "default": ["*.py"]
                    },
                    "exclude_patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Patterns to exclude from analysis",
                        "default": ["__pycache__", ".git", ".venv", "venv", "test_*"]
                    },
                    "max_files": {
                        "type": "integer",
                        "description": "Maximum number of files to analyze",
                        "default": 100
                    }
                },
                "required": ["directory_path"]
            }
        )
    
    def _tool_generate_report(self) -> Tool:
        """Tool definition for generating comprehensive reports"""
        return Tool(
            name="solid-generate-report",
            description="Generate a comprehensive SOLID principles report for a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "Path to the directory to analyze"
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["text", "json", "markdown"],
                        "description": "Output format for the report",
                        "default": "text"
                    },
                    "include_suggestions": {
                        "type": "boolean",
                        "description": "Include improvement suggestions in the report",
                        "default": True
                    },
                    "severity_filter": {
                        "type": "string",
                        "enum": ["all", "high", "medium", "low"],
                        "description": "Filter violations by severity level",
                        "default": "all"
                    }
                },
                "required": ["directory_path"]
            }
        )
    
    def _tool_explain_principle(self) -> Tool:
        """Tool definition for explaining SOLID principles"""
        return Tool(
            name="solid-explain-principle",
            description="Get detailed explanation of a SOLID principle with examples",
            inputSchema={
                "type": "object",
                "properties": {
                    "principle": {
                        "type": "string",
                        "enum": ["SRP", "OCP", "LSP", "ISP", "DIP"],
                        "description": "SOLID principle to explain"
                    }
                },
                "required": ["principle"]
            }
        )
    
    def _tool_check_score(self) -> Tool:
        """Tool definition for getting SOLID compliance scores"""
        return Tool(
            name="solid-check-score",
            description="Get SOLID compliance score for a file or directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file or directory to score"
                    }
                },
                "required": ["path"]
            }
        )
    
    def _tool_list_violations(self) -> Tool:
        """Tool definition for listing violations"""
        return Tool(
            name="solid-list-violations",
            description="List all SOLID violations in a structured format",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string", 
                        "description": "Path to file or directory to analyze"
                    },
                    "principle_filter": {
                        "type": "string",
                        "enum": ["SRP", "OCP", "LSP", "ISP", "DIP", "ALL"],
                        "description": "Filter by specific SOLID principle",
                        "default": "ALL"
                    },
                    "severity_filter": {
                        "type": "string",
                        "enum": ["high", "medium", "low", "all"],
                        "description": "Filter by violation severity",
                        "default": "all"
                    }
                },
                "required": ["path"]
            }
        )
    
    def _tool_suggest_refactoring(self) -> Tool:
        """Tool definition for suggesting refactorings"""
        return Tool(
            name="solid-suggest-refactoring",
            description="Generate a prioritized refactoring plan with specific suggestions",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file or directory to analyze"
                    },
                    "max_suggestions": {
                        "type": "integer",
                        "description": "Maximum number of refactoring suggestions",
                        "default": 10
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low", "all"],
                        "description": "Priority level of suggestions",
                        "default": "all"
                    }
                },
                "required": ["path"]
            }
        )
    
    def _tool_dependency_graph(self) -> Tool:
        """Tool definition for dependency graph analysis"""
        return Tool(
            name="solid-dependency-graph",
            description="Analyze and visualize dependencies between classes",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file or directory to analyze"
                    },
                    "include_external": {
                        "type": "boolean",
                        "description": "Include external dependencies",
                        "default": False
                    },
                    "format": {
                        "type": "string",
                        "enum": ["text", "mermaid", "json"],
                        "description": "Output format for dependency graph",
                        "default": "text"
                    }
                },
                "required": ["path"]
            }
        )
    
    def _tool_analyze_inheritance(self) -> Tool:
        """Tool definition for inheritance tree analysis"""
        return Tool(
            name="solid-analyze-inheritance",
            description="Analyze class inheritance trees and detect issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file or directory to analyze"
                    },
                    "show_methods": {
                        "type": "boolean",
                        "description": "Include method information",
                        "default": True
                    }
                },
                "required": ["path"]
            }
        )
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls"""
        try:
            if name == "solid-check-file":
                return await self._solid_check_file(arguments)
            elif name == "solid-check-directory":
                return await self._solid_check_directory(arguments)
            elif name == "solid-generate-report":
                return await self._solid_generate_report(arguments)
            elif name == "solid-explain-principle":
                return await self._solid_explain_principle(arguments)
            elif name == "solid-check-score":
                return await self._solid_check_score(arguments)
            elif name == "solid-list-violations":
                return await self._solid_list_violations(arguments)
            elif name == "solid-suggest-refactoring":
                return await self._solid_suggest_refactoring(arguments)
            elif name == "solid-dependency-graph":
                return await self._solid_dependency_graph(arguments)
            elif name == "solid-analyze-inheritance":
                return await self._solid_analyze_inheritance(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]
    
    async def _solid_check_file(self, args: Dict[str, Any]) -> List[TextContent]:
        """Analyze a single file for SOLID violations"""
        file_path = Path(args["file_path"])
        if not file_path.is_absolute():
            file_path = self.project_root / file_path
        
        if not file_path.exists():
            return [TextContent(type="text", text=f"File not found: {file_path}")]
        
        if not file_path.suffix == ".py":
            return [TextContent(type="text", text=f"Only Python files are supported. Got: {file_path}")]
        
        # Use new architecture
        report = self.analyze_file_uc.execute(file_path)
        
        # Format output using new formatter
        output = self.formatter.format_file_report(report)
        return [TextContent(type="text", text=output)]
    
    async def _solid_check_directory(self, args: Dict[str, Any]) -> List[TextContent]:
        """Analyze all files in a directory"""
        directory_path = Path(args["directory_path"])
        if not directory_path.is_absolute():
            directory_path = self.project_root / directory_path
        
        if not directory_path.exists():
            return [TextContent(type="text", text=f"Directory not found: {directory_path}")]
        
        include_patterns = args.get("include_patterns", ["*.py"])
        exclude_patterns = args.get("exclude_patterns", 
            ["__pycache__", ".git", ".venv", "venv", "test_*"])
        
        # Use new architecture
        filters = DirectoryFilters(
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns
        )
        reports = self.analyze_dir_uc.execute(directory_path, filters)
        
        # Generate summary report
        output = self.generate_report_uc.execute(
            reports,
            ReportOptions(
                include_suggestions=False,
                output_format="text",
                severity_filter="all"
            )
        )
        
        return [TextContent(type="text", text=output)]
    
    async def _solid_generate_report(self, args: Dict[str, Any]) -> List[TextContent]:
        """Generate comprehensive SOLID report"""
        directory_path = Path(args["directory_path"])
        if not directory_path.is_absolute():
            directory_path = self.project_root / directory_path
        
        output_format = args.get("output_format", "text")
        include_suggestions = args.get("include_suggestions", True)
        severity_filter = args.get("severity_filter", "all")
        
        # Use new architecture
        filters = DirectoryFilters(
            include_patterns=["*.py"],
            exclude_patterns=["__pycache__", ".git", ".venv", "venv", "test_*"]
        )
        reports = self.analyze_dir_uc.execute(directory_path, filters)
        
        # Generate report
        options = ReportOptions(
            include_suggestions=include_suggestions,
            output_format=output_format,
            severity_filter=severity_filter
        )
        output = self.generate_report_uc.execute(reports, options)
        
        return [TextContent(type="text", text=output)]
    
    async def _solid_explain_principle(self, args: Dict[str, Any]) -> List[TextContent]:
        """Explain a SOLID principle"""
        principle = args["principle"]
        
        explanations = {
            "SRP": """
# Single Responsibility Principle (SRP)

**Definition**: A class should have only one reason to change, meaning it should have only one job or responsibility.

## What it means:
- Each class should focus on a single task or functionality
- Changes to one aspect of the system should only affect one class
- High cohesion within classes, low coupling between classes

## Common violations:
- Classes that handle multiple unrelated tasks (e.g., data access + business logic + presentation)
- Large classes with many methods doing different things
- Methods that are very long and handle multiple concerns

## How to fix:
- Split large classes into smaller, focused classes
- Use composition to combine different responsibilities
- Apply separation of concerns consistently

## Example:
```python
# VIOLATION - Multiple responsibilities
class Employee:
    def calculate_pay(self): pass      # Business logic
    def save_to_database(self): pass   # Data persistence
    def generate_report(self): pass    # Reporting

# BETTER - Single responsibilities
class Employee:
    def calculate_pay(self): pass

class EmployeeRepository:
    def save(self, employee): pass

class EmployeeReportGenerator:
    def generate_report(self, employee): pass
```
            """,
            "OCP": """
# Open-Closed Principle (OCP)

**Definition**: Software entities should be open for extension, but closed for modification.

## What it means:
- You should be able to add new functionality without changing existing code
- Use abstraction and polymorphism to enable extensions
- Existing, tested code remains untouched when adding features

## Common violations:
- Long if/elif chains for handling different types
- Modifying existing classes to add new behavior
- Type checking with isinstance() or type()

## How to fix:
- Use inheritance and polymorphism
- Apply the Strategy pattern
- Use abstract base classes or interfaces
- Implement plugin architectures

## Example:
```python
# VIOLATION - Must modify existing code for new shapes
def calculate_area(shape):
    if shape.type == "circle":
        return 3.14 * shape.radius ** 2
    elif shape.type == "rectangle":
        return shape.width * shape.height
    # Must add new elif for each shape type

# BETTER - Open for extension
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self): pass

class Circle(Shape):
    def area(self): return 3.14 * self.radius ** 2

class Rectangle(Shape):
    def area(self): return self.width * self.height
```
            """,
            "LSP": """
# Liskov Substitution Principle (LSP)

**Definition**: Objects of a superclass should be replaceable with objects of its subclasses without breaking functionality.

## What it means:
- Subclasses must be substitutable for their base classes
- Derived classes should not weaken preconditions or strengthen postconditions
- The behavior of the program should remain correct when using subclass instances

## Common violations:
- Subclasses that throw NotImplementedError
- Subclasses that change the expected behavior of parent methods
- Subclasses that require more restrictive input parameters
- Subclasses that provide weaker output guarantees

## How to fix:
- Ensure subclasses honor the contract of the parent class
- Use composition instead of inheritance when substitutability isn't natural
- Design base classes carefully with clear contracts

## Example:
```python
# VIOLATION - Rectangle/Square problem
class Rectangle:
    def set_width(self, width): self.width = width
    def set_height(self, height): self.height = height
    def area(self): return self.width * self.height

class Square(Rectangle):
    def set_width(self, width): 
        self.width = width
        self.height = width  # Violates LSP - unexpected side effect

# BETTER - Use composition or rethink hierarchy
class Shape(ABC):
    @abstractmethod
    def area(self): pass

class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height

class Square(Shape):
    def __init__(self, side):
        self.side = side
```
            """,
            "ISP": """
# Interface Segregation Principle (ISP)

**Definition**: Clients should not be forced to depend on interfaces they do not use.

## What it means:
- Create smaller, focused interfaces rather than large, monolithic ones
- Classes should only implement methods they actually need
- Split large interfaces into smaller, cohesive ones

## Common violations:
- Large interfaces with many unrelated methods
- Classes implementing interfaces with many empty/unused methods
- Fat interfaces that serve multiple client types

## How to fix:
- Split large interfaces into smaller, role-specific interfaces
- Use multiple inheritance to combine interfaces when needed
- Create client-specific interfaces

## Example:
```python
# VIOLATION - Fat interface
class Worker(ABC):
    @abstractmethod
    def work(self): pass
    @abstractmethod
    def eat(self): pass
    @abstractmethod
    def sleep(self): pass

class Robot(Worker):  # Robot doesn't eat or sleep!
    def work(self): return "Working"
    def eat(self): raise NotImplementedError  # Forced to implement
    def sleep(self): raise NotImplementedError  # Forced to implement

# BETTER - Segregated interfaces
class Workable(ABC):
    @abstractmethod
    def work(self): pass

class Feedable(ABC):
    @abstractmethod
    def eat(self): pass

class Sleepable(ABC):
    @abstractmethod
    def sleep(self): pass

class Human(Workable, Feedable, Sleepable):
    def work(self): return "Working"
    def eat(self): return "Eating"
    def sleep(self): return "Sleeping"

class Robot(Workable):  # Only implements what it needs
    def work(self): return "Working"
```
            """,
            "DIP": """
# Dependency Inversion Principle (DIP)

**Definition**: High-level modules should not depend on low-level modules. Both should depend on abstractions.

## What it means:
- Depend on abstractions (interfaces), not concretions (implementations)
- High-level policy should not depend on low-level details
- Details should depend on policies

## Common violations:
- Direct instantiation of concrete classes in high-level modules
- Tight coupling between layers
- Hard-coded dependencies in constructors

## How to fix:
- Use dependency injection
- Program to interfaces, not implementations
- Use factory patterns or IoC containers
- Pass dependencies as constructor parameters

## Example:
```python
# VIOLATION - High-level depends on low-level
class EmailService:  # Low-level
    def send_email(self, message): pass

class NotificationManager:  # High-level
    def __init__(self):
        self.email_service = EmailService()  # Direct dependency!
    
    def notify(self, message):
        self.email_service.send_email(message)

# BETTER - Both depend on abstraction
from abc import ABC, abstractmethod

class MessageSender(ABC):  # Abstraction
    @abstractmethod
    def send(self, message): pass

class EmailService(MessageSender):  # Low-level depends on abstraction
    def send(self, message): pass

class SMSService(MessageSender):  # Another implementation
    def send(self, message): pass

class NotificationManager:  # High-level depends on abstraction
    def __init__(self, sender: MessageSender):
        self.sender = sender  # Dependency injection
    
    def notify(self, message):
        self.sender.send(message)
```
            """
        }
        
        if principle not in explanations:
            return [TextContent(type="text", text=f"Unknown principle: {principle}")]
        
        return [TextContent(type="text", text=explanations[principle].strip())]
    
    async def _solid_check_score(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get SOLID compliance score"""
        path = Path(args["path"])
        if not path.is_absolute():
            path = self.project_root / path
        
        if path.is_file():
            # Single file score - use new architecture
            report = self.analyze_file_uc.execute(path)
            output = self.formatter.format_file_report(report)
        
        elif path.is_dir():
            # Directory score - use new architecture  
            filters = DirectoryFilters(
                include_patterns=["*.py"],
                exclude_patterns=["__pycache__", ".git", ".venv", "venv", "test_*"]
            )
            reports = self.analyze_dir_uc.execute(path, filters)
            options = ReportOptions(
                include_suggestions=False,
                output_format="text",
                severity_filter="all"
            )
            output = self.generate_report_uc.execute(reports, options)
        else:
            return [TextContent(type="text", text=f"Path not found: {path}")]
        
        return [TextContent(type="text", text=output)]
    
    async def _solid_list_violations(self, args: Dict[str, Any]) -> List[TextContent]:
        """List SOLID violations in structured format"""
        path = Path(args["path"])
        if not path.is_absolute():
            path = self.project_root / path
        
        # Get reports using new architecture
        if path.is_file():
            reports = [self.analyze_file_uc.execute(path)]
        elif path.is_dir():
            filters = DirectoryFilters(
                include_patterns=["*.py"],
                exclude_patterns=["__pycache__", ".git", ".venv", "venv", "test_*"]
            )
            reports = self.analyze_dir_uc.execute(path, filters)
        else:
            return [TextContent(type="text", text=f"Path not found: {path}")]
        
        # Format output using new formatter
        options = ReportOptions(
            include_suggestions=False,
            output_format="text",
            severity_filter=args.get("severity_filter", "all")
        )
        output = self.generate_report_uc.execute(reports, options)
        
        return [TextContent(type="text", text=output)]
    
    def _format_file_report(self, report) -> str:
        """Format single file report"""
        output = f"""
SOLID Analysis Report: {Path(report.file_path).name}
Score: {report.score:.1f}/100

Violations ({len(report.violations)} found):
        """.strip()
        
        if not report.violations:
            output += "\n✅ No SOLID violations found! Great job!"
            return output
        
        # Group by principle
        by_principle = {}
        for violation in report.violations:
            principle = violation.principle.value
            if principle not in by_principle:
                by_principle[principle] = []
            by_principle[principle].append(violation)
        
        for principle, violations in by_principle.items():
            output += f"\n\n{principle} ({len(violations)} violations):"
            for violation in violations:
                output += f"\n  📍 Line {violation.line_number} [{violation.severity.upper()}]: {violation.message}"
                output += f"\n     💡 {violation.suggestion}"
        
        return output
    
    def _format_directory_report(self, reports, summary, directory_path) -> str:
        """Format directory analysis report"""
        output = f"""
SOLID Analysis Report: {directory_path.name}
Average Score: {summary['average_score']}/100

Summary:
- Files analyzed: {summary['total_files']}
- Files with violations: {summary['files_with_violations']}
- Total violations: {summary['total_violations']}

Violations by Principle:
        """.strip()
        
        for principle, count in summary['violations_by_principle'].items():
            output += f"\n- {principle}: {count} violations"
        
        # Show worst files
        if summary['worst_files']:
            output += "\n\nFiles needing attention:"
            for report in summary['worst_files'][:5]:
                file_name = Path(report.file_path).name
                output += f"\n- {file_name}: {report.score:.1f}/100 ({len(report.violations)} violations)"
        
        return output
    
    def _format_json_report(self, reports, summary) -> str:
        """Format report as JSON"""
        data = {
            "summary": summary,
            "files": []
        }
        
        for report in reports:
            file_data = {
                "file_path": report.file_path,
                "score": report.score,
                "violations": [
                    {
                        "principle": v.principle.value,
                        "severity": v.severity,
                        "line_number": v.line_number,
                        "message": v.message,
                        "suggestion": v.suggestion
                    }
                    for v in report.violations
                ]
            }
            data["files"].append(file_data)
        
        return json.dumps(data, indent=2)
    
    def _format_markdown_report(self, reports, summary, include_suggestions) -> str:
        """Format report as Markdown"""
        output = f"""# SOLID Analysis Report

## Summary
- **Average Score**: {summary['average_score']}/100
- **Files analyzed**: {summary['total_files']}
- **Files with violations**: {summary['files_with_violations']}
- **Total violations**: {summary['total_violations']}

### Violations by Principle
        """.strip()
        
        for principle, count in summary['violations_by_principle'].items():
            output += f"\n- **{principle}**: {count} violations"
        
        # Detailed file reports
        output += "\n\n## Detailed Results\n"
        
        for report in reports:
            if not report.violations:
                continue
                
            file_name = Path(report.file_path).name
            output += f"\n### 📄 {file_name}\n"
            output += f"**Score**: {report.score:.1f}/100\n\n"
            
            for violation in report.violations:
                output += f"- **Line {violation.line_number}** [{violation.principle.value}] {violation.severity.upper()}: {violation.message}\n"
                if include_suggestions:
                    output += f"  - 💡 *{violation.suggestion}*\n"
        
        return output
    
    def _format_text_report(self, reports, summary, include_suggestions) -> str:
        """Format comprehensive text report"""
        output = f"""
SOLID PRINCIPLES ANALYSIS REPORT
{'=' * 50}

SUMMARY:
Average Score: {summary['average_score']}/100
Files Analyzed: {summary['total_files']}
Files with Violations: {summary['files_with_violations']}
Total Violations: {summary['total_violations']}

VIOLATIONS BY PRINCIPLE:
        """.strip()
        
        for principle, count in summary['violations_by_principle'].items():
            output += f"\n{principle}: {count} violations"
        
        # Most problematic files
        if summary['worst_files']:
            output += f"\n\nMOST PROBLEMATIC FILES:"
            for i, report in enumerate(summary['worst_files'][:5], 1):
                file_name = Path(report.file_path).name
                output += f"\n{i}. {file_name}: {report.score:.1f}/100 ({len(report.violations)} violations)"
        
        # Best files
        if summary['best_files']:
            output += f"\n\nBEST PERFORMING FILES:"
            for i, report in enumerate(summary['best_files'][:5], 1):
                file_name = Path(report.file_path).name
                output += f"\n{i}. {file_name}: {report.score:.1f}/100 ({len(report.violations)} violations)"
        
        # Detailed violations if requested
        if include_suggestions:
            output += f"\n\nDETAILED VIOLATIONS:"
            for report in reports:
                if not report.violations:
                    continue
                
                file_name = Path(report.file_path).name
                output += f"\n\n📄 {file_name} (Score: {report.score:.1f}/100):"
                
                for violation in report.violations:
                    output += f"\n  📍 Line {violation.line_number} [{violation.principle.value}] {violation.severity.upper()}"
                    output += f"\n     {violation.message}"
                    output += f"\n     💡 {violation.suggestion}"
        
        return output

    async def _solid_suggest_refactoring(
        self, args: Dict[str, Any]
    ) -> List[TextContent]:
        """Generate prioritized refactoring suggestions"""
        path = args["path"]
        max_suggestions = args.get("max_suggestions", 10)
        priority = args.get("priority", "all")

        path_obj = Path(path)
        if not path_obj.is_absolute():
            path_obj = self.project_root / path_obj
            
        if not path_obj.exists():
            return [
                TextContent(
                    type="text",
                    text=f"❌ Path not found: {path}"
                )
            ]

        # Use new architecture
        options = RefactoringOptions(
            max_suggestions=max_suggestions,
            priority_filter=priority
        )
        suggestions = self.suggest_refactoring_uc.execute(path_obj, options)
        
        # Format using formatter
        output = self.formatter.format_suggestions(suggestions)
        
        return [TextContent(type="text", text=output)]

        # Format output
        output = f"""
🔧 REFACTORING SUGGESTIONS (Top {len(suggestions)})
{'=' * 60}

Priority Score Calculation:
- High severity: +10 points
- Medium severity: +5 points
- Low severity: +2 points

"""
        for i, sugg in enumerate(suggestions, 1):
            severity_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(sugg['severity'], '⚪')

            output += f"""
{i}. {severity_emoji} Priority Score: {sugg['priority_score']}
   File: {sugg['file']} (line {sugg['line']})
   Principle: {sugg['principle']} - {sugg['severity'].upper()}
   
   Problem: {sugg['message']}
   
   💡 Suggestion: {sugg['suggestion']}
   
   Code Context:
{sugg['code']}
{'─' * 60}
"""
        return [TextContent(type="text", text=output.strip())]

    def _calculate_priority_score(
        self, violation: SolidViolation
    ) -> int:
        """Calculate priority score for a violation"""
        severity_scores = {"high": 10, "medium": 5, "low": 2}
        score = severity_scores.get(violation.severity, 0)

        # Boost SRP and DIP violations (foundation principles)
        if violation.principle in [
            SolidPrinciple.SINGLE_RESPONSIBILITY,
            SolidPrinciple.DEPENDENCY_INVERSION
        ]:
            score += 2

        # Boost violations with specific keywords
        high_impact_keywords = [
            'constructor', 'dependency', 'inheritance',
            'signature', 'coupling'
        ]
        if any(kw in violation.message.lower()
               for kw in high_impact_keywords):
            score += 1

        return score

    async def _solid_dependency_graph(
        self, args: Dict[str, Any]
    ) -> List[TextContent]:
        """Generate dependency graph visualization"""
        path = args["path"]
        output_format = args.get("format", "text")
        include_methods = args.get("include_methods", False)

        path_obj = Path(path)
        if not path_obj.exists():
            return [
                TextContent(
                    type="text",
                    text=f"❌ Path not found: {path}"
                )
            ]

        # Collect all Python files
        if path_obj.is_file():
            files = [path_obj]
        else:
            files = list(path_obj.rglob("*.py"))
            files = [
                f for f in files
                if "__pycache__" not in str(f)
            ]

        # Parse and extract dependencies
        dependencies = {}
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())

                # Extract classes and their dependencies
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        deps = {
                            'file': str(file_path.name),
                            'bases': [
                                b.id if isinstance(b, ast.Name) else str(b)
                                for b in node.bases
                            ],
                            'imports': [],
                            'methods': []
                        }

                        if include_methods:
                            deps['methods'] = [
                                m.name for m in node.body
                                if isinstance(m, ast.FunctionDef)
                            ]

                        dependencies[class_name] = deps

                # Extract imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            for cls in dependencies.values():
                                if cls['file'] == file_path.name:
                                    cls['imports'].append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            for cls in dependencies.values():
                                if cls['file'] == file_path.name:
                                    cls['imports'].append(node.module)

            except Exception:
                continue

        if not dependencies:
            return [
                TextContent(
                    type="text",
                    text="⚠️  No classes found to analyze"
                )
            ]

        # Format output based on requested format
        if output_format == "mermaid":
            output = self._format_mermaid_graph(
                dependencies, include_methods
            )
        elif output_format == "json":
            import json
            output = json.dumps(dependencies, indent=2)
        else:  # text
            output = self._format_text_graph(
                dependencies, include_methods
            )

        return [TextContent(type="text", text=output)]

    def _format_mermaid_graph(
        self, dependencies: Dict, include_methods: bool
    ) -> str:
        """Format dependencies as Mermaid diagram"""
        output = "```mermaid\nclassDiagram\n"

        for class_name, info in dependencies.items():
            # Class definition
            if include_methods and info['methods']:
                output += f"    class {class_name} {{\n"
                for method in info['methods'][:5]:  # Limit methods
                    output += f"        +{method}()\n"
                output += "    }\n"
            else:
                output += f"    class {class_name}\n"

            # Inheritance relationships
            for base in info['bases']:
                if base in dependencies:
                    output += f"    {base} <|-- {class_name}\n"

        output += "```"
        return output

    def _format_text_graph(
        self, dependencies: Dict, include_methods: bool
    ) -> str:
        """Format dependencies as text tree"""
        output = """
📊 DEPENDENCY GRAPH
{'=' * 60}

"""
        for class_name, info in dependencies.items():
            output += f"\n📦 {class_name}"
            output += f" ({info['file']})\n"

            if info['bases']:
                output += "   ├─ Inherits from: "
                output += ", ".join(info['bases']) + "\n"

            if info['imports']:
                output += "   ├─ Imports: "
                output += ", ".join(info['imports'][:3])
                if len(info['imports']) > 3:
                    output += f" (+{len(info['imports'])-3} more)"
                output += "\n"

            if include_methods and info['methods']:
                output += "   └─ Methods: "
                output += ", ".join(info['methods'][:5])
                if len(info['methods']) > 5:
                    output += f" (+{len(info['methods'])-5} more)"
                output += "\n"

        # Detect circular dependencies
        circular = self._detect_circular_deps(dependencies)
        if circular:
            output += "\n\n⚠️  CIRCULAR DEPENDENCIES DETECTED:\n"
            for cycle in circular:
                output += f"   • {' → '.join(cycle)}\n"

        return output.strip()

    def _detect_circular_deps(
        self, dependencies: Dict
    ) -> List[List[str]]:
        """Detect circular dependency chains"""
        circular = []

        def has_path(start, end, visited=None):
            if visited is None:
                visited = set()
            if start == end and visited:
                return True
            if start in visited:
                return False
            visited.add(start)

            if start in dependencies:
                for base in dependencies[start]['bases']:
                    if has_path(base, end, visited.copy()):
                        return True
            return False

        # Check each class for cycles
        for class_name in dependencies:
            for base in dependencies[class_name]['bases']:
                if has_path(base, class_name):
                    circular.append([class_name, base, class_name])

        return circular

    async def _solid_analyze_inheritance(
        self, args: Dict[str, Any]
    ) -> List[TextContent]:
        """Analyze inheritance hierarchies"""
        path = args["path"]
        max_depth = args.get("max_depth", 5)
        include_methods = args.get("include_methods", True)

        path_obj = Path(path)
        if not path_obj.exists():
            return [
                TextContent(
                    type="text",
                    text=f"❌ Path not found: {path}"
                )
            ]

        # Collect all Python files
        if path_obj.is_file():
            files = [path_obj]
        else:
            files = list(path_obj.rglob("*.py"))
            files = [
                f for f in files
                if "__pycache__" not in str(f)
            ]

        # Parse and build inheritance tree
        classes = {}
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_info = {
                            'name': node.name,
                            'file': str(file_path.name),
                            'bases': [
                                b.id if isinstance(b, ast.Name)
                                else str(b)
                                for b in node.bases
                            ],
                            'methods': [],
                            'line': node.lineno
                        }

                        if include_methods:
                            for item in node.body:
                                if isinstance(item, ast.FunctionDef):
                                    class_info['methods'].append({
                                        'name': item.name,
                                        'line': item.lineno,
                                        'args': [
                                            a.arg for a in item.args.args
                                        ]
                                    })

                        classes[node.name] = class_info

            except Exception:
                continue

        if not classes:
            return [
                TextContent(
                    type="text",
                    text="⚠️  No classes found to analyze"
                )
            ]

        # Build inheritance tree
        output = """
🌳 INHERITANCE HIERARCHY ANALYSIS
{'=' * 60}

"""

        # Find root classes (no bases or external bases)
        root_classes = [
            name for name, info in classes.items()
            if not info['bases'] or
            all(b not in classes for b in info['bases'])
        ]

        for root in root_classes:
            output += self._format_inheritance_tree(
                root, classes, 0, max_depth, include_methods
            )

        # Check for LSP violations
        lsp_violations = self._check_lsp_violations(classes)
        if lsp_violations:
            output += "\n\n⚠️  LISKOV SUBSTITUTION VIOLATIONS:\n"
            for violation in lsp_violations:
                output += f"   • {violation}\n"

        return [TextContent(type="text", text=output.strip())]

    def _format_inheritance_tree(
        self,
        class_name: str,
        classes: Dict,
        depth: int,
        max_depth: int,
        include_methods: bool
    ) -> str:
        """Format inheritance tree recursively"""
        if depth >= max_depth or class_name not in classes:
            return ""

        indent = "  " * depth
        marker = "└─" if depth > 0 else "📦"

        output = f"{indent}{marker} {class_name}"

        if class_name in classes:
            info = classes[class_name]
            output += f" ({info['file']}:{info['line']})\n"

            if include_methods and info['methods']:
                method_indent = "  " * (depth + 1)
                output += f"{method_indent}Methods:\n"
                for method in info['methods'][:5]:
                    args = ', '.join(method['args'])
                    output += f"{method_indent}  • "
                    output += f"{method['name']}({args})\n"
                if len(info['methods']) > 5:
                    remaining = len(info['methods']) - 5
                    output += f"{method_indent}  ... "
                    output += f"({remaining} more methods)\n"

        # Find children
        children = [
            name for name, info in classes.items()
            if class_name in info['bases']
        ]

        for child in children:
            output += self._format_inheritance_tree(
                child, classes, depth + 1, max_depth, include_methods
            )

        return output

    def _check_lsp_violations(self, classes: Dict) -> List[str]:
        """Check for Liskov Substitution Principle violations"""
        violations = []

        for class_name, class_info in classes.items():
            for base_class in class_info['bases']:
                if base_class not in classes:
                    continue

                base_methods = {
                    m['name']: m
                    for m in classes[base_class]['methods']
                }
                child_methods = {
                    m['name']: m for m in class_info['methods']
                }

                # Check method signature compatibility
                for method_name, base_method in base_methods.items():
                    if method_name in child_methods:
                        child_method = child_methods[method_name]
                        if len(child_method['args']) != len(
                            base_method['args']
                        ):
                            violations.append(
                                f"{class_name}.{method_name}() "
                                f"has different signature than "
                                f"{base_class}.{method_name}()"
                            )

        return violations
