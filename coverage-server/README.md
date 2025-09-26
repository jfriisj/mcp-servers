# Coverage MCP Server

A Model Context Protocol (MCP) server that provides comprehensive Python test coverage analysis using [pytest-cov](https://pytest-cov.readthedocs.io/) and [coverage.py](https://coverage.readthedocs.io/). This server is built with a modular, SOLID-compliant architecture for maintainability and extensibility.

## Features

### 🧪 Test Execution with Coverage

- **Integrated test running** - Execute tests with coverage measurement in one step
- **Configurable thresholds** - Set minimum coverage requirements
- **Parallel execution** - Run tests in parallel using pytest-xdist
- **Marker support** - Select/deselect tests using pytest markers
- **Verbose reporting** - Detailed test and coverage output

### 📊 Multiple Report Formats

- **HTML reports** - Interactive web-based coverage reports
- **XML reports** - Jenkins/CI-compatible coverage reports
- **JSON reports** - Machine-readable coverage data
- **Terminal reports** - Quick command-line coverage summaries
- **Missing line identification** - Show exactly which lines need coverage

### 🎯 Advanced Analysis

- **Threshold checking** - Verify coverage meets requirements
- **Per-file analysis** - Individual file coverage breakdown
- **Missing coverage identification** - Find specific lines without coverage
- **Coverage comparison** - Compare coverage across branches/commits
- **Context tracking** - See which tests exercise each line

## Architecture

This server follows SOLID design principles with a modular architecture:

### Core Modules

- **`models.py`** - Data models and configuration classes using dataclasses
- **`config.py`** - Configuration management and file discovery
- **`coverage_runner.py`** - Test execution and subprocess management
- **`coverage_analyzer.py`** - Coverage data parsing and statistics
- **`coverage_reporter.py`** - Report generation in multiple formats
- **`mcp_handler.py`** - MCP protocol handling and tool definitions
- **`server.py`** - Main server orchestration and resource management
- **`main.py`** - Application entry point

### Design Principles

- **Single Responsibility** - Each module has one clear purpose
- **Open/Closed** - Components can be extended without modification
- **Liskov Substitution** - Consistent interfaces across components
- **Interface Segregation** - Focused interfaces for specific needs
- **Dependency Inversion** - Loose coupling through dependency injection

## Available Tools

### `run-tests-with-coverage`

Run tests with coverage measurement using pytest-cov.

**Parameters:**

- `test_path` (string, optional): Path to tests directory or specific test file (default: "tests/")
- `source` (string, optional): Source directory to measure coverage for (default: "src/")
- `min_coverage` (number, optional): Minimum coverage percentage required (default: 80.0)
- `parallel` (boolean, optional): Run tests in parallel using pytest-xdist (default: false)
- `markers` (string, optional): Pytest markers to select/deselect tests (e.g. 'not slow')
- `verbose` (boolean, optional): Verbose output (default: false)

**Example usage:**

```json
{
  "test_path": "tests/unit/",
  "source": "src/",
  "min_coverage": 85.0,
  "parallel": true,
  "markers": "not slow and not integration"
}
```

### `generate-coverage-report`

Generate coverage reports in multiple formats (HTML, XML, JSON).

**Parameters:**

- `formats` (array, optional): Output formats - html, xml, json, term, term-missing (default: ["html", "xml", "term-missing"])
- `output_dir` (string, optional): Output directory for reports (default: "test-reports")
- `show_missing` (boolean, optional): Show line numbers of missing coverage (default: true)
- `skip_covered` (boolean, optional): Skip files with 100% coverage (default: false)

**Example usage:**

```json
{
  "formats": ["html", "json"],
  "output_dir": "coverage-reports",
  "show_missing": true
}
```

### `check-coverage-threshold`

Check if coverage meets minimum threshold requirements.

**Parameters:**

- `threshold` (number, optional): Minimum coverage percentage required (default: 80.0)
- `per_file` (boolean, optional): Check threshold per file (default: false)
- `fail_under` (boolean, optional): Fail if coverage is below threshold (default: true)

**Example usage:**

```json
{
  "threshold": 90.0,
  "per_file": true
}
```

### `find-missing-coverage`

Identify specific lines and files with missing coverage.

**Parameters:**

- `file_pattern` (string, optional): File pattern to analyze (glob pattern)
- `show_contexts` (boolean, optional): Show test contexts that hit each line (default: false)
- `min_coverage` (number, optional): Show only files below this coverage percentage (default: 100.0)

**Example usage:**

```json
{
  "file_pattern": "src/core/*",
  "min_coverage": 80.0,
  "show_contexts": true
}
```

### `coverage-diff`

Compare coverage between branches or commits.

**Parameters:**

- `base` (string, optional): Base branch/commit to compare against (default: "HEAD~1")
- `format` (string, optional): Output format - text, json (default: "text")

**Example usage:**

```json
{
  "base": "main",
  "format": "json"
}
```

### `coverage-summary`

Get a quick coverage summary with key metrics.

**Parameters:**

- `show_files` (boolean, optional): Include per-file coverage breakdown (default: true)
- `sort_by` (string, optional): Sort files by coverage, missing, or name (default: "coverage")

**Example usage:**

```json
{
  "show_files": true,
  "sort_by": "missing"
}
```

## Installation

### Prerequisites

- Python 3.8+
- pytest and coverage tools
- MCP client or compatible development environment

### Install Dependencies

```bash
cd mcp-servers/coverage-server
pip install -r requirements.txt
```

### Install Coverage Tools

```bash
pip install pytest pytest-cov coverage pytest-xdist
```

## Configuration

The server automatically detects and uses configuration files in this order:

1. `pytest.ini`
2. `pyproject.toml`
3. `tox.ini`
4. `setup.cfg`

### Example pyproject.toml configuration

```toml

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

addopts = [
    "--verbose",
    "--strict-markers",
    "--strict-config",
    "--cov=src",
    "--cov-report=html:test-reports/coverage-html",
    "--cov-report=xml:test-reports/coverage.xml",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
    "--junit-xml=test-reports/junit.xml"
]

markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow running tests"
]

[tool.coverage.run]
source = ["src"]
branch = true
parallel = true

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
fail_under = 80.0

exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "@(abc\\.)?abstractmethod"
]

[tool.coverage.html]
directory = "test-reports/coverage-html"
title = "Project Coverage Report"

[tool.coverage.xml]
output = "test-reports/coverage.xml"

[tool.coverage.json]
output = "test-reports/coverage.json"
```

## Integration with Project

This server integrates seamlessly with the existing afhandling project:

- Uses the project's `pytest.ini` and `pyproject.toml` configuration
- Compatible with existing test structure and patterns
- Generates reports in `test-reports/` directory (matching project structure)
- Supports all pytest markers and fixtures
- Integrates with CI/CD pipelines via XML and JSON reports

## Usage Examples

### Run tests with coverage

```python
# Through MCP client
await call_tool("run-tests-with-coverage", {
    "source": "src/",
    "min_coverage": 85.0,
    "parallel": True
})
```

### Generate HTML report

```python
await call_tool("generate-coverage-report", {
    "formats": ["html"],
    "output_dir": "coverage-reports"
})
```

### Check threshold compliance

```python
await call_tool("check-coverage-threshold", {
    "threshold": 90.0,
    "per_file": True
})
```

### Find files needing coverage

```python
await call_tool("find-missing-coverage", {
    "min_coverage": 80.0,
    "show_contexts": True
})
```

### Quick summary

```python
await call_tool("coverage-summary", {
    "show_files": True,
    "sort_by": "coverage"
})
```

## Output Formats

### HTML Reports

- Interactive web interface
- Line-by-line coverage highlighting
- Sortable file listings
- Branch coverage visualization
- Generated in `{output_dir}/coverage-html/`

### XML Reports

- Jenkins/GitLab CI compatible
- Cobertura format
- Machine-readable for CI/CD integration
- Generated as `{output_dir}/coverage.xml`

### JSON Reports

- Complete coverage data
- Programmatically accessible
- Per-file and per-line details
- Generated as `{output_dir}/coverage.json`

### Terminal Reports

- Quick command-line feedback
- Missing line numbers
- Summary statistics
- Color-coded output

## Error Handling

The server includes comprehensive error handling:

- Graceful fallback when tools are not installed
- Clear error messages for configuration issues
- Proper handling of test failures vs coverage failures
- Timeout protection for long-running test suites
- Detailed error reporting with context

## Performance Considerations

### Parallel Testing

- Use `parallel: true` for large test suites
- Automatic CPU core detection with pytest-xdist
- Significant speedup for I/O-bound tests
- Proper coverage aggregation across processes

### Coverage Optimization

- Branch coverage for thorough analysis
- Configurable exclusion patterns
- Smart context tracking
- Efficient report generation

### Large Codebases

- Incremental coverage analysis
- File pattern filtering
- Selective test execution with markers
- Memory-efficient processing

## Development

### Running the Server

```bash
python src/main.py [project_root]
```

### Testing the Server

The server includes fallback mode for development without the MCP package.

### Debugging

- Verbose mode for detailed output
- Context tracking for test coverage
- Missing line identification
- Error stacktraces with full context

## Compatibility

- **pytest version**: 7.0.0 or later
- **coverage version**: 7.0.0 or later
- **Python version**: 3.8+
- **MCP protocol**: 2024-11-05
- **Configuration**: pytest.ini, pyproject.toml, setup.cfg, tox.ini

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run tests with coverage
  run: |
    python mcp-servers/coverage-server/src/main.py
    # Use MCP tools via CI integration

- name: Upload coverage reports
  uses: codecov/codecov-action@v3
  with:
    file: test-reports/coverage.xml
```

### Jenkins

- XML reports compatible with Jenkins coverage plugins
- JUnit XML for test result integration
- HTML reports for artifact archiving

### GitLab CI

- Cobertura XML format support
- Coverage badges and merge request integration
- Artifact storage for HTML reports

This server provides enterprise-grade test coverage analysis while maintaining simplicity and integration with existing development workflows.
