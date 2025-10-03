"""
Data models for the Documentation and Prompts MCP Server
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class DocumentInfo:
    """Represents indexed document information"""

    path: str
    title: str
    content: str
    sections: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    last_modified: float
    file_hash: str
    doc_type: str
    links: List[str]
    code_blocks: List[Dict[str, str]]
    source_url: Optional[str] = None
    repo_name: Optional[str] = None
    repo_ref: Optional[str] = None
    download_timestamp: Optional[float] = None
    is_remote: bool = False


@dataclass
class PromptInfo:
    """Represents prompt information"""

    id: str
    name: str
    description: str
    category: str
    template: str
    variables: List[str]
    usage_count: int
    created_at: float
    modified_at: float
    tags: List[str]
    version: str
