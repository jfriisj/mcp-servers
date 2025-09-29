# Whisper MCP Server

An MCP server that provides audio transcription capabilities using the local Hugging Face Whisper Large V3 model with Docker and CUDA support for parallel processing.

## Features

- **Local Whisper Large V3 Model**: Run transcription locally without API calls
- **High-accuracy transcription** using OpenAI's Whisper Large V3 model
- **Multiple audio formats** support (MP3, WAV, M4A, FLAC, etc.)
- **Timestamp extraction** with detailed segment information
- **Language detection** and multi-language support
- **Batch processing** for multiple audio files
- **Parallel processing** with configurable concurrency
- **GPU acceleration** support with CUDA
- **Docker containerization** for easy deployment
- **Configurable output formats**
- **Direct file content transcription** - Agents can upload audio files directly as base64 content

## Quick Start with Docker

### Prerequisites

- Docker and Docker Compose
- NVIDIA GPU with CUDA support (optional but recommended)
- Hugging Face account with access token

### 1. Clone and Setup

```bash
git clone <repository-url>
cd whisper-server
```

### 2. Configure Environment

Create a `.env` file with your Hugging Face token:

```bash
HUGGINGFACE_TOKEN=your_actual_huggingface_token_here
```

### 3. Build and Run with Docker Compose

```bash
# Build and start the container
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 4. Place Audio Files

Put your audio files in the `audio/` directory (mounted as volume):

```bash
mkdir audio
cp your_audio_file.mp3 audio/
```

## Docker Configuration

### Environment Variables

- `HUGGINGFACE_TOKEN`: Your Hugging Face authentication token (required)
- `HF_TOKEN`: Alternative token variable name
- `USE_GPU`: Set to "true" to enable GPU acceleration (default: true)
- `ENABLE_PARALLEL_PROCESSING`: Enable parallel batch processing (default: true)
- `MAX_CONCURRENT_TRANSCRIPTIONS`: Max concurrent transcriptions (default: 3)
- `HF_HOME`: Custom cache directory for models (default: /app/models)

### GPU Support

For GPU acceleration, ensure you have:

1. NVIDIA Docker runtime installed
2. Uncomment the GPU configuration in `docker-compose.yml`:

```yaml
services:
  whisper-server:
    # ...
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    runtime: nvidia
```

## Manual Docker Usage

### Build the Image

```bash
docker build -t whisper-mcp-server .
```

### Run the Container

```bash
# With GPU support
docker run --gpus all \
  -e HUGGINGFACE_TOKEN=your_token \
  -v $(pwd)/audio:/app/audio:ro \
  -v whisper_models:/app/models \
  whisper-mcp-server

# CPU only
docker run \
  -e HUGGINGFACE_TOKEN=your_token \
  -e USE_GPU=false \
  -v $(pwd)/audio:/app/audio:ro \
  -v whisper_models:/app/models \
  whisper-mcp-server
```

## Installation

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set up Hugging Face authentication:
   - Get your token from: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
   - Update the `.env` file with your token:

     ```bash
     HUGGINGFACE_TOKEN=your_actual_huggingface_token_here
     ```

3. Optional: Enable GPU acceleration (if you have CUDA):

   ```bash
   # In .env file
   USE_GPU=true
   ```

## Configuration

The server supports the following audio formats:

- MP3, MP4, MPEG, MPGA, M4A, WAV, WEBM, FLAC, OGG

Maximum file size: 200MB (increased for large interview files)

### Parallel Processing Configuration

- `ENABLE_PARALLEL_PROCESSING`: Enable parallel batch processing (default: true)
- `MAX_CONCURRENT_TRANSCRIPTIONS`: Max concurrent transcriptions (default: 3)

### Model Configuration

- `WHISPER_MODEL`: Whisper model to use (default: "openai/whisper-large-v3")
- `HF_HOME`: Custom cache directory for models (optional)

## Tools

### `whisper-transcribe`

Transcribe an audio file to text.

**Parameters:**

- `audio_file` (required): Path to the audio file
- `language`: Language code (optional)
- `response_format`: Output format (default: "json")
- `temperature`: Sampling temperature (default: 0.0)
- `prompt`: Optional text prompt to guide transcription

### `whisper-transcribe-timestamps`

Transcribe audio with detailed timestamps and segments.

**Parameters:**

- `audio_file` (required): Path to the audio file
- `language`: Language code (optional)
- `temperature`: Sampling temperature (default: 0.0)
- `prompt`: Optional text prompt

### `whisper-detect-language`

Detect the primary language spoken in an audio file.

**Parameters:**

- `audio_file` (required): Path to the audio file

### `whisper-batch-transcribe`

Transcribe multiple audio files in a single operation.

**Parameters:**

- `audio_files` (required): Array of audio file paths
- `language`: Language code (optional)
- `response_format`: Output format (default: "json")
- `temperature`: Sampling temperature (default: 0.0)

## Usage

### VS Code Integration

Add to your `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "whisper": {
      "command": "python",
      "args": ["-m", "whisper-server.src.main"],
      "env": {
        "HUGGINGFACE_TOKEN": "your-huggingface-token-here"
      }
    }
  }
}
```

### Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "whisper": {
      "command": "python",
      "args": ["-m", "whisper-server.src.main"],
      "env": {
        "HUGGINGFACE_TOKEN": "your-huggingface-token-here"
      }
    }
  }
}
```

## Development

The server includes fallback implementations for development when the MCP package is not installed. All functionality is preserved through compatible interfaces.

### Running the Server

```bash
cd whisper-server/src
python main.py
```

### Testing

The server can be tested by calling the tools through the MCP protocol or by using the fallback mode for direct testing.

## Error Handling

The server provides clear error messages with emoji prefixes:

- ✅ Success operations
- ❌ Failed operations with detailed error messages

Common errors:

- Missing or invalid Hugging Face token
- Unsupported audio file formats
- Files exceeding size limits
- Model download or loading failures
- GPU/CUDA configuration issues

## License

This project follows the same license as the main mcp-servers repository.
