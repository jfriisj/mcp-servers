# MCP Servers

A collection of Model Context Protocol (MCP) servers providing specialized development tools through standardized AI assistant integration.

## 🚀 Overview

This repository contains two specialized MCP servers:

- **SOLID Server** - SOLID principles analysis and code quality assessment for Python
- **Whisper Server** - Audio transcription using local Hugging Face Whisper Large V3 model

These servers enable AI assistants to perform code quality analysis and audio transcription through the MCP protocol.

## 📦 Servers

### ⚖️ SOLID Server

**Location:** `solid-server/`

Provides comprehensive SOLID principles analysis for Python code, helping developers write more maintainable, testable, and flexible software.

**Features:**
- **Complete SOLID Analysis** - Checks all five principles: SRP, OCP, LSP, ISP, DIP
- **AST-based Analysis** - Uses Python's Abstract Syntax Tree for accurate parsing
- **Severity Classification** - High, medium, and low priority violations
- **Educational Content** - Detailed explanations with examples and best practices
- **Batch Processing** - Analyze entire directories and generate reports
- **Multiple Output Formats** - Text, JSON, and Markdown reports
- **Code Quality Scoring** - 0-100 compliance scores with improvement tracking

**Key Tools:**
- `solid-check-file` - Analyze single Python file for SOLID violations
- `solid-check-directory` - Batch analyze directory of Python files  
- `solid-generate-report` - Create comprehensive SOLID compliance reports
- `solid-explain-principle` - Get detailed explanations of SOLID principles
- `solid-check-score` - Get compliance scores for files or directories
- `solid-list-violations` - List violations with filtering options

### 🎙️ Whisper Server

**Location:** `whisper-server/`

Provides audio transcription capabilities using the local Hugging Face Whisper Large V3 model for converting speech to text.

**Features:**

- **Local Whisper Large V3 Model**: Run transcription locally without API calls
- **High-accuracy transcription** using OpenAI's Whisper Large V3 model
- **Multiple audio formats** support (MP3, WAV, M4A, FLAC, etc.)
- **Timestamp extraction** with detailed segment information
- **Language detection** and multi-language support
- **Batch processing** for multiple audio files
- **GPU acceleration** support (optional)
- **Configurable output formats** (text, JSON, SRT, VTT)

**Key Tools:**

- `whisper-transcribe` - Transcribe audio file to text
- `whisper-transcribe-timestamps` - Transcribe with timestamps
- `whisper-detect-language` - Detect audio language
- `whisper-batch-transcribe` - Batch transcribe multiple files

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- MCP-compatible client (VS Code with MCP extension, Claude Desktop, etc.)

### Quick Start

1. **Clone the repository:**

   ```bash
   git clone https://github.com/jfriisj/mcp-servers.git
   cd mcp-servers
   ```

2. **Install individual servers:**

   ```bash
   # SOLID Server
   cd solid-server
   pip install -r requirements.txt

   # Whisper Server
   cd ../whisper-server
   pip install -r requirements.txt
   # Set HUGGINGFACE_TOKEN environment variable or update .env file
   ```

3. **Configure MCP client** (example for VS Code `.vscode/mcp.json`):

   ```json
   {
     "servers": {
       "solid": {
         "command": "python",
         "args": ["${workspaceFolder}/mcp-servers/solid-server/src/main.py", "--project-root", "${workspaceFolder}"],
         "cwd": "${workspaceFolder}"
       },
       "whisper": {
         "command": "python",
         "args": ["${workspaceFolder}/mcp-servers/whisper-server/src/main.py"],
         "cwd": "${workspaceFolder}",
         "env": {
           "HUGGINGFACE_TOKEN": "your-huggingface-token-here"
         }
       }
     }
   }
   ```

## ⚙️ Configuration

### SOLID Server

The SOLID server analyzes Python code using AST parsing. No additional configuration is required, but you can customize analysis by filtering principles or severity levels when calling tools.

### Whisper Server

Requires Hugging Face authentication token set as environment variable:

