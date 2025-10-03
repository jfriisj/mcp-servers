# SOLID Principles MCP Server

A comprehensive Model Context Protocol (MCP) server that analyzes Python code files for adherence to SOLID principles, providing detailed reports, suggestions, and educational content to help developers write better, more maintainable code.

## 🚀 Overview

The SOLID Principles MCP Server transforms how AI assistants help with code quality by providing:

- **📊 Comprehensive SOLID Analysis** - Analyzes Python files against all five SOLID principles
- **🎯 Detailed Violation Reports** - Pinpoints exact issues with line numbers and explanations
- **💡 Actionable Suggestions** - Provides specific recommendations for fixing violations
- **📈 Scoring System** - Quantifies code quality with 0-100 scores
- **📚 Educational Content** - Includes detailed explanations and examples for each principle
- **🔄 Batch Processing** - Analyzes entire directories and generates comprehensive reports

## ✨ Key Features

### 🔍 SOLID Principles Analysis

- **Single Responsibility Principle (SRP)** - Detects classes with multiple responsibilities
- **Open-Closed Principle (OCP)** - Identifies code that's hard to extend without modification  
- **Liskov Substitution Principle (LSP)** - Finds inheritance issues and contract violations
- **Interface Segregation Principle (ISP)** - Spots fat interfaces and unused methods
- **Dependency Inversion Principle (DIP)** - Discovers tight coupling and concrete dependencies

### 📊 Advanced Analysis Features

- **AST-based Analysis** - Uses Python's Abstract Syntax Tree for accurate code parsing
- **Severity Levels** - Classifies violations as high, medium, or low priority
- **Code Snippets** - Shows context around violations for easier understanding
- **Multiple Output Formats** - Supports text, JSON, and Markdown report formats
- **Filtering Options** - Filter by principle, severity, or file patterns

### 🎓 Educational Tools

- **Principle Explanations** - Detailed guides with examples and best practices
- **Violation Context** - Shows exactly what's wrong and how to fix it
- **Best Practice Examples** - Demonstrates good vs. bad patterns
- **Progressive Learning** - Start with high-severity issues and work down

## 📁 Project Structure

