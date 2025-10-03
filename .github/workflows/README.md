# GitHub Actions Workflows

This directory contains GitHub Actions workflows for building and publishing Docker images.

## Docker SOLID Server Workflow

**File:** `docker-solid-server.yml`

### Trigger

This workflow builds and publishes the SOLID MCP Server Docker image **only when** the commit message contains `@build`.

### Usage

To trigger a Docker build, include `@build` in your commit message:

```bash
# This will trigger the Docker build
git commit -m "Update SOLID server @build"
git push

# This will NOT trigger the build
git commit -m "Update SOLID server documentation"
git push

# You can combine with other text
git commit -m "Fix bug in analyzer @build - rebuild container"
git push
```

### Manual Trigger

You can also manually trigger the workflow from the GitHub Actions tab using the "Run workflow" button.

### What It Does

When triggered (commit message contains `@build`):

1. **Checks out the repository**
2. **Sets up Docker Buildx** for multi-platform builds
3. **Logs in to GitHub Container Registry** (ghcr.io)
4. **Extracts metadata** for tagging (branch name, commit SHA, latest)
5. **Builds and pushes** the Docker image for:
   - `linux/amd64` (Intel/AMD 64-bit)
   - `linux/arm64` (ARM 64-bit, e.g., Apple Silicon, Raspberry Pi)
6. **Uses GitHub Actions cache** to speed up subsequent builds

### Tags Generated

The workflow creates the following tags:

- `main` - Current main branch build
- `develop` - Current develop branch build
- `main-<sha>` or `develop-<sha>` - Build from specific commit
- `latest` - Only on main branch (default branch)

### Example Docker Pull Commands

```bash
# Pull latest version (from main branch)
docker pull ghcr.io/jfriisj/solid-mcp-server:latest

# Pull specific branch
docker pull ghcr.io/jfriisj/solid-mcp-server:main
docker pull ghcr.io/jfriisj/solid-mcp-server:develop

# Pull specific commit
docker pull ghcr.io/jfriisj/solid-mcp-server:main-abc1234
```

## Benefits of This Approach

✅ **Faster CI/CD** - Only builds when you explicitly request it with `@build`  
✅ **Cost Efficient** - Saves GitHub Actions minutes by not building on every push  
✅ **Explicit Control** - You decide when to rebuild the container  
✅ **Simple** - No complex conditions, just add `@build` to your commit message  
✅ **Multi-platform** - Automatically builds for both Intel/AMD and ARM architectures  

## Tips

- Use `@build` when you've made changes to:
  - Dockerfile
  - requirements.txt
  - Source code that affects Docker image
  - Dependencies or configuration

- Don't use `@build` for:
  - Documentation updates
  - README changes
  - Minor code tweaks that don't need immediate Docker rebuild
  - Work in progress commits

## Troubleshooting

### Build Failed

Check the Actions tab on GitHub to see the error logs. Common issues:

- Docker build errors (check Dockerfile syntax)
- Missing dependencies in requirements.txt
- Python errors in the source code

### Image Not Found

Make sure:
- The workflow completed successfully
- You're pulling from the correct registry: `ghcr.io/jfriisj/solid-mcp-server`
- You have the correct permissions if the package is private

### Authentication Error

If pulling private images, authenticate with:

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

## Future Workflows

You can create similar workflows for other servers (e.g., whisper-server) using the same pattern:

1. Copy `docker-solid-server.yml`
2. Update the `IMAGE_NAME` environment variable
3. Update the `context` and `file` paths in the build step
4. Use `@build-whisper` or similar in commit messages to differentiate

---

**Last Updated:** October 3, 2025
