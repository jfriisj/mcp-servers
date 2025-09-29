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
)


class TranscriptionRequest(BaseModel):
    """Request model for transcription."""

    audio_file: Optional[str] = None  # Base64 encoded audio
    language: Optional[str] = "en"
    response_format: str = "json"
    temperature: float = 0.0
    prompt: Optional[str] = None


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

                # Transcribe using file content
                result = await self.whisper_runner.transcribe_file_content(
                    FileContentTranscriptionConfig(
                        file_content=request.audio_file,
                        file_name="uploaded_audio.wav",
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

                # Validate file type
                if not file.filename.lower().endswith(
                    (".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm")
                ):
                    raise HTTPException(
                        status_code=400, detail="Unsupported file format"
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

    def _detect_audio_format(self, file_data: bytes) -> Optional[str]:
        """Detect audio file format from binary data."""
        if len(file_data) < 12:
            return None

        # Check magic bytes for different audio formats
        if file_data.startswith(b"RIFF") and file_data[8:12] == b"WAVE":
            return "wav"
        elif (
            file_data.startswith(b"ID3")
            or file_data.startswith(b"\xff\xfb")
            or file_data.startswith(b"\xff\xf3")
            or file_data.startswith(b"\xff\xf2")
        ):
            return "mp3"
        elif file_data.startswith(b"ftypM4A") or file_data.startswith(b"ftypmp4"):
            return "m4a"
        elif file_data.startswith(b"fLaC"):
            return "flac"
        elif file_data.startswith(b"OggS"):
            return "ogg"
        elif file_data[4:8] == b"ftyp":
            return "mp4"
        elif file_data.startswith(b"WEBM"):
            return "webm"

        # Additional checks for MP3 without ID3 tag
        if len(file_data) >= 2:
            first_two = file_data[:2]
            if first_two in [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"\xff\xf1"]:
                return "mp3"

        return None


def create_app(project_root: Optional[Path] = None) -> FastAPI:
    """Create and return the FastAPI application."""
    fastapi_app = FastAPIApp(project_root)
    return fastapi_app.app
