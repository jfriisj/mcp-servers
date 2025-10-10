#!/bin/bash
# Docker entrypoint script for Whisper MCP Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎤 Starting Whisper MCP Server...${NC}"

# Function to print usage
usage() {
    echo -e "${YELLOW}Whisper MCP Server Docker Container${NC}"
    echo ""
    echo "Usage modes:"
    echo "  1. MCP Server mode (default):"
    echo "     docker run -v /path/to/audio:/workspace ghcr.io/jfriisj/whisper-mcp-server-cpu"
    echo ""
    echo "  2. FastAPI mode:"
    echo "     docker run -p 8000:8000 -v /path/to/audio:/workspace \\"
    echo "       ghcr.io/jfriisj/whisper-mcp-server-cpu --mode api"
    echo ""
    echo "  3. Interactive shell:"
    echo "     docker run -it -v /path/to/audio:/workspace \\"
    echo "       ghcr.io/jfriisj/whisper-mcp-server-cpu bash"
    echo ""
    echo "Options:"
    echo "  --mode MODE          Server mode: 'mcp' (default) or 'api'"
    echo "  --host HOST          FastAPI host (default: 0.0.0.0)"
    echo "  --port PORT          FastAPI port (default: 8000)"
    echo "  --root-folder PATH   Project root directory (default: /workspace)"
    echo "  --help              Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  USE_GPU             Enable GPU acceleration (true/false)"
    echo "  HF_HOME            Hugging Face model cache directory"
    echo "  TRANSFORMERS_CACHE  Transformers model cache directory"
    echo "  MAX_CONCURRENT_TRANSCRIPTIONS  Maximum parallel transcriptions"
    echo "  ENABLE_PARALLEL_PROCESSING     Enable parallel processing"
}

# Function to check GPU availability
check_gpu() {
    if [ "${USE_GPU:-false}" = "true" ]; then
        if command -v nvidia-smi &> /dev/null; then
            echo -e "${GREEN}🚀 GPU detected:${NC}"
            nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader,nounits | head -1
            export TORCH_DEVICE="cuda"
        else
            echo -e "${YELLOW}⚠️  GPU requested but nvidia-smi not found, falling back to CPU${NC}"
            export TORCH_DEVICE="cpu"
            export USE_GPU="false"
        fi
    else
        echo -e "${BLUE}💻 Using CPU-only mode${NC}"
        export TORCH_DEVICE="cpu"
    fi
}

# Function to check audio directory
check_audio_dir() {
    local dir="$1"
    
    if [ ! -d "$dir" ]; then
        echo -e "${RED}❌ Error: Audio directory '$dir' does not exist${NC}"
        echo -e "${YELLOW}💡 Make sure to mount your audio directory to /workspace:${NC}"
        echo -e "   docker run -v /path/to/your/audio:/workspace ghcr.io/jfriisj/whisper-mcp-server-cpu"
        exit 1
    fi
    
    # Check if there are any audio files
    audio_count=$(find "$dir" -type f \( -name "*.mp3" -o -name "*.wav" -o -name "*.m4a" -o -name "*.flac" -o -name "*.ogg" -o -name "*.mp4" -o -name "*.mov" -o -name "*.avi" \) 2>/dev/null | wc -l)
    
    if [ "$audio_count" -eq 0 ]; then
        echo -e "${YELLOW}⚠️  Warning: No audio/video files found in '$dir'${NC}"
        echo -e "${BLUE}ℹ️  The server will still start and can process files uploaded via API${NC}"
    else
        echo -e "${GREEN}✅ Found $audio_count audio/video files to process${NC}"
    fi
}

# Function to validate model cache
setup_model_cache() {
    local cache_dir="${HF_HOME:-/app/models}"
    
    echo -e "${BLUE}📦 Setting up model cache at: $cache_dir${NC}"
    mkdir -p "$cache_dir"
    
    # Check if Whisper model is already cached
    if [ -d "$cache_dir/models--openai--whisper-base" ] || [ -d "$cache_dir/whisper-base" ]; then
        echo -e "${GREEN}✅ Whisper model found in cache${NC}"
    else
        echo -e "${YELLOW}📥 Whisper model will be downloaded on first use${NC}"
        echo -e "${BLUE}ℹ️  This may take a few minutes for the first transcription${NC}"
    fi
}

# Function to test server health
test_health() {
    echo -e "${BLUE}🏥 Testing server health...${NC}"
    python -c "
import sys
sys.path.append('/app/src')
try:
    from presentation.mcp.server import WhisperMCPServer
    print('✅ MCP server imports successful')
except Exception as e:
    print(f'❌ MCP server import failed: {e}')
    sys.exit(1)
" || exit 1
}

# Parse command line arguments
PYTHON_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            usage
            exit 0
            ;;
        --test-health)
            test_health
            exit 0
            ;;
        bash|sh|/bin/bash|/bin/sh)
            echo -e "${BLUE}🐚 Starting interactive shell...${NC}"
            exec "$@"
            ;;
        *)
            # Pass through all arguments to the Python script
            PYTHON_ARGS+=("$1")
            shift
            ;;
    esac
done

# Set default workspace if not specified in args
WORKSPACE_DIR="/workspace"
for ((i=0; i<${#PYTHON_ARGS[@]}; i++)); do
    if [[ "${PYTHON_ARGS[i]}" == "--root-folder" ]] && [[ $((i+1)) -lt ${#PYTHON_ARGS[@]} ]]; then
        WORKSPACE_DIR="${PYTHON_ARGS[i+1]}"
        break
    fi
done

# If no --root-folder specified, add it
if [[ ! " ${PYTHON_ARGS[*]} " =~ " --root-folder " ]]; then
    PYTHON_ARGS+=("--root-folder" "$WORKSPACE_DIR")
fi

# System checks
check_gpu
setup_model_cache
check_audio_dir "$WORKSPACE_DIR"

# Display container information
echo -e "${BLUE}📦 Container Information:${NC}"
echo -e "   Workspace: $WORKSPACE_DIR"
echo -e "   Model Cache: ${HF_HOME:-/app/models}"
echo -e "   GPU Enabled: ${USE_GPU:-false}"
echo -e "   Device: ${TORCH_DEVICE:-cpu}"
echo -e "   Python Version: $(python --version)"
echo -e "   PyTorch Version: $(python -c 'import torch; print(torch.__version__)' 2>/dev/null || echo 'Not available')"
if [ "${USE_GPU:-false}" = "true" ]; then
    echo -e "   CUDA Available: $(python -c 'import torch; print(torch.cuda.is_available())' 2>/dev/null || echo 'Not available')"
fi
echo ""

# Start the server
echo -e "${GREEN}🎯 Starting Whisper server with arguments: ${PYTHON_ARGS[*]}${NC}"
echo -e "${BLUE}ℹ️  The server is now ready to receive requests${NC}"

# Change to src directory and run the server
cd /app/src
exec python main.py "${PYTHON_ARGS[@]}"