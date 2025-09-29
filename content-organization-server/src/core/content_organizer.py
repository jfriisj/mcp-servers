"""Content organization functionality for course materials."""

import os
import logging
from typing import List, Dict, Any, Optional, Set
import frontmatter
import yaml
from pathlib import Path

from .common_utils import (
    FileInfo,
    get_file_info,
    read_file_content,
    write_file_content,
    find_files,
    load_yaml_file,
    load_json_file,
    OrganizationError,
    ValidationError
)

logger = logging.getLogger(__name__)

class ContentOrganizer:
    """Handles organization of course content."""
    
    def __init__(self):
        """Initialize the content organizer."""
        self.current_template: Optional[Dict[str, Any]] = None
        self.metadata_schema: Optional[Dict[str, Any]] = None
        self.processed_files: Set[str] = set()
    
    async def load_structure_template(self, template_path: str) -> None:
        """
        Load content structure template from YAML file.
        
        Args:
            template_path: Path to template file
            
        Raises:
            ValidationError: If template is invalid
            FileSystemError: If template file cannot be read
        """
        template = await load_yaml_file(template_path)
        
        if not isinstance(template, dict):
            raise ValidationError("Invalid template format: must be a dictionary")
        
        required_keys = {'sections', 'metadata_fields'}
        if not all(key in template for key in required_keys):
            raise ValidationError(
                f"Template must contain all required keys: {required_keys}"
            )
        
        self.current_template = template
    
    async def load_metadata_schema(self, schema_path: str) -> None:
        """
        Load metadata schema from JSON file.
        
        Args:
            schema_path: Path to schema file
            
        Raises:
            ValidationError: If schema is invalid
            FileSystemError: If schema file cannot be read
        """
        schema = await load_json_file(schema_path)
        
        if not isinstance(schema, dict):
            raise ValidationError("Invalid schema format: must be a dictionary")
        
        if 'type' not in schema or schema['type'] != 'object':
            raise ValidationError("Schema must be a JSON Schema object type")
        
        self.metadata_schema = schema
    
    def _validate_content_type(self, content_type: str) -> bool:
        """
        Validate if content type is supported.
        
        Args:
            content_type: Content type to validate
            
        Returns:
            True if supported, False otherwise
        """
        return content_type in {
            'markdown',
            'pdf',
            'code',
            'exercises',
            'examples'
        }
    
    async def _process_content_file(
        self,
        file_info: FileInfo,
        target_dir: str
    ) -> Dict[str, Any]:
        """
        Process a single content file.
        
        Args:
            file_info: Information about the file
            target_dir: Target directory for processed content
            
        Returns:
            Dictionary containing processing results
            
        Raises:
            OrganizationError: If content processing fails
        """
        if not self._validate_content_type(file_info.content_type):
            raise ValidationError(f"Unsupported content type: {file_info.content_type}")
        
        try:
            # Read content
            content = await read_file_content(file_info.path)
            
            # Process based on content type
            if file_info.content_type == 'markdown':
                return await self._process_markdown(content, file_info, target_dir)
            elif file_info.content_type == 'code':
                return await self._process_code(content, file_info, target_dir)
            else:
                # For other types, just copy with metadata
                target_path = os.path.join(target_dir, file_info.relative_path)
                await write_file_content(target_path, content)
                return {
                    'path': target_path,
                    'content_type': file_info.content_type,
                    'metadata': file_info.metadata
                }
                
        except Exception as e:
            raise OrganizationError(
                f"Failed to process {file_info.path}: {str(e)}"
            )
    
    async def _process_markdown(
        self,
        content: str,
        file_info: FileInfo,
        target_dir: str
    ) -> Dict[str, Any]:
        """
        Process markdown content.
        
        Args:
            content: File content
            file_info: File information
            target_dir: Target directory
            
        Returns:
            Processing results
        """
        # Parse frontmatter
        post = frontmatter.loads(content)
        metadata = post.metadata
        
        # Validate metadata if schema is available
        if self.metadata_schema:
            # TODO: Implement JSON Schema validation
            pass
        
        # Determine target section based on metadata
        section = self._determine_section(metadata)
        if section:
            target_dir = os.path.join(target_dir, section)
        
        # Write processed content
        target_path = os.path.join(target_dir, file_info.relative_path)
        await write_file_content(target_path, frontmatter.dumps(post))
        
        return {
            'path': target_path,
            'content_type': 'markdown',
            'metadata': metadata,
            'section': section
        }
    
    async def _process_code(
        self,
        content: str,
        file_info: FileInfo,
        target_dir: str
    ) -> Dict[str, Any]:
        """
        Process code content.
        
        Args:
            content: File content
            file_info: File information
            target_dir: Target directory
            
        Returns:
            Processing results
        """
        # Extract code-specific metadata (e.g., from comments)
        metadata = self._extract_code_metadata(content)
        
        # Determine target location
        target_path = os.path.join(
            target_dir,
            'code',
            file_info.relative_path
        )
        
        # Write processed content
        await write_file_content(target_path, content)
        
        return {
            'path': target_path,
            'content_type': 'code',
            'metadata': metadata
        }
    
    def _determine_section(self, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Determine content section based on metadata.
        
        Args:
            metadata: Content metadata
            
        Returns:
            Section name or None
        """
        if not self.current_template:
            return None
            
        sections = self.current_template.get('sections', {})
        for section, rules in sections.items():
            if self._matches_section_rules(metadata, rules):
                return section
        
        return None
    
    def _matches_section_rules(
        self,
        metadata: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> bool:
        """
        Check if metadata matches section rules.
        
        Args:
            metadata: Content metadata
            rules: Section rules
            
        Returns:
            True if matches, False otherwise
        """
        required_fields = rules.get('required_fields', {})
        for field, value in required_fields.items():
            if field not in metadata or metadata[field] != value:
                return False
        
        return True
    
    def _extract_code_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata from code content.
        
        Args:
            content: Code content
            
        Returns:
            Extracted metadata
        """
        # Basic implementation - extract from top comments
        metadata = {}
        lines = content.split('\n')
        
        # Look for metadata in comments at the start of the file
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                # Look for key-value pairs in comments
                parts = line[1:].strip().split(':', 1)
                if len(parts) == 2:
                    key, value = parts
                    metadata[key.strip()] = value.strip()
            elif line and not line.startswith('#'):
                break
        
        return metadata
    
    async def generate_index(
        self,
        processed_files: List[Dict[str, Any]],
        output_dir: str
    ) -> None:
        """
        Generate index files for organized content.
        
        Args:
            processed_files: List of processed file results
            output_dir: Output directory
            
        Raises:
            OrganizationError: If index generation fails
        """
        try:
            # Group files by section
            sections: Dict[str, List[Dict[str, Any]]] = {}
            for file in processed_files:
                section = file.get('section', 'unsorted')
                if section not in sections:
                    sections[section] = []
                sections[section].append(file)
            
            # Generate main index
            main_index = ["# Content Index\n"]
            for section, files in sections.items():
                main_index.append(f"\n## {section.title()}\n")
                for file in sorted(files, key=lambda x: x['path']):
                    rel_path = os.path.relpath(file['path'], output_dir)
                    title = file['metadata'].get('title', os.path.basename(file['path']))
                    main_index.append(f"- [{title}]({rel_path})")
            
            # Write main index
            await write_file_content(
                os.path.join(output_dir, 'index.md'),
                '\n'.join(main_index)
            )
            
            # Generate section indexes
            for section, files in sections.items():
                if section == 'unsorted':
                    continue
                    
                section_index = [f"# {section.title()}\n"]
                for file in sorted(files, key=lambda x: x['path']):
                    rel_path = os.path.relpath(file['path'], os.path.join(output_dir, section))
                    title = file['metadata'].get('title', os.path.basename(file['path']))
                    desc = file['metadata'].get('description', '')
                    section_index.extend([
                        f"## {title}\n",
                        f"{desc}\n" if desc else "",
                        f"[View content]({rel_path})\n"
                    ])
                
                await write_file_content(
                    os.path.join(output_dir, section, 'index.md'),
                    '\n'.join(section_index)
                )
                
        except Exception as e:
            raise OrganizationError(f"Failed to generate indexes: {str(e)}")
    
    async def organize_content(
        self,
        content_dir: str,
        output_dir: str,
        content_types: Optional[List[str]] = None,
        preserve_original: bool = True,
        generate_index: bool = True
    ) -> Dict[str, Any]:
        """
        Organize course content according to template.
        
        Args:
            content_dir: Source content directory
            output_dir: Output directory
            content_types: List of content types to process
            preserve_original: Whether to preserve original files
            generate_index: Whether to generate index files
            
        Returns:
            Dictionary containing organization results
            
        Raises:
            OrganizationError: If organization fails
        """
        try:
            content_types = content_types or ['markdown']
            patterns = ['*.md', '*.py', '*.ipynb', '*.pdf']  # Add more as needed
            
            # Find all content files
            files = await find_files(content_dir, patterns, recursive=True)
            
            # Process each file
            processed_files = []
            for file_path in files:
                file_info = get_file_info(file_path, content_dir)
                
                if file_info.content_type not in content_types:
                    continue
                
                result = await self._process_content_file(file_info, output_dir)
                processed_files.append(result)
                self.processed_files.add(file_path)
            
            # Generate indexes if requested
            if generate_index:
                await self.generate_index(processed_files, output_dir)
            
            # Clean up if not preserving originals
            if not preserve_original:
                for file_path in self.processed_files:
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"Failed to remove {file_path}: {str(e)}")
            
            return {
                'success': True,
                'files_processed': len(processed_files),
                'output_directory': output_dir,
                'results': processed_files
            }
            
        except Exception as e:
            raise OrganizationError(f"Content organization failed: {str(e)}")