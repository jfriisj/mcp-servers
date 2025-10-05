#!/usr/bin/env python3
"""
Test script for Whisper MCP Server (Clean Architecture)
========================================================
Simple test suite using CompositionRoot instead of WhisperRunner.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from presentation.composition_root import CompositionRoot
from domain.models import (
    TranscriptionConfig,
    LanguageDetectionConfig,
)


async def test_composition_root():
    """Test CompositionRoot initialization."""
    print("Ì∑™ Testing CompositionRoot...")
    
    root = CompositionRoot()
    
    # Verify use cases are available
    assert hasattr(root, "transcribe_audio")
    assert hasattr(root, "detect_language")
    assert hasattr(root, "convert_audio")
    
    print("‚úÖ CompositionRoot tests passed")
    return root


async def test_configuration(root):
    """Test configuration."""
    print("Ì∑™ Testing Configuration...")
    
    config = root.get_configuration()
    whisper_config = config.get_whisper_config()
    
    assert "model" in whisper_config
    assert "device" in whisper_config
    
    print("‚úÖ Configuration tests passed")


async def main():
    """Run tests."""
    print("Ì∫Ä Whisper MCP Server Tests (Clean Architecture)\\n")
    
    try:
        root = await test_composition_root()
        await test_configuration(root)
        
        print("\\nÌæâ Tests passed! Using Clean Architecture ‚ú®")
        
    except Exception as e:
        print(f"\\n‚ùå Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
