# SLR MCP Server Deployment Script for Windows
# This script automates the deployment process for the SLR MCP Server on Windows

param(
    [Parameter(Position=0)]
    [string]$Command = "deploy"
)

# Configuration
$ProjectName = "slr-mcp-server"
$DockerImageName = "slr-mcp-server"
$ContainerName = "slr-server"
$DefaultPort = "8080"

# Functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Test-Requirements {
    Write-Info "Checking requirements..."
    
    # Check if Docker is installed
    try {
        docker --version | Out-Null
    }
    catch {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }
    
    # Check if Docker Compose is available
    try {
        docker-compose --version | Out-Null
    }
    catch {
        try {
            docker compose version | Out-Null
        }
        catch {
            Write-Error "Docker Compose is not available. Please ensure Docker Desktop is properly installed."
            exit 1
        }
    }
    
    # Check if Python is installed (for local development)
    try {
        python --version | Out-Null
    }
    catch {
        Write-Warn "Python is not installed. This is required for local development."
    }
    
    Write-Info "Requirements check completed."
}

function New-Directories {
    Write-Info "Creating necessary directories..."
    
    $directories = @("data", "logs", "papers", "config")
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir | Out-Null
        }
    }
    
    Write-Info "Directories created successfully."
}

function Initialize-Environment {
    Write-Info "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if (-not (Test-Path ".env")) {
        Write-Info "Creating .env file..."
        
        $envContent = @"
# SLR MCP Server Configuration
DATABASE_PATH=./data/slr_database.db
LOG_LEVEL=INFO
MCP_PORT=$DefaultPort
MAX_PAPERS_PER_ANALYSIS=100
ENABLE_CACHING=true
CACHE_SIZE_MB=256
WORKER_PROCESSES=4

# Optional API Keys (uncomment and fill in if needed)
# OPENAI_API_KEY=your_api_key_here
# ANTHROPIC_API_KEY=your_api_key_here
"@
        
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
    }
    else {
        Write-Info ".env file already exists, skipping creation."
    }
    
    Write-Info "Environment setup completed."
}

function Build-DockerImage {
    Write-Info "Building Docker image..."
    
    docker build -t "${DockerImageName}:latest" .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Info "Docker image built successfully."
    }
    else {
        Write-Error "Failed to build Docker image."
        exit 1
    }
}

function Deploy-WithDocker {
    Write-Info "Deploying with Docker..."
    
    # Stop existing container if running
    $existingContainer = docker ps -q -f name=$ContainerName
    if ($existingContainer) {
        Write-Info "Stopping existing container..."
        docker stop $ContainerName
        docker rm $ContainerName
    }
    
    # Run new container
    docker run -d `
        --name $ContainerName `
        --env-file .env `
        -p "${DefaultPort}:8080" `
        -v "${PWD}/data:/app/data" `
        -v "${PWD}/logs:/app/logs" `
        -v "${PWD}/papers:/app/papers:ro" `
        --restart unless-stopped `
        "${DockerImageName}:latest"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Info "Container deployed successfully."
    }
    else {
        Write-Error "Failed to deploy container."
        exit 1
    }
}

function Deploy-WithCompose {
    Write-Info "Deploying with Docker Compose..."
    
    # Check if docker-compose.yml exists
    if (-not (Test-Path "docker-compose.yml")) {
        Write-Error "docker-compose.yml not found."
        exit 1
    }
    
    # Deploy with compose
    try {
        docker-compose down
        docker-compose up -d --build
    }
    catch {
        docker compose down
        docker compose up -d --build
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Info "Services deployed successfully with Docker Compose."
    }
    else {
        Write-Error "Failed to deploy with Docker Compose."
        exit 1
    }
}

function Initialize-LocalDevelopment {
    Write-Info "Setting up local development environment..."
    
    # Create virtual environment
    if (-not (Test-Path "venv")) {
        python -m venv venv
        Write-Info "Virtual environment created."
    }
    
    # Activate virtual environment and install dependencies
    & "venv\Scripts\Activate.ps1"
    pip install --upgrade pip
    pip install -e ".[dev]"
    
    # Initialize database
    python -c "from src.database.schema import create_tables; create_tables('./data/slr_database.db')"
    
    Write-Info "Local development environment setup completed."
    Write-Info "To activate the environment, run: venv\Scripts\Activate.ps1"
    Write-Info "To start the server locally, run: python -m src.main"
}

