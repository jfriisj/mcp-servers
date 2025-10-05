# Docker MCP Testing Guide

This guide explains how to test the Whisper MCP Server running in Docker with the Clean Architecture implementation.

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose installed
- (Optional) NVIDIA GPU with Docker GPU support for CUDA acceleration
- Hugging Face token (for model downloads)

### 2. Set Environment Variables

```bash
# Set your Hugging Face token
export HUGGINGFACE_TOKEN=your_token_here

# Optional: Enable GPU (if you have NVIDIA GPU)
export USE_GPU=true
```

### 3. Run Automated Tests

```bash
# Make the test script executable (Linux/Mac)
chmod +x test-docker.sh

# Run the test suite
./test-docker.sh
```

Or on Windows (Git Bash):
```bash
bash test-docker.sh
```

## Manual Testing

### Test 1: Build Docker Image

```bash
docker-compose -f docker-compose.test.yml build
```

### Test 2: Run MCP Tests Inside Container

```bash
docker-compose -f docker-compose.test.yml run --rm whisper-mcp python tests/test_docker_mcp.py
```

Expected output:
```
🧪 Test 1: MCP Server Initialization
============================================================
✅ MCP Server initialized successfully
   - CompositionRoot: OK
   - MCPHandler: OK
   - Server instance: WhisperMCPServer

🧪 Test 2: MCP Tools Listing
============================================================
✅ Found 9 MCP tools:
   ✅ whisper-transcribe
   ✅ whisper-transcribe-timestamps
   ✅ whisper-transcribe-file-content
   ✅ whisper-detect-language
   ✅ whisper-batch-transcribe
   ✅ whisper-convert-audio
   ✅ whisper-model-info
   ✅ whisper-get-config
   ✅ whisper-audio-info

... (more tests)

📊 TEST SUMMARY
============================================================
   ✅ PASS: initialization
   ✅ PASS: tools_listing
   ✅ PASS: tool_schemas
   ✅ PASS: model_info
   ✅ PASS: config_tool
   ✅ PASS: conversion_schema
   ✅ PASS: docker_env
   ✅ PASS: composition_root

============================================================
Results: 8/8 tests passed
🎉 ALL TESTS PASSED!
✅ MCP server is ready for Docker deployment
```

### Test 3: Run Clean Architecture Tests

```bash
docker-compose -f docker-compose.test.yml run --rm whisper-mcp python tests/test_whisper.py
```

### Test 4: Start MCP Server (stdio mode)

```bash
docker-compose -f docker-compose.test.yml run --rm whisper-mcp --mode mcp
```

This starts the MCP server in stdio mode, ready to receive MCP protocol messages via stdin/stdout.

### Test 5: Start API Server (HTTP mode)

```bash
# Start in detached mode
docker-compose -f docker-compose.test.yml up -d whisper-api-test

# Test the health endpoint
curl http://localhost:8000/health

# View logs
docker-compose -f docker-compose.test.yml logs -f whisper-api-test

# Stop the server
docker-compose -f docker-compose.test.yml down
```

## MCP Client Integration Testing

### Configure Claude Desktop

