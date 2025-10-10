"""
GUI Integration Example for Native MCP Client.

This module demonstrates how to integrate the native MCP client
with the existing Study Buddy GUI, providing a drop-in replacement
for the HTTP-based AsyncMCPClient.
"""

import asyncio
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import Optional, Dict, Any, List
from pathlib import Path

from .native_mcp_client import NativeMCPClient, ConnectionConfig, ConnectionState, MCPResponse


class StudyBuddyMainWindow:
    """
    Main window for Study Buddy GUI with native MCP integration.
    
    This is an example of how to integrate the native MCP client
    with a Tkinter GUI, replacing HTTP calls with direct function calls.
    """
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Study Buddy - Native MCP Integration")
        self.root.geometry("1000x700")
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize native MCP client
        self.mcp_client = None
        self._connection_status = ConnectionState.DISCONNECTED
        
        # Document data
        self.documents: List[Dict[str, Any]] = []
        self.selected_document = None
        
        # Setup GUI
        self._setup_gui()
        self._setup_status_bar()
        
        # Initialize MCP client
        self.root.after(100, self._initialize_mcp_client)
    
    def _setup_gui(self):
        """Setup main GUI components."""
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Document list
        left_frame = ttk.LabelFrame(main_frame, text="Documents", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        
        # Document controls
        controls_frame = ttk.Frame(left_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            controls_frame, 
            text="Upload Document", 
            command=self._upload_document
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            controls_frame,
            text="Refresh",
            command=self._refresh_documents
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            controls_frame,
            text="Delete",
            command=self._delete_document
        ).pack(side=tk.LEFT)
        
        # Document listbox
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.document_listbox = tk.Listbox(list_frame, width=40)
        self.document_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.document_listbox.bind('<<ListboxSelect>>', self._on_document_select)
        
        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.document_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.document_listbox.yview)
        
        # Right panel - Document viewer
        right_frame = ttk.LabelFrame(main_frame, text="Document Viewer", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Document info
        info_frame = ttk.Frame(right_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_text = tk.Text(info_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        self.info_text.pack(fill=tk.X)
        
        # Document actions
        actions_frame = ttk.Frame(right_frame)
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            actions_frame,
            text="Index Document",
            command=self._index_document
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            actions_frame,
            text="Get Structure", 
            command=self._get_structure
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            actions_frame,
            text="Search",
            command=self._search_documents
        ).pack(side=tk.LEFT)
        
        # Content area
        content_frame = ttk.Frame(right_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.content_text = tk.Text(content_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Content scrollbar
        content_scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL)
        content_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_text.config(yscrollcommand=content_scrollbar.set)
        content_scrollbar.config(command=self.content_text.yview)
    
    def _setup_status_bar(self):
        """Setup status bar."""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="Initializing...",
            relief=tk.SUNKEN,
            padding=5
        )
        self.status_label.pack(side=tk.LEFT)
        
        self.connection_label = ttk.Label(
            self.status_frame,
            text="⚪ Disconnected",
            padding=5
        )
        self.connection_label.pack(side=tk.RIGHT)
    
    def _initialize_mcp_client(self):
        """Initialize native MCP client asynchronously."""
        async def init_client():
            try:
                # Create native MCP client
                config = ConnectionConfig(
                    database_path=None,  # Use default database
                    enable_logging=True
                )
                self.mcp_client = NativeMCPClient(config)
                
                # Add connection listener
                self.mcp_client.add_connection_listener(self._on_connection_change)
                
                # Connect
                success = await self.mcp_client.connect()
                
                if success:
                    self._set_status("Native MCP client connected successfully")
                    await self._refresh_documents()
                else:
                    self._set_status("Failed to connect native MCP client")
                    messagebox.showerror(
                        "Connection Error",
                        "Failed to initialize native MCP client. "
                        "Make sure you're running from the project root directory."
                    )
                    
            except Exception as e:
                self.logger.error(f"Error initializing MCP client: {e}")
                self._set_status(f"MCP client error: {e}")
                messagebox.showerror("Error", f"MCP client initialization failed: {e}")
        
        # Run async initialization
        asyncio.create_task(init_client())
    
    def _on_connection_change(self, state: ConnectionState):
        """Handle MCP connection state changes."""
        self._connection_status = state
        
        # Update UI based on connection state
        if state == ConnectionState.CONNECTED:
            self.connection_label.config(text="🟢 Connected", foreground="green")
        elif state == ConnectionState.CONNECTING:
            self.connection_label.config(text="🟡 Connecting", foreground="orange")
        elif state == ConnectionState.DISCONNECTED:
            self.connection_label.config(text="⚪ Disconnected", foreground="gray")
        elif state == ConnectionState.ERROR:
            self.connection_label.config(text="🔴 Error", foreground="red")
    
    def _set_status(self, message: str):
        """Update status bar message."""
        self.status_label.config(text=message)
        self.logger.info(message)
    
    async def _refresh_documents(self):
        """Refresh document list from MCP server."""
        if not self.mcp_client or not await self.mcp_client.is_connected():
            self._set_status("Not connected to MCP server")
            return
        
        try:
            self._set_status("Loading documents...")
            
            # Call native MCP client
            response = await self.mcp_client.list_documents()
            
            if response.success:
                self.documents = response.data.get("documents", [])
                self._update_document_list()
                self._set_status(f"Loaded {len(self.documents)} documents")
            else:
                self._set_status(f"Error loading documents: {response.error}")
                messagebox.showerror("Error", f"Failed to load documents: {response.error}")
                
        except Exception as e:
            self.logger.error(f"Error refreshing documents: {e}")
            self._set_status(f"Error: {e}")
    
    def _update_document_list(self):
        """Update document listbox."""
        self.document_listbox.delete(0, tk.END)
        
        for doc in self.documents:
            title = doc.get("title", "Untitled")
            file_type = doc.get("file_type", "unknown")
            item_text = f"{title} ({file_type})"
            self.document_listbox.insert(tk.END, item_text)
    
    def _on_document_select(self, event):
        """Handle document selection."""
        selection = self.document_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        self.selected_document = self.documents[index] if index < len(self.documents) else None
        
        if self.selected_document:
            self._update_document_info()
    
    def _update_document_info(self):
        """Update document info display."""
        if not self.selected_document:
            return
        
        # Update info text
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        info = f"""Title: {self.selected_document.get('title', 'N/A')}
File Type: {self.selected_document.get('file_type', 'N/A')}
Total Words: {self.selected_document.get('total_words', 'N/A'):,}
Total Pages: {self.selected_document.get('total_pages', 'N/A')}
Indexed: {'Yes' if self.selected_document.get('indexed') else 'No'}
Upload Date: {self.selected_document.get('upload_date', 'N/A')}
Tags: {', '.join(self.selected_document.get('tags', []))}"""
        
        self.info_text.insert(1.0, info)
        self.info_text.config(state=tk.DISABLED)
    
    def _upload_document(self):
        """Upload new document."""
        file_path = filedialog.askopenfilename(
            title="Select Document",
            filetypes=[
                ("PDF Files", "*.pdf"),
                ("Word Documents", "*.docx"),
                ("PowerPoint", "*.pptx"),
                ("Markdown", "*.md"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            asyncio.create_task(self._do_upload(file_path))
    
    async def _do_upload(self, file_path: str):
        """Perform document upload."""
        if not self.mcp_client or not await self.mcp_client.is_connected():
            messagebox.showerror("Error", "Not connected to MCP server")
            return
        
        try:
            self._set_status(f"Uploading {Path(file_path).name}...")
            
            response = await self.mcp_client.upload_document(file_path=file_path)
            
            if response.success:
                self._set_status("Upload successful")
                messagebox.showinfo("Success", f"Document uploaded successfully!")
                await self._refresh_documents()
            else:
                self._set_status(f"Upload failed: {response.error}")
                messagebox.showerror("Upload Error", f"Failed to upload document: {response.error}")
                
        except Exception as e:
            self.logger.error(f"Error uploading document: {e}")
            messagebox.showerror("Error", f"Upload failed: {e}")
    
    def _delete_document(self):
        """Delete selected document."""
        if not self.selected_document:
            messagebox.showwarning("Warning", "No document selected")
            return
        
        doc_title = self.selected_document.get("title", "Unknown")
        
        if messagebox.askyesno("Confirm Delete", f"Delete document '{doc_title}'?"):
            asyncio.create_task(self._do_delete())
    
    async def _do_delete(self):
        """Perform document deletion."""
        if not self.mcp_client or not self.selected_document:
            return
        
        try:
            doc_id = self.selected_document["id"]
            self._set_status("Deleting document...")
            
            response = await self.mcp_client.delete_document(document_id=doc_id)
            
            if response.success:
                self._set_status("Document deleted")
                messagebox.showinfo("Success", "Document deleted successfully!")
                await self._refresh_documents()
            else:
                self._set_status(f"Delete failed: {response.error}")
                messagebox.showerror("Delete Error", f"Failed to delete document: {response.error}")
                
        except Exception as e:
            self.logger.error(f"Error deleting document: {e}")
            messagebox.showerror("Error", f"Delete failed: {e}")
    
    def _index_document(self):
        """Index selected document."""
        if not self.selected_document:
            messagebox.showwarning("Warning", "No document selected")
            return
        
        asyncio.create_task(self._do_index())
    
    async def _do_index(self):
        """Perform document indexing."""
        if not self.mcp_client or not self.selected_document:
            return
        
        try:
            doc_id = self.selected_document["id"]
            self._set_status("Indexing document...")
            
            response = await self.mcp_client.index_document(
                document_id=doc_id,
                strategy="auto"
            )
            
            if response.success:
                chunks_created = response.data.get("chunks_created", 0)
                self._set_status(f"Indexing complete - {chunks_created} chunks created")
                messagebox.showinfo("Success", f"Document indexed successfully!\n{chunks_created} chunks created.")
                await self._refresh_documents()
            else:
                self._set_status(f"Indexing failed: {response.error}")
                messagebox.showerror("Indexing Error", f"Failed to index document: {response.error}")
                
        except Exception as e:
            self.logger.error(f"Error indexing document: {e}")
            messagebox.showerror("Error", f"Indexing failed: {e}")
    
    def _get_structure(self):
        """Get document structure."""
        if not self.selected_document:
            messagebox.showwarning("Warning", "No document selected")
            return
        
        asyncio.create_task(self._do_get_structure())
    
    async def _do_get_structure(self):
        """Get and display document structure."""
        if not self.mcp_client or not self.selected_document:
            return
        
        try:
            doc_id = self.selected_document["id"]
            self._set_status("Getting document structure...")
            
            response = await self.mcp_client.get_document_structure(document_id=doc_id)
            
            if response.success:
                chunks = response.data.get("chunks", [])
                self._display_structure(chunks)
                self._set_status(f"Structure loaded - {len(chunks)} chunks")
            else:
                self._set_status(f"Structure failed: {response.error}")
                messagebox.showerror("Structure Error", f"Failed to get structure: {response.error}")
                
        except Exception as e:
            self.logger.error(f"Error getting structure: {e}")
            messagebox.showerror("Error", f"Structure failed: {e}")
    
    def _display_structure(self, chunks: List[Dict[str, Any]]):
        """Display document structure in content area."""
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)
        
        content = "Document Structure:\n\n"
        
        for chunk in chunks:
            chunk_title = chunk.get("title", "Untitled Chunk")
            chunk_type = chunk.get("chunk_type", "unknown")
            word_count = chunk.get("word_count", 0)
            content += f"• {chunk_title} ({chunk_type}) - {word_count:,} words\n"
        
        self.content_text.insert(1.0, content)
        self.content_text.config(state=tk.DISABLED)
    
    def _search_documents(self):
        """Search documents."""
        query = tk.simpledialog.askstring("Search", "Enter search query:")
        if query:
            asyncio.create_task(self._do_search(query))
    
    async def _do_search(self, query: str):
        """Perform document search."""
        if not self.mcp_client:
            return
        
        try:
            self._set_status(f"Searching for '{query}'...")
            
            response = await self.mcp_client.search_documents(query=query)
            
            if response.success:
                results = response.data.get("results", [])
                self._display_search_results(results)
                self._set_status(f"Search complete - {len(results)} results")
            else:
                self._set_status(f"Search failed: {response.error}")
                messagebox.showerror("Search Error", f"Search failed: {response.error}")
                
        except Exception as e:
            self.logger.error(f"Error searching: {e}")
            messagebox.showerror("Error", f"Search failed: {e}")
    
    def _display_search_results(self, results: List[Dict[str, Any]]):
        """Display search results."""
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)
        
        content = f"Search Results ({len(results)} found):\n\n"
        
        for result in results:
            title = result.get("title", "Untitled")
            excerpt = result.get("match_excerpt", "No excerpt")
            relevance = result.get("relevance_score", 0)
            content += f"📄 {title} (Score: {relevance:.2f})\n"
            content += f"   {excerpt}\n\n"
        
        self.content_text.insert(1.0, content)
        self.content_text.config(state=tk.DISABLED)
    
    def on_closing(self):
        """Handle application closing."""
        async def cleanup():
            if self.mcp_client:
                await self.mcp_client.disconnect()
        
        try:
            asyncio.create_task(cleanup())
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        
        self.root.destroy()


def main():
    """Main entry point for native MCP GUI example."""
    
    # Setup asyncio for tkinter
    import tkinter.simpledialog
    
    # Create root window
    root = tk.Tk()
    
    # Create application
    app = StudyBuddyMainWindow(root)
    
    # Handle closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start GUI event loop
    root.mainloop()


if __name__ == "__main__":
    main()