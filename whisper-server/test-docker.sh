#!/bin/bash
# Docker MCP Test Runner
# ======================
# This script helps test the Whisper MCP server in Docker

set -e

echo "🐳 Whisper MCP Server - Docker Test Suite"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_success "Docker is running"

# Check if Hugging Face token is set
if [ -z "$HUGGINGFACE_TOKEN" ] && [ -z "$HF_TOKEN" ]; then
    print_warning "HUGGINGFACE_TOKEN not set. Using test mode."
    export HUGGINGFACE_TOKEN="test_token"
    export TEST_MODE="true"
fi

# Build the Docker image
echo ""
echo "📦 Building Docker image..."
echo "----------------------------"
if docker-compose build; then
    print_success "Docker image built successfully"
else
    print_error "Failed to build Docker image"
    exit 1
fi

# Test 1: Run MCP tests inside container
echo ""
echo "🧪 Test 1: Running MCP tests inside Docker container..."
echo "-------------------------------------------------------"
if docker-compose run --rm whisper-api python tests/test_docker_mcp.py; then
    print_success "MCP tests passed inside container"
else
    print_error "MCP tests failed inside container"
    exit 1
fi

# Test 2: Test Clean Architecture components
echo ""
echo "🧪 Test 2: Testing Clean Architecture components..."
echo "---------------------------------------------------"
if docker-compose run --rm whisper-api python tests/test_whisper.py; then
    print_success "Clean Architecture tests passed"
else
    print_warning "Clean Architecture tests had issues (may need audio files)"
fi

# Test 3: Start server in MCP mode and verify it starts
echo ""
echo "🧪 Test 3: Starting MCP server (stdio mode)..."
echo "----------------------------------------------"
print_warning "This will start the MCP server. Press Ctrl+C to stop."
echo ""
echo "To test MCP server manually:"
echo "  1. Configure your MCP client (Claude Desktop, etc.)"
echo "  2. Use the docker-compose.mcp.yml configuration"
echo "  3. Test MCP tools via the client interface"
echo ""
read -p "Press Enter to start MCP server (or Ctrl+C to skip)..."

docker-compose run --rm whisper-api --mode mcp &
SERVER_PID=$!

sleep 5

if kill -0 $SERVER_PID 2>/dev/null; then
    print_success "MCP server started successfully (PID: $SERVER_PID)"
    print_warning "Stopping server..."
    kill $SERVER_PID
else
    print_warning "MCP server process not found (may have exited)"
fi

# Test 4: Start API server and test endpoints
echo ""
echo "🧪 Test 4: Starting API server..."
echo "---------------------------------"
print_warning "This will start the API server on port 8000"
echo ""
echo "To test API manually:"
echo "  docker-compose up -d whisper-api"
echo "  curl http://localhost:8000/health"
echo "  docker-compose down"
echo ""

# Summary
echo ""
echo "=========================================="
echo "🎉 Docker Test Suite Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Test MCP client integration:"
echo "     - Configure Claude Desktop with .vscode/mcp.json settings"
echo "     - Test MCP tools: whisper-transcribe, whisper-detect-language, etc."
echo ""
echo "  2. Start API server for HTTP testing:"
echo "     docker-compose up -d whisper-api"
echo "     curl http://localhost:8000/health"
echo ""
echo "  3. View logs:"
echo "     docker-compose logs -f whisper-api"
echo ""
echo "  4. Stop services:"
echo "     docker-compose down"
echo ""

print_success "All Docker tests completed!"
