"""
FastAPI application for Whisper transcription
=============================================
Provides REST API endpoints for audio transcription using the Whisper model.
"""

import base64
import tempfile
import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from config import ConfigurationManager
from whisper_runner import WhisperRunner
from models import (
    TranscriptionConfig,
    TranscriptionWithTimestampsConfig,
    FileContentTranscriptionConfig,
    ConversionConfig,
)


class TranscriptionRequest(BaseModel):
    """Request model for transcription."""

    audio_file: Optional[str] = None  # Base64 encoded audio
    file_format: Optional[str] = None  # Optional format hint (e.g., "wma", "mp4")
    file_name: Optional[str] = None  # Optional original filename for format detection
    language: Optional[str] = "en"
    response_format: str = "json"
    temperature: float = 0.0
    prompt: Optional[str] = None


class ConversionRequest(BaseModel):
    """Request model for audio conversion."""
    
    input_file: str
    output_format: str = "wav"
    quality: str = "high"
    output_file: Optional[str] = None


class ConversionResponse(BaseModel):
    """Response model for audio conversion."""
    
    success: bool
    output_file: Optional[str] = None
    original_format: Optional[str] = None
    converted_format: Optional[str] = None
    duration: Optional[float] = None
    file_size_mb: Optional[float] = None
    conversion_method: Optional[str] = None
    error_message: Optional[str] = None
    temp_file: bool = False


class TranscriptionResponse(BaseModel):
    """Response model for transcription."""

    text: str
    language: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    duration: Optional[float] = None
    segments: Optional[list] = None


