"""  
FastAPI application for Whisper transcription
=============================================
Provides REST API endpoints for audio transcription using the Whisper model.

Refactored to use Clean Architecture with CompositionRoot.
"""

import base64
import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from domain.models import (
    ConversionConfig,
    LanguageDetectionConfig,
    TranscriptionConfig,
)
from presentation.composition_root import CompositionRoot


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

    def __init__(self, composition_root: CompositionRoot):
        """Initialize FastAPI app with composition root.
        
        Args:
            composition_root: Dependency injection container
        """
        self._root = composition_root
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
            model_info = self._root.get_whisper_model().get_model_info()
            model_loaded = model_info.get('model_name') is not None
            device = model_info.get('device', 'cpu')
            return {
                "status": "healthy" if model_loaded else "unhealthy",
                "model_loaded": model_loaded,
                "cuda_available": device == "cuda",
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
                    fmt = request.file_format.lower().lstrip('.')
                    filename = f"{filename}.{fmt}"
                elif '.' not in filename:
                    filename = f"{filename}.unknown"

                # Use transcribe_file_content use case
                result = await self._root.transcribe_file_content.execute(
                    file_content=request.audio_file,
                    file_name=filename,
                    file_format=request.file_format,
                    language=request.language,
                    response_format=request.response_format,
                    temperature=request.temperature,
                    prompt=request.prompt,
                    model="whisper-1",
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

                # Read file content
                content = await file.read()

                # Create temporary file
                suffix = f".{file.filename.split('.')[-1]}"
                with tempfile.NamedTemporaryFile(
                    suffix=suffix, delete=False
                ) as temp_file:
                    temp_file.write(content)
                    temp_file_path = temp_file.name

                try:
                    # Use appropriate use case based on response format
                    if response_format == "verbose_json":
                        config = TranscriptionConfig(
                            audio_file=temp_file_path,
                            language=language,
                            response_format=response_format,
                            temperature=temperature,
                            prompt=prompt,
                            model="whisper-1",
                        )
                        result = await self._root.transcribe_with_timestamps.execute(config)
                    else:
                        config = TranscriptionConfig(
                            audio_file=temp_file_path,
                            language=language,
                            response_format=response_format,
                            temperature=temperature,
                            prompt=prompt,
                            model="whisper-1",
                        )
                        result = await self._root.transcribe_audio.execute(config)

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
                file_data = base64.b64decode(
                    request.audio_file, validate=True
                )

                # Simple format detection
                detected_format = "wav"  # Default
                if file_data.startswith(b"RIFF") and len(file_data) > 12:
                    if file_data[8:12] == b"WAVE":
                        detected_format = "wav"
                elif file_data.startswith(b"ID3"):
                    detected_format = "mp3"
                elif file_data.startswith(b"\xff\xfb"):
                    detected_format = "mp3"

                suffix = f".{detected_format}"
                with tempfile.NamedTemporaryFile(
                    suffix=suffix, delete=False
                ) as temp_file:
                    temp_file.write(file_data)
                    temp_file_path = temp_file.name

                try:
                    # Use detect_language use case
                    config = LanguageDetectionConfig(
                        audio_file=temp_file_path
                    )
                    result = await self._root.detect_language.execute(config)

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

                        # Read file and encode
                        with open(audio_file, "rb") as f:
                            file_content = base64.b64encode(f.read()).decode()

                        # Use transcribe_file_content use case
                        result = await self._root.transcribe_file_content.execute(
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

                        if result.success:
                            successful += 1
                            results.append({
                                "success": True,
                                "text": result.text,
                                "language": result.language,
                                "duration": result.duration,
                                "segments": result.segments,
                            })
                        else:
                            failed += 1
                            results.append({
                                "success": False,
                                "error_message": result.error_message,
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

                # Use convert_audio use case
                config = ConversionConfig(
                    input_file=request.input_file,
                    output_format=request.output_format,
                    output_file=request.output_file,
                    quality=request.quality
                )

                result = await self._root.convert_audio.execute(config)
                
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


def create_app(project_root: Optional[Path] = None) -> FastAPI:
    """Create and return the FastAPI application."""
    # Create composition root with dependency injection
    root_path = str(project_root) if project_root else None
    composition_root = CompositionRoot(root_path)
    fastapi_app = FastAPIApp(composition_root)
    return fastapi_app.app
