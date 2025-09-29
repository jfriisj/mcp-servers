"""Cross-reference generation functionality."""

import os
import json
import logging
from typing import List, Dict, Any, Set, Optional
import networkx as nx
from pathlib import Path
from dataclasses import dataclass
import markdown
from bs4 import BeautifulSoup

from .common_utils import (
    FileInfo,
    get_file_info,
    read_file_content,
    write_file_content,
    find_files,
    extract_references,
    OrganizationError,
    ParseError
)

logger = logging.getLogger(__name__)

@dataclass
class Reference:
    """Represents a content reference."""
    source: str
    target: str
    ref_type: str  # 'link', 'citation', 'dependency', 'concept'
    context: str
    metadata: Dict[str, Any]

class CrossReferencer:
    """Handles cross-reference generation between content."""
    
    def __init__(self):
        """Initialize the cross referencer."""
        self.references: List[Reference] = []
        self.graph = nx.DiGraph()
        self.processed_files: Set[str] = set()
    
    def _extract_concepts(self, content: str) -> Set[str]:
        """
        Extract concepts from content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Set of concept identifiers
        """
        concepts = set()
        
        # Look for concept markers like [[concept]]
        matches = re.findall(r'\[\[(.*?)\]\]', content)
        concepts.update(matches)
        
        # Look for #concept tags
        matches = re.findall(r'#(\w+)', content)
        concepts.update(matches)
        
        return concepts
    
    def _extract_citations(self, content: str) -> List[Dict[str, str]]:
        """
        Extract citations from content.
        
        Args:
            content: Content to analyze
            
        Returns:
            List of citation information
        """
        citations = []
        
        # Look for citation patterns like [cite:key]
        matches = re.findall(r'\[cite:(.*?)\]', content)
        for key in matches:
            citations.append({
                'type': 'citation',
                'key': key
            })
        
        # Look for reference-style citations like [1], [2], etc.
        matches = re.findall(r'\[(\d+)\]', content)
        for num in matches:
            citations.append({
                'type': 'reference',
                'number': num
            })
        
        return citations
    
    def _extract_dependencies(self, content: str, file_path: str) -> List[str]:
        """
        Extract dependencies from content.
        
        Args:
            content: Content to analyze
            file_path: Path to the file
            
        Returns:
            List of dependency paths
        """
        dependencies = []
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.py':
            # Extract Python imports
            imports = re.findall(r'^(?:from|import)\s+(\S+)', content, re.MULTILINE)
            dependencies.extend(imports)
            
        elif ext == '.ipynb':
            # Extract notebook dependencies
            try:
                nb = json.loads(content)
                for cell in nb.get('cells', []):
                    if cell['cell_type'] == 'code':
                        code = ''.join(cell['source'])
                        imports = re.findall(r'^(?:from|import)\s+(\S+)', code, re.MULTILINE)
                        dependencies.extend(imports)
            except Exception as e:
                logger.warning(f"Failed to parse notebook {file_path}: {str(e)}")
        
        return dependencies
    
    async def _process_file(
        self,
        file_info: FileInfo,
        reference_types: List[str]
    ) -> List[Reference]:
        """
        Process a single file for references.
        
        Args:
            file_info: Information about the file
            reference_types: Types of references to extract
            
        Returns:
            List of found references
            
        Raises:
            ParseError: If file processing fails
        """
        try:
            content = await read_file_content(file_info.path)
            references = []
            
            if 'links' in reference_types:
                # Extract links using common utils
                links = extract_references(content, file_info.content_type)
                for link in links:
                    references.append(Reference(
                        source=file_info.path,
                        target=link,
                        ref_type='link',
                        context='',
                        metadata={}
                    ))
            
            if 'concepts' in reference_types:
                concepts = self._extract_concepts(content)
                for concept in concepts:
                    references.append(Reference(
                        source=file_info.path,
                        target=concept,
                        ref_type='concept',
                        context='',
                        metadata={'type': 'concept'}
                    ))
            
            if 'citations' in reference_types:
                citations = self._extract_citations(content)
                for citation in citations:
                    references.append(Reference(
                        source=file_info.path,
                        target=citation['key'] if 'key' in citation else citation['number'],
                        ref_type='citation',
                        context='',
                        metadata=citation
                    ))
            
            if 'dependencies' in reference_types:
                dependencies = self._extract_dependencies(content, file_info.path)
                for dep in dependencies:
                    references.append(Reference(
                        source=file_info.path,
                        target=dep,
                        ref_type='dependency',
                        context='',
                        metadata={'type': 'import'}
                    ))
            
            return references
            
        except Exception as e:
            raise ParseError(f"Failed to process {file_info.path}: {str(e)}")
    
    def _build_reference_graph(self) -> None:
        """
        Build networkx graph from references.
        """
        self.graph.clear()
        
        # Add nodes and edges
        for ref in self.references:
            self.graph.add_node(
                ref.source,
                type='source',
                metadata=ref.metadata
            )
            self.graph.add_node(
                ref.target,
                type='target',
                metadata=ref.metadata
            )
            self.graph.add_edge(
                ref.source,
                ref.target,
                type=ref.ref_type,
                context=ref.context,
                metadata=ref.metadata
            )
    
    def _detect_cycles(self) -> List[List[str]]:
        """
        Detect cycles in reference graph.
        
        Returns:
            List of cycles found
        """
        try:
            return list(nx.simple_cycles(self.graph))
        except Exception as e:
            logger.warning(f"Failed to detect cycles: {str(e)}")
            return []
    
    def _get_reference_chains(
        self,
        max_depth: int = 2
    ) -> Dict[str, List[List[str]]]:
        """
        Get reference chains up to specified depth.
        
        Args:
            max_depth: Maximum chain depth
            
        Returns:
            Dictionary mapping sources to their reference chains
        """
        chains = {}
        
        for node in self.graph.nodes():
            if self.graph.out_degree(node) > 0:  # Only process nodes with outgoing edges
                chains[node] = []
                for target in self.graph.nodes():
                    if node != target:
                        paths = list(nx.all_simple_paths(
                            self.graph,
                            node,
                            target,
                            cutoff=max_depth
                        ))
                        if paths:
                            chains[node].extend(paths)
        
        return chains
    
    async def generate_cross_references(
        self,
        content_dir: str,
        reference_types: List[str] = None,
        formats: List[str] = None,
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Generate cross-references for content.
        
        Args:
            content_dir: Directory containing content
            reference_types: Types of references to generate
            formats: File formats to analyze
            depth: Maximum reference chain depth
            
        Returns:
            Dictionary containing reference information
            
        Raises:
            OrganizationError: If reference generation fails
        """
        try:
            reference_types = reference_types or ['links', 'concepts']
            formats = formats or ['md']
            
            # Build file patterns
            patterns = [f'*.{fmt}' for fmt in formats]
            
            # Find all content files
            files = await find_files(content_dir, patterns, recursive=True)
            
            # Process each file
            all_references = []
            for file_path in files:
                file_info = get_file_info(file_path, content_dir)
                references = await self._process_file(file_info, reference_types)
                all_references.extend(references)
                self.processed_files.add(file_path)
            
            self.references = all_references
            
            # Build reference graph
            self._build_reference_graph()
            
            # Get reference chains
            chains = self._get_reference_chains(depth)
            
            # Check for cycles
            cycles = self._detect_cycles()
            
            return {
                'success': True,
                'files_processed': len(self.processed_files),
                'references_found': len(self.references),
                'reference_chains': chains,
                'cycles_detected': cycles,
                'graph_stats': {
                    'nodes': self.graph.number_of_nodes(),
                    'edges': self.graph.number_of_edges()
                }
            }
            
        except Exception as e:
            raise OrganizationError(f"Failed to generate cross-references: {str(e)}")
    
    async def export_references(
        self,
        output_file: str,
        graph_format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Export reference data to file.
        
        Args:
            output_file: Path to output file
            graph_format: Format for reference graph
            
        Returns:
            Dictionary containing export results
            
        Raises:
            OrganizationError: If export fails
        """
        try:
            if graph_format == 'json':
                data = {
                    'nodes': [
                        {
                            'id': node,
                            'type': attr['type'],
                            'metadata': attr['metadata']
                        }
                        for node, attr in self.graph.nodes(data=True)
                    ],
                    'edges': [
                        {
                            'source': source,
                            'target': target,
                            'type': attr['type'],
                            'context': attr['context'],
                            'metadata': attr['metadata']
                        }
                        for source, target, attr in self.graph.edges(data=True)
                    ]
                }
                
                await write_file_content(
                    output_file,
                    json.dumps(data, indent=2)
                )
                
            elif graph_format == 'graphml':
                nx.write_graphml(self.graph, output_file)
                
            elif graph_format == 'dot':
                nx.write_dot(self.graph, output_file)
                
            else:
                raise ValueError(f"Unsupported graph format: {graph_format}")
            
            return {
                'success': True,
                'format': graph_format,
                'output_file': output_file
            }
            
        except Exception as e:
            raise OrganizationError(f"Failed to export references: {str(e)}")
    
    async def generate_reference_docs(
        self,
        output_dir: str
    ) -> Dict[str, Any]:
        """
        Generate reference documentation.
        
        Args:
            output_dir: Directory for documentation
            
        Returns:
            Dictionary containing generation results
            
        Raises:
            OrganizationError: If documentation generation fails
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            generated_files = []
            
            # Generate main index
            index_content = [
                "# Cross-Reference Documentation\n",
                "\n## Summary\n",
                f"- Files processed: {len(self.processed_files)}",
                f"- References found: {len(self.references)}",
                f"- Nodes in graph: {self.graph.number_of_nodes()}",
                f"- Edges in graph: {self.graph.number_of_edges()}\n"
            ]
            
            # Add reference type sections
            ref_types = {ref.ref_type for ref in self.references}
            for ref_type in sorted(ref_types):
                refs = [r for r in self.references if r.ref_type == ref_type]
                index_content.extend([
                    f"\n## {ref_type.title()} References\n",
                    f"Total: {len(refs)}\n",
                    "| Source | Target | Context |",
                    "|--------|---------|----------|"
                ])
                
                for ref in sorted(refs, key=lambda x: (x.source, x.target))[:10]:
                    source = os.path.basename(ref.source)
                    target = os.path.basename(ref.target) if os.path.exists(ref.target) else ref.target
                    context = ref.context[:50] + "..." if len(ref.context) > 50 else ref.context
                    index_content.append(f"| {source} | {target} | {context} |")
                
                if len(refs) > 10:
                    index_content.append("| ... | ... | ... |")
            
            # Write main index
            index_path = os.path.join(output_dir, 'index.md')
            await write_file_content(
                index_path,
                '\n'.join(index_content)
            )
            generated_files.append(index_path)
            
            # Generate detailed reference pages
            for ref_type in ref_types:
                refs = [r for r in self.references if r.ref_type == ref_type]
                content = [
                    f"# {ref_type.title()} References\n",
                    f"Total references: {len(refs)}\n"
                ]
                
                for ref in sorted(refs, key=lambda x: (x.source, x.target)):
                    content.extend([
                        f"\n## {os.path.basename(ref.source)} → {os.path.basename(ref.target)}\n",
                        f"- Source: `{ref.source}`",
                        f"- Target: `{ref.target}`",
                        f"- Type: {ref.ref_type}",
                        f"- Context: {ref.context}" if ref.context else "",
                        "\nMetadata:",
                        "```json",
                        json.dumps(ref.metadata, indent=2),
                        "```\n"
                    ])
                
                ref_path = os.path.join(output_dir, f'{ref_type}_references.md')
                await write_file_content(
                    ref_path,
                    '\n'.join(content)
                )
                generated_files.append(ref_path)
            
            return {
                'success': True,
                'files_generated': len(generated_files),
                'generated_files': generated_files
            }
            
        except Exception as e:
            raise OrganizationError(f"Failed to generate reference docs: {str(e)}")
    
    def get_reference_stats(self) -> Dict[str, Any]:
        """
        Get statistics about references.
        
        Returns:
            Dictionary containing reference statistics
        """
        stats = {
            'total_references': len(self.references),
            'files_processed': len(self.processed_files),
            'reference_types': {},
            'graph_stats': {
                'nodes': self.graph.number_of_nodes(),
                'edges': self.graph.number_of_edges(),
                'density': nx.density(self.graph),
                'strongly_connected_components': nx.number_strongly_connected_components(self.graph),
                'weakly_connected_components': nx.number_weakly_connected_components(self.graph)
            }
        }
        
        # Count references by type
        for ref_type in {ref.ref_type for ref in self.references}:
            type_refs = [r for r in self.references if r.ref_type == ref_type]
            stats['reference_types'][ref_type] = {
                'count': len(type_refs),
                'unique_sources': len({r.source for r in type_refs}),
                'unique_targets': len({r.target for r in type_refs})
            }
        
        return stats