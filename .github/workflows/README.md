# MCP Servers Unified Workflow

This directory contains the unified GitHub Actions workflow for building and publishing all MCP servers.

## 🚀 Usage

The `mcp-servers.yml` workflow builds different servers based on commit message triggers:

### Single Server Builds
- `@solid` - Build SOLID MCP Server
- `@import-analysis` - Build Import Analysis MCP Server  
- `@whisper-cpu` or `@whisper` - Build Whisper CPU MCP Server
- `@whisper-gpu` - Build Whisper GPU MCP Server (Docker Hub only)

### Batch Builds
- `@all` - Build all servers except GPU version (due to GitHub size limits)

## 📦 Registry Strategy

| Server | Registry | Size | Platform Support |
|--------|----------|------|------------------|
| SOLID MCP | GitHub Container Registry | ~500MB | linux/amd64, linux/arm64 |
| Import Analysis MCP | GitHub Container Registry | ~300MB | linux/amd64, linux/arm64 |
| Whisper CPU MCP | GitHub Container Registry | ~2GB | linux/amd64, linux/arm64 |
| Whisper GPU MCP | Docker Hub | ~8-10GB | linux/amd64 |

## 🔧 Configuration

### Required Secrets
- `GITHUB_TOKEN` - Automatically provided for GitHub Container Registry
- `DOCKERHUB_USERNAME` - Docker Hub username (for GPU builds)
- `DOCKERHUB_TOKEN` - Docker Hub access token (for GPU builds)

### Image Naming Convention
- GitHub Container Registry: `ghcr.io/jfriisj/{server-name}-mcp-server`
- Docker Hub: `jfriisj/{server-name}-mcp-server-gpu`

## 📝 Example Commits

```bash
# Build single server
git commit -m "feat: Update SOLID analyzer @solid"

# Build Whisper CPU version
git commit -m "fix: PyTorch compatibility @whisper"

# Build all compatible servers
git commit -m "feat: Major updates across all servers @all"

# Build GPU version (Docker Hub)
git commit -m "feat: CUDA acceleration improvements @whisper-gpu"
```

## 🏗️ Workflow Features

- **Conditional Builds**: Only triggered by specific commit message patterns
- **Multi-platform Support**: AMD64 and ARM64 for compatible images
- **Build Caching**: GitHub Actions cache for faster subsequent builds
- **Size Monitoring**: Automatic image size reporting
- **Health Checks**: Container validation after build
- **Build Summary**: Comprehensive status report with trigger documentation

## 🎯 Pull Commands

### GitHub Container Registry
```bash
# SOLID MCP Server
docker pull ghcr.io/jfriisj/solid-mcp-server:latest

# Import Analysis MCP Server
docker pull ghcr.io/jfriisj/import-analysis-mcp-server:latest

# Whisper CPU MCP Server
docker pull ghcr.io/jfriisj/whisper-mcp-server-cpu:latest
```

### Docker Hub
```bash
# Whisper GPU MCP Server
docker pull jfriisj/whisper-mcp-server-gpu:latest
```

## 🔍 Benefits

✅ **Unified Management** - Single workflow file for all servers  
✅ **Selective Building** - Build only what you need with targeted triggers  
✅ **Cost Efficient** - Saves GitHub Actions minutes with conditional builds  
✅ **Registry Optimization** - Lightweight images on GitHub, full features on Docker Hub  
✅ **Multi-platform Support** - AMD64 and ARM64 where applicable  
✅ **Comprehensive Reporting** - Detailed build summaries and documentation  

## 🚨 Important Notes

- **GPU builds use Docker Hub** due to GitHub Container Registry size limits (>2GB)
- **`@all` excludes GPU** to prevent GitHub size limit failures
- **Docker Hub credentials required** for `@whisper-gpu` builds
- **Multi-platform builds** automatically enabled for compatible servers

---

**Last Updated:** October 10, 2025