```bash
export HUGGINGFACE_TOKEN="your-huggingface-token-here"
```

Or create a `.env` file in the whisper-server directory:

```bash
HUGGINGFACE_TOKEN=your_actual_huggingface_token_here
USE_GPU=true  # Optional: enable GPU acceleration
```

Supported audio formats: MP3, WAV, M4A, FLAC, OGG, WEBM
Maximum file size: 100MB (local processing allows larger files than API limits)

## 📖 Usage Examples

### Analyzing Python Code for SOLID Principles

```python
# Analyze a single file
await call_tool("solid-check-file", {
    "file_path": "src/main.py",
    "principles": ["SRP", "DIP"]
})

# Analyze entire directory
await call_tool("solid-check-directory", {
    "directory_path": "src/",
    "max_files": 50
})

# Generate comprehensive report
await call_tool("solid-generate-report", {
    "directory_path": "src/",
    "output_format": "markdown",
    "include_suggestions": True
})

# Get principle explanation
await call_tool("solid-explain-principle", {
    "principle": "SRP"
})
```

### Audio Transcription

```python
# Transcribe audio file
await call_tool("whisper-transcribe", {
    "audio_file": "recording.mp3",
    "language": "en",
    "response_format": "json"
})

# Transcribe with timestamps
await call_tool("whisper-transcribe-timestamps", {
    "audio_file": "interview.wav"
})

# Detect language
await call_tool("whisper-detect-language", {
    "audio_file": "unknown_language.mp3"
})

# Batch transcribe
await call_tool("whisper-batch-transcribe", {
    "audio_files": ["file1.mp3", "file2.wav", "file3.m4a"]
})
```

## 🔗 Integration

### VS Code

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "solid": {
      "command": "python",
      "args": [
        "solid-server/src/main.py",
        "--project-root",
        "${workspaceFolder}"
      ],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    "whisper": {
      "command": "python",
      "args": [
        "whisper-server/src/main.py"
      ],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "HUGGINGFACE_TOKEN": "your-huggingface-token-here"
      }
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "solid": {
      "command": "python",
      "args": ["path/to/solid-server/src/main.py", "--project-root", "path/to/project"]
    },
    "whisper": {
      "command": "python",
      "args": ["path/to/whisper-server/src/main.py"],
      "env": {
        "HUGGINGFACE_TOKEN": "your-huggingface-token-here"
      }
    }
  }
}
```

## 🏗️ Development

### Running Individual Servers

```bash
# SOLID Server
cd solid-server/src
python main.py --project-root /path/to/project

# SOLID Server (test mode)
python main.py --test

# Whisper Server
cd whisper-server/src
python main.py
```

### Testing

Each server includes test mode for development:

```bash
# Test SOLID server
python solid-server/src/main.py --test

# Test MCP protocol
python test_solid_mcp_protocol.py

# Test Whisper server
python whisper-server/tests/test_whisper.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

### Development Guidelines

- Follow existing code patterns and structure
- Include comprehensive documentation
- Add unit tests for new functionality
- Update README files for any changes
- Test with multiple MCP clients

## 📋 Requirements

### SOLID Server Dependencies

- Python 3.8+
- mcp>=0.1.0
- pydantic>=2.0.0

### Whisper Server Dependencies

- Python 3.8+
- mcp>=0.1.0
- transformers>=4.35.0
- torch>=2.0.0
- torchaudio>=2.0.0
- datasets>=2.14.0
- accelerate>=0.24.0
- python-dotenv>=1.0.0

## 📄 License

This project is open source. See individual server directories for specific licensing information.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for the standardized AI assistant integration
- [Ruff](https://github.com/astral-sh/ruff) for inspiring fast, modern Python tooling
- [OpenAI Whisper](https://github.com/openai/whisper) for the Whisper model
- [Hugging Face](https://huggingface.co/) for the Transformers library and model hosting

---

**Note:** These servers are designed to work with MCP-compatible clients. Ensure your development environment supports the Model Context Protocol for full functionality.
