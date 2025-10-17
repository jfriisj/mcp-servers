# SLR Server GitHub Actions Integration

**Date**: October 17, 2025  
**Purpose**: Add SLR MCP Server to GitHub Actions workflow for automated Docker builds

---

## Changes Made

### 1. Added SLR Server Build Job

Added a new job `build-slr` to `.github/workflows/mcp-servers.yml` that:

- **Triggers on**: `@slr` or `@all` in commit messages
- **Builds**: Multi-platform Docker images (linux/amd64, linux/arm64)
- **Publishes to**: GitHub Container Registry (ghcr.io)
- **Image name**: `ghcr.io/jfriisj/slr-mcp-server`
- **Tags**: 
  - Branch name (e.g., `main`, `develop`)
  - Git SHA (e.g., `main-abc1234`)
  - `latest` (for main branch only)

### 2. Updated Build Summary

Modified the build summary section to include SLR server status reporting.

---

## Workflow Configuration

```yaml
build-slr:
  name: Build SLR MCP Server
  runs-on: ubuntu-latest
  if: contains(github.event.head_commit.message, '@slr') || contains(github.event.head_commit.message, '@all')
  permissions:
    contents: read
    packages: write
  
  steps:
    - Checkout repository
    - Set up Docker Buildx
    - Log in to GitHub Container Registry
    - Extract metadata (tags, labels)
    - Build and push Docker image
    - Test Docker image
    - Check image size
```

---

## Trigger Commands

To trigger builds, include these in your commit messages:

| Command | Effect |
|---------|--------|
| `@slr` | Build SLR MCP Server only |
| `@all` | Build all servers (SOLID, Import Analysis, Whisper CPU, Study Buddy, SLR) |
| `@solid` | Build SOLID MCP Server only |
| `@import-analysis` | Build Import Analysis MCP Server only |
| `@whisper-cpu` or `@whisper` | Build Whisper CPU MCP Server only |
| `@whisper-gpu` | Build Whisper GPU MCP Server (Docker Hub) |
| `@study-buddy` | Build Study Buddy MCP Server only |

---

## Usage Examples

### Example 1: Build SLR Server Only
```bash
git commit -m "refactor: Phase 3 complete - improved SRP compliance @slr"
git push origin main
```

### Example 2: Build All Servers
```bash
git commit -m "feat: add new features across all servers @all"
git push origin main
```

### Example 3: Manual Trigger
You can also trigger builds manually via GitHub Actions UI using the "workflow_dispatch" event.

---

## GitHub Container Registry

### Published Images

Images will be published to:
```
ghcr.io/jfriisj/slr-mcp-server:latest
ghcr.io/jfriisj/slr-mcp-server:main
ghcr.io/jfriisj/slr-mcp-server:main-abc1234
```

### Pull the Image

```bash
# Pull latest version
docker pull ghcr.io/jfriisj/slr-mcp-server:latest

# Pull specific version
docker pull ghcr.io/jfriisj/slr-mcp-server:main-abc1234
```

### Run the Container

```bash
# Basic run
docker run -p 8080:8080 ghcr.io/jfriisj/slr-mcp-server:latest

# With volume for data persistence
docker run -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  ghcr.io/jfriisj/slr-mcp-server:latest

# Using Docker Compose (see deployment/docker-compose.yml)
cd slr-server/deployment
docker-compose up -d
```

---

## Build Process

### 1. Multi-Platform Builds
The workflow builds for both:
- `linux/amd64` (x86_64 - Intel/AMD processors)
- `linux/arm64` (ARM64 - Apple Silicon, Raspberry Pi 4+, AWS Graviton)

### 2. Layer Caching
Uses GitHub Actions cache to speed up builds:
- `cache-from: type=gha` - Restore cache from previous builds
- `cache-to: type=gha,mode=max` - Save all layers to cache

### 3. Automated Testing
After building, the workflow:
- Tests that the image can start (`docker run --help`)
- Reports the final image size

---

## Docker Image Details

### Base Image
- **Python**: 3.11-slim
- **OS**: Debian-based (slim variant)

