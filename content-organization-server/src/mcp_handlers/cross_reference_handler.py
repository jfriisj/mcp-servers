"""Handler for cross-reference generation tool."""

from typing import Dict, Any, List
import logging
import os
from .base_handler import ContentOrganizationHandler

logger = logging.getLogger(__name__)

class CrossReferenceHandler(ContentOrganizationHandler):
    """Handler for generating cross-references."""
    
    async def handle_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle cross-reference generation request.
        
        Args:
            name: Tool name
            arguments: Tool arguments:
                - content_dir: Directory containing content
                - output_file: Optional path to save cross-reference data
                - reference_types: Types of references to generate
                - formats: File formats to analyze
                - depth: Maximum depth for reference chains
                - generate_graph: Whether to generate a reference graph
                - graph_format: Format for reference graph
                
        Returns:
            Cross-reference results or error response
        """
        try:
            # Extract arguments
            content_dir = arguments['content_dir']
            output_file = arguments.get('output_file')
            reference_types = arguments.get('reference_types', ['links', 'concepts'])
            formats = arguments.get('formats', ['md'])
            depth = arguments.get('depth', 2)
            generate_graph = arguments.get('generate_graph', False)
            graph_format = arguments.get('graph_format', 'json')
            
            # Generate cross-references
            result = await self.cross_referencer.generate_cross_references(
                content_dir=content_dir,
                reference_types=reference_types,
                formats=formats,
                depth=depth
            )
            
            if not result['success']:
                return result
            
            # Export references if output file specified
            if output_file:
                export_result = await self.cross_referencer.export_references(
                    output_file=output_file,
                    graph_format=graph_format
                )
                if not export_result['success']:
                    return export_result
                result['export'] = export_result
            
            # Generate documentation
            if generate_graph:
                docs_dir = os.path.dirname(output_file) if output_file else 'references'
                docs_result = await self.cross_referencer.generate_reference_docs(
                    output_dir=docs_dir
                )
                if not docs_result['success']:
                    return docs_result
                result['documentation'] = docs_result
            
            # Add reference statistics
            result['statistics'] = self.cross_referencer.get_reference_stats()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate cross-references: {str(e)}")
            return self._format_error(e)