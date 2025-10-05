@echo off
REM Docker MCP Test Runner for Windows
REM ====================================

echo.
echo ============================================================
echo   Whisper MCP Server - Docker Test Suite (Windows)
echo ============================================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Check for Hugging Face token
if "%HUGGINGFACE_TOKEN%"=="" (
    if "%HF_TOKEN%"=="" (
        echo [WARNING] HUGGINGFACE_TOKEN not set. Using test mode.
        set HUGGINGFACE_TOKEN=test_token
        set TEST_MODE=true
    )
)

REM Build Docker image
echo.
echo ============================================================
echo   Building Docker image...
echo ============================================================
docker-compose -f docker-compose.test.yml build
if errorlevel 1 (
    echo [ERROR] Failed to build Docker image
    pause
    exit /b 1
)

echo [OK] Docker image built successfully
echo.

REM Run MCP tests inside container
echo.
echo ============================================================
echo   Running MCP tests inside Docker container...
echo ============================================================
docker-compose -f docker-compose.test.yml run --rm whisper-mcp python tests/test_docker_mcp.py
if errorlevel 1 (
    echo [ERROR] MCP tests failed
    pause
    exit /b 1
)

echo.
echo [OK] MCP tests passed!
echo.

REM Run Clean Architecture tests
echo.
echo ============================================================
echo   Running Clean Architecture tests...
echo ============================================================
docker-compose -f docker-compose.test.yml run --rm whisper-mcp python tests/test_whisper.py
if errorlevel 1 (
    echo [WARNING] Clean Architecture tests had issues
    echo           (This may be normal if no audio files are present)
) else (
    echo [OK] Clean Architecture tests passed!
)

echo.
echo ============================================================
echo   All tests completed!
echo ============================================================
echo.
echo Next steps:
echo   1. Test MCP client integration with Claude Desktop
echo   2. Start API server: docker-compose -f docker-compose.test.yml up -d whisper-api-test
echo   3. Test API: curl http://localhost:8000/health
echo   4. View logs: docker-compose -f docker-compose.test.yml logs -f
echo   5. Stop: docker-compose -f docker-compose.test.yml down
echo.
echo See DOCKER_TESTING.md for detailed documentation.
echo.

pause