class FastAPIApp:
    """FastAPI application for Whisper transcription."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.config_manager = ConfigurationManager(self.project_root)
        self.whisper_runner = WhisperRunner(self.config_manager)
        self.app = FastAPI(
            title="Whisper Transcription API",
            description="REST API for audio transcription using Whisper",
            version="1.0.0",
        )
        self._setup_routes()

    def _setup_routes(self):
        """Set up FastAPI routes."""

        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "message": "Whisper Transcription API",
                "version": "1.0.0",
                "endpoints": {
                    "/transcribe": "POST - Transcribe audio file",
                    "/transcribe-file": "POST - Transcribe uploaded file",
                    "/convert-audio": "POST - Convert audio file format",
                    "/detect-language": "POST - Detect audio language",
                    "/batch-transcribe": "POST - Batch transcribe files",
                    "/health": "GET - Health check",
                },
            }

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            model_loaded = self.whisper_runner._model_loaded
            return {
                "status": "healthy" if model_loaded else "unhealthy",
                "model_loaded": model_loaded,
                "cuda_available": self.config_manager.device == "cuda",
            }

        @self.app.post("/transcribe", response_model=TranscriptionResponse)
        async def transcribe_audio(request: TranscriptionRequest):
            """Transcribe audio from base64 content."""
            try:
                if not request.audio_file:
                    raise HTTPException(
                        status_code=400, detail="audio_file is required"
                    )

                # Determine filename for better format detection
                filename = request.file_name or "uploaded_audio"
                if request.file_format:
                    filename = f"{filename}.{request.file_format.lower().lstrip('.')}"
                elif not '.' in filename:
                    filename = f"{filename}.unknown"

                # Transcribe using file content
                result = await self.whisper_runner.transcribe_file_content(
                    FileContentTranscriptionConfig(
                        file_content=request.audio_file,
                        file_name=filename,
                        file_format=request.file_format,
                        language=request.language,
                        response_format=request.response_format,
                        temperature=request.temperature,
                        prompt=request.prompt,
                        model="whisper-1",
                    )
                )

                return TranscriptionResponse(
                    text=result.text,
                    language=result.language,
                    success=result.success,
                    error_message=result.error_message
                    if not result.success
                    else None,
                    duration=result.duration,
                    segments=result.segments,
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Transcription failed: {str(e)}"
                )

        @self.app.post(
            "/transcribe-file",
            response_model=TranscriptionResponse
        )
        async def transcribe_file(
            file: UploadFile = File(...),
            language: str = Form("en"),
            response_format: str = Form("json"),
            temperature: float = Form(0.0),
            prompt: Optional[str] = Form(None),
        ):
            """Transcribe uploaded audio file."""
            try:
                # Validate file object
                if not file or not file.filename:
                    raise HTTPException(
                        status_code=400, detail="Invalid file upload"
                    )

                # Check if file type is supported (either native or convertible)
                file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
                whisper_formats = self.config_manager.supported_audio_formats
                convertible_formats = self.config_manager.conversion_supported_formats if hasattr(self.config_manager, 'conversion_supported_formats') else []
                
                if file_ext not in whisper_formats and file_ext not in convertible_formats:
                    supported_formats = whisper_formats + convertible_formats
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Unsupported file format '{file_ext}'. Supported formats: {', '.join(supported_formats[:10])}{'...' if len(supported_formats) > 10 else ''}"
                    )

                # Read file content
                content = await file.read()

                # Create temporary file
                with tempfile.NamedTemporaryFile(
                    suffix=f".{file.filename.split('.')[-1]}", delete=False
                ) as temp_file:
                    temp_file.write(content)
                    temp_file_path = temp_file.name

                try:
                    # Validate the temporary file
                    is_valid, error_msg = self.config_manager.validate_audio_file(
                        temp_file_path
                    )
                    if not is_valid:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid audio file: {error_msg}"
                        )

                    # Determine transcription method based on response format
                    if response_format == "verbose_json":
                        result = await self.whisper_runner.transcribe_with_timestamps(
                            TranscriptionWithTimestampsConfig(
                                audio_file=temp_file_path,
                                language=language,
                                response_format=response_format,
                                temperature=temperature,
                                prompt=prompt,
                                model="whisper-1",
                            )
                        )
                    else:
                        result = await self.whisper_runner.transcribe_audio(
                            TranscriptionConfig(
                                audio_file=temp_file_path,
                                language=language,
                                response_format=response_format,
                                temperature=temperature,
                                prompt=prompt,
                                model="whisper-1",
                            )
                        )

                    return TranscriptionResponse(
                        text=result.text,
                        language=result.language,
                        success=result.success,
                        error_message=result.error_message \
                            if not result.success
                            else None,
                        duration=result.duration,
                        segments=result.segments,
                    )

                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_file_path)
                    except OSError:
                        pass

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Transcription failed: {str(e)}"
                )

        @self.app.post("/detect-language")
        async def detect_language(request: TranscriptionRequest):
            """Detect language of audio content."""
            try:
                if not request.audio_file:
                    raise HTTPException(
                        status_code=400, detail="audio_file is required"
                    )

                # Create temporary file from base64
                file_data = base64.b64decode(request.audio_file, validate=True)
                detected_format = self._detect_audio_format(file_data)

                if not detected_format:
                    raise HTTPException(
                        status_code=400, detail="Unsupported audio format"
                    )

                with tempfile.NamedTemporaryFile(
                    suffix=f".{detected_format}", delete=False
                ) as temp_file:
                    temp_file.write(file_data)
                    temp_file_path = temp_file.name

                try:
                    result = await self.whisper_runner.detect_language(
                        type("Config", (), {"audio_file": temp_file_path})()
                    )

                    return {
                        "detected_language": result.detected_language,
                        "confidence": result.confidence,
                        "success": result.success,
                        "error_message": result.error_message
                        if not result.success
                        else None,
                    }

                finally:
                    try:
                        os.unlink(temp_file_path)
                    except OSError:
                        pass

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Language detection failed: {str(e)}"
                )

        @self.app.post("/batch-transcribe")
        async def batch_transcribe(request: dict):
            """Batch transcribe multiple audio files."""
            try:
                audio_files = request.get("audio_files", [])
                if not audio_files:
                    raise HTTPException(
                        status_code=400, detail="audio_files is required"
                    )

                results = []
                total_files = len(audio_files)
                successful = 0
                failed = 0

                for audio_file in audio_files:
                    try:
                        # Read file content
                        if not os.path.exists(audio_file):
                            results.append({
                                "success": False,
                                "error_message": f"File not found: {audio_file}",
                                "text": ""
                            })
                            failed += 1
                            continue

                        with open(audio_file, "rb") as f:
                            file_content = base64.b64encode(f.read()).decode()

                        # Transcribe using file content
                        transcription_result = await self.whisper_runner.\
                            transcribe_file_content(
                                FileContentTranscriptionConfig(
                                    file_content=file_content,
                                    file_name=os.path.basename(audio_file),
                                    language=request.get("language"),
                                    response_format=request.get(
                                        "response_format", "json"
                                    ),
                                    temperature=request.get("temperature", 0.0),
                                    prompt=None,
                                    model="whisper-1",
                                )
                            )

                        if transcription_result.success:
                            successful += 1
                            results.append({
                                "success": True,
                                "text": transcription_result.text,
                                "language": transcription_result.language,
                                "duration": transcription_result.duration,
                                "segments": transcription_result.segments,
                            })
                        else:
                            failed += 1
                            results.append({
                                "success": False,
                                "error_message":
                                    transcription_result.error_message,
                                "text": ""
                            })

                    except Exception as e:
                        failed += 1
                        results.append({
                            "success": False,
                            "error_message": str(e),
                            "text": ""
                        })

                return {
                    "total_files": total_files,
                    "successful_transcriptions": successful,
                    "failed_transcriptions": failed,
                    "results": results,
                    "success": successful > 0
                }

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Batch transcription failed: {str(e)}"
                )

        @self.app.post("/convert-audio", response_model=ConversionResponse)
        async def convert_audio(request: ConversionRequest):
            """Convert audio file to different format."""
            try:
                # Validate input file exists
                if not os.path.exists(request.input_file):
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Input file not found: {request.input_file}"
                    )
                
                # Configure conversion
                conversion_config = ConversionConfig(
                    input_file=request.input_file,
                    output_format=request.output_format,
                    output_file=request.output_file,
                    quality=request.quality
                )
                
                # Perform conversion
                result = await self.whisper_runner.convert_audio_file(conversion_config)
                
                return ConversionResponse(
                    success=result.success,
                    output_file=result.output_file,
                    original_format=result.original_format,
                    converted_format=result.converted_format,
                    duration=result.duration,
                    file_size_mb=result.file_size_mb,
                    conversion_method=result.conversion_method,
                    error_message=result.error_message,
                    temp_file=result.temp_file
                )
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Audio conversion failed: {str(e)}"
                )

    def _detect_audio_format(self, file_data: bytes, file_name: Optional[str] = None, format_hint: Optional[str] = None) -> Optional[str]:
        """Detect audio file format from binary data, filename, or format hint."""
        
        # If format hint is provided, validate and use it
        if format_hint:
            format_hint = format_hint.lower().lstrip('.')
            # Check if it's a supported format
            converter_formats = self.whisper_runner.config_manager.conversion_supported_formats
            whisper_formats = self.whisper_runner.config_manager.supported_audio_formats
            if format_hint in converter_formats or format_hint in whisper_formats:
                return format_hint
        
        # Try to detect from filename extension as fallback
        if file_name:
            extension = file_name.lower().split('.')[-1] if '.' in file_name else None
            if extension:
                converter_formats = self.whisper_runner.config_manager.conversion_supported_formats
                whisper_formats = self.whisper_runner.config_manager.supported_audio_formats
                if extension in converter_formats or extension in whisper_formats:
                    return extension
        
        # Fallback to magic byte detection
        if len(file_data) < 12:
            return None

        # Check magic bytes for different audio formats
        if file_data.startswith(b"RIFF") and file_data[8:12] == b"WAVE":
            return "wav"
        elif file_data.startswith(b"RIFF") and file_data[8:12] == b"AVI ":
            return "avi"
        elif (
            file_data.startswith(b"ID3")
            or file_data.startswith(b"\xff\xfb")
            or file_data.startswith(b"\xff\xf3")
            or file_data.startswith(b"\xff\xf2")
        ):
            return "mp3"
        elif file_data.startswith(b"ftypM4A") or file_data.startswith(b"ftypmp4"):
            return "m4a" if b"M4A" in file_data[:20] else "mp4"
        elif file_data.startswith(b"fLaC"):
            return "flac"
        elif file_data.startswith(b"OggS"):
            return "ogg"
        elif file_data[4:8] == b"ftyp":
            # Check for various MP4 container types
            if b"qt  " in file_data[8:20]:
                return "mov"
            return "mp4"
        elif file_data.startswith(b"WEBM") or (b"webm" in file_data[:20].lower()):
            return "webm"
        # WMA format detection
        elif file_data.startswith(b"\x30\x26\xB2\x75\x8E\x66\xCF\x11\xA6\xD9\x00\xAA\x00\x62\xCE\x6C"):
            return "wma"
        # ASF format (which WMA uses)
        elif file_data.startswith(b"\x30\x26\xB2\x75"):
            return "wma"

        # Additional checks for MP3 without ID3 tag
        if len(file_data) >= 2:
            first_two = file_data[:2]
            if first_two in [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2",
                             b"\xff\xf1"]:
                return "mp3"

        return None


def create_app(project_root: Optional[Path] = None) -> FastAPI:
    """Create and return the FastAPI application."""
    fastapi_app = FastAPIApp(project_root)
    return fastapi_app.app