function Test-Health {
    Write-Info "Performing health check..."
    
    $maxAttempts = 30
    $attempt = 1
    
    while ($attempt -le $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$DefaultPort/health" -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Info "Health check passed! Server is running."
                return $true
            }
        }
        catch {
            # Continue to next attempt
        }
        
        Write-Info "Attempt $attempt/$maxAttempts`: Server not ready yet, waiting..."
        Start-Sleep -Seconds 2
        $attempt++
    }
    
    Write-Error "Health check failed. Server may not be running properly."
    return $false
}

function Show-Status {
    Write-Info "Showing deployment status..."
    
    Write-Host ""
    Write-Host "=== SLR MCP Server Status ===" -ForegroundColor Cyan
    
    # Docker container status
    $containerStatus = docker ps -q -f name=$ContainerName
    if ($containerStatus) {
        Write-Host "Docker Container: Running" -ForegroundColor Green
        docker ps --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}" -f name=$ContainerName
    }
    else {
        Write-Host "Docker Container: Not running" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # Docker Compose status
    if (Test-Path "docker-compose.yml") {
        Write-Host "=== Docker Compose Services ===" -ForegroundColor Cyan
        try {
            docker-compose ps
        }
        catch {
            docker compose ps
        }
    }
    
    Write-Host ""
    
    # URLs
    Write-Host "=== Access URLs ===" -ForegroundColor Cyan
    Write-Host "Server: http://localhost:$DefaultPort"
    Write-Host "Health Check: http://localhost:$DefaultPort/health"
    Write-Host ""
}

function Remove-Deployment {
    Write-Info "Cleaning up deployment..."
    
    # Stop and remove containers
    $containerStatus = docker ps -q -f name=$ContainerName
    if ($containerStatus) {
        docker stop $ContainerName
        docker rm $ContainerName
    }
    
    # Clean up with compose
    if (Test-Path "docker-compose.yml") {
        try {
            docker-compose down -v
        }
        catch {
            docker compose down -v
        }
    }
    
    # Remove Docker image
    $imageId = docker images -q $DockerImageName
    if ($imageId) {
        docker rmi "${DockerImageName}:latest"
    }
    
    Write-Info "Cleanup completed."
}

function Show-Help {
    Write-Host "SLR MCP Server Deployment Script for Windows" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\deploy.ps1 [COMMAND]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  build          Build Docker image"
    Write-Host "  deploy         Deploy with Docker (default)"
    Write-Host "  compose        Deploy with Docker Compose"
    Write-Host "  local          Setup local development environment"
    Write-Host "  status         Show deployment status"
    Write-Host "  health         Perform health check"
    Write-Host "  cleanup        Clean up deployment"
    Write-Host "  help           Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\deploy.ps1 deploy      # Deploy with Docker"
    Write-Host "  .\deploy.ps1 compose     # Deploy with Docker Compose"
    Write-Host "  .\deploy.ps1 local       # Setup for local development"
    Write-Host "  .\deploy.ps1 status      # Check deployment status"
}

# Main execution
switch ($Command.ToLower()) {
    "build" {
        Test-Requirements
        New-Directories
        Initialize-Environment
        Build-DockerImage
    }
    "deploy" {
        Test-Requirements
        New-Directories
        Initialize-Environment
        Build-DockerImage
        Deploy-WithDocker
        Test-Health
        Show-Status
    }
    "compose" {
        Test-Requirements
        New-Directories
        Initialize-Environment
        Deploy-WithCompose
        Test-Health
        Show-Status
    }
    "local" {
        New-Directories
        Initialize-Environment
        Initialize-LocalDevelopment
    }
    "status" {
        Show-Status
    }
    "health" {
        Test-Health
    }
    "cleanup" {
        Remove-Deployment
    }
    { $_ -in @("help", "-h", "--help") } {
        Show-Help
    }
    default {
        Write-Error "Unknown command: $Command"
        Show-Help
        exit 1
    }
}