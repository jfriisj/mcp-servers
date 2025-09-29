#!/bin/bash

# Docker entrypoint script for Whisper MCP Server
set -e

echo "🚀 Starting Whisper MCP Server with CUDA support"

# Activate virtual environment
source /opt/venv/bin/activate

# Check if CUDA is available
if python -c "import torch; print('CUDA available:', torch.cuda.is_available())" 2>/dev/null; then
    echo "✅ CUDA is available and ready"
else
    echo "⚠️  CUDA not available, falling back to CPU"
    export USE_GPU=false
fi

# Check Hugging Face token
if [ -z "$HUGGINGFACE_TOKEN" ] && [ -z "$HF_TOKEN" ]; then
    if [ "$TEST_MODE" = "true" ] || [ "$RUN_HTTP_API" = "true" ]; then
        echo "⚠️  Using dummy token for testing - model downloads may fail"
        export HUGGINGFACE_TOKEN="dummy_token_for_testing"
    else
        echo "❌ Error: HUGGINGFACE_TOKEN or HF_TOKEN environment variable must be set"
        echo "Please set your Hugging Face token:"
        echo "export HUGGINGFACE_TOKEN=your_token_here"
        exit 1
    fi
fi

# Create audio directory if it doesn't exist
mkdir -p /app/audio

echo "🔧 Configuration:"
echo "  GPU Enabled: $USE_GPU"
echo "  Parallel Processing: ${ENABLE_PARALLEL_PROCESSING:-true}"
echo "  Max Concurrent: ${MAX_CONCURRENT_TRANSCRIPTIONS:-3}"
echo "  Model Cache: ${HF_HOME:-/app/models}"

# Start the MCP server
echo "🎯 Starting MCP server..."
cd /app/src
echo "Current directory: $(pwd)"
echo "Python path: $(which python)"
echo "Files in /app/src:"
ls -la
echo "Running: python main.py"
echo "Starting python main.py now..."
exec python main.py