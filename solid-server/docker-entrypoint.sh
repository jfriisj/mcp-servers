#!/bin/bash
# Docker entrypoint script for SOLID Principles MCP Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting SOLID Principles MCP Server...${NC}"

# Function to print usage
usage() {
    echo -e "${YELLOW}SOLID Principles MCP Server Docker Container${NC}"
    echo ""
    echo "Usage modes:"
    echo "  1. MCP Server mode (default):"
    echo "     docker run -v /path/to/code:/workspace ghcr.io/jfriisj/solid-mcp-server"
    echo ""
    echo "  2. Test mode:"
    echo "     docker run -v /path/to/code:/workspace ghcr.io/jfriisj/solid-mcp-server --test"
    echo ""
    echo "  3. Interactive analysis:"
    echo "     docker run -it -v /path/to/code:/workspace ghcr.io/jfriisj/solid-mcp-server bash"
    echo ""
    echo "  4. Generate report to host:"
    echo "     docker run -v /path/to/code:/workspace -v /path/to/output:/output \\"
    echo "       ghcr.io/jfriisj/solid-mcp-server --generate-report"
    echo ""
    echo "Options:"
    echo "  --test                Run in test mode"
    echo "  --generate-report     Generate report and exit"
    echo "  --project-root PATH   Set project root directory (default: /workspace)"
    echo "  --help               Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  SOLID_PROJECT_ROOT   Project root directory"
    echo "  SOLID_OUTPUT_DIR     Output directory for reports"
    echo "  SOLID_FORMAT         Report format (text|json|markdown)"
    echo "  SOLID_SEVERITY       Filter by severity (all|high|medium|low)"
}

# Function to check if directory exists and has Python files
check_project_dir() {
    local dir="$1"
    
    if [ ! -d "$dir" ]; then
        echo -e "${RED}❌ Error: Project directory '$dir' does not exist${NC}"
        echo -e "${YELLOW}💡 Make sure to mount your code directory to /workspace:${NC}"
        echo -e "   docker run -v /path/to/your/code:/workspace ghcr.io/jfriisj/solid-mcp-server"
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

# Function to generate report and exit
generate_report() {
    local project_root="${SOLID_PROJECT_ROOT:-/workspace}"
    local output_dir="${SOLID_OUTPUT_DIR:-/output}"
    local format="${SOLID_FORMAT:-markdown}"
    local severity="${SOLID_SEVERITY:-all}"
    
    echo -e "${BLUE}📊 Generating SOLID compliance report...${NC}"
    echo -e "${BLUE}📁 Project: $project_root${NC}"
    echo -e "${BLUE}💾 Output: $output_dir${NC}"
    echo -e "${BLUE}📝 Format: $format${NC}"
    
    # Ensure output directory exists
    mkdir -p "$output_dir"
    
    # Generate timestamp for report filename
    timestamp=$(date +"%Y%m%d_%H%M%S")
    report_file="$output_dir/solid_report_${timestamp}.${format}"
    
    # Run the analysis and save report
    python src/main.py --test --project-root "$project_root" > "$report_file" 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Report generated successfully: $report_file${NC}"
        
        # Also create a summary
        echo -e "${BLUE}📋 Creating summary...${NC}"
        echo "SOLID Compliance Report - $(date)" > "$output_dir/summary.txt"
        echo "Project: $project_root" >> "$output_dir/summary.txt"
        echo "Generated: $(date)" >> "$output_dir/summary.txt"
        echo "" >> "$output_dir/summary.txt"
        tail -20 "$report_file" >> "$output_dir/summary.txt"
        
        echo -e "${GREEN}✅ Summary created: $output_dir/summary.txt${NC}"
    else
        echo -e "${RED}❌ Report generation failed${NC}"
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
        --project-root)
            SOLID_PROJECT_ROOT="$2"
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
PROJECT_ROOT="${SOLID_PROJECT_ROOT:-/workspace}"

# Special case: generate report mode
if [ "$GENERATE_REPORT" = true ]; then
    generate_report
fi

# Check project directory
check_project_dir "$PROJECT_ROOT"

# Display container information
echo -e "${BLUE}📦 Container Information:${NC}"
echo -e "   Project Root: $PROJECT_ROOT"
echo -e "   Output Dir: ${SOLID_OUTPUT_DIR:-/output}"
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
    exec python src/main.py --project-root "$PROJECT_ROOT" "${PYTHON_ARGS[@]}"
fi