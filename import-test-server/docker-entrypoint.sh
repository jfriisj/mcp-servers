#!/bin/bash
# Docker entrypoint script for Import Test MCP Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Starting Import Test MCP Server...${NC}"

# Function to print usage
usage() {
    echo -e "${YELLOW}Import Test MCP Server Docker Container${NC}"
    echo ""
    echo "Usage modes:"
    echo "  1. MCP Server mode (default):"
    echo "     docker run -v /path/to/code:/workspace ghcr.io/jfriisj/import-test-mcp-server"
    echo ""
    echo "  2. Test mode:"
    echo "     docker run -v /path/to/code:/workspace ghcr.io/jfriisj/import-test-mcp-server --test"
    echo ""
    echo "  3. Interactive analysis:"
    echo "     docker run -it -v /path/to/code:/workspace ghcr.io/jfriisj/import-test-mcp-server bash"
    echo ""
    echo "  4. Generate report to host:"
    echo "     docker run -v /path/to/code:/workspace -v /path/to/output:/output \\"
    echo "       ghcr.io/jfriisj/import-test-mcp-server --generate-report"
    echo ""
    echo "  5. Quick analysis:"
    echo "     docker run -v /path/to/code:/workspace \\"
    echo "       ghcr.io/jfriisj/import-test-mcp-server --quick-check"
    echo ""
    echo "Options:"
    echo "  --test                Run in test mode"
    echo "  --generate-report     Generate comprehensive report and exit"
    echo "  --quick-check         Run quick import validation and exit"
    echo "  --project-root PATH   Set project root directory (default: /workspace)"
    echo "  --help               Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  IMPORT_TEST_PROJECT_ROOT   Project root directory"
    echo "  IMPORT_TEST_OUTPUT_DIR     Output directory for reports"
    echo "  IMPORT_TEST_MAX_FILES      Maximum files to analyze (default: 100)"
    echo "  IMPORT_TEST_INCLUDE_TESTS  Include test files (default: true)"
}

# Function to check if directory exists and has Python files
check_project_dir() {
    local dir="$1"
    
    # Convert Windows paths to Unix paths if needed (Git Bash on Windows)
    if [[ "$dir" =~ ^[A-Z]: ]]; then
        echo -e "${YELLOW}⚠️  Detected Windows path format. Converting to Unix format...${NC}"
        # This shouldn't happen in Docker, but just in case
        dir="/workspace"
        echo -e "${BLUE}ℹ️  Using mounted workspace: $dir${NC}"
    fi
    
    if [ ! -d "$dir" ]; then
        echo -e "${RED}❌ Error: Project directory '$dir' does not exist${NC}"
        echo -e "${YELLOW}💡 Make sure to mount your code directory to /workspace:${NC}"
        echo -e "   docker run -v /path/to/your/code:/workspace ghcr.io/jfriisj/import-test-mcp-server"
        exit 1
    fi
    
    # Check if there are any Python files
    if ! find "$dir" -name "*.py" -type f | head -1 | grep -q .; then
        echo -e "${YELLOW}⚠️  Warning: No Python files found in '$dir'${NC}"
        echo -e "${BLUE}ℹ️  The server will still start, but there's nothing to analyze${NC}"
    else
        local py_count=$(find "$dir" -name "*.py" -type f | wc -l)
        echo -e "${GREEN}✅ Found $py_count Python files to analyze${NC}"
    fi
}

# Function to run quick import check
quick_check() {
    local project_root="${IMPORT_TEST_PROJECT_ROOT:-/workspace}"
    
    echo -e "${BLUE}⚡ Running quick import validation...${NC}"
    echo -e "${BLUE}📁 Project: $project_root${NC}"
    
    # Check project directory
    check_project_dir "$project_root"
    
    # Run quick analysis
    echo -e "${BLUE}🔍 Analyzing imports...${NC}"
    python src/main.py --test --project-root "$project_root"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Quick check completed successfully${NC}"
    else
        echo -e "${RED}❌ Quick check found issues${NC}"
        exit 1
    fi
    
    exit 0
}

