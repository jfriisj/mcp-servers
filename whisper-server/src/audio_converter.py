"""
Audio Converter for Whisper MCP Server
======================================
Handles conversion of various audio/video file formats to formats supported by Whisper.
Supports both ffmpeg and librosa conversion methods with fallback options.
"""

import os
import tempfile
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Union
import logging
from dataclasses import dataclass

# Audio processing imports with fallback
try:
    import librosa
    import soundfile as sf
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False
    librosa = None
    sf = None

# FFmpeg Python wrapper with fallback
try:
    import ffmpeg
    HAS_FFMPEG_PYTHON = True
except ImportError:
    HAS_FFMPEG_PYTHON = False
    ffmpeg = None


logger = logging.getLogger(__name__)


@dataclass
class ConversionConfig:
    """Configuration for audio conversion."""
    input_file: str
    output_format: str = "wav"  # Default to WAV for best compatibility
    output_file: Optional[str] = None  # If None, will generate temp file
    sample_rate: Optional[int] = None  # If None, keep original
    channels: Optional[int] = None  # If None, keep original (mono=1, stereo=2)
    quality: str = "high"  # high, medium, low
    remove_input: bool = False  # Whether to remove input file after conversion


@dataclass
class ConversionResult:
    """Result of audio conversion operation."""
    success: bool
    output_file: Optional[str] = None
    original_format: Optional[str] = None
    converted_format: Optional[str] = None
    duration: Optional[float] = None
    file_size_mb: Optional[float] = None
    conversion_method: Optional[str] = None  # ffmpeg, librosa, etc.
    error_message: Optional[str] = None
    temp_file: bool = False  # Whether output file is temporary


