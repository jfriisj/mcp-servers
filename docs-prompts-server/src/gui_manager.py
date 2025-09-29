"""
GUI management for the Documentation and Prompts MCP Server
"""

import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


class GUIManager:
    """Manages GUI operations"""

    _gui_launched = False

    def __init__(self, db_path: Path, server_instance=None):
        self.db_path = db_path
        self.server_instance = server_instance

    def launch_gui(self):
        """Launch GUI in a separate thread"""
        if not GUIManager._gui_launched:
            gui_thread = threading.Thread(target=self._launch_gui_thread, daemon=True)
            gui_thread.start()
            GUIManager._gui_launched = True

    def _launch_gui_thread(self):
        """Launch GUI in a separate daemon thread"""
        try:
            logger.info("Launching GUI...")
            from docs_db_viewer import DocsPromptsViewer, DocsPromptsGUI

            viewer = DocsPromptsViewer(str(self.db_path))
            gui = DocsPromptsGUI(viewer, server=self.server_instance)
            gui.run()
        except Exception as e:  # noqa: BLE001
            logger.error("Error launching GUI: %s", e)