```
solid-server/
├── src/
│   ├── main.py                # Main MCP server entry point
│   ├── server.py              # Core MCP server implementation  
│   ├── mcp_handler.py         # MCP protocol handling
│   ├── solid_analyzer.py      # Core SOLID analysis engine
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- MCP-compatible client (VS Code with MCP extension, Claude Desktop, etc.)

### 1. Install Dependencies

```bash
cd solid-server
pip install -r requirements.txt
```

### 2. Add to MCP Configuration

#### VS Code (.vscode/mcp.json)

```json
{
  "servers": {
    "solid": {
      "command": "python",
      "args": [
        "solid-server/src/main.py",
        "--project-root",
        "${workspaceFolder}"
      ],
      "cwd": "C:/github/mcp-servers",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

#### Claude Desktop (claude_desktop_config.json)

```json
{
  "mcpServers": {
    "solid": {
      "command": "python",
      "args": [
        "/path/to/solid-server/src/main.py",
        "--project-root",
        "/path/to/your/project"
      ]
    }
  }
}
```

### 3. Command Line Options

The server supports several command line arguments:

- `--project-root PATH`: Specify the root directory for analysis (defaults to current directory)
- `--test`: Run in test mode for debugging and validation

**Example usage:**

```bash
# Use specific project root
python src/main.py --project-root /path/to/project

# Test mode for debugging
python src/main.py --test --project-root /path/to/project
```

## 🔧 Available Tools

### Core Analysis Tools

#### `solid-check-file`
Analyze a single Python file for SOLID violations.

```json
{
  "file_path": "path/to/file.py",
  "principles": ["SRP", "OCP", "LSP", "ISP", "DIP"]  // or ["ALL"]
}
```

#### `solid-check-directory`
Analyze all Python files in a directory.

```json
{
  "directory_path": "path/to/directory",
  "include_patterns": ["*.py"],
  "exclude_patterns": ["__pycache__", ".git", "test_*"],
  "max_files": 100
}
```

#### `solid-generate-report`
Generate comprehensive SOLID analysis reports.

```json
{
  "directory_path": "path/to/directory", 
  "output_format": "text|json|markdown",
  "include_suggestions": true,
  "severity_filter": "all|high|medium|low"
}
```

### Educational Tools

#### `solid-explain-principle`
Get detailed explanations of SOLID principles.

```json
{
  "principle": "SRP|OCP|LSP|ISP|DIP"
}
```

### Reporting Tools

#### `solid-check-score`
Get compliance scores for files or directories.

```json
{
  "path": "path/to/file_or_directory"
}
```

#### `solid-list-violations`
List violations with filtering options.

```json
{
  "path": "path/to/analyze",
  "principle_filter": "SRP|OCP|LSP|ISP|DIP|ALL",
  "severity_filter": "high|medium|low|all"
}
```

## 📊 Understanding the Analysis

### Violation Severity Levels

- **High** 🚨 - Critical issues that break SOLID principles (e.g., NotImplementedError in overrides)
- **Medium** ⚠️ - Significant violations that impact maintainability (e.g., multiple responsibilities)  
- **Low** 💡 - Minor issues and code smells (e.g., long methods, many parameters)

### Scoring System

- **100** - Perfect SOLID compliance, no violations found
- **90-99** - Excellent with minor improvements needed
- **70-89** - Good with some violations to address
- **50-69** - Needs improvement, multiple violations present
- **0-49** - Poor compliance, significant refactoring needed

### Common Violations Detected

#### Single Responsibility Principle
- Classes with multiple distinct responsibilities
- Methods that are too long (>30 lines)
- Classes handling data access, business logic, and presentation

#### Open-Closed Principle
- Type checking with `isinstance()` or `type()`
- Long if/elif chains in functions
- Code that requires modification to add new behavior

#### Liskov Substitution Principle
- `NotImplementedError` in overridden methods
- Method signature mismatches between parent and child classes
- Subclasses that strengthen preconditions or weaken postconditions

#### Interface Segregation Principle
- Interfaces with too many methods (>10)
- Empty method implementations
- Classes forced to implement unused methods

#### Dependency Inversion Principle
- Direct instantiation of concrete classes
- Hard-coded dependencies in constructors
- High-level modules depending on low-level modules

## 🎓 Educational Examples

### Good vs Bad Examples

#### Single Responsibility Principle

**❌ Violation:**
```python
class Employee:
    def calculate_pay(self): pass      # Business logic
    def save_to_database(self): pass   # Data persistence
    def generate_report(self): pass    # Reporting
```

**✅ Better:**
```python
class Employee:
    def calculate_pay(self): pass

class EmployeeRepository:
    def save(self, employee): pass

class EmployeeReportGenerator:
    def generate_report(self, employee): pass
```

#### Open-Closed Principle

**❌ Violation:**
```python
def calculate_area(shape):
    if shape.type == "circle":
        return 3.14 * shape.radius ** 2
    elif shape.type == "rectangle":
        return shape.width * shape.height
    # Must modify for new shapes
```

**✅ Better:**
```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self): pass

class Circle(Shape):
    def area(self): return 3.14 * self.radius ** 2

class Rectangle(Shape):
    def area(self): return self.width * self.height
```

## 🔄 Integration Workflows

### 1. Code Review Workflow
1. Run `solid-check-directory` on changed files
2. Focus on high-severity violations first
3. Use `solid-explain-principle` for team education
4. Generate reports for documentation

### 2. Refactoring Workflow  
1. Get baseline score with `solid-check-score`
2. Use `solid-list-violations` to prioritize work
3. Apply suggestions and re-analyze
4. Track improvement over time

### 3. Learning Workflow
1. Start with `solid-explain-principle` for each principle
2. Analyze your code with `solid-check-file`
3. Practice fixing violations using suggestions
4. Use examples to understand better patterns

## 🚀 Advanced Usage

### Batch Analysis Script

```python
from solid_analyzer import SolidBatchAnalyzer
from pathlib import Path

analyzer = SolidBatchAnalyzer()
reports = analyzer.analyze_directory(Path("src"))
summary = analyzer.generate_summary_report(reports)

print(f"Average score: {summary['average_score']}")
print(f"Total violations: {summary['total_violations']}")
```

### Custom Filtering

```python
# Filter by specific principles and severity
violations = []
for report in reports:
    for violation in report.violations:
        if (violation.principle.value in ["SRP", "DIP"] and 
            violation.severity == "high"):
            violations.append(violation)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality  
4. Update documentation
5. Submit a pull request

### Development Guidelines

- Follow existing code patterns
- Add docstrings to all functions
- Test with various Python codebases
- Update README for new features
- Ensure MCP compatibility

## 📋 Requirements

- **Python 3.8+** for async support and modern features
- **mcp>=0.1.0** for MCP protocol support
- **pydantic>=2.0.0** for data validation

No external analysis tools required - uses Python's built-in AST parser for accurate code analysis.

## 🐛 Troubleshooting

### Common Issues

**Server won't start:**
- Check Python version (3.8+)
- Verify MCP package installation
- Ensure project root exists

**No files analyzed:**
- Check include/exclude patterns
- Verify file extensions (.py)
- Confirm directory permissions

**Analysis errors:**
- Check Python file syntax
- Verify file encoding (UTF-8)
- Review error messages in logs

### Debug Mode

Use `--test` flag to run in debug mode:

```bash
python src/main.py --test --project-root /path/to/project
```

This will analyze a few files and show results without MCP protocol overhead.

## 📄 License

This project is open source. Check the main repository for licensing information.

## 🙏 Acknowledgments

- [Robert C. Martin (Uncle Bob)](https://blog.cleancoder.com/) for the SOLID principles
- [Model Context Protocol](https://modelcontextprotocol.io/) for the standardized AI integration
- [Python AST module](https://docs.python.org/3/library/ast.html) for code parsing capabilities

---

**Ready to improve your code quality? Start analyzing with SOLID principles today!**