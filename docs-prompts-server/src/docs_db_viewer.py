#!/usr/bin/env python3
"""
GUI Database Viewer for Documentation and Prompts MCP Server

Provides an interactive GUI to explore indexed content, view statistics,
and manage prompts and documents.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse

logger = logging.getLogger(__name__)


class DocsPromptsViewer:
    """Handles database operations for the GUI viewer"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {db_path}")

    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Document statistics
                doc_cursor = conn.execute(
                    "SELECT COUNT(*), COUNT(DISTINCT doc_type) FROM documents"
                )
                doc_count, doc_types = doc_cursor.fetchone()

                # Prompt statistics
                prompt_cursor = conn.execute("""
                    SELECT COUNT(*), COUNT(DISTINCT category)
                    FROM prompts
                """)
                prompt_count, categories = prompt_cursor.fetchone()

                # Usage statistics
                usage_cursor = conn.execute(
                    "SELECT COUNT(*) FROM prompt_usage"
                )
                usage_count = usage_cursor.fetchone()[0]

                # Search index statistics
                search_cursor = conn.execute(
                    "SELECT COUNT(*) FROM search_index"
                )
                search_count = search_cursor.fetchone()[0]

                return {
                    "documents": doc_count,
                    "document_types": doc_types,
                    "prompts": prompt_count,
                    "categories": categories,
                    "usage_records": usage_count,
                    "search_entries": search_count,
                }
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return {}

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents with metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT path, title, doc_type, metadata, last_modified
                    FROM documents ORDER BY title
                """)

                documents = []
                for row in cursor.fetchall():
                    documents.append({
                        "path": row[0],
                        "title": row[1],
                        "doc_type": row[2],
                        "metadata": json.loads(row[3]) if row[3] else {},
                        "last_modified": row[4],
                    })
                return documents
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []

    def get_document_content(self, path: str) -> Optional[Dict[str, Any]]:
        """Get full document content and metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT path, title, content, sections, metadata,
                           last_modified, doc_type, links, code_blocks
                    FROM documents WHERE path = ?
                """, (path,))

                row = cursor.fetchone()
                if row:
                    return {
                        "path": row[0],
                        "title": row[1],
                        "content": row[2],
                        "sections": json.loads(row[3]) if row[3] else [],
                        "metadata": json.loads(row[4]) if row[4] else {},
                        "last_modified": row[5],
                        "doc_type": row[6],
                        "links": json.loads(row[7]) if row[7] else [],
                        "code_blocks": json.loads(row[8]) if row[8] else [],
                    }
                return None
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return None

    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Get all prompts with metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, name, description, category, tags,
                           usage_count, effectiveness_score
                    FROM prompts ORDER BY category, name
                """)

                prompts = []
                for row in cursor.fetchall():
                    prompts.append({
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "category": row[3],
                        "tags": json.loads(row[4]) if row[4] else [],
                        "usage_count": row[5],
                        "effectiveness_score": row[6] or 0.0,
                    })
                return prompts
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []

    def get_prompt_details(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get full prompt details"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, name, description, category, template,
                           variables, tags, created_at, updated_at,
                           usage_count, effectiveness_score
                    FROM prompts WHERE id = ?
                """, (prompt_id,))

                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "category": row[3],
                        "template": row[4],
                        "variables": json.loads(row[5]) if row[5] else [],
                        "tags": json.loads(row[6]) if row[6] else [],
                        "created_at": row[7],
                        "updated_at": row[8],
                        "usage_count": row[9],
                        "effectiveness_score": row[10] or 0.0,
                    }
                return None
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return None

    def get_usage_stats(self) -> List[Dict[str, Any]]:
        """Get usage statistics for all prompts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT p.id, p.name, p.category, p.usage_count,
                           p.effectiveness_score, COUNT(pu.id) as total_uses,
                           AVG(pu.effectiveness) as avg_effectiveness
                    FROM prompts p
                    LEFT JOIN prompt_usage pu ON p.id = pu.prompt_id
                    GROUP BY p.id ORDER BY p.usage_count DESC
                """)

                stats = []
                for row in cursor.fetchall():
                    stats.append({
                        "id": row[0],
                        "name": row[1],
                        "category": row[2],
                        "usage_count": row[3],
                        "effectiveness_score": row[4] or 0.0,
                        "total_uses": row[5],
                        "avg_effectiveness": row[6] or 0.0,
                    })
                return stats
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []

    def search_content(self, query: str) -> List[Dict[str, Any]]:
        """Search across documents and prompts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Search documents
                doc_results = []
                doc_cursor = conn.execute("""
                    SELECT DISTINCT d.path, d.title, d.doc_type,
                           s.section_title, s.content_chunk
                    FROM documents d
                    JOIN search_index s ON d.path = s.doc_path
                    WHERE s.content_chunk LIKE ? OR d.title LIKE ?
                    LIMIT 20
                """, (f"%{query}%", f"%{query}%"))

                for row in doc_cursor.fetchall():
                    snippet_text = (
                        row[4][:200] + "..." if len(row[4]) > 200 else row[4]
                    )
                    doc_results.append({
                        "type": "document",
                        "path": row[0],
                        "title": row[1],
                        "doc_type": row[2],
                        "section": row[3],
                        "snippet": snippet_text,
                    })

                # Search prompts
                prompt_results = []
                prompt_cursor = conn.execute("""
                    SELECT id, name, description, category
                    FROM prompts
                    WHERE name LIKE ? OR description LIKE ?
                    LIMIT 10
                """, (f"%{query}%", f"%{query}%"))

                for row in prompt_cursor.fetchall():
                    prompt_results.append({
                        "type": "prompt",
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "category": row[3],
                    })

                return doc_results + prompt_results
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []


class DocsPromptsGUI:
    """Main GUI application for the database viewer"""

    def __init__(self, viewer: DocsPromptsViewer, server=None):
        self.viewer = viewer
        self.server = server

        # Create main window
        self.root = tk.Tk()
        self.root.title("Documentation & Prompts Database Viewer")
        self.root.geometry("1400x800")

        # Status bar variable (must be created early)
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.create_stats_tab()
        self.create_documents_tab()
        self.create_prompts_tab()
        self.create_analytics_tab()
        self.create_tools_tab()

        # Status bar
        status_bar = ttk.Label(
            self.root, textvariable=self.status_var, relief=tk.SUNKEN
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def create_stats_tab(self):
        """Create database statistics tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📊 Statistics")

        # Stats display
        stats_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=20)
        stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Refresh button
        refresh_btn = ttk.Button(
            frame, text="Refresh",
            command=lambda: self.update_stats(stats_text)
        )
        refresh_btn.pack(pady=5)

        # Initial load
        self.update_stats(stats_text)

    def create_documents_tab(self):
        """Create documents explorer tab with integrated search"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="� Documents")

        # Search controls at the top
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(search_frame, text="Filter:").pack(side=tk.LEFT)
        self.doc_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.doc_search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", self.on_document_filter)

        clear_btn = ttk.Button(search_frame, text="Clear", command=self.clear_document_filter)
        clear_btn.pack(side=tk.LEFT, padx=5)

        # Split pane for documents and content
        paned = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - document list
        left_frame = ttk.Frame(paned)
        paned.add(left_frame)

        # Document list
        columns = ("title", "type", "path")
        self.doc_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=20)
        self.doc_tree.heading("title", text="Title")
        self.doc_tree.heading("type", text="Type")
        self.doc_tree.heading("path", text="Path")
        self.doc_tree.column("title", width=200)
        self.doc_tree.column("type", width=50)
        self.doc_tree.column("path", width=300)

        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.doc_tree.yview)
        self.doc_tree.configure(yscrollcommand=scrollbar.set)

        self.doc_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Right panel - content viewer
        right_frame = ttk.Frame(paned)
        paned.add(right_frame)

        content_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD)
        content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Bind selection event
        self.doc_tree.bind("<<TreeviewSelect>>", lambda e: self.show_document_content(content_text))

        # Store all documents for filtering
        self.all_documents = []
        # Load documents
        self.load_all_documents()

    def create_prompts_tab(self):
        """Create prompts library tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🎯 Prompts")

        # Split pane
        paned = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - prompt list
        left_frame = ttk.Frame(paned)
        paned.add(left_frame)

        # Prompt list
        columns = ("name", "category", "usage")
        self.prompt_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=20)
        self.prompt_tree.heading("name", text="Name")
        self.prompt_tree.heading("category", text="Category")
        self.prompt_tree.heading("usage", text="Usage")

        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.prompt_tree.yview)
        self.prompt_tree.configure(yscrollcommand=scrollbar.set)

        self.prompt_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Right panel - prompt details
        right_frame = ttk.Frame(paned)
        paned.add(right_frame)

        details_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD)
        details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Bind selection event
        self.prompt_tree.bind("<<TreeviewSelect>>", lambda e: self.show_prompt_details(details_text))

        # Load prompts
        self.load_prompts()

    def create_analytics_tab(self):
        """Create usage analytics tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📈 Analytics")

        # Analytics display
        analytics_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=25)
        analytics_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        refresh_btn = ttk.Button(
            frame, text="Refresh Analytics",
            command=lambda: self.update_analytics(analytics_text)
        )
        refresh_btn.pack(pady=5)

        # Initial load
        self.update_analytics(analytics_text)



    def update_stats(self, text_widget):
        """Update database statistics display"""
        stats = self.viewer.get_database_stats()
        text_widget.delete(1.0, tk.END)

        if stats:
            text_widget.insert(tk.END, "📊 Database Statistics\n")
            text_widget.insert(tk.END, "=" * 50 + "\n\n")

            text_widget.insert(tk.END, f"📄 Documents: {stats['documents']}\n")
            doc_types = stats['document_types']
            text_widget.insert(tk.END, f"📁 Document Types: {doc_types}\n")
            text_widget.insert(tk.END, f"🎯 Prompts: {stats['prompts']}\n")
            text_widget.insert(tk.END, f"🏷️ Categories: {stats['categories']}\n")
            text_widget.insert(tk.END, f"📈 Usage Records: {stats['usage_records']}\n")
            text_widget.insert(tk.END, f"🔍 Search Entries: {stats['search_entries']}\n")
        else:
            text_widget.insert(tk.END, "❌ Unable to load database statistics")

        self.status_var.set("Statistics updated")

    def load_all_documents(self):
        """Load all documents and store them for filtering"""
        self.all_documents = self.viewer.get_all_documents()
        self.display_filtered_documents("")

    def display_filtered_documents(self, filter_text):
        """Display documents filtered by the given text"""
        # Clear existing items
        for item in self.doc_tree.get_children():
            self.doc_tree.delete(item)

        # Filter documents
        if filter_text.strip():
            filtered_docs = []
            filter_lower = filter_text.lower()
            for doc in self.all_documents:
                # Search in title, path, and content
                searchable_text = (
                    doc["title"].lower() + " " +
                    doc["path"].lower() + " " +
                    (doc.get("content", "").lower()
                     if "content" in doc else "")
                )
                if filter_lower in searchable_text:
                    filtered_docs.append(doc)
        else:
            filtered_docs = self.all_documents

        # Display filtered documents
        for doc in filtered_docs:
            self.doc_tree.insert("", tk.END, values=(
                doc["title"],
                doc["doc_type"],
                doc["path"]
            ))

        # Update status
        self.status_var.set(
            f"Showing {len(filtered_docs)} of "
            f"{len(self.all_documents)} documents"
        )

    def on_document_filter(self, event):
        """Handle document filter input changes"""
        filter_text = self.doc_search_var.get().strip()
        self.display_filtered_documents(filter_text)

    def clear_document_filter(self):
        """Clear the document filter"""
        self.doc_search_var.set("")
        self.display_filtered_documents("")

    def show_document_content(self, text_widget):
        """Show selected document content"""
        selection = self.doc_tree.selection()
        if not selection:
            return

        item = self.doc_tree.item(selection[0])
        path = item["values"][2]

        content = self.viewer.get_document_content(path)
        text_widget.delete(1.0, tk.END)

        if content:
            text_widget.insert(tk.END, f"📄 {content['title']}\n")
            text_widget.insert(tk.END, f"📁 Path: {content['path']}\n")
            text_widget.insert(tk.END, f"🏷️ Type: {content['doc_type']}\n\n")

            text_widget.insert(tk.END, "📖 Content:\n")
            text_widget.insert(tk.END, "-" * 50 + "\n")
            text_widget.insert(tk.END, content['content'] + "\n\n")

            if content['sections']:
                text_widget.insert(tk.END, "📑 Sections:\n")
                text_widget.insert(tk.END, "-" * 50 + "\n")
                for section in content['sections']:
                    text_widget.insert(tk.END, f"• {section['title']}\n")
        else:
            text_widget.insert(tk.END, "❌ Unable to load document content")

    def load_prompts(self):
        """Load prompts into the tree view"""
        # Clear existing items
        for item in self.prompt_tree.get_children():
            self.prompt_tree.delete(item)

        prompts = self.viewer.get_all_prompts()
        for prompt in prompts:
            self.prompt_tree.insert("", tk.END, values=(
                prompt["name"],
                prompt["category"],
                prompt["usage_count"]
            ))

    def show_prompt_details(self, text_widget):
        """Show selected prompt details"""
        selection = self.prompt_tree.selection()
        if not selection:
            return

        item = self.prompt_tree.item(selection[0])
        name = item["values"][0]

        # Find prompt by name (this is a bit inefficient, but works for GUI)
        prompts = self.viewer.get_all_prompts()
        prompt = next((p for p in prompts if p["name"] == name), None)

        if prompt:
            details = self.viewer.get_prompt_details(prompt["id"])
            text_widget.delete(1.0, tk.END)

            if details:
                text_widget.insert(tk.END, f"🎯 {details['name']}\n")
                text_widget.insert(tk.END,
                                   f"🏷️ Category: {details['category']}\n")
                text_widget.insert(tk.END,
                                   f"📊 Usage: {details['usage_count']}\n")
                text_widget.insert(tk.END,
                                   f"⭐ Effectiveness: "
                                   f"{details['effectiveness_score']:.2f}\n\n")

                text_widget.insert(tk.END, "📝 Description:\n")
                text_widget.insert(tk.END, "-" * 50 + "\n")
                text_widget.insert(tk.END, details['description'] + "\n\n")

                text_widget.insert(tk.END, "📋 Template:\n")
                text_widget.insert(tk.END, "-" * 50 + "\n")
                text_widget.insert(tk.END, details['template'] + "\n\n")

                if details['variables']:
                    text_widget.insert(tk.END, "🔧 Variables:\n")
                    text_widget.insert(tk.END, "-" * 50 + "\n")
                    for var in details['variables']:
                        text_widget.insert(tk.END, f"• {var}\n")

                if details['tags']:
                    text_widget.insert(tk.END, "\n🏷️ Tags:\n")
                    text_widget.insert(tk.END, "-" * 50 + "\n")
                    text_widget.insert(tk.END, ", ".join(details['tags']))
            else:
                text_widget.insert(tk.END, "❌ Unable to load prompt details")
        else:
            text_widget.insert(tk.END, "❌ Prompt not found")

    def update_analytics(self, text_widget):
        """Update usage analytics display"""
        stats = self.viewer.get_usage_stats()
        text_widget.delete(1.0, tk.END)

        if stats:
            text_widget.insert(tk.END, "📈 Usage Analytics\n")
            text_widget.insert(tk.END, "=" * 50 + "\n\n")

            text_widget.insert(tk.END, "🏆 Top Prompts by Usage:\n")
            text_widget.insert(tk.END, "-" * 30 + "\n")

            for i, stat in enumerate(stats[:10], 1):
                text_widget.insert(tk.END,
                                   f"{i}. {stat['name']} ({stat['category']})\n"
                                   f"   Usage: {stat['usage_count']} | "
                                   f"Effectiveness: "
                                   f"{stat['effectiveness_score']:.2f}\n\n"
                                   )

            # Category breakdown
            categories = {}
            for stat in stats:
                cat = stat['category']
                categories[cat] = categories.get(cat, 0) + stat['usage_count']

            text_widget.insert(tk.END, "🏷️ Usage by Category:\n")
            text_widget.insert(tk.END, "-" * 30 + "\n")

            for category, usage in sorted(
                    categories.items(), key=lambda x: x[1], reverse=True):
                text_widget.insert(tk.END, f"• {category}: {usage} uses\n")
        else:
            text_widget.insert(tk.END, "❌ Unable to load analytics data")

        self.status_var.set("Analytics updated")

    def on_search(self, event):
        """Handle search input changes"""
        query = self.search_var.get().strip()
        if len(query) >= 2:  # Minimum search length
            self.perform_search()

    def perform_search(self):
        """Perform search across content"""
        query = self.search_var.get().strip()
        if not query:
            return

        results = self.viewer.search_content(query)
        self.search_results.delete(1.0, tk.END)

        if results:
            self.search_results.insert(tk.END,
                                      f"🔍 Search Results for: '{query}'\n")
            self.search_results.insert(tk.END, "=" * 50 + "\n\n")

            for result in results:
                if result["type"] == "document":
                    self.search_results.insert(tk.END,
                                               f"📄 {result['title']} "
                                               f"({result['doc_type']})\n"
                                               f"   📁 {result['path']}\n"
                                               f"   📑 {result['section']}\n"
                                               f"   💬 {result['snippet']}\n\n")
                elif result["type"] == "prompt":
                    self.search_results.insert(tk.END,
                                               f"🎯 {result['name']} "
                                               f"({result['category']})\n"
                                               f"   📝 "
                                               f"{result['description']}\n\n")
        else:
            self.search_results.insert(tk.END,
                                      f"❌ No results found for: '{query}'")

        self.status_var.set(f"Found {len(results)} results")

    def create_tools_tab(self):
        """Create MCP tools information tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🛠️ Tools")

        # Tools display
        tools_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=30)
        tools_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Load tools information
        self.display_tools_info(tools_text)

    def display_tools_info(self, text_widget):
        """Display MCP tools information with descriptions for agents"""
        tools_info = self.get_mcp_tools_info()
        text_widget.delete(1.0, tk.END)

        text_widget.insert(tk.END, "🛠️ MCP Server Tools for AI Agents\n")
        text_widget.insert(tk.END, "=" * 60 + "\n\n")

        text_widget.insert(tk.END, "This MCP server provides tools that AI agents can use to:\n")
        text_widget.insert(tk.END, "• Search and access documentation\n")
        text_widget.insert(tk.END, "• Manage and use prompt templates\n")
        text_widget.insert(tk.END, "• Extract architecture information\n")
        text_widget.insert(tk.END, "• Generate contextual prompts\n\n")

        for tool in tools_info:
            text_widget.insert(tk.END, f"🔧 {tool['name']}\n")
            text_widget.insert(tk.END, "-" * 40 + "\n")
            text_widget.insert(tk.END, f"📝 {tool['description']}\n\n")

            if tool['parameters']:
                text_widget.insert(tk.END, "📋 Parameters:\n")
                for param in tool['parameters']:
                    required = " (required)" if param['required'] else " (optional)"
                    text_widget.insert(tk.END, f"  • {param['name']}: {param['description']}{required}\n")
                text_widget.insert(tk.END, "\n")

            text_widget.insert(tk.END, f"🎯 Agent Usage:\n{tool['usage']}\n\n")
            text_widget.insert(tk.END, "💡 Example:\n" + tool['example'] + "\n\n")
            text_widget.insert(tk.END, "=" * 60 + "\n\n")

    def get_mcp_tools_info(self):
        """Get formatted information about all MCP tools"""
        return [
            {
                "name": "search_docs",
                "description": "Search through indexed documentation using keywords or phrases",
                "parameters": [
                    {"name": "query", "description": "Search keywords or phrases", "required": True},
                    {"name": "doc_type", "description": "Filter by document type (.md, .rst, etc.)", "required": False},
                    {"name": "limit", "description": "Maximum results (1-50)", "required": False}
                ],
                "usage": "Use when agents need to find specific information in documentation, research topics, or understand project structure.",
                "example": '{"query": "authentication flow", "doc_type": ".md", "limit": 10}'
            },
            {
                "name": "get_architecture_info",
                "description": "Extract architecture patterns and design information from documentation",
                "parameters": [],
                "usage": "Use when agents need to understand system architecture, design patterns, or technical decisions.",
                "example": "{}"
            },
            {
                "name": "index_documentation",
                "description": "Re-index all documentation files to update the search database",
                "parameters": [
                    {"name": "force", "description": "Force complete re-indexing", "required": False}
                ],
                "usage": "Use when new documentation has been added or when search results seem outdated.",
                "example": '{"force": true}'
            },
            {
                "name": "search_prompts",
                "description": "Search through available prompt templates by keyword, category, or tags",
                "parameters": [
                    {"name": "query", "description": "Search terms for prompt name/description/tags", "required": True},
                    {"name": "category", "description": "Filter by prompt category", "required": False},
                    {"name": "limit", "description": "Maximum results (1-50)", "required": False}
                ],
                "usage": "Use when agents need to find appropriate prompt templates for specific tasks or domains.",
                "example": '{"query": "code review", "category": "development", "limit": 5}'
            },
            {
                "name": "get_prompt",
                "description": "Retrieve complete details of a specific prompt template by ID",
                "parameters": [
                    {"name": "prompt_id", "description": "Unique identifier of the prompt", "required": True}
                ],
                "usage": "Use when agents have a specific prompt ID and need the full template details and variables.",
                "example": '{"prompt_id": "code-review-template-001"}'
            },
            {
                "name": "suggest_prompts",
                "description": "Get context-aware prompt suggestions based on current task or content",
                "parameters": [
                    {"name": "context", "description": "Description of the current task or context", "required": False}
                ],
                "usage": "Use when agents need help selecting appropriate prompts for their current task.",
                "example": '{"context": "analyzing Python code for security vulnerabilities"}'
            },
            {
                "name": "create_prompt",
                "description": "Create a new custom prompt template for future use",
                "parameters": [
                    {"name": "name", "description": "Name of the prompt", "required": True},
                    {"name": "description", "description": "What the prompt does", "required": True},
                    {"name": "template", "description": "Prompt template with {variable} placeholders", "required": True},
                    {"name": "category", "description": "Prompt category", "required": False},
                    {"name": "variables", "description": "List of variable names used in template", "required": False},
                    {"name": "tags", "description": "Tags for searching and categorization", "required": False}
                ],
                "usage": "Use when agents want to save reusable prompt templates for future tasks.",
                "example": '{"name": "API Analysis", "description": "Analyze API endpoints", "template": "Analyze this API: {api_spec}", "variables": ["api_spec"]}'
            },
            {
                "name": "generate_contextual_prompt",
                "description": "Generate a prompt based on current documentation context and task type",
                "parameters": [
                    {"name": "task", "description": "Task type (code_review, documentation, etc.)", "required": True},
                    {"name": "docs_query", "description": "Query to find relevant documentation", "required": True}
                ],
                "usage": "Use when agents need dynamically generated prompts tailored to specific documentation and tasks.",
                "example": '{"task": "code_review", "docs_query": "authentication security"}'
            },
            {
                "name": "apply_prompt_with_context",
                "description": "Apply a prompt template with documentation context automatically filled",
                "parameters": [
                    {"name": "prompt_id", "description": "ID of prompt template to use", "required": True},
                    {"name": "content", "description": "Content to analyze with the prompt", "required": True},
                    {"name": "auto_fill_context", "description": "Auto-fill context variables", "required": False}
                ],
                "usage": "Use when agents want to apply prompt templates with automatic context filling from documentation.",
                "example": '{"prompt_id": "security-review-001", "content": "function authenticate(user, pass) { ... }", "auto_fill_context": true}'
            }
        ]

    def run(self):
        """Start the GUI application"""
        try:
            self.root.mainloop()
        except Exception as e:
            logger.error(f"GUI error: {e}")
            messagebox.showerror("Error", f"GUI Error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Documentation & Prompts Database Viewer")
    parser.add_argument("--db", default=".docs_prompts_index.db",
                       help="Path to database file")
    parser.add_argument("--gui", action="store_true",
                       help="Launch GUI viewer")

    args = parser.parse_args()

    if args.gui:
        try:
            viewer = DocsPromptsViewer(args.db)
            gui = DocsPromptsGUI(viewer)
            gui.run()
        except FileNotFoundError:
            print(f"❌ Database not found: {args.db}")
            print("💡 Run the MCP server first to create the database")
        except Exception as e:
            print(f"❌ Error launching GUI: {e}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
