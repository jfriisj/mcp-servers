# SOLID Principles MCP Server - Docker Guide

This document provides comprehensive instructions for using the SOLID Principles MCP Server with Docker.

## 🚀 Quick Start

### Pull from GitHub Container Registry

```bash
# Pull the latest image
docker pull ghcr.io/jfriisj/solid-mcp-server:latest

# Test with sample code
docker run --rm -v /path/to/your/code:/workspace ghcr.io/jfriisj/solid-mcp-server:latest --test
```

### Build Locally

```bash
# Clone the repository
git clone https://github.com/jfriisj/mcp-servers.git
cd mcp-servers/solid-server

# Build the image
docker build -t solid-mcp-server .

# Test the build
docker run --rm -v $(pwd)/src:/workspace solid-mcp-server --test
```

## 📦 Available Images

| Tag | Description | Platforms |
|-----|-------------|-----------|
| `latest` | Latest stable release | `linux/amd64`, `linux/arm64` |
| `main` | Latest from main branch | `linux/amd64`, `linux/arm64` |
| `develop` | Latest from develop branch | `linux/amd64`, `linux/arm64` |
| `v1.0.0` | Specific version releases | `linux/amd64`, `linux/arm64` |

## 🔧 Usage Modes

### 1. Test Mode (Quick Analysis)

Test your code for SOLID principle violations:

```bash
# Basic test
docker run --rm \
  -v /path/to/your/code:/workspace:ro \
  ghcr.io/jfriisj/solid-mcp-server:latest \
  --test

# Test specific directory structure
docker run --rm \
  -v /path/to/your/src:/workspace/src:ro \
  -v /path/to/your/tests:/workspace/tests:ro \
  ghcr.io/jfriisj/solid-mcp-server:latest \
  --test
```

### 2. MCP Server Mode

Run as an MCP protocol server:

```bash
# Run MCP server with stdio
docker run -i \
  -v /path/to/your/code:/workspace:ro \
  ghcr.io/jfriisj/solid-mcp-server:latest

# Run with custom project root
docker run -i \
  -v /path/to/your/code:/workspace:ro \
  ghcr.io/jfriisj/solid-mcp-server:latest \
  --project-root /workspace
```

### 3. Report Generation

Generate comprehensive SOLID compliance reports:

```bash
# Generate markdown report
docker run --rm \
  -v /path/to/your/code:/workspace:ro \
  -v /path/to/output:/output \
  -e SOLID_FORMAT=markdown \
  ghcr.io/jfriisj/solid-mcp-server:latest \
  --generate-report

# Generate JSON report with severity filter
docker run --rm \
  -v /path/to/your/code:/workspace:ro \
  -v /path/to/output:/output \
  -e SOLID_FORMAT=json \
  -e SOLID_SEVERITY=high \
  ghcr.io/jfriisj/solid-mcp-server:latest \
  --generate-report
```

### 4. Interactive Analysis

Enter the container for interactive analysis:

```bash
# Start interactive session
docker run -it \
  -v /path/to/your/code:/workspace \
  -v /path/to/output:/output \
  ghcr.io/jfriisj/solid-mcp-server:latest \
  bash

# Inside the container, you can run:
# python src/main.py --test --project-root /workspace
# python -c "from src.solid_analyzer import SolidAnalyzer; print('SOLID analysis ready!')"
```

## 🔨 Docker Compose Usage

Use the provided `docker-compose.yml` for common scenarios:

### Development/Testing

```bash
# Test with example violations
docker-compose up solid-dev

# Test your own code
PROJECT_PATH=/path/to/your/code docker-compose up solid-mcp
```

### Report Generation

```bash
# Generate report with custom settings
PROJECT_PATH=/path/to/your/code \
OUTPUT_PATH=/path/to/reports \
REPORT_FORMAT=markdown \
SEVERITY_FILTER=high \
docker-compose up solid-report
```

### Interactive Development

```bash
# Start interactive container
PROJECT_PATH=/path/to/your/code docker-compose run solid-interactive
```

### Using GitHub Registry Image

```bash
# Use pre-built image from GitHub
PROJECT_PATH=/path/to/your/code docker-compose --profile ghcr up solid-ghcr
```

## 🌍 Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `SOLID_PROJECT_ROOT` | Root directory for analysis | `/workspace` | `/workspace/src` |
| `SOLID_OUTPUT_DIR` | Output directory for reports | `/output` | `/reports` |
| `SOLID_FORMAT` | Report format | `markdown` | `json`, `text` |
| `SOLID_SEVERITY` | Filter by severity | `all` | `high`, `medium`, `low` |

### Example with Environment Variables

```bash
docker run --rm \
  -v /path/to/your/code:/workspace:ro \
  -v /path/to/output:/output \
  -e SOLID_PROJECT_ROOT=/workspace/src \
  -e SOLID_OUTPUT_DIR=/output/reports \
  -e SOLID_FORMAT=json \
  -e SOLID_SEVERITY=high \
  ghcr.io/jfriisj/solid-mcp-server:latest \
  --generate-report
```

## 📂 Volume Mounts

### Required Mounts

- **`/workspace`**: Your code directory (read-only recommended)

