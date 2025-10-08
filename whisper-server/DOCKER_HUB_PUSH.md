# Pushing Whisper Server to Docker Hub

## 🎉 Image Size Optimization Results

**Before optimization:** 15.3GB  
**After optimization:** 6.18GB  
**Savings:** 9.12GB (60% reduction!)

## Optimization Techniques Applied

1. **Multi-stage build** - Separate builder and runtime stages
2. **Smaller CUDA base** - CUDA 12.1.1 instead of 13.0.1
3. **Ubuntu 22.04** - More stable and smaller than 24.04
4. **Removed build tools** - Only runtime dependencies in final image
5. **No git** - Not needed at runtime
6. **Optimized PyTorch** - Specific version (2.1.0) for CUDA 12.1
7. **Better layer caching** - Improved build times

---

## Prerequisites

1. **Docker Hub Account**
   - Create free account at https://hub.docker.com
   - Free tier supports unlimited public repositories
   - Private repos require Pro ($5/month)

2. **Login to Docker Hub**
   ```bash
   docker login
   # Enter your Docker Hub username and password
   ```

---

## Step 1: Tag Your Image

Replace `yourusername` with your Docker Hub username:

```bash
# Tag with 'latest'
docker tag whisper-server-whisper-api:latest yourusername/whisper-server-gpu:latest

# Tag with version (recommended)
docker tag whisper-server-whisper-api:latest yourusername/whisper-server-gpu:v1.0

# Tag with optimization info
docker tag whisper-server-whisper-api:latest yourusername/whisper-server-gpu:optimized
```

---

## Step 2: Push to Docker Hub

```bash
# Push latest tag
docker push yourusername/whisper-server-gpu:latest

# Push version tag
docker push yourusername/whisper-server-gpu:v1.0

# Push optimized tag
docker push yourusername/whisper-server-gpu:optimized
```

**Note:** Pushing 6.18GB will take some time depending on your upload speed.

---

## Step 3: Verify on Docker Hub

1. Visit https://hub.docker.com/r/yourusername/whisper-server-gpu
2. Check that all tags are visible
3. Update repository description with usage instructions

---

## Usage: Pulling the Image

Others can now pull your image:

```bash
# Pull latest
docker pull yourusername/whisper-server-gpu:latest

# Pull specific version
docker pull yourusername/whisper-server-gpu:v1.0
```

---

## Update docker-compose.yml to Use Docker Hub Image

Instead of building locally, you can use the pushed image:

```yaml
services:
  whisper-api:
    image: yourusername/whisper-server-gpu:latest  # Use pre-built image
    # Remove the 'build:' section
    container_name: whisper-api-server
    environment:
      # ... same environment variables
```

---

## Automated Push Script

Create a script to automate tagging and pushing:

**push-to-dockerhub.sh:**
```bash
#!/bin/bash

# Configuration
DOCKERHUB_USERNAME="yourusername"
IMAGE_NAME="whisper-server-gpu"
LOCAL_IMAGE="whisper-server-whisper-api:latest"
VERSION="1.0"

# Tag images
echo "🏷️  Tagging images..."
docker tag $LOCAL_IMAGE $DOCKERHUB_USERNAME/$IMAGE_NAME:latest
docker tag $LOCAL_IMAGE $DOCKERHUB_USERNAME/$IMAGE_NAME:v$VERSION
docker tag $LOCAL_IMAGE $DOCKERHUB_USERNAME/$IMAGE_NAME:optimized

# Push images
echo "📤 Pushing to Docker Hub..."
docker push $DOCKERHUB_USERNAME/$IMAGE_NAME:latest
docker push $DOCKERHUB_USERNAME/$IMAGE_NAME:v$VERSION
docker push $DOCKERHUB_USERNAME/$IMAGE_NAME:optimized

echo "✅ Successfully pushed to Docker Hub!"
echo "View at: https://hub.docker.com/r/$DOCKERHUB_USERNAME/$IMAGE_NAME"
```

Make it executable:
```bash
chmod +x push-to-dockerhub.sh
./push-to-dockerhub.sh
```

---

## Repository Description Template

When setting up your Docker Hub repository, use this description:

```markdown
# Whisper Server with GPU Support (Optimized)

High-performance audio transcription server using OpenAI Whisper with NVIDIA GPU acceleration.

## Features
- 🚀 Optimized size: 6.18GB (60% smaller than standard builds)
- 🎯 CUDA 12.1 support with cuDNN 8
- 🔊 Multi-format audio support (MP3, WAV, M4A, etc.)
- ⚡ FastAPI HTTP API
- 🔄 Automatic audio segmentation for long files
- 📦 Clean Architecture implementation

## Quick Start
```bash
docker pull yourusername/whisper-server-gpu:latest
docker run --gpus all -p 8000:8000 yourusername/whisper-server-gpu:latest
```

## Requirements
- NVIDIA GPU with CUDA support
- nvidia-docker runtime
- 8GB+ GPU memory recommended

## Source Code
https://github.com/jfriisj/mcp-servers/tree/main/whisper-server
```

---

## GitHub Container Registry Alternative

If you prefer GitHub Container Registry (ghcr.io):

```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Tag for GitHub
docker tag whisper-server-whisper-api:latest ghcr.io/yourusername/whisper-server-gpu:latest

# Push to GitHub
docker push ghcr.io/yourusername/whisper-server-gpu:latest
```

**Note:** GitHub free tier has 500MB limit, so 6.18GB requires a paid plan.

---

## Comparison: Registry Options

| Registry | Free Limit | Your 6.18GB Image | Cost |
|----------|-----------|-------------------|------|
| Docker Hub | ∞ public | ✅ Supported | Free |
| Docker Hub Private | 1 repo | ✅ Supported | $5/month |
| GitHub (ghcr.io) | 500MB | ❌ Too large | Need paid plan |
| AWS ECR | 500GB (1yr) | ✅ Supported | ~$0.60/month after |
| Azure ACR | None free | ✅ Supported | $5/month (Basic) |

**Recommendation:** Use Docker Hub for best value with this image size.

---

## Maintenance

### Rebuilding and Pushing Updates

```bash
# Rebuild with optimizations
docker compose build --no-cache

# Check new size
docker images whisper-server-whisper-api:latest

# Tag and push
docker tag whisper-server-whisper-api:latest yourusername/whisper-server-gpu:latest
docker push yourusername/whisper-server-gpu:latest
```

### Version Tagging Strategy

Use semantic versioning:
- `latest` - Most recent stable build
- `v1.0`, `v1.1`, etc. - Specific versions
- `optimized` - Optimization milestone
- `cuda12.1` - CUDA version specific
- `dev` - Development/testing builds

---

## Troubleshooting

### Push is slow
- Normal for 6.18GB image
- Estimated time: 10-30 minutes depending on upload speed
- Progress shown in terminal

### Authentication failed
```bash
docker logout
docker login
# Re-enter credentials
```

### Layer already exists
- This is good! Docker reuses layers
- Speeds up subsequent pushes

---

## Next Steps

1. ✅ Build optimized image (DONE - 6.18GB)
2. ⏭️ Tag with your Docker Hub username
3. ⏭️ Push to Docker Hub
4. ⏭️ Update README with pull instructions
5. ⏭️ Share with team/community

---

## Support

For issues or questions:
- GitHub: https://github.com/jfriisj/mcp-servers
- Docker Hub: https://hub.docker.com/r/yourusername/whisper-server-gpu
