"""
MCP protocol handling for Whisper Server
========================================
Manages MCP tool definitions and protocol interactions.
"""

from typing import Any, Dict, List
import requests

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

    def __init__(self, whisper_runner):
        self.whisper_runner = whisper_runner

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
        """Handle whisper-transcribe tool call by delegating to FastAPI."""
        try:
            response = requests.post(
                "http://localhost:8000/transcribe",
                json={
                    "audio_file": args["audio_file"],
                    "language": args.get("language"),
                    "response_format": args.get("response_format", "json"),
                    "temperature": args.get("temperature", 0.0),
                    "prompt": args.get("prompt"),
                },
            )
            response.raise_for_status()
            result = response.json()
            return [
                types.TextContent(
                    type="text",
                    text=(
                        f"✅ Transcription completed successfully!\n\n"
                        f"**Text:** {result['text']}\n"
                        f"**Language:** {result.get('language', 'N/A')}"
                    ),
                )
            ]
        except requests.RequestException as e:
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
        from models import TranscriptionWithTimestampsConfig

        config = TranscriptionWithTimestampsConfig(
            audio_file=args["audio_file"],
            model=args.get("model", "whisper-1"),
            language=args.get("language"),
            response_format="verbose_json",
            temperature=args.get("temperature", 0.0),
            prompt=args.get("prompt"),
        )

        result = await self.whisper_runner.transcribe_with_timestamps(config)
        return [
            self._format_transcription_result(
                "Transcription with timestamps", result
            )
        ]

    async def _handle_detect_language(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle whisper-detect-language tool call."""
        from models import LanguageDetectionConfig

        config = LanguageDetectionConfig(
            audio_file=args["audio_file"],
            model=args.get("model", "whisper-1"),
        )

        result = await self.whisper_runner.detect_language(config)
        return [self._format_language_detection_result(result)]

    async def _handle_batch_transcribe(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle whisper-batch-transcribe tool call."""
        from models import BatchTranscriptionConfig

        config = BatchTranscriptionConfig(
            audio_files=args["audio_files"],
            model=args.get("model", "whisper-1"),
            language=args.get("language"),
            response_format=args.get("response_format", "json"),
            temperature=args.get("temperature", 0.0),
        )

        result = await self.whisper_runner.batch_transcribe(config)
        return [self._format_batch_result(result)]

    async def _handle_transcribe_file_content(
        self,
        args: Dict[str, Any],
    ) -> List[types.TextContent]:
        """Handle whisper-transcribe-file-content tool call."""
        from models import FileContentTranscriptionConfig

        config = FileContentTranscriptionConfig(
            file_content=args["file_content"],
            file_name=args.get("file_name", "uploaded_audio.wav"),
            model=args.get("model", "whisper-1"),
            language=args.get("language"),
            response_format=args.get("response_format", "json"),
            temperature=args.get("temperature", 0.0),
            prompt=args.get("prompt"),
        )

        result = await self.whisper_runner.transcribe_file_content(config)
        return [
            self._format_transcription_result(
                "Transcription from file content", result
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
                    f"**Segments:** {len(result.segments)} segments available\n"
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