Update your Claude Desktop MCP configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "whisper-docker": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e", "HUGGINGFACE_TOKEN=your_token_here",
        "whisper-mcp-test",
        "--mode", "mcp"
      ]
    }
  }
}
```

Or use docker-compose:

```json
{
  "mcpServers": {
    "whisper-docker": {
      "command": "docker-compose",
      "args": [
        "-f", "/path/to/whisper-server/docker-compose.test.yml",
        "run",
        "--rm",
        "whisper-mcp",
        "--mode", "mcp"
      ],
      "env": {
        "HUGGINGFACE_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Test MCP Tools in Claude

Once configured, you can test MCP tools in Claude Desktop:

1. **Get model information:**
   ```
   Use the whisper-model-info tool to show me the current model details
   ```

2. **Get configuration:**
   ```
   Use whisper-get-config to show me the server configuration
   ```

3. **Transcribe audio (if you have audio files mounted):**
   ```
   Use whisper-transcribe to transcribe the file audio/test.wav in English
   ```

## Troubleshooting

### Issue: "HUGGINGFACE_TOKEN not set"

**Solution:** Export your token before running tests:
```bash
export HUGGINGFACE_TOKEN=hf_your_token_here
```

Or create a `.env` file in the whisper-server directory:
```
HUGGINGFACE_TOKEN=hf_your_token_here
```

### Issue: "CUDA not available"

**Solution 1:** Run in CPU mode:
```bash
export USE_GPU=false
docker-compose -f docker-compose.test.yml run --rm whisper-mcp python tests/test_docker_mcp.py
```

**Solution 2:** Install NVIDIA Docker support:
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker)
- Uncomment GPU sections in `docker-compose.test.yml`

### Issue: "Cannot find module 'presentation.composition_root'"

**Solution:** This means the Clean Architecture refactoring is not in your src directory. Make sure you have:
- `src/domain/`
- `src/application/`
- `src/infrastructure/`
- `src/presentation/`

### Issue: Tests timeout or hang

**Solution:** The model download can be slow on first run. Options:
1. Use a persistent volume for model cache (already configured)
2. Pre-download models outside Docker
3. Use a smaller model for testing (edit config)

## Test Coverage

The `test_docker_mcp.py` script tests:

| Test | Description | What it Checks |
|------|-------------|----------------|
| 1. Server Initialization | MCP server starts | CompositionRoot, MCPHandler created |
| 2. Tools Listing | Tools are registered | All 9 MCP tools available |
| 3. Tool Schemas | Schemas are valid | Input schemas have correct structure |
| 4. Model Info Tool | Tool execution | whisper-model-info returns data |
| 5. Config Tool | Tool execution | whisper-get-config returns config |
| 6. Conversion Schema | Schema validation | Audio conversion params defined |
| 7. Docker Environment | Env vars set | CUDA, tokens, paths configured |
| 8. CompositionRoot | Clean Architecture | All use cases and adapters work |

## Architecture Verification

The tests verify the Clean Architecture implementation:

```
Docker Container
├── Domain Layer (interfaces.py, models.py)
├── Infrastructure Layer (adapters/)
├── Application Layer (use_cases/)
├── Presentation Layer (composition_root.py)
└── Entry Points
    ├── MCP Server (server.py, mcp_handler.py)
    └── FastAPI (api.py)
```

All tests use CompositionRoot for dependency injection, ensuring the Clean Architecture pattern is maintained in Docker.

## Performance Testing

To test performance with actual audio files:

1. Place audio files in `audio/` directory
2. Run batch transcription test:

```bash
docker-compose -f docker-compose.test.yml run --rm whisper-mcp python -c "
from presentation.composition_root import CompositionRoot
from domain.models import BatchTranscriptionConfig
import asyncio

async def test():
    root = CompositionRoot()
    config = BatchTranscriptionConfig(
        audio_files=['audio/file1.wav', 'audio/file2.wav'],
        language='en',
        response_format='json',
        temperature=0.0
    )
    result = await root.batch_transcribe.execute(config)
    print(f'Processed {result.successful_transcriptions}/{result.total_files} files')

asyncio.run(test())
"
```

## Continuous Integration

For CI/CD pipelines, use the test script:

```yaml
# Example GitHub Actions
- name: Test Whisper MCP in Docker
  run: |
    export HUGGINGFACE_TOKEN=${{ secrets.HF_TOKEN }}
    export USE_GPU=false
    bash test-docker.sh
```

## Next Steps

1. ✅ Run automated tests with `./test-docker.sh`
2. ✅ Verify all 8 tests pass
3. ✅ Configure MCP client (Claude Desktop)
4. ✅ Test MCP tools via client
5. ✅ Deploy to production

For production deployment, see `DOCKER.md` in the main directory.
