"""
MCP protocol handling for Whisper Server
========================================
Manages MCP tool definitions and protocol interactions.

Refactored to use Clean Architecture with CompositionRoot.
"""

from typing import Any, Dict, List

from mcp import types

# Domain models
from domain.models import (
    TranscriptionConfig,
    LanguageDetectionConfig,
    BatchTranscriptionConfig,
    ConversionConfig,
)

# Presentation layer
from presentation.composition_root import CompositionRoot

# MCP imports (these would be installed as dependencies)
try:
    from mcp import types

    HAS_MCP = True
except ImportError:
    HAS_MCP = False

    # Fallback for development without MCP
    class types:
        @staticmethod
        def Tool(**kwargs):
            return kwargs

        @staticmethod
        def TextContent(**kwargs):
            return kwargs


class MCPHandler:
    """Handles MCP protocol interactions and tool definitions."""

    def __init__(self, composition_root: CompositionRoot):
        """Initialize MCP handler with composition root.
        
        Args:
            composition_root: Dependency injection container with use cases
        """
        self._root = composition_root

    def get_tools(self) -> List[types.Tool]:
        """Get list of available Whisper tools."""
        return self._load_tools_from_yaml()

    def _load_tools_from_yaml(self) -> List[types.Tool]:
        """Load tool definitions from YAML file"""
        try:
            import yaml
        except ImportError:
            # Fallback to hardcoded tools if YAML not available
            return self._get_fallback_tools()

        # Find the tools directory relative to this module
        try:
            from pathlib import Path

            module_dir = Path(__file__).parent
            tools_dir = module_dir.parent / "tools"
            yaml_file = tools_dir / "tools_schemas.yaml"
        except Exception:
            # Fallback if path resolution fails
            return self._get_fallback_tools()

        if not yaml_file.exists():
            # Fallback to hardcoded tools if YAML file doesn't exist
            return self._get_fallback_tools()

        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    return self._get_fallback_tools()

                tools = []
                for tool_data in data.values():
                    try:
                        tool = types.Tool(
                            name=tool_data["name"],
                            description=tool_data["description"],
                            inputSchema=tool_data["inputSchema"],
                        )
                        tools.append(tool)
                    except KeyError:
                        continue

                return tools if tools else self._get_fallback_tools()
        except Exception:
            return self._get_fallback_tools()

    def _get_fallback_tools(self) -> List[types.Tool]:
        """Fallback hardcoded tool definitions"""
        return [
            types.Tool(
                name="whisper-transcribe",
                description="Transcribe audio file to text using OpenAI Whisper",
                inputSchema=self._get_transcribe_schema(),
            ),
            types.Tool(
                name="whisper-transcribe-timestamps",
                description="Transcribe audio with timestamps and segments",
                inputSchema=self._get_transcribe_timestamps_schema(),
            ),
            types.Tool(
                name="whisper-detect-language",
                description="Detect the language of an audio file",
                inputSchema=self._get_detect_language_schema(),
            ),
            types.Tool(
                name="whisper-batch-transcribe",
                description="Transcribe multiple audio files in batch",
                inputSchema=self._get_batch_transcribe_schema(),
            ),
            types.Tool(
                name="whisper-transcribe-file-content",
                description="Transcribe uploaded audio file content (base64) to text",
                inputSchema=self._get_transcribe_file_content_schema(),
            ),
            types.Tool(
                name="whisper-convert-audio",
                description="Convert audio/video file to Whisper-compatible format",
                inputSchema=self._get_convert_audio_schema(),
            ),
            types.Tool(
                name="whisper-model-info",
                description="Get information about the loaded Whisper model",
                inputSchema=self._get_model_info_schema(),
            ),
            types.Tool(
                name="whisper-audio-info",
                description="Get detailed information about an audio file",
                inputSchema=self._get_audio_info_schema(),
            ),
            types.Tool(
                name="whisper-get-config",
                description="Get current Whisper server configuration",
                inputSchema=self._get_config_schema(),
            ),
        ]

    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> List[types.TextContent]:
        """Handle tool calls."""
        try:
            if name == "whisper-transcribe":
                return await self._handle_transcribe(arguments)
            elif name == "whisper-transcribe-timestamps":
                return await self._handle_transcribe_timestamps(arguments)
            elif name == "whisper-detect-language":
                return await self._handle_detect_language(arguments)
            elif name == "whisper-batch-transcribe":
                return await self._handle_batch_transcribe(arguments)
            elif name == "whisper-transcribe-file-content":
                return await self._handle_transcribe_file_content(arguments)
            elif name == "whisper-convert-audio":
                return await self._handle_convert_audio(arguments)
            elif name == "whisper-model-info":
                return await self._handle_model_info(arguments)
            elif name == "whisper-audio-info":
                return await self._handle_audio_info(arguments)
            elif name == "whisper-get-config":
                return await self._handle_get_config(arguments)
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error executing tool {name}: {str(e)}",
                ),
            ]

    async def _handle_transcribe(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle whisper-transcribe tool call using Clean Architecture."""
        try:
            # Create transcription config from arguments
            config = TranscriptionConfig(
                audio_file=args["audio_file"],
                language=args.get("language"),
                response_format=args.get("response_format", "json"),
                temperature=args.get("temperature", 0.0),
                prompt=args.get("prompt"),
            )
            
            # Execute use case
            result = await self._root.transcribe_audio.execute(config)
            
            if result.success:
                return [
                    types.TextContent(
                        type="text",
                        text=(
                            f"✅ Transcription completed successfully!\n\n"
                            f"**Text:** {result.text}\n"
                            f"**Language:** {result.language or 'N/A'}"
                        ),
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"❌ {result.error_message}",
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Transcription failed: {str(e)}",
                )
            ]

    async def _handle_transcribe_timestamps(
        self,
        args: Dict[str, Any],
    ) -> List[types.TextContent]:
        """Handle whisper-transcribe-timestamps tool call."""
        try:
            # Create transcription config
            config = TranscriptionConfig(
                audio_file=args["audio_file"],
                language=args.get("language"),
                response_format="verbose_json",
                temperature=args.get("temperature", 0.0),
                prompt=args.get("prompt"),
            )
            
            # Execute use case
            result = await self._root.transcribe_with_timestamps.execute(
                config
            )
            
            if result.success:
                segments_count = len(result.segments) if result.segments else 0
                return [
                    types.TextContent(
                        type="text",
                        text=(
                            "✅ Transcription with timestamps completed!\n\n"
                            f"**Text:** {result.text}\n"
                            f"**Language:** {result.language or 'N/A'}\n"
                            f"**Duration:** {result.duration or 'N/A'}s\n"
                            f"**Segments:** {segments_count}"
                        ),
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"❌ {result.error_message}",
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=(
                        f"❌ Transcription with timestamps failed: {str(e)}"
                    ),
                )
            ]

    async def _handle_detect_language(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle whisper-detect-language tool call."""
        try:
            # Create language detection config
            config = LanguageDetectionConfig(
                audio_file=args["audio_file"],
            )
            
            # Execute use case
            result = await self._root.detect_language.execute(config)
            
            if result.success:
                return [
                    types.TextContent(
                        type="text",
                        text=(
                            "✅ Language detection completed!\n\n"
                            f"**Detected:** {result.detected_language}\n"
                            f"**Confidence:** {result.confidence:.2f}"
                        ),
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"❌ {result.error_message}",
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Language detection failed: {str(e)}",
                )
            ]

    async def _handle_batch_transcribe(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle whisper-batch-transcribe tool call."""
        try:
            # Create batch transcription config
            config = BatchTranscriptionConfig(
                audio_files=args["audio_files"],
                language=args.get("language"),
                response_format=args.get("response_format", "json"),
                temperature=args.get("temperature", 0.0),
            )
            
            # Execute use case
            result = await self._root.batch_transcribe.execute(config)
            
            return [self._format_batch_result(result)]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Batch transcription failed: {str(e)}",
                )
            ]

    async def _handle_transcribe_file_content(
        self,
        args: Dict[str, Any],
    ) -> List[types.TextContent]:
        """Handle whisper-transcribe-file-content tool call."""
        try:
            # Execute use case directly with file content
            result = await self._root.transcribe_file_content.execute(
                file_content=args["file_content"],
                file_name=args.get("file_name"),
                file_format=args.get("file_format"),
                language=args.get("language"),
                response_format=args.get("response_format", "json"),
                temperature=args.get("temperature", 0.0),
                prompt=args.get("prompt"),
            )
            
            return [
                self._format_transcription_result(
                    "Transcription from file content", result
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=(
                        f"❌ File content transcription failed: {str(e)}"
                    ),
                )
            ]

    async def _handle_convert_audio(
        self,
        args: Dict[str, Any],
    ) -> List[types.TextContent]:
        """Handle whisper-convert-audio tool call."""
        try:
            config = ConversionConfig(
                input_file=args["input_file"],
                output_format=args.get("output_format", "wav"),
                quality=args.get("quality", "high"),
                output_file=args.get("output_file")
            )
            
            result = await self._root.convert_audio.execute(config)

            if result.success:
                return [
                    types.TextContent(
                        type="text",
                        text=(
                            "✅ Audio conversion completed successfully!\n\n"
                            f"**Output File:** {result.output_file}\n"
                            f"**Format:** {result.converted_format}\n"
                            f"**Duration:** {result.duration}s\n"
                        ),
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"❌ Audio conversion failed: "
                        f"{result.error_message}",
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Audio conversion failed: {str(e)}",
                )
            ]

    def _format_transcription_result(
        self, operation: str, result
    ) -> types.TextContent:
        """Format transcription result for MCP response."""
        if result.success:
            response = f"✅ {operation} completed successfully!\n\n"
            response += f"**Text:** {result.text}\n"

            if result.language:
                response += f"**Language:** {result.language}\n"

            if hasattr(result, "duration") and result.duration:
                response += f"**Duration:** {result.duration:.2f} seconds\n"

            if hasattr(result, "segments") and result.segments:
                response += (
                    f"**Segments:** {len(result.segments)} "
                    "segments available\n"
                )

            return types.TextContent(type="text", text=response)
        else:
            return types.TextContent(
                type="text",
                text=f"❌ {operation} failed: {result.error_message}",
            )

    def _format_language_detection_result(
        self, result: Any
    ) -> types.TextContent:
        """Format language detection result for MCP response."""
        if result.success:
            response = "✅ Language detection completed successfully!\n\n"
            response += f"**Detected Language:** {result.detected_language}\n"
            response += f"**Confidence:** {result.confidence:.2f}\n"

            return types.TextContent(type="text", text=response)
        else:
            return types.TextContent(
                type="text",
                text=f"❌ Language detection failed: {result.error_message}",
            )

    def _format_batch_result(
        self, result: Any
    ) -> Any:
        """Format batch transcription result for MCP response."""
        if result.success:
            response = "✅ Batch transcription completed successfully!\n\n"
            response += f"**Total files:** {result.total_files}\n"
            response += f"**Successful:** {result.successful_transcriptions}\n"
            response += f"**Failed:** {result.failed_transcriptions}\n\n"

            for i, transcription_result in enumerate(result.results):
                response += f"**File {i + 1}:**\n"
                if transcription_result.success:
                    response += f"  ✅ {transcription_result.text[:100]}"
                    if len(transcription_result.text) > 100:
                        response += "..."
                    response += "\n"
                else:
                    response += f"  ❌ {transcription_result.error_message}\n"
                response += "\n"

            return types.TextContent(type="text", text=response)
        else:
            return types.TextContent(
                type="text",
                text=f"❌ Batch transcription failed: {result.error_message}",
            )

    def _get_transcribe_schema(self) -> Dict[str, Any]:
        """Get JSON schema for whisper-transcribe tool."""
        return {
            "type": "object",
            "properties": {
                "audio_file": {
                    "type": "string",
                    "description": "Path to the audio file to transcribe",
                },
                "model": {
                    "type": "string",
                    "description": "Whisper model to use",
                    "default": "whisper-1",
                    "enum": ["whisper-1"],
                },
                "language": {
                    "type": "string",
                    "description": "Language of the audio (ISO-639-1 format)",
                },
                "response_format": {
                    "type": "string",
                    "description": "Format of the response",
                    "default": "json",
                    "enum": ["json", "text", "srt", "verbose_json", "vtt"],
                },
                "temperature": {
                    "type": "number",
                    "description": "Sampling temperature between 0 and 1",
                    "default": 0.0,
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "prompt": {
                    "type": "string",
                    "description": "Optional text to guide the model's style",
                },
            },
            "required": ["audio_file"],
        }

    def _get_transcribe_timestamps_schema(self) -> Dict[str, Any]:
        """Get JSON schema for whisper-transcribe-timestamps tool."""
        return {
            "type": "object",
            "properties": {
                "audio_file": {
                    "type": "string",
                    "description": "Path to the audio file to transcribe",
                },
                "model": {
                    "type": "string",
                    "description": "Whisper model to use",
                    "default": "whisper-1",
                    "enum": ["whisper-1"],
                },
                "language": {
                    "type": "string",
                    "description": "Language of the audio (ISO-639-1 format)",
                },
                "temperature": {
                    "type": "number",
                    "description": "Sampling temperature between 0 and 1",
                    "default": 0.0,
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "prompt": {
                    "type": "string",
                    "description": "Optional text to guide the model's style",
                },
            },
            "required": ["audio_file"],
        }

    def _get_detect_language_schema(self) -> Dict[str, Any]:
        """Get JSON schema for whisper-detect-language tool."""
        return {
            "type": "object",
            "properties": {
                "audio_file": {
                    "type": "string",
                    "description": "Path to the audio file to analyze",
                },
                "model": {
                    "type": "string",
                    "description": "Whisper model to use",
                    "default": "whisper-1",
                    "enum": ["whisper-1"],
                },
            },
            "required": ["audio_file"],
        }

    def _get_batch_transcribe_schema(self) -> Dict[str, Any]:
        """Get JSON schema for whisper-batch-transcribe tool."""
        return {
            "type": "object",
            "properties": {
                "audio_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "List of paths to audio files to transcribe"
                    ),
                },
                "model": {
                    "type": "string",
                    "description": "Whisper model to use",
                    "default": "whisper-1",
                    "enum": ["whisper-1"],
                },
                "language": {
                    "type": "string",
                    "description": "Language of the audio (ISO-639-1 format)",
                },
                "response_format": {
                    "type": "string",
                    "description": "Format of the response",
                    "default": "json",
                    "enum": ["json", "text", "srt", "verbose_json", "vtt"],
                },
                "temperature": {
                    "type": "number",
                    "description": "Sampling temperature between 0 and 1",
                    "default": 0.0,
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
            },
            "required": ["audio_files"],
        }

    def _get_transcribe_file_content_schema(self) -> Dict[str, Any]:
        """Get JSON schema for whisper-transcribe-file-content tool."""
        return {
            "type": "object",
            "properties": {
                "file_content": {
                    "type": "string",
                    "description": "Base64 encoded audio file content",
                },
                "file_name": {
                    "type": "string",
                    "description": (
                        "Original file name (optional, for context)"
                    ),
                    "default": "uploaded_audio.wav",
                },
                "model": {
                    "type": "string",
                    "description": "Whisper model to use",
                    "default": "whisper-1",
                    "enum": ["whisper-1"],
                },
                "language": {
                    "type": "string",
                    "description": "Language of the audio (ISO-639-1 format)",
                },
                "response_format": {
                    "type": "string",
                    "description": "Format of the response",
                    "default": "json",
                    "enum": ["json", "text", "srt", "verbose_json", "vtt"],
                },
                "temperature": {
                    "type": "number",
                    "description": "Sampling temperature between 0 and 1",
                    "default": 0.0,
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "prompt": {
                    "type": "string",
                    "description": "Optional text to guide the model's style",
                },
            },
            "required": ["file_content"],
        }

    def _get_convert_audio_schema(self) -> Dict[str, Any]:
        """Get JSON schema for whisper-convert-audio tool."""
        return {
            "type": "object",
            "properties": {
                "input_file": {
                    "type": "string",
                    "description": "Path to the audio/video file to convert",
                },
                "output_format": {
                    "type": "string",
                    "description": "Target output format",
                    "default": "wav",
                    "enum": ["wav", "mp3", "m4a", "flac", "ogg"],
                },
                "output_file": {
                    "type": "string",
                    "description": "Output file path (optional, will generate if not provided)",
                },
                "quality": {
                    "type": "string",
                    "description": "Conversion quality setting",
                    "default": "high",
                    "enum": ["high", "medium", "low"],
                },
            },
            "required": ["input_file"],
        }

    async def _handle_model_info(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle whisper-model-info tool call."""
        try:
            # Get model information from composition root
            model_info = self._root.get_whisper_model().get_model_info()
            
            model_name = model_info.get('model_name', 'openai/whisper-large-v3')
            device = model_info.get('device', 'auto')
            
            # Extract model size from name
            if 'large' in model_name:
                size = 'Large (1550M parameters)'
                context = '30 seconds'
            elif 'medium' in model_name:
                size = 'Medium (769M parameters)'
                context = '30 seconds'
            elif 'small' in model_name:
                size = 'Small (244M parameters)'
                context = '30 seconds'
            elif 'base' in model_name:
                size = 'Base (74M parameters)'
                context = '30 seconds'
            elif 'tiny' in model_name:
                size = 'Tiny (39M parameters)'
                context = '30 seconds'
            else:
                size = 'Unknown'
                context = 'Unknown'
            
            output = f"""
🤖 WHISPER MODEL INFORMATION
{'=' * 60}

**Model:** {model_name}
**Size:** {size}
**Device:** {device}
**Audio Context:** {context}

**Supported Languages:** 99+ languages
**Output Formats:** text, json, srt, vtt, verbose_json

**Capabilities:**
• Multilingual transcription
• Language detection
• Timestamp generation
• Speaker diarization (basic)
• Audio format conversion

**Model Features:**
• Transformer-based architecture
• Trained on 680,000 hours of multilingual data
• Robust to accents and background noise
• Fast inference with GPU acceleration
"""
            
            return [types.TextContent(type="text", text=output.strip())]
            
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Failed to get model info: {str(e)}",
                )
            ]

    async def _handle_audio_info(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle whisper-audio-info tool call."""
        try:
            audio_file = args["audio_file"]
            
            # Check if file exists
            from pathlib import Path
            audio_path = Path(audio_file)
            if not audio_path.exists():
                return [
                    types.TextContent(
                        type="text",
                        text=f"❌ Audio file not found: {audio_file}",
                    )
                ]
            
            # Get file size
            file_size_bytes = audio_path.stat().st_size
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            # Get audio properties using ffprobe if available
            import subprocess
            import json
            
            try:
                result = subprocess.run(
                    [
                        "ffprobe",
                        "-v", "quiet",
                        "-print_format", "json",
                        "-show_format",
                        "-show_streams",
                        str(audio_path)
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    probe_data = json.loads(result.stdout)
                    
                    # Extract audio stream info
                    audio_streams = [
                        s for s in probe_data.get('streams', [])
                        if s.get('codec_type') == 'audio'
                    ]
                    
                    if audio_streams:
                        stream = audio_streams[0]
                        duration = float(
                            probe_data.get('format', {}).get('duration', 0)
                        )
                        sample_rate = stream.get('sample_rate', 'Unknown')
                        channels = stream.get('channels', 'Unknown')
                        codec = stream.get('codec_name', 'Unknown')
                        bit_rate = stream.get('bit_rate', 'Unknown')
                        
                        output = f"""
🎵 AUDIO FILE INFORMATION
{'=' * 60}

**File:** {audio_path.name}
**Path:** {audio_file}
**Size:** {file_size_mb:.2f} MB ({file_size_bytes:,} bytes)

**Audio Properties:**
• Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)
• Sample Rate: {sample_rate} Hz
• Channels: {channels}
• Codec: {codec}
• Bit Rate: {bit_rate} bps

