"""
MCP Handler for SOLID Principles Analysis
========================================
Handles MCP protocol tool calls for SOLID analysis.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from mcp.types import TextContent, Tool
from solid_analyzer import SolidAnalyzer, SolidBatchAnalyzer, SolidPrinciple


class MCPHandler:
    """MCP protocol handler for SOLID analysis tools"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.analyzer = SolidAnalyzer()
        self.batch_analyzer = SolidBatchAnalyzer()
    
    def get_tools(self) -> List[Tool]:
        """Return list of available SOLID analysis tools"""
        return [
            Tool(
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
            ),
            Tool(
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
            ),
            Tool(
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
            ),
            Tool(
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
            ),
            Tool(
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
            ),
            Tool(
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
        ]
    
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
        
        principles = args.get("principles", ["ALL"])
        
        # Analyze the file
        report = self.analyzer.analyze_file(file_path)
        
        # Filter by requested principles if not ALL
        if "ALL" not in principles:
            principle_enums = []
            for p in principles:
                try:
                    principle_enums.append(SolidPrinciple(p))
                except ValueError:
                    return [TextContent(type="text", text=f"Invalid principle: {p}")]
            
            filtered_violations = [v for v in report.violations if v.principle in principle_enums]
            report.violations = filtered_violations
        
        # Format output
        output = self._format_file_report(report)
        return [TextContent(type="text", text=output)]
    
    async def _solid_check_directory(self, args: Dict[str, Any]) -> List[TextContent]:
        """Analyze all files in a directory"""
        directory_path = Path(args["directory_path"])
        if not directory_path.is_absolute():
            directory_path = self.project_root / directory_path
        
        if not directory_path.exists():
            return [TextContent(type="text", text=f"Directory not found: {directory_path}")]
        
        include_patterns = args.get("include_patterns", ["*.py"])
        exclude_patterns = args.get("exclude_patterns", ["__pycache__", ".git", ".venv", "venv", "test_*"])
        max_files = args.get("max_files", 100)
        
        # Analyze directory
        reports = self.batch_analyzer.analyze_directory(
            directory_path, include_patterns, exclude_patterns
        )
        
        # Limit results
        if len(reports) > max_files:
            reports = reports[:max_files]
        
        # Generate summary
        summary = self.batch_analyzer.generate_summary_report(reports)
        
        # Format output
        output = self._format_directory_report(reports, summary, directory_path)
        return [TextContent(type="text", text=output)]
    
    async def _solid_generate_report(self, args: Dict[str, Any]) -> List[TextContent]:
        """Generate comprehensive SOLID report"""
        directory_path = Path(args["directory_path"])
        if not directory_path.is_absolute():
            directory_path = self.project_root / directory_path
        
        output_format = args.get("output_format", "text")
        include_suggestions = args.get("include_suggestions", True)
        severity_filter = args.get("severity_filter", "all")
        
        # Analyze directory
        reports = self.batch_analyzer.analyze_directory(directory_path)
        summary = self.batch_analyzer.generate_summary_report(reports)
        
        # Filter by severity
        if severity_filter != "all":
            for report in reports:
                report.violations = [v for v in report.violations if v.severity == severity_filter]
        
        # Generate report based on format
        if output_format == "json":
            output = self._format_json_report(reports, summary)
        elif output_format == "markdown":
            output = self._format_markdown_report(reports, summary, include_suggestions)
        else:
            output = self._format_text_report(reports, summary, include_suggestions)
        
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
            # Single file score
            report = self.analyzer.analyze_file(path)
            output = f"""
SOLID Compliance Score for: {path.name}
Score: {report.score:.1f}/100

Violation Summary:
- SRP: {report.summary.get(SolidPrinciple.SINGLE_RESPONSIBILITY, 0)} violations
- OCP: {report.summary.get(SolidPrinciple.OPEN_CLOSED, 0)} violations  
- LSP: {report.summary.get(SolidPrinciple.LISKOV_SUBSTITUTION, 0)} violations
- ISP: {report.summary.get(SolidPrinciple.INTERFACE_SEGREGATION, 0)} violations
- DIP: {report.summary.get(SolidPrinciple.DEPENDENCY_INVERSION, 0)} violations

Total Violations: {len(report.violations)}
            """.strip()
        
        elif path.is_dir():
            # Directory score
            reports = self.batch_analyzer.analyze_directory(path)
            summary = self.batch_analyzer.generate_summary_report(reports)
            output = f"""
SOLID Compliance Score for: {path.name}
Average Score: {summary['average_score']}/100

Summary:
- Total Files: {summary['total_files']}
- Files with Violations: {summary['files_with_violations']}
- Total Violations: {summary['total_violations']}

Violations by Principle:
- SRP: {summary['violations_by_principle']['SRP']} violations
- OCP: {summary['violations_by_principle']['OCP']} violations
- LSP: {summary['violations_by_principle']['LSP']} violations  
- ISP: {summary['violations_by_principle']['ISP']} violations
- DIP: {summary['violations_by_principle']['DIP']} violations
            """.strip()
        else:
            return [TextContent(type="text", text=f"Path not found: {path}")]
        
        return [TextContent(type="text", text=output)]
    
    async def _solid_list_violations(self, args: Dict[str, Any]) -> List[TextContent]:
        """List SOLID violations in structured format"""
        path = Path(args["path"])
        if not path.is_absolute():
            path = self.project_root / path
        
        principle_filter = args.get("principle_filter", "ALL")
        severity_filter = args.get("severity_filter", "all")
        
        # Get reports
        if path.is_file():
            reports = [self.analyzer.analyze_file(path)]
        elif path.is_dir():
            reports = self.batch_analyzer.analyze_directory(path)
        else:
            return [TextContent(type="text", text=f"Path not found: {path}")]
        
        # Filter violations
        all_violations = []
        for report in reports:
            for violation in report.violations:
                # Filter by principle
                if principle_filter != "ALL" and violation.principle.value != principle_filter:
                    continue
                
                # Filter by severity
                if severity_filter != "all" and violation.severity != severity_filter:
                    continue
                
                all_violations.append({
                    "file": report.file_path,
                    "violation": violation
                })
        
        if not all_violations:
            return [TextContent(type="text", text="No violations found matching the criteria.")]
        
        # Format output
        output = f"Found {len(all_violations)} violations:\n\n"
        
        for item in all_violations[:50]:  # Limit to 50 violations
            v = item["violation"]
            file_name = Path(item["file"]).name
            output += f"📍 {file_name}:{v.line_number} [{v.principle.value}] {v.severity.upper()}\n"
            output += f"   {v.message}\n"
            output += f"   💡 {v.suggestion}\n\n"
        
        if len(all_violations) > 50:
            output += f"... and {len(all_violations) - 50} more violations.\n"
        
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