# Function to generate comprehensive report and exit
generate_report() {
    local project_root="${IMPORT_TEST_PROJECT_ROOT:-/workspace}"
    local output_dir="${IMPORT_TEST_OUTPUT_DIR:-/output}"
    local max_files="${IMPORT_TEST_MAX_FILES:-100}"
    local include_tests="${IMPORT_TEST_INCLUDE_TESTS:-true}"
    
    echo -e "${BLUE}📊 Generating comprehensive import analysis report...${NC}"
    echo -e "${BLUE}📁 Project: $project_root${NC}"
    echo -e "${BLUE}💾 Output: $output_dir${NC}"
    echo -e "${BLUE}📋 Max files: $max_files${NC}"
    echo -e "${BLUE}🧪 Include tests: $include_tests${NC}"
    
    # Check project directory
    check_project_dir "$project_root"
    
    # Ensure output directory exists
    mkdir -p "$output_dir"
    
    # Generate timestamp for report filename
    timestamp=$(date +"%Y%m%d_%H%M%S")
    
    # Generate main analysis report
    echo -e "${BLUE}🔍 Running comprehensive analysis...${NC}"
    python src/main.py --test --project-root "$project_root" > "$output_dir/import_analysis_${timestamp}.txt" 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Analysis completed successfully${NC}"
        
        # Create a summary file
        summary_file="$output_dir/import_summary_${timestamp}.md"
        
        echo "# Import Analysis Report" > "$summary_file"
        echo "" >> "$summary_file"
        echo "**Project:** $project_root" >> "$summary_file"
        echo "**Generated:** $(date)" >> "$summary_file"
        echo "**Analysis Scope:** Up to $max_files Python files" >> "$summary_file"
        echo "**Include Tests:** $include_tests" >> "$summary_file"
        echo "" >> "$summary_file"
        
        # Extract key metrics from the analysis
        echo "## Summary" >> "$summary_file"
        tail -20 "$output_dir/import_analysis_${timestamp}.txt" | head -10 >> "$summary_file"
        
        echo "" >> "$summary_file"
        echo "## Files" >> "$summary_file"
        echo "- **Full Report:** import_analysis_${timestamp}.txt" >> "$summary_file"
        echo "- **Summary:** import_summary_${timestamp}.md" >> "$summary_file"
        
        echo -e "${GREEN}✅ Reports generated:${NC}"
        echo -e "   📄 Full report: $output_dir/import_analysis_${timestamp}.txt"
        echo -e "   📋 Summary: $summary_file"
    else
        echo -e "${RED}❌ Analysis failed${NC}"
        exit 1
    fi
    
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            usage
            exit 0
            ;;
        --test)
            TEST_MODE=true
            shift
            ;;
        --generate-report)
            GENERATE_REPORT=true
            shift
            ;;
        --quick-check)
            QUICK_CHECK=true
            shift
            ;;
        --project-root)
            IMPORT_TEST_PROJECT_ROOT="$2"
            shift 2
            ;;
        bash|sh|/bin/bash|/bin/sh)
            echo -e "${BLUE}🐚 Starting interactive shell...${NC}"
            exec "$@"
            ;;
        *)
            # Pass through other arguments to the Python script
            PYTHON_ARGS+=("$1")
            shift
            ;;
    esac
done

# Set default project root if not specified
PROJECT_ROOT="${IMPORT_TEST_PROJECT_ROOT:-/workspace}"

# Special case: quick check mode
if [ "$QUICK_CHECK" = true ]; then
    quick_check
fi

# Special case: generate report mode
if [ "$GENERATE_REPORT" = true ]; then
    generate_report
fi

# Check project directory
check_project_dir "$PROJECT_ROOT"

# Display container information
echo -e "${BLUE}📦 Container Information:${NC}"
echo -e "   Project Root: $PROJECT_ROOT"
echo -e "   Output Dir: ${IMPORT_TEST_OUTPUT_DIR:-/output}"
echo -e "   Max Files: ${IMPORT_TEST_MAX_FILES:-100}"
echo -e "   Python Version: $(python --version)"
echo -e "   User: $(whoami)"
echo ""

if [ "$TEST_MODE" = true ]; then
    echo -e "${YELLOW}🧪 Running in test mode...${NC}"
    exec python src/main.py --test --project-root "$PROJECT_ROOT" "${PYTHON_ARGS[@]}"
else
    echo -e "${GREEN}🎯 Starting MCP server mode...${NC}"
    echo -e "${BLUE}ℹ️  The server is now ready to receive MCP protocol messages${NC}"
    echo -e "${BLUE}ℹ️  Connect your MCP client to this container's stdio${NC}"
    echo ""
    echo -e "${YELLOW}💡 Available MCP tools:${NC}"
    echo -e "   - import-test-analyze-file: Analyze single file imports"
    echo -e "   - import-test-analyze-project: Analyze entire project"
    echo -e "   - import-test-circular-imports: Detect circular dependencies"
    echo -e "   - import-test-validate-dependencies: Check dependencies"
    echo -e "   - import-test-unused-imports: Find unused imports"
    echo -e "   - import-test-get-stats: Get project statistics"
    echo ""
    exec python src/main.py --project-root "$PROJECT_ROOT" "${PYTHON_ARGS[@]}"
fi