**Format:** {probe_data.get('format', {}).get('format_name', 'Unknown')}

**Whisper Compatibility:**
✅ File is accessible
{'✅' if int(sample_rate) >= 16000 else '⚠️'} Sample rate {'adequate' if int(sample_rate) >= 16000 else 'low (recommend 16kHz+)'}
{'✅' if duration < 1800 else '⚠️'} Duration {'acceptable' if duration < 1800 else 'long (consider splitting)'}
"""
                        return [
                            types.TextContent(type="text", text=output.strip())
                        ]
                
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                pass
            
            # Fallback if ffprobe not available
            output = f"""
🎵 AUDIO FILE INFORMATION
{'=' * 60}

**File:** {audio_path.name}
**Path:** {audio_file}
**Size:** {file_size_mb:.2f} MB ({file_size_bytes:,} bytes)
**Extension:** {audio_path.suffix}

⚠️  Detailed audio properties unavailable (ffprobe not found)
✅ File is accessible and ready for transcription

**Note:** Install ffmpeg/ffprobe for detailed audio analysis
"""
            return [types.TextContent(type="text", text=output.strip())]
            
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Failed to get audio info: {str(e)}",
                )
            ]

    async def _handle_get_config(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle whisper-get-config tool call."""
        try:
            # Get configuration from composition root
            model_info = self._root.get_whisper_model().get_model_info()
            config_provider = self._root.get_configuration()
            
            model_name = model_info.get(
                'model_name', 'openai/whisper-large-v3'
            )
            max_size_bytes = getattr(
                config_provider, 'max_file_size', 100*1024*1024
            )
            
            config_info = {
                'model': model_name,
                'device': model_info.get('device', 'auto'),
                'compute_type': model_info.get('compute_type', 'default'),
                'host': getattr(config_provider, 'host', 'localhost'),
                'port': getattr(config_provider, 'port', 8000),
                'max_file_size': f"{max_size_bytes / (1024*1024):.0f}MB",
            }
            
            output = f"""
⚙️  WHISPER SERVER CONFIGURATION
{'=' * 60}

**Model Configuration:**
• Model: {config_info['model']}
• Device: {config_info['device']}
• Compute Type: {config_info['compute_type']}

**Server Configuration:**
• Host: {config_info['host']}
• Port: {config_info['port']}
• Max File Size: {config_info['max_file_size']}

**Default Settings:**
• Temperature: 0.0
• Response Format: json
• Language: auto-detect

**Supported Audio Formats:**
• Input: mp3, wav, m4a, flac, ogg, webm, mp4, etc.
• Output: text, json, srt, vtt, verbose_json

**Performance Tips:**
• GPU acceleration available (if CUDA/Metal installed)
• Batch processing supported for multiple files
• Audio conversion available for incompatible formats
"""
            
            return [types.TextContent(type="text", text=output.strip())]
            
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Failed to get configuration: {str(e)}",
                )
            ]

    def _get_model_info_schema(self) -> Dict[str, Any]:
        """Schema for whisper-model-info tool."""
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def _get_audio_info_schema(self) -> Dict[str, Any]:
        """Schema for whisper-audio-info tool."""
        return {
            "type": "object",
            "properties": {
                "audio_file": {
                    "type": "string",
                    "description": "Path to the audio file to analyze",
                }
            },
            "required": ["audio_file"],
        }

    def _get_config_schema(self) -> Dict[str, Any]:
        """Schema for whisper-get-config tool."""
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

