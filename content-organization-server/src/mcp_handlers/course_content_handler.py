"""Handler for course content organization tool."""

from typing import Dict, Any, List, Optional
import logging
import os
from .base_handler import ContentOrganizationHandler

logger = logging.getLogger(__name__)

class CourseContentHandler(ContentOrganizationHandler):
    """Handler for organizing course content."""
    
    async def handle_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle course content organization request.
        
        Args:
            name: Tool name
            arguments: Tool arguments:
                - content_dir: Directory containing course content
                - output_dir: Directory where organized content should be saved
                - structure_template: Optional path to structure template
                - metadata_schema: Optional path to metadata schema
                - content_types: Optional list of content types to process
                - preserve_original: Whether to preserve original files
                - generate_index: Whether to generate index files
                
        Returns:
            Organization results or error response
        """
        try:
            # Extract arguments
            content_dir = arguments['content_dir']
            output_dir = arguments['output_dir']
            structure_template = arguments.get('structure_template')
            metadata_schema = arguments.get('metadata_schema')
            content_types = arguments.get('content_types', ['markdown'])
            preserve_original = arguments.get('preserve_original', True)
            generate_index = arguments.get('generate_index', True)
            
            # Load templates and schemas if provided
            if structure_template:
                await self.content_organizer.load_structure_template(structure_template)
            
            if metadata_schema:
                await self.content_organizer.load_metadata_schema(metadata_schema)
            
            # Organize content
            result = await self.content_organizer.organize_content(
                content_dir=content_dir,
                output_dir=output_dir,
                content_types=content_types,
                preserve_original=preserve_original,
                generate_index=generate_index
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to organize course content: {str(e)}")
            return self._format_error(e)