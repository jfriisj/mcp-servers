"""
Data models for the Documentation and Prompts MCP Server
"""
from dataclasses import dataclass
from typing import Dict, List, Any


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
