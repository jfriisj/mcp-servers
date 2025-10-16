"""
Content Extraction Service Implementation

Handles extraction of text content from various file formats.
Follows SRP by only handling content extraction.
"""

import os
from pathlib import Path
from typing import Optional
import logging

from domain.services.chunking_service import IContentExtractionService
from domain.models import ResearchPaper

logger = logging.getLogger(__name__)


class ContentExtractionService(IContentExtractionService):
    """
    Content extraction service implementation.
    
    Follows SOLID principles:
    - Single Responsibility: Only handles content extraction
    - Open/Closed: Can be extended with new file format handlers
    - Dependency Inversion: Implements interface, not concrete dependency
    """
    
    def extract_paper_content(self, paper: ResearchPaper) -> str:
        """Extract text content from paper file."""
        # Start with basic metadata
        content = f"Title: {paper.title}\n\n"
        if paper.abstract:
            content += f"Abstract: {paper.abstract}\n\n"
        
        # Try to extract from actual file if available
        if paper.file_path and os.path.exists(paper.file_path):
            try:
                file_path = Path(paper.file_path)
                file_extension = file_path.suffix.lower()
                
                if file_extension == '.pdf':
                    content += self.extract_from_pdf(paper.file_path)
                elif file_extension in ['.txt', '.md']:
                    content += self.extract_from_text_file(paper.file_path)
                elif file_extension in ['.doc', '.docx']:
                    content += self.extract_from_word_doc(paper.file_path)
                else:
                    # Fallback for unknown file types
                    content += f"[Note: File type {file_extension} not fully supported, using metadata only]"
                    
            except Exception as e:
                # If file extraction fails, log the error and continue with metadata
                logger.warning(f"Could not extract full text from file {paper.file_path}: {str(e)}")
                content += f"[Note: Could not extract full text from file: {str(e)}]"
        else:
            # No file available, use metadata only
            if paper.keywords:
                content += f"Keywords: {', '.join(paper.keywords)}\n\n"
            
            content += "[Note: Full text not available, using metadata only]"
        
        return content.strip()
    
    def extract_from_pdf(self, file_path: str) -> str:
        """Extract text content from PDF file."""
        try:
            # Try pymupdf first (better text extraction)
            import fitz
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text.strip()
            
        except ImportError:
            # Fallback to PyPDF2 if pymupdf not available
            return self._extract_pdf_with_pypdf2(file_path)
        except Exception as e:
            # If pymupdf fails, try PyPDF2
            logger.warning(f"PyMuPDF extraction failed for {file_path}, trying PyPDF2: {str(e)}")
            return self._extract_pdf_with_pypdf2(file_path)
    
    def extract_from_text_file(self, file_path: str) -> str:
        """Extract content from text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except UnicodeDecodeError:
            # Try different encodings
            encodings = ['latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read().strip()
                except UnicodeDecodeError:
                    continue
            logger.error(f"Could not decode text file {file_path} with any encoding")
            return "[Text file encoding not supported]"
        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {str(e)}")
            return f"[Text extraction failed: {str(e)}]"
    
    def extract_from_word_doc(self, file_path: str) -> str:
        """Extract content from Word document."""
        try:
            # Try to import python-docx if available
            import docx
            doc = docx.Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return '\n'.join(text).strip()
        except ImportError:
            logger.warning(f"python-docx not available for Word document extraction: {file_path}")
            return "[Word document extraction requires python-docx package]"
        except Exception as e:
            logger.error(f"Word document extraction failed for {file_path}: {str(e)}")
            return f"[Word document extraction failed: {str(e)}]"
    
    def _extract_pdf_with_pypdf2(self, file_path: str) -> str:
        """Fallback PDF extraction using PyPDF2."""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed for {file_path}: {str(e)}")
            return f"[PDF extraction failed: {str(e)}]"