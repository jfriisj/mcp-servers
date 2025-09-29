"""Handler for file reorganization tool."""

from typing import Dict, Any, List
import logging
import os
from .base_handler import ContentOrganizationHandler

logger = logging.getLogger(__name__)

class FileReorganizationHandler(ContentOrganizationHandler):
    """Handler for file reorganization operations."""
    
    async def handle_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle file reorganization request.
        
        Args:
            name: Tool name
            arguments: Tool arguments:
                - source_dir: Source directory
                - target_dir: Target directory
                - organization_rules: List of organization rules
                - recursive: Whether to process subdirectories
                - dry_run: Whether to simulate execution
                
        Returns:
            Reorganization results or error response
        """
        try:
            # Extract arguments
            source_dir = arguments['source_dir']
            target_dir = arguments['target_dir']
            rules = arguments['organization_rules']
            recursive = arguments.get('recursive', True)
            dry_run = arguments.get('dry_run', False)
            
            # Plan reorganization
            operations = await self.file_reorganizer.plan_reorganization(
                source_dir=source_dir,
                target_dir=target_dir,
                rules=rules,
                recursive=recursive
            )
            
            # Check for conflicts
            conflicts = self.file_reorganizer.validate_operations()
            if conflicts:
                return {
                    'success': False,
                    'error_code': 'FILE_CONFLICT',
                    'error_message': f"Found {len(conflicts)} file conflicts",
                    'conflicts': conflicts
                }
            
            # Execute reorganization
            result = await self.file_reorganizer.execute_reorganization(dry_run=dry_run)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to reorganize files: {str(e)}")
            return self._format_error(e)