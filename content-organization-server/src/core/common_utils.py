"""Common utilities for content organization operations."""

import os
import re
import glob
import json
import yaml
import fnmatch
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
import aiofiles
import frontmatter
from bs4 import BeautifulSoup
import markdown
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class OrganizationError(Exception):
    """Base exception for content organization errors."""
    pass

class FileSystemError(OrganizationError):
    """Exception for file system operation failures."""
    pass

class ValidationError(OrganizationError):
    """Exception for content validation failures."""
    pass

class ParseError(OrganizationError):
    """Exception for content parsing failures."""
    pass

@dataclass
class FileInfo:
    """Information about a file."""
    path: str
    relative_path: str
    content_type: str
    metadata: Dict[str, Any]
    size: int
    modified_time: float

async def read_file_content(path: str) -> str:
    """
    Read file content asynchronously.
    
    Args:
        path: Path to the file
        
    Returns:
        File content as string
        
    Raises:
        FileSystemError: If file cannot be read
    """
    try:
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            return await f.read()
    except Exception as e:
        raise FileSystemError(f"Failed to read file {path}: {str(e)}")

async def write_file_content(path: str, content: str) -> None:
    """
    Write content to file asynchronously.
    
    Args:
        path: Path to write to
        content: Content to write
        
    Raises:
        FileSystemError: If file cannot be written
    """
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(content)
    except Exception as e:
        raise FileSystemError(f"Failed to write file {path}: {str(e)}")

def get_file_info(path: str, base_dir: str) -> FileInfo:
    """
    Get information about a file.
    
    Args:
        path: Path to the file
        base_dir: Base directory for relative path calculation
        
    Returns:
        FileInfo object
        
    Raises:
        FileSystemError: If file information cannot be retrieved
    """
    try:
        stat = os.stat(path)
        relative_path = os.path.relpath(path, base_dir)
        content_type = determine_content_type(path)
        metadata = extract_metadata(path, content_type)
        
        return FileInfo(
            path=path,
            relative_path=relative_path,
            content_type=content_type,
            metadata=metadata,
            size=stat.st_size,
            modified_time=stat.st_mtime
        )
    except Exception as e:
        raise FileSystemError(f"Failed to get file info for {path}: {str(e)}")

def determine_content_type(path: str) -> str:
    """
    Determine content type from file extension.
    
    Args:
        path: Path to the file
        
    Returns:
        Content type string
    """
    ext = os.path.splitext(path)[1].lower()
    return {
        '.md': 'markdown',
        '.rst': 'restructuredtext',
        '.txt': 'text',
        '.py': 'python',
        '.ipynb': 'notebook',
        '.pdf': 'pdf'
    }.get(ext, 'unknown')

def extract_metadata(path: str, content_type: str) -> Dict[str, Any]:
    """
    Extract metadata from file content.
    
    Args:
        path: Path to the file
        content_type: Type of content
        
    Returns:
        Dictionary of metadata
    """
    try:
        if content_type == 'markdown':
            with open(path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                return post.metadata
        # Add support for other content types as needed
        return {}
    except Exception as e:
        logger.warning(f"Failed to extract metadata from {path}: {str(e)}")
        return {}

async def find_files(
    directory: str,
    patterns: List[str],
    recursive: bool = True
) -> List[str]:
    """
    Find files matching patterns in directory.
    
    Args:
        directory: Directory to search
        patterns: List of glob patterns to match
        recursive: Whether to search recursively
        
    Returns:
        List of matching file paths
        
    Raises:
        FileSystemError: If directory cannot be searched
    """
    try:
        matches = []
        for pattern in patterns:
            if recursive:
                for root, _, files in os.walk(directory):
                    for file in fnmatch.filter(files, pattern):
                        matches.append(os.path.join(root, file))
            else:
                matches.extend(glob.glob(os.path.join(directory, pattern)))
        return sorted(set(matches))
    except Exception as e:
        raise FileSystemError(f"Failed to search directory {directory}: {str(e)}")

def evaluate_organization_rule(
    file_info: FileInfo,
    rule: Dict[str, Any]
) -> Optional[str]:
    """
    Evaluate an organization rule against a file.
    
    Args:
        file_info: Information about the file
        rule: Organization rule to evaluate
        
    Returns:
        Target path if rule matches, None otherwise
    """
    try:
        if not fnmatch.fnmatch(file_info.path, rule['pattern']):
            return None
            
        if rule['action'] == 'categorize':
            return os.path.join(
                rule.get('target_subdir', ''),
                file_info.content_type,
                os.path.basename(file_info.path)
            )
        elif rule['action'] in ['move', 'copy']:
            return os.path.join(
                rule.get('target_subdir', ''),
                os.path.basename(file_info.path)
            )
        elif rule['action'] == 'rename':
            template = rule.get('rename_template')
            if template:
                # Basic template substitution
                name = os.path.basename(file_info.path)
                base, ext = os.path.splitext(name)
                return template.format(
                    name=name,
                    base=base,
                    ext=ext,
                    **file_info.metadata
                )
        return None
    except Exception as e:
        logger.warning(f"Failed to evaluate rule for {file_info.path}: {str(e)}")
        return None

def extract_references(content: str, content_type: str) -> Set[str]:
    """
    Extract references from content.
    
    Args:
        content: Content to analyze
        content_type: Type of content
        
    Returns:
        Set of extracted references
    """
    references = set()
    
    if content_type == 'markdown':
        # Convert markdown to HTML for easier parsing
        html = markdown.markdown(content)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all links
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                references.add(href)
        
        # Find all images
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                references.add(src)
                
        # Find inline references [ref]
        references.update(re.findall(r'\[(.*?)\]', content))
    
    return references

async def load_yaml_file(path: str) -> Dict[str, Any]:
    """
    Load YAML file asynchronously.
    
    Args:
        path: Path to YAML file
        
    Returns:
        Parsed YAML content
        
    Raises:
        FileSystemError: If file cannot be read or parsed
    """
    try:
        content = await read_file_content(path)
        return yaml.safe_load(content)
    except Exception as e:
        raise FileSystemError(f"Failed to load YAML file {path}: {str(e)}")

async def load_json_file(path: str) -> Dict[str, Any]:
    """
    Load JSON file asynchronously.
    
    Args:
        path: Path to JSON file
        
    Returns:
        Parsed JSON content
        
    Raises:
        FileSystemError: If file cannot be read or parsed
    """
    try:
        content = await read_file_content(path)
        return json.loads(content)
    except Exception as e:
        raise FileSystemError(f"Failed to load JSON file {path}: {str(e)}")

def validate_file_operations(
    operations: List[Tuple[str, str, str]]
) -> List[Tuple[str, str]]:
    """
    Validate file operations for conflicts.
    
    Args:
        operations: List of (source, target, operation) tuples
        
    Returns:
        List of (file1, file2) tuples representing conflicts
        
    Example:
        >>> ops = [
        ...     ('a.txt', 'out/a.txt', 'move'),
        ...     ('b.txt', 'out/a.txt', 'move')
        ... ]
        >>> validate_file_operations(ops)
        [('b.txt', 'a.txt')]  # Conflict: both try to move to same target
    """
    conflicts = []
    targets = {}
    
    for source, target, op in operations:
        if target in targets:
            conflicts.append((source, targets[target]))
        else:
            targets[target] = source
    
    return conflicts