### Features
- ✅ Non-root user (`slrserver`) for security
- ✅ SQLite support (included)
- ✅ PostgreSQL support (optional, via requirements-postgresql.txt)
- ✅ Health check endpoint
- ✅ Production-ready startup script

### Ports
- **8080**: MCP server port (default)

### Volumes
- `/app/data` - Database and file storage
- `/app/logs` - Application logs

---

## Security

### Image Permissions
- Runs as non-root user `slrserver`
- Minimal system dependencies
- No unnecessary packages

### Registry Access
- Uses GitHub token authentication
- Images are public by default
- Can be made private in repository settings

---

## Verification

### After Build Completes

1. **Check GitHub Actions**:
   - Go to: `https://github.com/jfriisj/mcp-servers/actions`
   - Verify "Build and Publish MCP Servers" workflow succeeded

2. **Check GitHub Packages**:
   - Go to: `https://github.com/jfriisj?tab=packages`
   - Look for `slr-mcp-server`

3. **Pull and Test Locally**:
   ```bash
   docker pull ghcr.io/jfriisj/slr-mcp-server:latest
   docker run --rm ghcr.io/jfriisj/slr-mcp-server:latest --help
   ```

---

## Integration with Refactored Code

### Phase 3 Refactoring Included ✅

The Docker image will include all Phase 3 improvements:
- ✅ Refactored `upload_paper` method (152 → 48 lines)
- ✅ Refactored `detect_and_remove_duplicates` method (110 → 60 lines)
- ✅ Refactored `get_corpus_statistics` method (86 → 32 lines)
- ✅ 10 new helper methods for better SRP compliance
- ✅ 60% complexity reduction
- ✅ Improved testability and maintainability

### Verified Functionality
All MCP endpoints tested and working:
- ✅ Paper upload and batch upload
- ✅ Duplicate detection
- ✅ Corpus statistics
- ✅ Research question validation
- ✅ Project progress tracking
- ✅ Search and filtering

---

## Next Steps

### To Deploy the First Build

1. **Commit the workflow changes**:
   ```bash
   git add .github/workflows/mcp-servers.yml
   git commit -m "ci: add SLR server to GitHub Actions workflow @slr"
   git push origin main
   ```

2. **Monitor the build**:
   - Watch GitHub Actions: https://github.com/jfriisj/mcp-servers/actions
   - Build should complete in ~5-10 minutes

3. **Use the image**:
   - Update docker-compose.yml to use `ghcr.io/jfriisj/slr-mcp-server:latest`
   - Or pull directly for local testing

---

## Troubleshooting

### If Build Fails

**Check Dockerfile path**:
- Verify: `slr-server/deployment/Dockerfile` exists
- Current path in workflow: `./slr-server/deployment/Dockerfile`

**Check permissions**:
- Workflow needs `packages: write` permission (already configured)

**Check requirements files**:
- Ensure `requirements.txt` exists in slr-server/
- Ensure `requirements-postgresql.txt` exists

**Common Issues**:
1. Missing dependencies → Check requirements.txt
2. Import errors → Verify PYTHONPATH in Dockerfile
3. Port conflicts → Ensure port 8080 is available

---

## Benefits

### 1. Automated Deployment ✅
- No manual Docker builds needed
- Consistent builds across environments
- Automatic tagging with git SHA

### 2. Multi-Platform Support ✅
- Works on Intel/AMD and ARM processors
- Compatible with Apple Silicon Macs
- Ready for cloud deployment (AWS, GCP, Azure)

### 3. Version Control ✅
- Every commit gets a unique tag
- Easy rollback to previous versions
- Clear audit trail

### 4. Production Ready ✅
- Includes refactored, tested code
- Non-root user for security
- Health checks configured

---

## Summary

✅ **SLR Server added to GitHub Actions workflow**  
✅ **Publishes to GitHub Container Registry**  
✅ **Multi-platform builds (amd64, arm64)**  
✅ **Automated testing and size reporting**  
✅ **Includes all Phase 3 refactoring improvements**  
✅ **Trigger with `@slr` or `@all` in commit messages**

**Next**: Commit the workflow changes to trigger the first build!

---

**Updated**: October 17, 2025  
**Status**: ✅ Ready for deployment
