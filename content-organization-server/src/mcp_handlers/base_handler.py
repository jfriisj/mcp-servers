"""Base handler for content organization tools."""

from typing import Dict, Any, List
import json
import logging
from mcp_base.mcp_handler import MCPHandler
from ..core.content_organizer import ContentOrganizer
from ..core.file_reorganizer import FileReorganizer
from ..core.cross_referencer import CrossReferencer
from ..core.common_utils import OrganizationError, ValidationError, FileSystemError

logger = logging.getLogger(__name__)

class ContentOrganizationHandler(MCPHandler):
    """Base handler for content organization tools."""
    
    def __init__(self):
        """Initialize the content organization handler."""
        super().__init__()
        self.content_organizer = ContentOrganizer()
        self.file_reorganizer = FileReorganizer()
        self.cross_referencer = CrossReferencer()
    
    def _format_error(self, error: Exception) -> Dict[str, Any]:
        """
        Format error response.
        
        Args:
            error: The error that occurred
            
        Returns:
            Error response dictionary
        """
        if isinstance(error, ValidationError):
            return {
                'success': False,
                'error_code': 'VALIDATION_ERROR',
                'error_message': str(error)
            }
        elif isinstance(error, FileSystemError):
            return {
                'success': False,
                'error_code': 'FS_ERROR',
                'error_message': str(error)
            }
        elif isinstance(error, OrganizationError):
            return {
                'success': False,
                'error_code': 'ORGANIZATION_ERROR',
                'error_message': str(error)
            }
        else:
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'error_message': f"An unexpected error occurred: {str(error)}"
            }
    
    async def handle_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tool execution.
        
        Args:
            name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution results
            
        Raises:
            NotImplementedError: If tool is not implemented
        """
        raise NotImplementedError(f"Tool {name} is not implemented")