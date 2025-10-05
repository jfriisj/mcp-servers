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
from fastapi.responses import FileResponse
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
    # Optional format hint (e.g., "wma", "mp4")
    file_format: Optional[str] = None
    # Optional original filename for format detection
    file_name: Optional[str] = None
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

    async def _validate_and_read_upload(
        self, file: UploadFile
    ) -> tuple[bytes, str]:
        """Validate uploaded file and read its content.
        
        Args:
            file: Uploaded file object
            
        Returns:
            Tuple of (file_content, file_suffix)
            
        Raises:
            HTTPException: If file is invalid
        """
        if not file or not file.filename:
            raise HTTPException(
                status_code=400, detail="Invalid file upload"
            )
        
        content = await file.read()
        suffix = f".{file.filename.split('.')[-1]}"
        return content, suffix

    async def _handle_transcribe_logic(
        self, request: TranscriptionRequest
    ) -> TranscriptionResponse:
        """Handle transcription logic for base64 audio content.
        
        Args:
            request: Transcription request with base64 audio
            
        Returns:
            TranscriptionResponse with transcription result
        """
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
            error_message=result.error_message if not result.success else None,
            duration=result.duration,
            segments=result.segments,
        )

    async def _handle_file_transcribe_logic(
        self,
        file: UploadFile,
        language: str,
        response_format: str,
        temperature: float,
        prompt: Optional[str]
    ) -> TranscriptionResponse:
        """Handle transcription logic for uploaded file.
        
        Args:
            file: Uploaded file
            language: Language code
            response_format: Response format
            temperature: Temperature parameter
            prompt: Optional prompt
            
        Returns:
            TranscriptionResponse with transcription result
        """
        # Validate and read file
        content, suffix = await self._validate_and_read_upload(file)

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Always use transcribe_with_timestamps for file uploads
            # to handle automatic segmentation for long audio files
            config = TranscriptionConfig(
                audio_file=temp_file_path,
                language=language,
                response_format=response_format,
                temperature=temperature,
                prompt=prompt,
                model="whisper-1",
            )
            result = await self._root.transcribe_with_timestamps.execute(
                config
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

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

    async def _handle_language_detection_logic(
        self, request: TranscriptionRequest
    ) -> dict:
        """Handle language detection logic.
        
        Args:
            request: Transcription request with base64 audio
            
        Returns:
            Dictionary with detection results
        """
        if not request.audio_file:
            raise HTTPException(
                status_code=400, detail="audio_file is required"
            )

        # Create temporary file from base64
        file_data = base64.b64decode(request.audio_file, validate=True)

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
            config = LanguageDetectionConfig(audio_file=temp_file_path)
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

    async def _handle_batch_transcribe_logic(self, request: dict) -> dict:
        """Handle batch transcription logic.
        
        Args:
            request: Batch transcription request dictionary
            
        Returns:
            Dictionary with batch results
        """
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
                    response_format=request.get("response_format", "json"),
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

    def _setup_routes(self):
        """Set up FastAPI routes."""

        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "message": "Whisper Transcription API",
                "version": "1.0.0",
                "endpoints": {
                    "/transcribe": "POST - Transcribe audio (base64)",
                    "/transcribe-file": "POST - Transcribe uploaded file",
                    "/detect-language": "POST - Detect language (base64)",
                    "/detect-language-file": "POST - Detect language (upload)",
                    "/convert-audio": "POST - Convert audio (path-based)",
                    "/convert-audio-file": "POST - Convert audio (upload)",
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
                return await self._handle_transcribe_logic(request)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Transcription failed: {str(e)}"
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
                return await self._handle_file_transcribe_logic(
                    file, language, response_format, temperature, prompt
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Transcription failed: {str(e)}"
                )

        @self.app.post("/detect-language")
        async def detect_language(request: TranscriptionRequest):
            """Detect language of audio content."""
            try:
                return await self._handle_language_detection_logic(request)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Language detection failed: {str(e)}"
                )

        @self.app.post("/batch-transcribe")
        async def batch_transcribe(request: dict):
            """Batch transcribe multiple audio files."""
            try:
                return await self._handle_batch_transcribe_logic(request)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Batch transcription failed: {str(e)}"
                )

        @self.app.post("/convert-audio", response_model=ConversionResponse)
        async def convert_audio(request: ConversionRequest):
            """Convert audio file to different format (path-based)."""
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

        @self.app.post("/convert-audio-file")
        async def convert_audio_file(
            file: UploadFile = File(...),
            output_format: str = Form("wav"),
            quality: str = Form("high")
        ):
            """Convert uploaded audio file and return the converted file."""
            try:
                # Validate and read uploaded file
                content, input_suffix = await self._validate_and_read_upload(
                    file
                )

                # Create temporary input file
                with tempfile.NamedTemporaryFile(
                    suffix=input_suffix, delete=False
                ) as temp_input:
                    temp_input.write(content)
                    temp_input_path = temp_input.name

                try:
                    # Use convert_audio use case
                    config = ConversionConfig(
                        input_file=temp_input_path,
                        output_format=output_format,
                        output_file=None,
                        quality=quality
                    )

                    result = await self._root.convert_audio.execute(config)

                    if not result.success or not result.output_file:
                        raise HTTPException(
                            status_code=500,
                            detail=(
                                result.error_message or
                                "Conversion failed"
                            )
                        )

                    # Return the converted file as a download
                    return FileResponse(
                        path=result.output_file,
                        media_type=f"audio/{output_format}",
                        filename=f"converted.{output_format}"
                    )

                finally:
                    # Clean up temporary input file
                    try:
                        os.unlink(temp_input_path)
                    except OSError:
                        pass

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Audio conversion failed: {str(e)}"
                )

        @self.app.post("/detect-language-file")
        async def detect_language_file(file: UploadFile = File(...)):
            """Detect language of uploaded audio file."""
            try:
                # Validate and read uploaded file
                content, suffix = await self._validate_and_read_upload(file)

                # Create temporary file
                with tempfile.NamedTemporaryFile(
                    suffix=suffix, delete=False
                ) as temp_file:
                    temp_file.write(content)
                    temp_file_path = temp_file.name

                try:
                    # Use detect_language use case
                    config = LanguageDetectionConfig(
                        audio_file=temp_file_path
                    )
                    result = await self._root.detect_language.execute(
                        config
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
                    status_code=500,
                    detail=f"Language detection failed: {str(e)}"
                )


def create_app(project_root: Optional[Path] = None) -> FastAPI:
    """Create and return the FastAPI application."""
    # Create composition root with dependency injection
    root_path = str(project_root) if project_root else None
    composition_root = CompositionRoot(root_path)
    fastapi_app = FastAPIApp(composition_root)
    return fastapi_app.app
