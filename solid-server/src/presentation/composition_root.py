"""
Composition Root for SOLID Analysis MCP Server
==============================================
Handles all dependency injection and object composition following clean architecture.
This fixes DIP violations by centralizing object creation and dependency wiring.
"""

from pathlib import Path
from typing import Optional

# MCP imports (fallback mode for testing)
try:
    from mcp.server import Server
except ImportError:
    # Fallback for testing without MCP
    class Server:
        def __init__(self, name): self.name = name

# Domain imports
from domain.interfaces import IAnalyzer, IFormatter

# Application imports  
from application.analyze_file import AnalyzeFileUseCase
from application.analyze_directory import AnalyzeDirectoryUseCase
from application.generate_report import GenerateReportUseCase
from application.suggest_refactoring import SuggestRefactoringUseCase

# Infrastructure imports
from infrastructure.analyzers.ast_analyzer import ASTAnalyzer
from infrastructure.analyzers.principle_checkers.srp_checker import SRPChecker
from infrastructure.analyzers.principle_checkers.ocp_checker import OCPChecker
from infrastructure.analyzers.principle_checkers.lsp_checker import LSPChecker
from infrastructure.analyzers.principle_checkers.isp_checker import ISPChecker
from infrastructure.analyzers.principle_checkers.dip_checker import DIPChecker
from infrastructure.formatters.text_formatter import TextFormatter

# Presentation imports (from root src level)
from mcp_handler import MCPHandler
from server import SolidMCPServer


class CompositionRoot:
    """
    Composition root that wires all dependencies following clean architecture.
    
    This class eliminates DIP violations by:
    1. Centralizing all object creation
    2. Using dependency injection
    3. Following dependency inversion principle
    4. Providing a single place to configure the system
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize composition root with project configuration."""
        self.project_root = project_root or Path.cwd()
        
        # Initialize all dependencies in correct order
        self._analyzer: Optional[IAnalyzer] = None
        self._formatter: Optional[IFormatter] = None
        self._use_cases: Optional[dict] = None
        self._mcp_handler: Optional[MCPHandler] = None
        self._server: Optional[SolidMCPServer] = None
    
    def get_server(self) -> SolidMCPServer:
        """Get fully configured MCP server with all dependencies injected."""
        if self._server is None:
            self._server = self._create_server()
        return self._server
    
    def _create_server(self) -> SolidMCPServer:
        """Create MCP server with injected dependencies."""
        mcp_server = Server("solid-mcp-server")
        mcp_handler = self._get_mcp_handler()
        return SolidMCPServer(
            project_root=self.project_root,
            server=mcp_server,
            mcp_handler=mcp_handler
        )
    
    def _get_mcp_handler(self) -> MCPHandler:
        """Get MCP handler with injected use cases."""
        if self._mcp_handler is None:
            use_cases = self._get_use_cases()
            self._mcp_handler = MCPHandler(
                project_root=self.project_root,
                analyze_file_uc=use_cases['analyze_file'],
                analyze_dir_uc=use_cases['analyze_directory'],
                generate_report_uc=use_cases['generate_report'],
                suggest_refactoring_uc=use_cases['suggest_refactoring']
            )
        return self._mcp_handler
    
    def _get_use_cases(self) -> dict:
        """Get all use cases with injected dependencies."""
        if self._use_cases is None:
            analyzer = self._get_analyzer()
            formatter = self._get_formatter()
            
            self._use_cases = {
                'analyze_file': AnalyzeFileUseCase(analyzer),
                'analyze_directory': AnalyzeDirectoryUseCase(analyzer),
                'generate_report': GenerateReportUseCase(formatter),
                'suggest_refactoring': SuggestRefactoringUseCase()
            }
        return self._use_cases
    
    def _get_analyzer(self) -> IAnalyzer:
        """Get analyzer with injected principle checkers."""
        if self._analyzer is None:
            checkers = self._create_principle_checkers()
            self._analyzer = ASTAnalyzer(checkers)
        return self._analyzer
    
    def _get_formatter(self) -> IFormatter:
        """Get formatter implementation."""
        if self._formatter is None:
            self._formatter = TextFormatter()
        return self._formatter
    
    def _create_principle_checkers(self) -> list:
        """Create all SOLID principle checkers."""
        return [
            SRPChecker(),
            OCPChecker(),
            LSPChecker(),
            ISPChecker(),
            DIPChecker()
        ]


# Factory function for easy server creation
def create_solid_server(project_root: Optional[Path] = None) -> SolidMCPServer:
    """
    Factory function to create a fully configured SOLID MCP server.
    
    This eliminates the need for main.py to know about internal dependencies.
    """
    composition_root = CompositionRoot(project_root)
    return composition_root.get_server()