### Optional Mounts

- **`/output`**: Report output directory (read-write)
- **`/config`**: Custom configuration files (read-only)

### Mount Examples

```bash
# Minimal mount (code only)
-v /path/to/code:/workspace:ro

# With output directory
-v /path/to/code:/workspace:ro \
-v /path/to/reports:/output

# Multi-directory project
-v /path/to/project/src:/workspace/src:ro \
-v /path/to/project/tests:/workspace/tests:ro \
-v /path/to/project/docs:/workspace/docs:ro \
-v /path/to/output:/output
```

## 🔐 Security Features

### Non-Root User

The container runs as a non-root user (`soliduser`) for enhanced security:

```bash
# Container user information
docker run --rm ghcr.io/jfriisj/solid-mcp-server:latest whoami
# Output: soliduser
```

### Read-Only Mounts

Recommend mounting code directories as read-only:

```bash
# Read-only mount prevents accidental file modifications
-v /path/to/code:/workspace:ro
```

### Security Scanning

All published images are scanned for vulnerabilities using Trivy.

## 📊 Performance Optimization

### Multi-Platform Support

Images support both AMD64 and ARM64 architectures:

```bash
# Automatically pulls the correct architecture
docker pull ghcr.io/jfriisj/solid-mcp-server:latest
```

### Build Cache

For local builds, leverage Docker BuildKit cache:

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Build with cache
docker build \
  --cache-from ghcr.io/jfriisj/solid-mcp-server:latest \
  -t solid-mcp-server .
```

### Resource Limits

Set appropriate resource limits for large codebases:

```bash
# Limit memory and CPU
docker run --rm \
  --memory=2g \
  --cpus=2 \
  -v /path/to/large/codebase:/workspace:ro \
  ghcr.io/jfriisj/solid-mcp-server:latest \
  --test
```

## 🔍 Troubleshooting

### Common Issues

#### 1. No Python Files Found

```bash
# Error: No Python files found
# Solution: Check mount path and directory structure
docker run --rm -v $(pwd):/workspace ghcr.io/jfriisj/solid-mcp-server:latest ls -la /workspace
```

#### 2. Permission Denied

```bash
# Error: Permission denied on output directory
# Solution: Ensure output directory is writable
chmod 755 /path/to/output
```

#### 3. Container Won't Start

```bash
# Debug container startup
docker run --rm --entrypoint bash ghcr.io/jfriisj/solid-mcp-server:latest -c "ls -la /app"
```

### Debug Mode

```bash
# Run with debug output
docker run --rm \
  -v /path/to/code:/workspace:ro \
  ghcr.io/jfriisj/solid-mcp-server:latest \
  --help

# Check container health
docker run --rm ghcr.io/jfriisj/solid-mcp-server:latest --test --project-root /app/src
```

### Log Analysis

```bash
# View container logs
docker logs <container_id>

# Follow logs in real-time
docker logs -f <container_id>
```

## 📈 Integration Examples

### CI/CD Pipeline (GitHub Actions)

```yaml
- name: SOLID Analysis
  run: |
    docker run --rm \
      -v ${{ github.workspace }}:/workspace:ro \
      -v $PWD/reports:/output \
      ghcr.io/jfriisj/solid-mcp-server:latest \
      --generate-report

- name: Upload Reports
  uses: actions/upload-artifact@v3
  with:
    name: solid-reports
    path: reports/
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('SOLID Analysis') {
            steps {
                script {
                    docker.image('ghcr.io/jfriisj/solid-mcp-server:latest').inside(
                        '-v ${WORKSPACE}:/workspace:ro -v ${WORKSPACE}/reports:/output'
                    ) {
                        sh 'python src/main.py --generate-report --project-root /workspace'
                    }
                }
            }
        }
    }
}
```

### GitLab CI

```yaml
solid_analysis:
  image: ghcr.io/jfriisj/solid-mcp-server:latest
  script:
    - python src/main.py --test --project-root $CI_PROJECT_DIR
  artifacts:
    reports:
      junit: reports/solid-report.xml
```

## 📋 Health Checks

The container includes built-in health checks:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' <container_id>

# Manual health check
docker exec <container_id> python src/main.py --test --project-root /app/src
```

## 🔄 Updates and Maintenance

### Updating the Image

```bash
# Pull latest version
docker pull ghcr.io/jfriisj/solid-mcp-server:latest

# Remove old images
docker image prune
```

### Version Pinning

```bash
# Pin to specific version for reproducible builds
docker pull ghcr.io/jfriisj/solid-mcp-server:v1.0.0
```

## 📞 Support

For Docker-specific issues:

1. Check the [troubleshooting section](#-troubleshooting)
2. Review the [GitHub Issues](https://github.com/jfriisj/mcp-servers/issues)
3. Create a new issue with:
   - Docker version: `docker --version`
   - Image version: `docker inspect ghcr.io/jfriisj/solid-mcp-server:latest`
   - Error logs: `docker logs <container_id>`
   - System info: OS, architecture, available resources

---

**Ready to containerize your SOLID analysis? Start with `docker pull ghcr.io/jfriisj/solid-mcp-server:latest`!**