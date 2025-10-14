#!/bin/bash

# SLR MCP Server Deployment Script
# This script automates the deployment process for the SLR MCP Server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="slr-mcp-server"
DOCKER_IMAGE_NAME="slr-mcp-server"
CONTAINER_NAME="slr-server"
DEFAULT_PORT="8080"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Python is installed (for local development)
    if ! command -v python3 &> /dev/null; then
        log_warn "Python 3 is not installed. This is required for local development."
    fi
    
    log_info "Requirements check completed."
}

create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p data
    mkdir -p logs
    mkdir -p papers
    mkdir -p config
    
    log_info "Directories created successfully."
}

setup_environment() {
    log_info "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        log_info "Creating .env file..."
        cat > .env << EOF
# SLR MCP Server Configuration
DATABASE_PATH=./data/slr_database.db
LOG_LEVEL=INFO
MCP_PORT=${DEFAULT_PORT}
MAX_PAPERS_PER_ANALYSIS=100
ENABLE_CACHING=true
CACHE_SIZE_MB=256
WORKER_PROCESSES=4

# Optional API Keys (uncomment and fill in if needed)
# OPENAI_API_KEY=your_api_key_here
# ANTHROPIC_API_KEY=your_api_key_here
EOF
    else
        log_info ".env file already exists, skipping creation."
    fi
    
    # Set proper permissions
    chmod 600 .env
    
    log_info "Environment setup completed."
}

build_docker_image() {
    log_info "Building Docker image..."
    
    docker build -t ${DOCKER_IMAGE_NAME}:latest .
    
    if [ $? -eq 0 ]; then
        log_info "Docker image built successfully."
    else
        log_error "Failed to build Docker image."
        exit 1
    fi
}

deploy_with_docker() {
    log_info "Deploying with Docker..."
    
    # Stop existing container if running
    if docker ps -q -f name=${CONTAINER_NAME} | grep -q .; then
        log_info "Stopping existing container..."
        docker stop ${CONTAINER_NAME}
        docker rm ${CONTAINER_NAME}
    fi
    
    # Run new container
    docker run -d \
        --name ${CONTAINER_NAME} \
        --env-file .env \
        -p ${DEFAULT_PORT}:8080 \
        -v $(pwd)/data:/app/data \
        -v $(pwd)/logs:/app/logs \
        -v $(pwd)/papers:/app/papers:ro \
        --restart unless-stopped \
        ${DOCKER_IMAGE_NAME}:latest
    
    if [ $? -eq 0 ]; then
        log_info "Container deployed successfully."
    else
        log_error "Failed to deploy container."
        exit 1
    fi
}

deploy_with_compose() {
    log_info "Deploying with Docker Compose..."
    
    # Check if docker-compose.yml exists
    if [ ! -f docker-compose.yml ]; then
        log_error "docker-compose.yml not found."
        exit 1
    fi
    
    # Deploy with compose
    if command -v docker-compose &> /dev/null; then
        docker-compose down
        docker-compose up -d --build
    else
        docker compose down
        docker compose up -d --build
    fi
    
    if [ $? -eq 0 ]; then
        log_info "Services deployed successfully with Docker Compose."
    else
        log_error "Failed to deploy with Docker Compose."
        exit 1
    fi
}

setup_local_development() {
    log_info "Setting up local development environment..."
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_info "Virtual environment created."
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -e ".[dev]"
    
    # Initialize database
    python -c "from src.database.schema import create_tables; create_tables('./data/slr_database.db')"
    
    log_info "Local development environment setup completed."
    log_info "To activate the environment, run: source venv/bin/activate"
    log_info "To start the server locally, run: python -m src.main"
}

health_check() {
    log_info "Performing health check..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:${DEFAULT_PORT}/health &> /dev/null; then
            log_info "Health check passed! Server is running."
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: Server not ready yet, waiting..."
        sleep 2
        ((attempt++))
    done
    
    log_error "Health check failed. Server may not be running properly."
    return 1
}

show_status() {
    log_info "Showing deployment status..."
    
    echo ""
    echo "=== SLR MCP Server Status ==="
    
    # Docker container status
    if docker ps -q -f name=${CONTAINER_NAME} | grep -q .; then
        echo "Docker Container: Running"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" -f name=${CONTAINER_NAME}
    else
        echo "Docker Container: Not running"
    fi
    
    echo ""
    
    # Docker Compose status
    if [ -f docker-compose.yml ]; then
        echo "=== Docker Compose Services ==="
        if command -v docker-compose &> /dev/null; then
            docker-compose ps
        else
            docker compose ps
        fi
    fi
    
    echo ""
    
    # URLs
    echo "=== Access URLs ==="
    echo "Server: http://localhost:${DEFAULT_PORT}"
    echo "Health Check: http://localhost:${DEFAULT_PORT}/health"
    echo ""
}

cleanup() {
    log_info "Cleaning up deployment..."
    
    # Stop and remove containers
    if docker ps -q -f name=${CONTAINER_NAME} | grep -q .; then
        docker stop ${CONTAINER_NAME}
        docker rm ${CONTAINER_NAME}
    fi
    
    # Clean up with compose
    if [ -f docker-compose.yml ]; then
        if command -v docker-compose &> /dev/null; then
            docker-compose down -v
        else
            docker compose down -v
        fi
    fi
    
    # Remove Docker image
    if docker images -q ${DOCKER_IMAGE_NAME} | grep -q .; then
        docker rmi ${DOCKER_IMAGE_NAME}:latest
    fi
    
    log_info "Cleanup completed."
}

show_help() {
    echo "SLR MCP Server Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build          Build Docker image"
    echo "  deploy         Deploy with Docker (default)"
    echo "  compose        Deploy with Docker Compose"
    echo "  local          Setup local development environment"
    echo "  status         Show deployment status"
    echo "  health         Perform health check"
    echo "  cleanup        Clean up deployment"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy      # Deploy with Docker"
    echo "  $0 compose     # Deploy with Docker Compose"
    echo "  $0 local       # Setup for local development"
    echo "  $0 status      # Check deployment status"
}

# Main execution
main() {
    local command=${1:-deploy}
    
    case $command in
        "build")
            check_requirements
            create_directories
            setup_environment
            build_docker_image
            ;;
        "deploy")
            check_requirements
            create_directories
            setup_environment
            build_docker_image
            deploy_with_docker
            health_check
            show_status
            ;;
        "compose")
            check_requirements
            create_directories
            setup_environment
            deploy_with_compose
            health_check
            show_status
            ;;
        "local")
            create_directories
            setup_environment
            setup_local_development
            ;;
        "status")
            show_status
            ;;
        "health")
            health_check
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"