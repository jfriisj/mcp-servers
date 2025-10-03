#!/bin/bash

# Docker entrypoint script for Whisper MCP Server
set -e

# Parse command line arguments
MODE="mcp"  # Default mode
HOST="0.0.0.0"
PORT="8000"

while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            # Pass remaining arguments to main.py
            break
            ;;
    esac
done

echo "🎯 Starting Whisper MCP Server with CUDA support" >&2

# Activate virtual environment
source /opt/venv/bin/activate

# Check if CUDA is available
if python -c "import torch; print('CUDA available:', torch.cuda.is_available())" >/dev/null 2>&1; then
    echo "✅ CUDA is available and ready" >&2
else
    echo "⚠️  CUDA not available, falling back to CPU" >&2
    export USE_GPU=false
fi

# Check Hugging Face token
if [ -z "$HUGGINGFACE_TOKEN" ] && [ -z "$HF_TOKEN" ]; then
    if [ "$TEST_MODE" = "true" ] || [ "$RUN_HTTP_API" = "true" ]; then
        echo "⚠️  Using dummy token for testing - model downloads may fail" >&2
        export HUGGINGFACE_TOKEN="dummy_token_for_testing"
    else
        echo "❌ Error: HUGGINGFACE_TOKEN or HF_TOKEN environment variable must be set" >&2
        echo "Please set your Hugging Face token:" >&2
        echo "export HUGGINGFACE_TOKEN=your_token_here" >&2
        exit 1
    fi
fi

# Create audio directory if it doesn't exist
mkdir -p /app/audio

echo "🔧 Configuration:" >&2
echo "  Mode: $MODE" >&2
echo "  GPU Enabled: $USE_GPU" >&2
echo "  Parallel Processing: ${ENABLE_PARALLEL_PROCESSING:-true}" >&2
echo "  Max Concurrent: ${MAX_CONCURRENT_TRANSCRIPTIONS:-3}" >&2
echo "  Model Cache: ${HF_HOME:-/app/models}" >&2

# Start the server
cd /app/src
echo "Current directory: $(pwd)" >&2
echo "Python path: $(which python)" >&2

# Start MCP server
echo "Running: python main.py --mode $MODE $*" >&2
exec python main.py --mode $MODE "$@"