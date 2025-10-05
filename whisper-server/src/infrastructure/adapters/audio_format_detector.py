"""
Audio Format Detector - Infrastructure Adapter
===============================================
Detects audio file formats from multiple sources (magic bytes, filenames, hints).

This adapter consolidates duplicate format detection logic that was previously
scattered across whisper_runner.py (20 branches) and api.py (19 branches),
eliminating 39 total conditional branches and providing a single source of truth.

Implements: IAudioFormatDetector from domain layer
Dependencies: None (standalone service)
"""

from typing import Optional

from domain.interfaces import IAudioFormatDetector


class AudioFormatDetector(IAudioFormatDetector):
    """
    Audio format detection service using magic bytes, file extensions, and hints.

    Detection priority:
    1. Explicit format_hint (if provided and valid)
    2. Magic number/byte signature from file_data (most reliable)
    3. File extension from file_name (fallback)

    This eliminates duplicate code and reduces conditional complexity.
    """

    # Formats Whisper can natively process without conversion
    WHISPER_NATIVE_FORMATS = {
        "mp3", "wav", "m4a", "flac", "ogg", "webm"
    }

    # Formats that can be converted to Whisper-compatible formats
    CONVERTIBLE_FORMATS = {
        # Video formats (extract audio)
        "mp4", "mov", "avi", "mkv", "wmv", "flv", "webm", "3gp", "m4v",
        # Audio formats requiring conversion
        "aac", "ac3", "aiff", "amr", "ape", "au", "dts", "mka", "mpc",
        "ra", "wma", "opus", "spx", "tta", "voc", "wv", "xa",
        # Less common formats
        "caf", "dss", "dvf", "gsm", "iff", "m4r", "mmf", "mxf", "nist",
        "pvf", "raw", "sln", "vms", "vox", "w64"
    }

    # Magic byte signatures for format detection
    MAGIC_SIGNATURES = [
        # (signature, offset, format)
        (b"RIFF", 0, b"WAVE", 8, "wav"),  # WAV: RIFF....WAVE
        (b"RIFF", 0, b"AVI ", 8, "avi"),  # AVI: RIFF....AVI
        (b"ID3", 0, None, None, "mp3"),   # MP3 with ID3 tag
        (b"\xff\xfb", 0, None, None, "mp3"),  # MP3 frame sync
        (b"\xff\xf3", 0, None, None, "mp3"),  # MP3 frame sync
        (b"\xff\xf2", 0, None, None, "mp3"),  # MP3 frame sync
        (b"\xff\xf1", 0, None, None, "mp3"),  # MP3 frame sync
        (b"fLaC", 0, None, None, "flac"),     # FLAC
        (b"OggS", 0, None, None, "ogg"),      # OGG
        (b"wvpk", 0, None, None, "wv"),       # WavPack
        (b"WEBM", 0, None, None, "webm"),     # WebM
        # WMA/ASF (Windows Media Audio)
        (b"\x30\x26\xB2\x75\x8E\x66\xCF\x11\xA6\xD9\x00\xAA\x00\x62\xCE\x6C",
         0, None, None, "wma"),
        (b"\x30\x26\xB2\x75", 0, None, None, "wma"),  # Shorter ASF signature
    ]

    # MP4/M4A/MOV detection (ftyp-based)
    FTYP_SIGNATURES = [
        (b"ftypM4A", "m4a"),
        (b"ftypmp42", "mp4"),
        (b"ftypisom", "mp4"),
        (b"ftypmp41", "mp4"),
        (b"ftypMSNV", "mp4"),
        (b"ftypqt  ", "mov"),
    ]

    def detect_format(
        self,
        file_data: Optional[bytes] = None,
        file_name: Optional[str] = None,
        format_hint: Optional[str] = None,
    ) -> Optional[str]:
        """
        Detect audio file format using available information.

        Priority:
        1. format_hint (explicit user-provided hint)
        2. file_data magic bytes (most reliable)
        3. file_name extension (fallback)

        Args:
            file_data: Binary file content for magic number detection
            file_name: File name for extension-based detection
            format_hint: Explicit format hint from user

        Returns:
            Detected format (lowercase, no dot) or None if unable to detect
        """
        # Priority 1: Explicit format hint
        if format_hint:
            normalized = self._normalize_format(format_hint)
            if self._is_valid_format(normalized):
                return normalized

        # Priority 2: Magic byte detection (most reliable)
        if file_data:
            detected = self._detect_from_magic_bytes(file_data)
            if detected:
                return detected

        # Priority 3: File extension fallback
        if file_name:
            detected = self._detect_from_filename(file_name)
            if detected:
                return detected

        return None

    def is_supported_format(self, format_str: str) -> bool:
        """
        Check if format is natively supported by Whisper.

        Args:
            format_str: Format string (e.g., 'mp3', 'wav', '.wav')

        Returns:
            True if Whisper can process this format directly
        """
        normalized = self._normalize_format(format_str)
        return normalized in self.WHISPER_NATIVE_FORMATS

    def is_convertible_format(self, format_str: str) -> bool:
        """
        Check if format can be converted to Whisper-compatible format.

        Args:
            format_str: Format string (e.g., 'wma', 'avi', '.wma')

        Returns:
            True if format can be converted using FFmpeg or similar
        """
        normalized = self._normalize_format(format_str)
        return normalized in self.CONVERTIBLE_FORMATS

    def _normalize_format(self, format_str: str) -> str:
        """
        Normalize format string (lowercase, remove leading dot).

        Args:
            format_str: Raw format string

        Returns:
            Normalized format (e.g., 'mp3', 'wav')
        """
        return format_str.lower().lstrip(".")

    def _is_valid_format(self, format_str: str) -> bool:
        """Check if format is either supported or convertible."""
        return (
            format_str in self.WHISPER_NATIVE_FORMATS
            or format_str in self.CONVERTIBLE_FORMATS
        )

    def _detect_from_magic_bytes(self, file_data: bytes) -> Optional[str]:
        """
        Detect format from magic byte signatures.

        Args:
            file_data: Binary file content

        Returns:
            Detected format or None
        """
        if len(file_data) < 12:
            return None

        # Check standard magic signatures
        for signature in self.MAGIC_SIGNATURES:
            if len(signature) == 5:  # (sig, offset, secondary, sec_offset, format)
                sig_bytes, offset, secondary, sec_offset, fmt = signature
                if file_data[offset:offset + len(sig_bytes)] == sig_bytes:
                    # Check secondary signature if present
                    if secondary and sec_offset is not None:
                        if file_data[sec_offset:sec_offset + len(secondary)] == secondary:
                            return fmt
                    else:
                        return fmt

        # Check ftyp-based formats (MP4, M4A, MOV)
        if len(file_data) >= 12:
            # ftyp is usually at offset 4
            if file_data[4:8] == b"ftyp":
                for ftyp_sig, fmt in self.FTYP_SIGNATURES:
                    if file_data[4:4 + len(ftyp_sig)] == ftyp_sig:
                        return fmt
                # Generic MP4 if ftyp present but no specific match
                return "mp4"

            # Direct ftyp at start (less common)
            for ftyp_sig, fmt in self.FTYP_SIGNATURES:
                if file_data.startswith(ftyp_sig):
                    return fmt

        # Check for webm in first 20 bytes (case-insensitive)
        if len(file_data) >= 20 and b"webm" in file_data[:20].lower():
            return "webm"

        return None

    def _detect_from_filename(self, file_name: str) -> Optional[str]:
        """
        Detect format from file extension.

        Args:
            file_name: File name with extension

        Returns:
            Detected format or None
        """
        if "." not in file_name:
            return None

        extension = file_name.lower().split(".")[-1]
        if self._is_valid_format(extension):
            return extension

        return None