class AudioConverter:
    """Handles audio file format conversion for Whisper transcription."""

    # Supported input formats (can be converted)
    CONVERTIBLE_FORMATS = [
        # Video formats (extract audio)
        "mp4", "mov", "avi", "mkv", "wmv", "flv", "webm", "3gp", "m4v",
        # Audio formats that may need conversion
        "aac", "ac3", "aiff", "amr", "ape", "au", "dts", "mka", "mpc", 
        "ra", "wma", "opus", "spx", "tta", "voc", "wv", "xa",
        # Less common formats
        "caf", "dss", "dvf", "gsm", "iff", "m4r", "mmf", "mxf", "nist", 
        "pvf", "raw", "sln", "vms", "vox", "w64"
    ]

    # Output formats Whisper can handle directly
    WHISPER_SUPPORTED_FORMATS = [
        "mp3", "wav", "m4a", "flac", "ogg", "webm"
    ]

    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize the audio converter.
        
        Args:
            temp_dir: Directory for temporary files. If None, uses system temp.
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.ffmpeg_path = self._find_ffmpeg()
        
    def _find_ffmpeg(self) -> Optional[str]:
        """Find ffmpeg executable path."""
        # Check common locations for ffmpeg
        possible_paths = [
            "ffmpeg",  # In PATH
            "ffmpeg.exe",  # Windows in PATH
            r"C:\github\mcp-servers\whisper-server\ffmpeg.exe",  # Local installation
            "/usr/bin/ffmpeg",  # Linux
            "/usr/local/bin/ffmpeg",  # macOS with Homebrew
            "/opt/homebrew/bin/ffmpeg",  # macOS with Apple Silicon Homebrew
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run(
                    [path, "-version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    logger.info(f"Found ffmpeg at: {path}")
                    return path
            except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        logger.warning("FFmpeg not found in common locations")
        return None

    def needs_conversion(self, file_path: str) -> bool:
        """Check if a file needs conversion for Whisper compatibility.
        
        Args:
            file_path: Path to the audio/video file
            
        Returns:
            True if file needs conversion, False otherwise
        """
        if not Path(file_path).exists():
            return False
            
        file_ext = Path(file_path).suffix.lower().lstrip(".")
        
        # If it's already in a Whisper-supported format, no conversion needed
        if file_ext in self.WHISPER_SUPPORTED_FORMATS:
            return False
            
        # If it's in convertible formats, it needs conversion
        return file_ext in self.CONVERTIBLE_FORMATS

    def get_file_info(self, file_path: str) -> dict:
        """Get information about an audio/video file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        info = {
            "exists": False,
            "format": None,
            "duration": None,
            "sample_rate": None,
            "channels": None,
            "size_mb": None
        }
        
        if not Path(file_path).exists():
            return info
            
        info["exists"] = True
        info["format"] = Path(file_path).suffix.lower().lstrip(".")
        info["size_mb"] = Path(file_path).stat().st_size / (1024 * 1024)
        
        # Try to get audio info using ffprobe if available
        if self.ffmpeg_path:
            try:
                # Try to find ffprobe
                ffprobe_path = self.ffmpeg_path.replace("ffmpeg", "ffprobe")
                if not Path(ffprobe_path).exists() and self.ffmpeg_path == "ffmpeg":
                    # If ffmpeg is in PATH, try ffprobe in PATH too
                    ffprobe_path = "ffprobe"
                
                # Test if ffprobe is available
                test_result = subprocess.run([ffprobe_path, "-version"], 
                                           capture_output=True, timeout=5)
                if test_result.returncode != 0:
                    logger.debug("ffprobe not available")
                    return info
                
                result = subprocess.run([
                    ffprobe_path, "-v", "quiet", "-show_entries",
                    "format=duration:stream=sample_rate,channels", 
                    "-of", "csv=p=0", file_path
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line and ',' in line:
                            parts = line.split(',')
                            if len(parts) >= 2:
                                info["sample_rate"] = int(parts[0]) if parts[0] else None
                                info["channels"] = int(parts[1]) if parts[1] else None
                        elif line and line.replace('.', '').isdigit():
                            info["duration"] = float(line)
            except (subprocess.SubprocessError, ValueError, subprocess.TimeoutExpired, FileNotFoundError):
                logger.debug("Could not get file info using ffprobe")
        
        return info

    async def convert_file(self, config: ConversionConfig) -> ConversionResult:
        """Convert an audio/video file to a Whisper-compatible format.
        
        Args:
            config: Conversion configuration
            
        Returns:
            ConversionResult with conversion status and output file info
        """
        if not Path(config.input_file).exists():
            return ConversionResult(
                success=False,
                error_message=f"Input file does not exist: {config.input_file}"
            )

        # Get file info
        file_info = self.get_file_info(config.input_file)
        input_format = file_info["format"]
        
        # Determine output file path
        if config.output_file:
            output_file = config.output_file
            temp_file = False
        else:
            # Generate temporary file
            suffix = f".{config.output_format}"
            temp_fd, output_file = tempfile.mkstemp(suffix=suffix, dir=self.temp_dir)
            os.close(temp_fd)  # Close the file descriptor, we just need the path
            temp_file = True

        # Try conversion methods in order of preference
        conversion_methods = self._get_conversion_methods()
        
        for method_name, method_func in conversion_methods:
            try:
                logger.info(f"Attempting conversion using {method_name}")
                result = await method_func(config, output_file, file_info)
                
                if result.success:
                    result.original_format = input_format
                    result.converted_format = config.output_format
                    result.conversion_method = method_name
                    result.temp_file = temp_file
                    
                    # Clean up input file if requested
                    if config.remove_input:
                        try:
                            os.unlink(config.input_file)
                        except OSError:
                            logger.warning(f"Could not remove input file: {config.input_file}")
                    
                    return result
                    
            except Exception as e:
                logger.debug(f"Conversion method {method_name} failed: {str(e)}")
                continue
        
        # All methods failed
        if temp_file and Path(output_file).exists():
            os.unlink(output_file)
            
        return ConversionResult(
            success=False,
            error_message="All conversion methods failed. Check logs for details."
        )

    def _get_conversion_methods(self) -> List[Tuple[str, callable]]:
        """Get available conversion methods in order of preference."""
        methods = []
        
        # Prefer ffmpeg for best compatibility
        if self.ffmpeg_path:
            methods.append(("ffmpeg", self._convert_with_ffmpeg))
        
        # Librosa as fallback for audio-only files
        if HAS_LIBROSA:
            methods.append(("librosa", self._convert_with_librosa))
        
        # Add more methods here as needed
        
        if not methods:
            logger.error("No conversion methods available. Install ffmpeg or librosa.")
        
        return methods

    async def _convert_with_ffmpeg(
        self, 
        config: ConversionConfig, 
        output_file: str, 
        file_info: dict
    ) -> ConversionResult:
        """Convert audio using ffmpeg."""
        cmd = [self.ffmpeg_path, "-i", config.input_file]
        
        # Add conversion parameters based on quality and config
        if config.sample_rate:
            cmd.extend(["-ar", str(config.sample_rate)])
        
        if config.channels:
            cmd.extend(["-ac", str(config.channels)])
        
        # Quality settings
        if config.output_format == "mp3":
            quality_map = {"high": "0", "medium": "5", "low": "9"}
            cmd.extend(["-q:a", quality_map.get(config.quality, "5")])
        elif config.output_format == "wav":
            # WAV is lossless, but we can set bit depth
            cmd.extend(["-acodec", "pcm_s16le"])
        
        # Overwrite output file and suppress banner
        cmd.extend(["-y", "-hide_banner", "-loglevel", "error"])
        cmd.append(output_file)
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0 and Path(output_file).exists():
                # Get output file info
                output_info = self.get_file_info(output_file)
                
                return ConversionResult(
                    success=True,
                    output_file=output_file,
                    duration=output_info.get("duration"),
                    file_size_mb=output_info.get("size_mb")
                )
            else:
                error_msg = result.stderr or "FFmpeg conversion failed"
                return ConversionResult(
                    success=False,
                    error_message=f"FFmpeg error: {error_msg}"
                )
                
        except subprocess.TimeoutExpired:
            return ConversionResult(
                success=False,
                error_message="FFmpeg conversion timed out (>5 minutes)"
            )
        except Exception as e:
            return ConversionResult(
                success=False,
                error_message=f"FFmpeg conversion error: {str(e)}"
            )

    async def _convert_with_librosa(
        self, 
        config: ConversionConfig, 
        output_file: str, 
        file_info: dict
    ) -> ConversionResult:
        """Convert audio using librosa (audio files only)."""
        try:
            # Load audio file
            y, sr = librosa.load(
                config.input_file,
                sr=config.sample_rate,  # Will resample if specified
                mono=(config.channels == 1) if config.channels else None
            )
            
            # Convert to stereo if requested
            if config.channels == 2 and y.ndim == 1:
                y = librosa.to_stereo(y)
            
            # Save using soundfile
            sf.write(output_file, y, sr)
            
            if Path(output_file).exists():
                output_info = self.get_file_info(output_file)
                
                return ConversionResult(
                    success=True,
                    output_file=output_file,
                    duration=len(y) / sr,
                    file_size_mb=output_info.get("size_mb")
                )
            else:
                return ConversionResult(
                    success=False,
                    error_message="Librosa conversion failed - output file not created"
                )
                
        except Exception as e:
            return ConversionResult(
                success=False,
                error_message=f"Librosa conversion error: {str(e)}"
            )

    def cleanup_temp_files(self, file_paths: Union[str, List[str]]):
        """Clean up temporary files created during conversion.
        
        Args:
            file_paths: Single file path or list of file paths to clean up
        """
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        
        for file_path in file_paths:
            try:
                if Path(file_path).exists():
                    os.unlink(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except OSError as e:
                logger.warning(f"Could not clean up temp file {file_path}: {e}")

    def get_supported_input_formats(self) -> List[str]:
        """Get list of supported input formats for conversion."""
        return self.CONVERTIBLE_FORMATS + self.WHISPER_SUPPORTED_FORMATS

    def get_recommended_output_format(self, input_format: str) -> str:
        """Get recommended output format for a given input format.
        
        Args:
            input_format: Input file format (extension without dot)
            
        Returns:
            Recommended output format
        """
        # For video files, extract to WAV for best quality
        video_formats = ["mp4", "mov", "avi", "mkv", "wmv", "flv", "webm", "3gp", "m4v"]
        if input_format.lower() in video_formats:
            return "wav"
        
        # For high-quality audio, prefer WAV
        lossless_formats = ["flac", "ape", "wv", "tta"]
        if input_format.lower() in lossless_formats:
            return "wav"
        
        # For compressed audio, MP3 is usually fine
        return "mp3"


class TempFileManager:
    """Manages temporary files created during conversion process."""
    
    def __init__(self):
        self.temp_files = []
    
    def add_temp_file(self, file_path: str):
        """Add a temporary file to be tracked for cleanup."""
        if file_path not in self.temp_files:
            self.temp_files.append(file_path)
    
    def cleanup_all(self):
        """Clean up all tracked temporary files."""
        for file_path in self.temp_files:
            try:
                if Path(file_path).exists():
                    os.unlink(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except OSError as e:
                logger.warning(f"Could not clean up temp file {file_path}: {e}")
        
        self.temp_files.clear()
    
    def __del__(self):
        """Ensure cleanup on object destruction."""
        self.cleanup_all()