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
import yaml
import threading
import asyncio
from datetime import datetime

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
                usage_cursor = conn.execute("SELECT COUNT(*) FROM prompt_usage")
                usage_count = usage_cursor.fetchone()[0]

                # Search index statistics
                search_cursor = conn.execute("SELECT COUNT(*) FROM search_index")
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
                    documents.append(
                        {
                            "path": row[0],
                            "title": row[1],
                            "doc_type": row[2],
                            "metadata": json.loads(row[3]) if row[3] else {},
                            "last_modified": row[4],
                        }
                    )
                return documents
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []

    def get_document_content(self, path: str) -> Optional[Dict[str, Any]]:
        """Get full document content and metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT path, title, content, sections, metadata,
                           last_modified, doc_type, links, code_blocks
                    FROM documents WHERE path = ?
                """,
                    (path,),
                )

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
                    prompts.append(
                        {
                            "id": row[0],
                            "name": row[1],
                            "description": row[2],
                            "category": row[3],
                            "tags": json.loads(row[4]) if row[4] else [],
                            "usage_count": row[5],
                            "effectiveness_score": row[6] or 0.0,
                        }
                    )
                return prompts
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []

    def get_prompt_details(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get full prompt details"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT id, name, description, category, template,
                           variables, tags, created_at, updated_at,
                           usage_count, effectiveness_score
                    FROM prompts WHERE id = ?
                """,
                    (prompt_id,),
                )

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
                    stats.append(
                        {
                            "id": row[0],
                            "name": row[1],
                            "category": row[2],
                            "usage_count": row[3],
                            "effectiveness_score": row[4] or 0.0,
                            "total_uses": row[5],
                            "avg_effectiveness": row[6] or 0.0,
                        }
                    )
                return stats
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []

    def get_remote_documents(self) -> List[Dict[str, Any]]:
        """Get all remote documents"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT path, title, doc_type, metadata, last_modified,
                           file_hash, source_url, repo_name, repo_ref,
                           download_timestamp
                    FROM documents
                    WHERE is_remote = 1
                    ORDER BY download_timestamp DESC
                """)

                documents = []
                for row in cursor.fetchall():
                    documents.append({
                        "path": row[0],
                        "title": row[1],
                        "doc_type": row[2],
                        "metadata": json.loads(row[3]) if row[3] else {},
                        "last_modified": row[4],
                        "file_hash": row[5],
                        "source_url": row[6],
                        "repo_name": row[7],
                        "repo_ref": row[8],
                        "download_timestamp": row[9],
                    })
                return documents
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []

    def get_collection_history(self) -> List[Dict[str, Any]]:
        """Get collection history grouped by repository"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT source_url, repo_name, repo_ref,
                           COUNT(*) as doc_count,
                           MAX(download_timestamp) as last_collected,
                           GROUP_CONCAT(DISTINCT doc_type) as doc_types
                    FROM documents
                    WHERE is_remote = 1 AND source_url IS NOT NULL
                    GROUP BY source_url, repo_name, repo_ref
                    ORDER BY last_collected DESC
                """)

                history = []
                for row in cursor.fetchall():
                    history.append({
                        "url": row[0],
                        "repo_name": row[1],
                        "repo_ref": row[2],
                        "documents": row[3],
                        "timestamp": row[4],
                        "doc_types": row[5].split(',') if row[5] else [],
                        "status": "Completed"  # Assume completed if in history
                    })
                return history
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []

    def is_github_url(self, url: str) -> bool:
        """Check if the given URL is a valid GitHub repository URL."""
        if not url or not isinstance(url, str):
            return False

        url = url.strip().lower()
        if not url.startswith(('http://', 'https://')):
            return False

        # Remove protocol and www
        url = url.replace('http://', '').replace('https://', '').replace('www.', '')

        # Check if it's github.com followed by owner/repo pattern
        if url.startswith('github.com/'):
            parts = url[len('github.com/'):].split('/')
            # Should have at least owner/repo
            return len(parts) >= 2 and parts[0] and parts[1] and not parts[1].endswith(('.git', '.zip', '.tar.gz'))

        return False


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
        self.create_remote_collection_tab()
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
            frame, text="Refresh", command=lambda: self.update_stats(stats_text)
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
        search_entry = ttk.Entry(
            search_frame, textvariable=self.doc_search_var, width=40
        )
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", self.on_document_filter)

        clear_btn = ttk.Button(
            search_frame, text="Clear", command=self.clear_document_filter
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        # Index management buttons
        ttk.Button(
            search_frame, text="Clear All Indexes", command=self.clear_all_indexes
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            search_frame, text="Index All Documents", command=self.index_all_documents
        ).pack(side=tk.LEFT, padx=5)

        # Split pane for documents and content
        paned = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - document list
        left_frame = ttk.Frame(paned)
        paned.add(left_frame)

        # Document list
        columns = ("title", "type", "path")
        self.doc_tree = ttk.Treeview(
            left_frame, columns=columns, show="headings", height=20
        )
        self.doc_tree.heading("title", text="Title")
        self.doc_tree.heading("type", text="Type")
        self.doc_tree.heading("path", text="Path")
        self.doc_tree.column("title", width=200)
        self.doc_tree.column("type", width=50)
        self.doc_tree.column("path", width=300)

        scrollbar = ttk.Scrollbar(
            left_frame, orient=tk.VERTICAL, command=self.doc_tree.yview
        )
        self.doc_tree.configure(yscrollcommand=scrollbar.set)

        self.doc_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Right panel - content viewer
        right_frame = ttk.Frame(paned)
        paned.add(right_frame)

        content_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD)
        content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Bind selection event
        self.doc_tree.bind(
            "<<TreeviewSelect>>", lambda e: self.show_document_content(content_text)
        )

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
        self.prompt_tree = ttk.Treeview(
            left_frame, columns=columns, show="headings", height=20
        )
        self.prompt_tree.heading("name", text="Name")
        self.prompt_tree.heading("category", text="Category")
        self.prompt_tree.heading("usage", text="Usage")

        scrollbar = ttk.Scrollbar(
            left_frame, orient=tk.VERTICAL, command=self.prompt_tree.yview
        )
        self.prompt_tree.configure(yscrollcommand=scrollbar.set)

        self.prompt_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Right panel - prompt details
        right_frame = ttk.Frame(paned)
        paned.add(right_frame)

        details_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD)
        details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Bind selection event
        self.prompt_tree.bind(
            "<<TreeviewSelect>>", lambda e: self.show_prompt_details(details_text)
        )

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
            frame,
            text="Refresh Analytics",
            command=lambda: self.update_analytics(analytics_text),
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
            doc_types = stats["document_types"]
            text_widget.insert(tk.END, f"📁 Document Types: {doc_types}\n")
            text_widget.insert(tk.END, f"🎯 Prompts: {stats['prompts']}\n")
            text_widget.insert(tk.END, f"🏷️ Categories: {stats['categories']}\n")
            text_widget.insert(tk.END, f"📈 Usage Records: {stats['usage_records']}\n")
            text_widget.insert(
                tk.END, f"🔍 Search Entries: {stats['search_entries']}\n"
            )
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
                    doc["title"].lower()
                    + " "
                    + doc["path"].lower()
                    + " "
                    + (doc.get("content", "").lower() if "content" in doc else "")
                )
                if filter_lower in searchable_text:
                    filtered_docs.append(doc)
        else:
            filtered_docs = self.all_documents

        # Display filtered documents
        for doc in filtered_docs:
            self.doc_tree.insert(
                "", tk.END, values=(doc["title"], doc["doc_type"], doc["path"])
            )

        # Update status
        self.status_var.set(
            f"Showing {len(filtered_docs)} of {len(self.all_documents)} documents"
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
            text_widget.insert(tk.END, content["content"] + "\n\n")

            if content["sections"]:
                text_widget.insert(tk.END, "📑 Sections:\n")
                text_widget.insert(tk.END, "-" * 50 + "\n")
                for section in content["sections"]:
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
            self.prompt_tree.insert(
                "",
                tk.END,
                values=(prompt["name"], prompt["category"], prompt["usage_count"]),
            )

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
                text_widget.insert(tk.END, f"🏷️ Category: {details['category']}\n")
                text_widget.insert(tk.END, f"📊 Usage: {details['usage_count']}\n")
                text_widget.insert(
                    tk.END,
                    f"⭐ Effectiveness: {details['effectiveness_score']:.2f}\n\n",
                )

                text_widget.insert(tk.END, "📝 Description:\n")
                text_widget.insert(tk.END, "-" * 50 + "\n")
                text_widget.insert(tk.END, details["description"] + "\n\n")

                text_widget.insert(tk.END, "📋 Template:\n")
                text_widget.insert(tk.END, "-" * 50 + "\n")
                text_widget.insert(tk.END, details["template"] + "\n\n")

                if details["variables"]:
                    text_widget.insert(tk.END, "🔧 Variables:\n")
                    text_widget.insert(tk.END, "-" * 50 + "\n")
                    for var in details["variables"]:
                        text_widget.insert(tk.END, f"• {var}\n")

                if details["tags"]:
                    text_widget.insert(tk.END, "\n🏷️ Tags:\n")
                    text_widget.insert(tk.END, "-" * 50 + "\n")
                    text_widget.insert(tk.END, ", ".join(details["tags"]))
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
                text_widget.insert(
                    tk.END,
                    f"{i}. {stat['name']} ({stat['category']})\n"
                    f"   Usage: {stat['usage_count']} | "
                    f"Effectiveness: "
                    f"{stat['effectiveness_score']:.2f}\n\n",
                )

            # Category breakdown
            categories = {}
            for stat in stats:
                cat = stat["category"]
                categories[cat] = categories.get(cat, 0) + stat["usage_count"]

            text_widget.insert(tk.END, "🏷️ Usage by Category:\n")
            text_widget.insert(tk.END, "-" * 30 + "\n")

            for category, usage in sorted(
                categories.items(), key=lambda x: x[1], reverse=True
            ):
                text_widget.insert(tk.END, f"• {category}: {usage} uses\n")
        else:
            text_widget.insert(tk.END, "❌ Unable to load analytics data")

        self.status_var.set("Analytics updated")

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

        text_widget.insert(
            tk.END, "This MCP server provides tools that AI agents can use to:\n"
        )
        text_widget.insert(tk.END, "• Search and access documentation\n")
        text_widget.insert(tk.END, "• Manage and use prompt templates\n")
        text_widget.insert(tk.END, "• Extract architecture information\n")
        text_widget.insert(tk.END, "• Generate contextual prompts\n\n")

        for tool in tools_info:
            text_widget.insert(tk.END, f"🔧 {tool['name']}\n")
            text_widget.insert(tk.END, "-" * 40 + "\n")
            text_widget.insert(tk.END, f"📝 {tool['description']}\n\n")

            if tool["parameters"]:
                text_widget.insert(tk.END, "📋 Parameters:\n")
                for param in tool["parameters"]:
                    required = " (required)" if param["required"] else " (optional)"
                    text_widget.insert(
                        tk.END,
                        f"  • {param['name']}: {param['description']}{required}\n",
                    )
                text_widget.insert(tk.END, "\n")

            text_widget.insert(tk.END, f"🎯 Agent Usage:\n{tool['usage']}\n\n")
            text_widget.insert(tk.END, "💡 Example:\n" + tool["example"] + "\n\n")
            text_widget.insert(tk.END, "=" * 60 + "\n\n")

    def get_mcp_tools_info(self):
        """Get formatted information about all MCP tools from YAML config"""
        config_dir = Path(__file__).parent.parent / "config"
        config_path = config_dir / "mcp_tools_info.yaml"
        logger.info("Loading MCP tools config from %s", config_path)
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("tools", [])
        except FileNotFoundError:
            logger.error("MCP tools config not found at %s", config_path)
            return []
        except yaml.YAMLError as e:
            logger.error("Error parsing MCP tools config: %s", e)
            return []
        except Exception as e:
            logger.error("Unexpected error loading MCP tools config: %s", e)
            return []

    def create_remote_collection_tab(self):
        """Create the remote collection tab for URL-based document collection."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Remote Collection")

        # URL input section
        url_frame = ttk.LabelFrame(frame, text="GitHub Repository URL", padding=10)
        url_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(url_frame, text="Repository URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.url_entry = ttk.Entry(url_frame, width=60)
        self.url_entry.grid(row=0, column=1, padx=(10, 0), pady=2, sticky=tk.EW)

        # Example URLs
        example_frame = ttk.Frame(url_frame)
        example_frame.grid(row=1, column=0, columnspan=2, pady=(5, 0))
        ttk.Label(example_frame, text="Examples:").pack(anchor=tk.W)
        examples = [
            "https://github.com/microsoft/vscode",
            "https://github.com/python/cpython",
            "https://github.com/torvalds/linux"
        ]
        for example in examples:
            ttk.Label(example_frame, text=f"• {example}", foreground="blue").pack(anchor=tk.W)

        # Collection controls
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        self.collect_button = ttk.Button(
            control_frame,
            text="Collect from URL",
            command=self.start_collection
        )
        self.collect_button.pack(side=tk.LEFT, padx=(0, 10))

        self.cancel_button = ttk.Button(
            control_frame,
            text="Cancel",
            command=self.cancel_collection,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT)

        # Progress section
        progress_frame = ttk.LabelFrame(frame, text="Collection Progress", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)

        self.progress_var = tk.StringVar(value="Ready to collect documents...")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.pack(anchor=tk.W)

        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))

        # Collection history section
        history_frame = ttk.LabelFrame(frame, text="Collection History", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # History treeview
        columns = ("timestamp", "url", "status", "documents")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=8)

        self.history_tree.heading("timestamp", text="Timestamp")
        self.history_tree.heading("url", text="Repository URL")
        self.history_tree.heading("status", text="Status")
        self.history_tree.heading("documents", text="Documents")

        self.history_tree.column("timestamp", width=150)
        self.history_tree.column("url", width=300)
        self.history_tree.column("status", width=100)
        self.history_tree.column("documents", width=100)

        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # History controls
        history_control_frame = ttk.Frame(history_frame)
        history_control_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(
            history_control_frame,
            text="Refresh History",
            command=self.refresh_collection_history
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            history_control_frame,
            text="View Remote Documents",
            command=self.view_remote_documents
        ).pack(side=tk.LEFT)

        # Bind double-click to view details
        self.history_tree.bind("<Double-1>", self.show_collection_details)

        # Initialize collection state
        self.collection_thread = None
        self.collection_cancelled = False

        # Load initial history
        self.refresh_collection_history()

    def start_collection(self):
        """Start collecting documents from the entered URL."""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a GitHub repository URL")
            return

        # Validate URL format
        if not self.viewer.is_github_url(url):
            messagebox.showerror("Error", "Please enter a valid GitHub repository URL")
            return

        # Disable controls and start collection
        self.collect_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.url_entry.config(state=tk.DISABLED)
        self.progress_var.set("Starting collection...")
        self.progress_bar.start()
        self.collection_cancelled = False

        # Start collection in background thread
        self.collection_thread = threading.Thread(target=self._collect_documents, args=(url,))
        self.collection_thread.daemon = True
        self.collection_thread.start()

    def cancel_collection(self):
        """Cancel the current collection operation."""
        self.collection_cancelled = True
        self.progress_var.set("Cancelling collection...")
        self.cancel_button.config(state=tk.DISABLED)

    def _collect_documents(self, url):
        """Background thread for document collection."""
        try:
            self.root.after(0, lambda: self.progress_var.set("Collecting documents from repository..."))

            # Use the server's document indexer to collect from URL
            if self.server and hasattr(self.server, 'document_indexer'):
                result = asyncio.run(self.server.document_indexer.index_remote_repository(url))

                if self.collection_cancelled:
                    self.root.after(0, lambda: self.progress_var.set("Collection cancelled"))
                else:
                    success_count = result.get("success_count", 0)
                    error_count = result.get("error_count", 0)
                    self.root.after(0, lambda: self.progress_var.set(
                        f"Collection complete! {success_count} documents collected, {error_count} errors"
                    ))

                    # Refresh history
                    self.root.after(0, self.refresh_collection_history)

                    # Show success message
                    if success_count > 0:
                        self.root.after(0, lambda: messagebox.showinfo(
                            "Success",
                            f"Successfully collected {success_count} documents from {url}"
                        ))
                    elif error_count > 0:
                        self.root.after(0, lambda: messagebox.showwarning(
                            "Partial Success",
                            f"Collection completed with {error_count} errors. Check logs for details."
                        ))
                    else:
                        self.root.after(0, lambda: messagebox.showwarning(
                            "No Documents",
                            "No documents were found in the repository"
                        ))
            else:
                self.root.after(0, lambda: self.progress_var.set("Server not available for collection"))

        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.progress_var.set(f"Collection failed: {error_msg}"))
            self.root.after(0, lambda: messagebox.showerror("Collection Error", f"Failed to collect documents: {error_msg}"))

        finally:
            # Re-enable controls
            self.root.after(0, lambda: self._reset_collection_controls())

    def _reset_collection_controls(self):
        """Reset collection control states."""
        self.collect_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.url_entry.config(state=tk.NORMAL)
        self.progress_bar.stop()

    def refresh_collection_history(self):
        """Refresh the collection history display."""
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        try:
            # Get collection history from viewer
            history = self.viewer.get_collection_history()

            for entry in history:
                timestamp = entry.get("timestamp", "")
                url = entry.get("url", "")
                status = entry.get("status", "Unknown")
                documents = entry.get("documents", 0)

                # Format timestamp
                if timestamp:
                    try:
                        # Assume timestamp is ISO format
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        timestamp = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass  # Keep original format if parsing fails

                self.history_tree.insert("", tk.END, values=(timestamp, url, status, documents))

        except Exception as e:
            logger.error(f"Failed to load collection history: {e}")
            messagebox.showerror("Error", f"Failed to load collection history: {e}")

    def view_remote_documents(self):
        """Switch to documents tab and filter for remote documents."""
        # Switch to documents tab
        self.notebook.select(1)  # Documents tab is index 1

        # Set filter to show only remote documents
        # This would need to be implemented in the documents tab
        # For now, just show a message
        messagebox.showinfo("Remote Documents", "Switched to Documents tab. Use the search to filter for remote documents.")

    def show_collection_details(self, event):
        """Show details of the selected collection."""
        selection = self.history_tree.selection()
        if not selection:
            return

        item = self.history_tree.item(selection[0])
        values = item['values']
        url = values[1]  # URL is in second column

        # Show basic details in a message box
        details = f"Repository: {url}\nTimestamp: {values[0]}\nStatus: {values[2]}\nDocuments: {values[3]}"
        messagebox.showinfo("Collection Details", details)

    def run(self):
        """Start the GUI application"""
        try:
            self.root.mainloop()
        except Exception as e:
            logger.error(f"GUI error: {e}")
            messagebox.showerror("Error", f"GUI Error: {e}")

    def clear_all_indexes(self):
        """Clear all documents and search indexes"""
        if messagebox.askyesno(
            "Confirm Clear",
            "Are you sure you want to clear all indexes? "
            "This will delete all indexed documents.",
        ):
            try:
                if self.server:
                    self.server.clear_index()
                    messagebox.showinfo("Success", "All indexes cleared successfully!")
                    self.status_var.set("Indexes cleared")
                    # Refresh the document list
                    self.load_all_documents()
                else:
                    messagebox.showerror("Error", "Server not available")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear indexes: {e}")

    def index_all_documents(self):
        """Index all documents in the project"""
        try:
            if self.server:
                # Run indexing in a separate thread to avoid blocking GUI
                import threading

                def do_index():
                    try:
                        # Use synchronous indexing to avoid nested
                        # event loop issues
                        result = self.server.index_all_documents_sync()
                        self.root.after(
                            0, lambda: self._show_index_result(result)
                        )
                    except Exception as e:
                        error_msg = str(e)
                        self.root.after(
                            0,
                            lambda: messagebox.showerror(
                                "Error",
                                f"Failed to index documents: {error_msg}"
                            ),
                        )

                threading.Thread(target=do_index, daemon=True).start()
                self.status_var.set("Indexing documents...")
            else:
                messagebox.showerror("Error", "Server not available")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start indexing: {e}")

    def _show_index_result(self, result):
        """Show the result of document indexing"""
        indexed = result.get("indexed_count", 0)
        errors = result.get("error_count", 0)
        total = result.get("total_documents", 0)

        message = (
            f"Indexing complete!\n"
            f"Indexed: {indexed}\n"
            f"Errors: {errors}\n"
            f"Total documents: {total}"
        )
        messagebox.showinfo("Indexing Complete", message)
        self.status_var.set(f"Indexed {indexed} documents")

        # Refresh the document list
        self.load_all_documents()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Documentation & Prompts Database Viewer"
    )
    parser.add_argument(
        "--db", default=".docs_prompts_index.db", help="Path to database file"
    )
    parser.add_argument("--gui", action="store_true", help="Launch GUI viewer")

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
