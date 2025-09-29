"""File reorganization functionality."""

import os
import shutil
import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import fnmatch
import re
from dataclasses import dataclass

from .common_utils import (
    FileInfo,
    get_file_info,
    find_files,
    validate_file_operations,
    OrganizationError,
    FileSystemError
)

logger = logging.getLogger(__name__)

@dataclass
class FileOperation:
    """Represents a file operation."""
    source: str
    target: str
    operation: str  # 'move', 'copy', 'categorize', 'rename'
    rule: Dict[str, Any]

class FileReorganizer:
    """Handles file reorganization operations."""
    
    def __init__(self):
        """Initialize the file reorganizer."""
        self.operations: List[FileOperation] = []
        self.processed_files: List[str] = []
    
    def _validate_rule(self, rule: Dict[str, Any]) -> None:
        """
        Validate an organization rule.
        
        Args:
            rule: Rule to validate
            
        Raises:
            ValueError: If rule is invalid
        """
        required_fields = {'pattern', 'action'}
        if not all(field in rule for field in required_fields):
            raise ValueError(
                f"Rule must contain all required fields: {required_fields}"
            )
        
        valid_actions = {'move', 'copy', 'categorize', 'rename'}
        if rule['action'] not in valid_actions:
            raise ValueError(
                f"Invalid action '{rule['action']}'. Must be one of: {valid_actions}"
            )
        
        if rule['action'] == 'rename' and 'rename_template' not in rule:
            raise ValueError("Rename action requires 'rename_template' field")
    
    def _validate_rename_template(
        self,
        template: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Validate that a rename template can be applied.
        
        Args:
            template: Rename template
            metadata: File metadata
            
        Returns:
            True if template can be applied, False otherwise
        """
        try:
            # Extract template variables
            variables = re.findall(r'\{([^}]+)\}', template)
            
            # Check if all required variables are available
            required_vars = {v for v in variables if not v.startswith('base')}
            available_vars = set(metadata.keys()) | {'name', 'ext'}
            
            return all(v in available_vars for v in required_vars)
        except Exception:
            return False
    
    def _apply_rename_template(
        self,
        template: str,
        file_info: FileInfo
    ) -> str:
        """
        Apply rename template to generate new filename.
        
        Args:
            template: Rename template
            file_info: File information
            
        Returns:
            New filename
        """
        name = os.path.basename(file_info.path)
        base, ext = os.path.splitext(name)
        
        # Basic template variables
        variables = {
            'name': name,
            'base': base,
            'ext': ext,
            **file_info.metadata
        }
        
        # Handle base name transformations
        for match in re.finditer(r'\{base\.([^}]+)\}', template):
            transform = match.group(1)
            if transform == 'lower':
                variables[f'base.{transform}'] = base.lower()
            elif transform == 'upper':
                variables[f'base.{transform}'] = base.upper()
            elif transform == 'title':
                variables[f'base.{transform}'] = base.title()
            elif transform.startswith('prefix:'):
                prefix = transform.split(':', 1)[1]
                variables[f'base.{transform}'] = f"{prefix}{base}"
            elif transform.startswith('suffix:'):
                suffix = transform.split(':', 1)[1]
                variables[f'base.{transform}'] = f"{base}{suffix}"
        
        return template.format(**variables)
    
    async def plan_reorganization(
        self,
        source_dir: str,
        target_dir: str,
        rules: List[Dict[str, Any]],
        recursive: bool = True
    ) -> List[FileOperation]:
        """
        Plan file reorganization operations.
        
        Args:
            source_dir: Source directory
            target_dir: Target directory
            rules: List of organization rules
            recursive: Whether to process subdirectories
            
        Returns:
            List of planned operations
            
        Raises:
            OrganizationError: If planning fails
        """
        try:
            # Validate rules
            for rule in rules:
                self._validate_rule(rule)
            
            # Find all files
            patterns = [rule['pattern'] for rule in rules]
            files = await find_files(source_dir, patterns, recursive)
            
            operations = []
            for file_path in files:
                file_info = get_file_info(file_path, source_dir)
                
                # Find matching rules
                for rule in rules:
                    if not fnmatch.fnmatch(file_path, rule['pattern']):
                        continue
                    
                    # Determine target path based on action
                    if rule['action'] == 'categorize':
                        target_subdir = os.path.join(
                            target_dir,
                            rule.get('target_subdir', ''),
                            file_info.content_type
                        )
                        target_path = os.path.join(
                            target_subdir,
                            os.path.basename(file_path)
                        )
                    
                    elif rule['action'] == 'rename':
                        template = rule['rename_template']
                        if not self._validate_rename_template(template, file_info.metadata):
                            logger.warning(
                                f"Cannot apply rename template to {file_path}: "
                                "missing required metadata"
                            )
                            continue
                            
                        new_name = self._apply_rename_template(template, file_info)
                        target_path = os.path.join(
                            target_dir,
                            rule.get('target_subdir', ''),
                            new_name
                        )
                    
                    else:  # move or copy
                        target_path = os.path.join(
                            target_dir,
                            rule.get('target_subdir', ''),
                            os.path.basename(file_path)
                        )
                    
                    operations.append(FileOperation(
                        source=file_path,
                        target=target_path,
                        operation=rule['action'],
                        rule=rule
                    ))
            
            self.operations = operations
            return operations
            
        except Exception as e:
            raise OrganizationError(f"Failed to plan reorganization: {str(e)}")
    
    def _create_operation_tuples(
        self
    ) -> List[Tuple[str, str, str]]:
        """
        Create operation tuples for validation.
        
        Returns:
            List of (source, target, operation) tuples
        """
        return [
            (op.source, op.target, op.operation)
            for op in self.operations
        ]
    
    def validate_operations(self) -> List[Tuple[str, str]]:
        """
        Validate planned operations for conflicts.
        
        Returns:
            List of conflicting file pairs
        """
        return validate_file_operations(self._create_operation_tuples())
    
    async def execute_reorganization(
        self,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Execute planned reorganization operations.
        
        Args:
            dry_run: Whether to simulate execution
            
        Returns:
            Dictionary containing execution results
            
        Raises:
            OrganizationError: If execution fails
        """
        if not self.operations:
            return {
                'success': True,
                'operations_executed': 0,
                'files_affected': 0,
                'dry_run': dry_run
            }
        
        # Check for conflicts
        conflicts = self.validate_operations()
        if conflicts:
            raise OrganizationError(
                f"Found {len(conflicts)} file conflicts: {conflicts}"
            )
        
        executed_ops = []
        try:
            for operation in self.operations:
                target_dir = os.path.dirname(operation.target)
                
                if not dry_run:
                    # Ensure target directory exists
                    os.makedirs(target_dir, exist_ok=True)
                    
                    # Execute operation
                    if operation.operation == 'copy':
                        shutil.copy2(operation.source, operation.target)
                    elif operation.operation in {'move', 'categorize', 'rename'}:
                        shutil.move(operation.source, operation.target)
                
                executed_ops.append({
                    'source': operation.source,
                    'target': operation.target,
                    'operation': operation.operation,
                    'dry_run': dry_run
                })
                
                if not dry_run:
                    self.processed_files.append(operation.target)
            
            return {
                'success': True,
                'operations_executed': len(executed_ops),
                'files_affected': len(set(op['source'] for op in executed_ops)),
                'dry_run': dry_run,
                'operations': executed_ops
            }
            
        except Exception as e:
            raise OrganizationError(f"Failed to execute reorganization: {str(e)}")
    
    def undo_reorganization(self) -> Dict[str, Any]:
        """
        Undo the last reorganization operation.
        
        Returns:
            Dictionary containing undo results
            
        Raises:
            OrganizationError: If undo fails
        """
        if not self.processed_files:
            return {
                'success': True,
                'files_restored': 0,
                'message': "No operations to undo"
            }
        
        restored = []
        failed = []
        
        try:
            for operation in reversed(self.operations):
                try:
                    if os.path.exists(operation.target):
                        if operation.operation == 'copy':
                            os.remove(operation.target)
                        else:
                            shutil.move(operation.target, operation.source)
                        restored.append(operation.target)
                except Exception as e:
                    logger.error(f"Failed to undo {operation.target}: {str(e)}")
                    failed.append(operation.target)
            
            return {
                'success': len(failed) == 0,
                'files_restored': len(restored),
                'failed_files': len(failed),
                'restored': restored,
                'failed': failed
            }
            
        except Exception as e:
            raise OrganizationError(f"Failed to undo reorganization: {str(e)}")