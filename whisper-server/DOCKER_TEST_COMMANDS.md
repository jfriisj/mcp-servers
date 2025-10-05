# Docker MCP Testing - Quick Reference

## Quick Test Commands

### Windows
```cmd
test-docker.bat
```

### Linux/Mac/Git Bash
```bash
bash test-docker.sh
```

## Individual Test Commands

### 1. Build Docker Image
```bash
docker-compose -f docker-compose.test.yml build
```

### 2. Run MCP Tests
```bash
docker-compose -f docker-compose.test.yml run --rm whisper-mcp python tests/test_docker_mcp.py
```

### 3. Run Clean Architecture Tests
```bash
docker-compose -f docker-compose.test.yml run --rm whisper-mcp python tests/test_whisper.py
```

### 4. Start MCP Server (Interactive)
```bash
docker-compose -f docker-compose.test.yml run --rm whisper-mcp --mode mcp
```

### 5. Start API Server
```bash
# Start
docker-compose -f docker-compose.test.yml up -d whisper-api-test

# Test
curl http://localhost:8000/health

# Logs
docker-compose -f docker-compose.test.yml logs -f whisper-api-test

# Stop
docker-compose -f docker-compose.test.yml down
```

### 6. Test Specific MCP Tool
```bash
docker-compose -f docker-compose.test.yml run --rm whisper-mcp python -c "
import asyncio
from server import WhisperMCPServer

async def test():
    server = WhisperMCPServer()
    result = await server.mcp_handler.call_tool('whisper-model-info', {})
    print(result[0].text)

asyncio.run(test())
"
```

### 7. Test CompositionRoot
```bash
docker-compose -f docker-compose.test.yml run --rm whisper-mcp python -c "
from presentation.composition_root import CompositionRoot
root = CompositionRoot()
print('âœ… All use cases available:', hasattr(root, 'transcribe_audio'))
print('âœ… All adapters available:', root.get_whisper_model() is not None)
"
```

### 8. Shell Access for Debugging
```bash
docker-compose -f docker-compose.test.yml run --rm --entrypoint bash whisper-mcp
```

## Environment Variables

Set before running tests:

```bash
# Required for model downloads
export HUGGINGFACE_TOKEN=hf_your_token_here

# Optional GPU settings
export USE_GPU=true
export CUDA_VISIBLE_DEVICES=0

# Optional test mode (skips model downloads)
export TEST_MODE=true
```

## Expected Output

### Successful MCP Test Output:
```
í·ª Test 1: MCP Server Initialization
============================================================
âœ… MCP Server initialized successfully
   - CompositionRoot: OK
   - MCPHandler: OK

í·ª Test 2: MCP Tools Listing
============================================================
âœ… Found 9 MCP tools:
   âœ… whisper-transcribe
   âœ… whisper-transcribe-timestamps
   âœ… whisper-transcribe-file-content
   âœ… whisper-detect-language
   âœ… whisper-batch-transcribe
   âœ… whisper-convert-audio
   âœ… whisper-model-info
   âœ… whisper-get-config
   âœ… whisper-audio-info

í³Š TEST SUMMARY
============================================================
Results: 8/8 tests passed
í¾‰ ALL TESTS PASSED!
```

## Troubleshooting

| Issue | Command to Diagnose |
|-------|---------------------|
| Build fails | `docker-compose -f docker-compose.test.yml build --no-cache` |
| Python errors | `docker-compose -f docker-compose.test.yml run --rm whisper-mcp python --version` |
| Import errors | `docker-compose -f docker-compose.test.yml run --rm whisper-mcp ls -la src/` |
| CUDA issues | `docker-compose -f docker-compose.test.yml run --rm whisper-mcp python -c "import torch; print(torch.cuda.is_available())"` |
| MCP config | `docker-compose -f docker-compose.test.yml run --rm whisper-mcp python -c "from server import WhisperMCPServer; s=WhisperMCPServer(); print('OK')"` |

## Files Created for Testing

- `tests/test_docker_mcp.py` - Comprehensive MCP tests
- `docker-compose.test.yml` - Test-specific Docker Compose config
- `test-docker.sh` - Linux/Mac test runner
- `test-docker.bat` - Windows test runner
- `DOCKER_TESTING.md` - Detailed testing guide
- `DOCKER_TEST_COMMANDS.md` - This quick reference

## Test Coverage

âœ… MCP server initialization  
âœ… CompositionRoot dependency injection  
âœ… All 9 MCP tools available  
âœ… Tool schemas validation  
âœ… Model info tool execution  
âœ… Config tool execution  
âœ… Docker environment variables  
âœ… Clean Architecture components  

See `DOCKER_TESTING.md` for complete documentation.
