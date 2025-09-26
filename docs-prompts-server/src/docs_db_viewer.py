#!/usr/bin/env python3
"""
Docs-Prompts Database Viewer
A frontend to explore the .docs_prompts_index.db file and understand
what the docs-prompts-server is doing.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse

# GUI imports
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

# MCP server integration
import asyncio
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from docs_prompts_mcp_server import DocumentationPromptsServer


class DocsPromptsViewer:
    """Frontend viewer for the docs-prompts database"""

    def __init__(self, db_path: str = ".docs_prompts_index.db"):
        # Try multiple possible locations for the database, prioritizing project root
        possible_paths = [
            Path(__file__).parent.parent.parent / ".docs_prompts_index.db",  # Project root first
            Path(db_path) if Path(db_path).is_absolute() else Path.cwd() / db_path,
            Path(__file__).parent.parent / ".docs_prompts_index.db",
            Path.cwd() / ".docs_prompts_index.db"
        ]
        
        self.db_path = None
        for path in possible_paths:
            if path.exists():
                self.db_path = path
                break
        
        if self.db_path is None:
            print("❌ Database not found. Tried locations:")
            for path in possible_paths:
                print(f"   {path}")
            print("Make sure the docs-prompts-server has been run to "
                  "create the database.")
            exit(1)

    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Document statistics
            doc_cursor = conn.execute(
                "SELECT COUNT(*), SUM(LENGTH(content)) FROM documents")
            doc_count, total_content_size = doc_cursor.fetchone()

            # Prompt statistics
            prompt_cursor = conn.execute(
                "SELECT COUNT(*), SUM(usage_count) FROM prompts")
            prompt_count, total_usage = prompt_cursor.fetchone()

            # Search index statistics
            search_cursor = conn.execute("SELECT COUNT(*) FROM search_index")
            search_count = search_cursor.fetchone()[0]

            # Usage statistics
            usage_cursor = conn.execute("SELECT COUNT(*) FROM prompt_usage")
            usage_count = usage_cursor.fetchone()[0]

            return {
                "documents": {
                    "total_count": doc_count or 0,
                    "total_content_size_kb": round((total_content_size or 0) / 1024, 2)
                },
                "prompts": {
                    "total_count": prompt_count or 0,
                    "total_usage": total_usage or 0
                },
                "search_index": {
                    "total_chunks": search_count
                },
                "usage_tracking": {
                    "total_usage_records": usage_count
                }
            }

    def list_documents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all indexed documents"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT path, title, doc_type, metadata, last_modified, LENGTH(content) as size
                FROM documents
                ORDER BY title
                LIMIT ?
            """, (limit,))

            documents = []
            for row in cursor.fetchall():
                documents.append({
                    "path": row[0],
                    "title": row[1],
                    "doc_type": row[2],
                    "metadata": json.loads(row[3]),
                    "last_modified": datetime.fromtimestamp(
                        row[4]).strftime('%Y-%m-%d %H:%M:%S'),
                    "size_bytes": row[5]
                })

            return documents

    def list_prompts(self, category: Optional[str] = None,
                     limit: int = 50) -> List[Dict[str, Any]]:
        """List all prompts, optionally filtered by category"""
        with sqlite3.connect(self.db_path) as conn:
            if category:
                cursor = conn.execute("""
                    SELECT id, name, description, category, tags,
                           usage_count, effectiveness_score
                    FROM prompts
                    WHERE category = ?
                    ORDER BY usage_count DESC, name
                    LIMIT ?
                """, (category, limit))
            else:
                cursor = conn.execute("""
                    SELECT id, name, description, category, tags,
                           usage_count, effectiveness_score
                    FROM prompts
                    ORDER BY category, usage_count DESC, name
                    LIMIT ?
                """, (limit,))

            prompts = []
            for row in cursor.fetchall():
                prompts.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "category": row[3],
                    "tags": json.loads(row[4]),
                    "usage_count": row[5],
                    "effectiveness_score": row[6] or 0
                })

            return prompts

    def get_categories(self) -> List[str]:
        """Get all prompt categories"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT DISTINCT category FROM prompts ORDER BY category")
            return [row[0] for row in cursor.fetchall()]

    def search_documents(self, query: str,
                         limit: int = 20) -> List[Dict[str, Any]]:
        """Search documents using the same logic as the server"""
        with sqlite3.connect(self.db_path) as conn:
            sql = """
                SELECT DISTINCT d.path, d.title, d.doc_type, d.metadata,
                                s.section_title, s.content_chunk, s.chunk_type
                FROM documents d
                JOIN search_index s ON d.path = s.doc_path
                WHERE (s.content_chunk LIKE ? OR d.title LIKE ?)
                ORDER BY (CASE WHEN d.title LIKE ? THEN 1 ELSE 2 END), d.title
                LIMIT ?
            """
            params = [f"%{query}%", f"%{query}%", f"%{query}%", limit]

            cursor = conn.execute(sql, params)
            results = []

            for row in cursor.fetchall():
                results.append({
                    "path": row[0],
                    "title": row[1],
                    "doc_type": row[2],
                    "metadata": json.loads(row[3]),
                    "section_title": row[4],
                    "content_snippet": row[5][:500] + "..." if len(row[5]) > 500 else row[5],
                    "chunk_type": row[6]
                })

            return results

    def get_architecture_info(self) -> Dict[str, Any]:
        """Get architecture-related information"""
        arch_keywords = [
            "architecture", "design", "pattern", "microservice", "api",
            "endpoint", "service", "component", "module", "database",
            "schema", "model", "workflow", "deployment", "infrastructure"
        ]

        results = []
        for keyword in arch_keywords:
            search_results = self.search_documents(keyword, limit=3)
            results.extend(search_results)

        # Remove duplicates
        seen = set()
        unique_results = []
        for result in results:
            if result["path"] not in seen:
                seen.add(result["path"])
                unique_results.append(result)

        return {
            "architecture_documents": unique_results,
            "total_count": len(unique_results),
            "keywords_searched": arch_keywords
        }

    def get_prompt_usage_stats(self) -> List[Dict[str, Any]]:
        """Get prompt usage statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT p.id, p.name, p.category, p.usage_count, p.effectiveness_score,
                       COUNT(pu.id) as total_uses, AVG(pu.effectiveness) as avg_effectiveness
                FROM prompts p
                LEFT JOIN prompt_usage pu ON p.id = pu.prompt_id
                GROUP BY p.id
                ORDER BY p.usage_count DESC
            """)

            stats = []
            for row in cursor.fetchall():
                stats.append({
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "usage_count": row[3],
                    "effectiveness_score": row[4],
                    "total_uses": row[5],
                    "avg_effectiveness": row[6] or 0
                })

            return stats

    def show_document_details(self, doc_path: str) -> Optional[Dict[str, Any]]:
        """Show detailed information about a specific document"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT path, title, content, sections, metadata, last_modified,
                       file_hash, doc_type, links, code_blocks, indexed_at
                FROM documents
                WHERE path = ?
            """, (doc_path,))

            result = cursor.fetchone()
            if result:
                return {
                    "path": result[0],
                    "title": result[1],
                    "content": result[2],
                    "sections": json.loads(result[3]),
                    "metadata": json.loads(result[4]),
                    "last_modified": datetime.fromtimestamp(
                        result[5]).strftime('%Y-%m-%d %H:%M:%S'),
                    "file_hash": result[6],
                    "doc_type": result[7],
                    "links": json.loads(result[8]),
                    "code_blocks": json.loads(result[9]),
                    "indexed_at": datetime.fromtimestamp(
                        result[10]).strftime('%Y-%m-%d %H:%M:%S')
                }
            return None

    def show_prompt_details(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Show detailed information about a specific prompt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, name, description, category, template, variables, tags,
                       created_at, updated_at, usage_count, effectiveness_score
                FROM prompts
                WHERE id = ?
            """, (prompt_id,))

            result = cursor.fetchone()
            if result:
                return {
                    "id": result[0],
                    "name": result[1],
                    "description": result[2],
                    "category": result[3],
                    "template": result[4],
                    "variables": json.loads(result[5]),
                    "tags": json.loads(result[6]),
                    "created_at": datetime.fromtimestamp(result[7]).strftime('%Y-%m-%d %H:%M:%S'),
                    "updated_at": datetime.fromtimestamp(
                        result[8]).strftime('%Y-%m-%d %H:%M:%S'),
                    "usage_count": result[9],
                    "effectiveness_score": result[10] or 0
                }
            return None


class DocsPromptsGUI:
    """GUI interface for the docs-prompts database viewer"""

    def __init__(self, viewer: DocsPromptsViewer, server: Optional['DocumentationPromptsServer'] = None):
        self.viewer = viewer
        # Use provided server instance or create a new one for tool execution
        if server is not None:
            self.mcp_server = server
            self.mcp_available = True
        else:
            # Initialize MCP server for real tool execution (mandatory)
            # Use the parent directory of the project as the project root
            import os
            project_root = os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))))
            # Import dynamically to avoid global instance creation issues
            from docs_prompts_mcp_server import DocumentationPromptsServer
            self.mcp_server = DocumentationPromptsServer(project_root)
            self.mcp_available = True
        self.root = tk.Tk()
        self.root.title("Docs-Prompts Database Viewer")
        self.root.geometry("1200x800")

        # Status bar (create first)
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Create main notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.create_overview_tab()
        self.create_documents_tab()
        self.create_prompts_tab()
        self.create_search_tab()
        self.create_tools_tab()

    def create_overview_tab(self):
        """Create the overview/statistics tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Overview")

        # Stats display
        stats_frame = ttk.LabelFrame(frame, text="Database Statistics", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.stats_text = scrolledtext.ScrolledText(stats_frame, wrap=tk.WORD,
                                                   height=15, font=("Courier", 10))
        self.stats_text.pack(fill=tk.BOTH, expand=True)

        # Refresh button
        refresh_btn = ttk.Button(frame, text="Refresh Statistics",
                                command=self.refresh_overview)
        refresh_btn.pack(pady=5)

        # Initial load
        self.refresh_overview()

    def create_documents_tab(self):
        """Create the documents browsing tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Documents")

        # Treeview for documents
        tree_frame = ttk.LabelFrame(frame, text="Indexed Documents", padding=10)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview with scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ("title", "type", "size", "modified")
        self.docs_tree = ttk.Treeview(tree_frame, columns=columns,
                                     show="headings", yscrollcommand=tree_scroll.set)

        # Configure columns
        self.docs_tree.heading("title", text="Title")
        self.docs_tree.heading("type", text="Type")
        self.docs_tree.heading("size", text="Size (bytes)")
        self.docs_tree.heading("modified", text="Last Modified")

        self.docs_tree.column("title", width=300)
        self.docs_tree.column("type", width=100)
        self.docs_tree.column("size", width=100)
        self.docs_tree.column("modified", width=150)

        self.docs_tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.docs_tree.yview)

        # Bind selection event
        self.docs_tree.bind("<<TreeviewSelect>>", self.on_document_select)

        # Document details panel
        details_frame = ttk.LabelFrame(frame, text="Document Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.doc_details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD,
                                                        height=10, font=("Courier", 9))
        self.doc_details_text.pack(fill=tk.BOTH, expand=True)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        refresh_docs_btn = ttk.Button(btn_frame, text="Refresh Documents",
                                     command=self.refresh_documents)
        refresh_docs_btn.pack(side=tk.LEFT, padx=5)

        # Initial load
        self.refresh_documents()

    def create_prompts_tab(self):
        """Create the prompts browsing tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Prompts")

        # Category filter
        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(filter_frame, text="Category:").pack(side=tk.LEFT, padx=5)
        self.category_var = tk.StringVar(value="All")
        self.category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var,
                                          state="readonly")
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind("<<ComboboxSelected>>", self.on_category_change)

        # Treeview for prompts
        tree_frame = ttk.LabelFrame(frame, text="Available Prompts", padding=10)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview with scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ("name", "category", "usage", "score")
        self.prompts_tree = ttk.Treeview(tree_frame, columns=columns,
                                        show="headings", yscrollcommand=tree_scroll.set)

        # Configure columns
        self.prompts_tree.heading("name", text="Name")
        self.prompts_tree.heading("category", text="Category")
        self.prompts_tree.heading("usage", text="Usage Count")
        self.prompts_tree.heading("score", text="Score")

        self.prompts_tree.column("name", width=250)
        self.prompts_tree.column("category", width=150)
        self.prompts_tree.column("usage", width=100)
        self.prompts_tree.column("score", width=80)

        self.prompts_tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.prompts_tree.yview)

        # Bind selection event
        self.prompts_tree.bind("<<TreeviewSelect>>", self.on_prompt_select)

        # Prompt details panel
        details_frame = ttk.LabelFrame(frame, text="Prompt Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.prompt_details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD,
                                                           height=10, font=("Courier", 9))
        self.prompt_details_text.pack(fill=tk.BOTH, expand=True)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        refresh_prompts_btn = ttk.Button(btn_frame, text="Refresh Prompts",
                                        command=self.refresh_prompts)
        refresh_prompts_btn.pack(side=tk.LEFT, padx=5)

        # Initial load
        self.refresh_prompts()

    def create_search_tab(self):
        """Create the search tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Search")

        # Search input
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(search_frame, text="Search Query:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.perform_search())

        search_btn = ttk.Button(search_frame, text="Search",
                               command=self.perform_search)
        search_btn.pack(side=tk.LEFT, padx=5)

        # Results treeview
        results_frame = ttk.LabelFrame(frame, text="Search Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview with scrollbar
        tree_scroll = ttk.Scrollbar(results_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ("title", "section", "snippet")
        self.search_tree = ttk.Treeview(results_frame, columns=columns,
                                       show="headings", yscrollcommand=tree_scroll.set)

        # Configure columns
        self.search_tree.heading("title", text="Document")
        self.search_tree.heading("section", text="Section")
        self.search_tree.heading("snippet", text="Content Snippet")

        self.search_tree.column("title", width=250)
        self.search_tree.column("section", width=200)
        self.search_tree.column("snippet", width=400)

        self.search_tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.search_tree.yview)

        # Bind selection event
        self.search_tree.bind("<<TreeviewSelect>>", self.on_search_result_select)

        # Result details
        details_frame = ttk.LabelFrame(frame, text="Result Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.search_details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD,
                                                           height=8, font=("Courier", 9))
        self.search_details_text.pack(fill=tk.BOTH, expand=True)

    def refresh_overview(self):
        """Refresh the overview statistics"""
        try:
            stats = self.viewer.get_database_stats()
            self.stats_text.delete(1.0, tk.END)

            self.stats_text.insert(tk.END, "📊 DATABASE STATISTICS\n")
            self.stats_text.insert(tk.END, "=" * 50 + "\n\n")

            self.stats_text.insert(tk.END,
                f"📚 Documents: {stats['documents']['total_count']}\n")
            self.stats_text.insert(tk.END,
                f"   Content Size: {stats['documents']['total_content_size_kb']} KB\n\n")

            self.stats_text.insert(tk.END,
                f"🎯 Prompts: {stats['prompts']['total_count']}\n")
            self.stats_text.insert(tk.END,
                f"   Total Usage: {stats['prompts']['total_usage']}\n\n")

            self.stats_text.insert(tk.END,
                f"🔍 Search Index: {stats['search_index']['total_chunks']} chunks\n\n")

            self.stats_text.insert(tk.END,
                f"📈 Usage Tracking: {stats['usage_tracking']['total_usage_records']} records\n")

            self.status_var.set("Statistics refreshed")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh statistics: {e}")
            self.status_var.set("Error refreshing statistics")

    def refresh_documents(self):
        """Refresh the documents list"""
        try:
            # Clear existing items
            for item in self.docs_tree.get_children():
                self.docs_tree.delete(item)

            docs = self.viewer.list_documents(limit=100)

            for doc in docs:
                self.docs_tree.insert("", tk.END, values=(
                    doc["title"],
                    doc["doc_type"],
                    doc["size_bytes"],
                    doc["last_modified"]
                ), tags=(doc["path"],))

            self.status_var.set(f"Loaded {len(docs)} documents")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh documents: {e}")
            self.status_var.set("Error refreshing documents")

    def refresh_prompts(self):
        """Refresh the prompts list and categories"""
        try:
            # Update categories
            categories = ["All"] + self.viewer.get_categories()
            self.category_combo["values"] = categories

            # Clear existing items
            for item in self.prompts_tree.get_children():
                self.prompts_tree.delete(item)

            category = self.category_var.get()
            if category == "All":
                prompts = self.viewer.list_prompts(limit=100)
            else:
                prompts = self.viewer.list_prompts(category=category, limit=100)

            for prompt in prompts:
                self.prompts_tree.insert("", tk.END, values=(
                    prompt["name"],
                    prompt["category"],
                    prompt["usage_count"],
                    f"{prompt['effectiveness_score']:.1f}"
                ), tags=(prompt["id"],))

            self.status_var.set(f"Loaded {len(prompts)} prompts")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh prompts: {e}")
            self.status_var.set("Error refreshing prompts")

    def perform_search(self):
        """Perform search and display results"""
        query = self.search_var.get().strip()
        if not query:
            return

        try:
            # Clear existing results
            for item in self.search_tree.get_children():
                self.search_tree.delete(item)

            results = self.viewer.search_documents(query, limit=50)

            for result in results:
                self.search_tree.insert("", tk.END, values=(
                    result["title"],
                    result["section_title"] or "N/A",
                    result["content_snippet"]
                ), tags=(result["path"],))

            self.status_var.set(f"Found {len(results)} search results for '{query}'")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to perform search: {e}")
            self.status_var.set("Error performing search")

    def on_document_select(self, event):
        """Handle document selection"""
        selection = self.docs_tree.selection()
        if selection:
            item = selection[0]
            doc_path = self.docs_tree.item(item, "tags")[0]

            try:
                doc = self.viewer.show_document_details(doc_path)
                if doc:
                    self.doc_details_text.delete(1.0, tk.END)
                    self.doc_details_text.insert(tk.END, f"Path: {doc['path']}\n")
                    self.doc_details_text.insert(tk.END, f"Title: {doc['title']}\n")
                    self.doc_details_text.insert(tk.END, f"Type: {doc['doc_type']}\n")
                    self.doc_details_text.insert(tk.END, f"Size: {len(doc['content'])} characters\n")
                    self.doc_details_text.insert(tk.END, f"Sections: {len(doc['sections'])}\n")
                    self.doc_details_text.insert(tk.END, f"Links: {len(doc['links'])}\n")
                    self.doc_details_text.insert(tk.END, f"Code blocks: {len(doc['code_blocks'])}\n")
                    self.doc_details_text.insert(tk.END, f"Last modified: {doc['last_modified']}\n")
                    self.doc_details_text.insert(tk.END, f"Indexed at: {doc['indexed_at']}\n\n")
                    self.doc_details_text.insert(tk.END, f"Content preview:\n{doc['content'][:5000]}...")
                else:
                    self.doc_details_text.delete(1.0, tk.END)
                    self.doc_details_text.insert(tk.END, f"Document not found: {doc_path}")

            except Exception as e:
                self.doc_details_text.delete(1.0, tk.END)
                self.doc_details_text.insert(tk.END, f"Error loading document: {e}")

    def on_prompt_select(self, event):
        """Handle prompt selection"""
        selection = self.prompts_tree.selection()
        if selection:
            item = selection[0]
            prompt_id = self.prompts_tree.item(item, "tags")[0]

            try:
                prompt = self.viewer.show_prompt_details(prompt_id)
                if prompt:
                    self.prompt_details_text.delete(1.0, tk.END)
                    self.prompt_details_text.insert(tk.END, f"ID: {prompt['id']}\n")
                    self.prompt_details_text.insert(tk.END, f"Name: {prompt['name']}\n")
                    self.prompt_details_text.insert(tk.END, f"Category: {prompt['category']}\n")
                    self.prompt_details_text.insert(tk.END, f"Description: {prompt['description']}\n")
                    self.prompt_details_text.insert(tk.END, f"Variables: {', '.join(prompt['variables'])}\n")
                    self.prompt_details_text.insert(tk.END, f"Tags: {', '.join(prompt['tags'])}\n")
                    self.prompt_details_text.insert(tk.END, f"Usage count: {prompt['usage_count']}\n")
                    self.prompt_details_text.insert(tk.END, f"Effectiveness: {prompt['effectiveness_score']:.1f}\n")
                    self.prompt_details_text.insert(tk.END, f"Created: {prompt['created_at']}\n")
                    self.prompt_details_text.insert(tk.END, f"Updated: {prompt['updated_at']}\n\n")
                    self.prompt_details_text.insert(tk.END, f"Template:\n{prompt['template']}")
                else:
                    self.prompt_details_text.delete(1.0, tk.END)
                    self.prompt_details_text.insert(tk.END, f"Prompt not found: {prompt_id}")

            except Exception as e:
                self.prompt_details_text.delete(1.0, tk.END)
                self.prompt_details_text.insert(tk.END, f"Error loading prompt: {e}")

    def on_category_change(self, event):
        """Handle category filter change"""
        self.refresh_prompts()

    def on_search_result_select(self, event):
        """Handle search result selection"""
        selection = self.search_tree.selection()
        if selection:
            item = selection[0]
            doc_path = self.search_tree.item(item, "tags")[0]

            try:
                doc = self.viewer.show_document_details(doc_path)
                if doc:
                    self.search_details_text.delete(1.0, tk.END)
                    self.search_details_text.insert(tk.END, f"Document: {doc['title']}\n")
                    self.search_details_text.insert(tk.END, f"Path: {doc['path']}\n")
                    self.search_details_text.insert(tk.END, f"Type: {doc['doc_type']}\n")
                    self.search_details_text.insert(tk.END, f"Last modified: {doc['last_modified']}\n\n")
                    self.search_details_text.insert(tk.END, f"Full content:\n{doc['content']}")
                else:
                    self.search_details_text.delete(1.0, tk.END)
                    self.search_details_text.insert(tk.END, f"Document not found: {doc_path}")

            except Exception as e:
                self.search_details_text.delete(1.0, tk.END)
                self.search_details_text.insert(tk.END, f"Error loading document: {e}")

    def create_tools_tab(self):
        """Create the tools execution tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Tools")

        # Tool selection
        selection_frame = ttk.LabelFrame(frame, text="Tool Selection", padding=10)
        selection_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(selection_frame, text="Select Tool:").pack(side=tk.LEFT, padx=5)
        self.tool_var = tk.StringVar()
        self.tool_combo = ttk.Combobox(selection_frame, textvariable=self.tool_var,
                                      state="readonly", width=40)
        self.tool_combo.pack(side=tk.LEFT, padx=5)
        self.tool_combo.bind("<<ComboboxSelected>>", self.on_tool_select)

        # Tool description
        self.tool_desc_label = ttk.Label(selection_frame, text="", wraplength=400)
        self.tool_desc_label.pack(side=tk.LEFT, padx=20)

        # Parameters frame
        self.params_frame = ttk.LabelFrame(frame, text="Parameters", padding=10)
        self.params_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollable frame for parameters
        self.params_canvas = tk.Canvas(self.params_frame)
        self.params_scrollbar = ttk.Scrollbar(self.params_frame, orient="vertical",
                                             command=self.params_canvas.yview)
        self.params_scrollable_frame = ttk.Frame(self.params_canvas)

        self.params_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.params_canvas.configure(scrollregion=self.params_canvas.bbox("all"))
        )

        self.params_canvas.create_window((0, 0), window=self.params_scrollable_frame, anchor="nw")
        self.params_canvas.configure(yscrollcommand=self.params_scrollbar.set)

        self.params_canvas.pack(side="left", fill="both", expand=True)
        self.params_scrollbar.pack(side="right", fill="y")

        # Execute button
        execute_btn = ttk.Button(frame, text="Execute Tool",
                                command=self.execute_tool)
        execute_btn.pack(pady=10)

        # Results frame
        results_frame = ttk.LabelFrame(frame, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tool_results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD,
                                                          height=15, font=("Courier", 9))
        self.tool_results_text.pack(fill=tk.BOTH, expand=True)

        # Initialize tools
        self.available_tools = self.get_available_tools()
        tool_names = [tool["name"] for tool in self.available_tools]
        self.tool_combo["values"] = tool_names

        # Parameter input widgets storage
        self.param_widgets = {}

    def get_available_tools(self):
        """Get list of available MCP tools"""
        return [
            {
                "name": "search_docs",
                "description": "Search documentation using keywords or phrases",
                "parameters": {
                    "query": {"type": "string", "description": "Search query (keywords or phrases)", "required": True},
                    "doc_type": {"type": "string", "description": "Filter by document type (.md, .rst, .yaml, etc.)", "required": False},
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 10, "required": False}
                }
            },
            {
                "name": "get_architecture_info",
                "description": "Extract architecture patterns and design information",
                "parameters": {}
            },
            {
                "name": "index_documentation",
                "description": "Re-index all documentation files",
                "parameters": {
                    "force": {"type": "boolean", "description": "Force re-indexing of all files", "default": False, "required": False}
                }
            },
            {
                "name": "search_prompts",
                "description": "Search prompts by keyword, category, or tags",
                "parameters": {
                    "query": {"type": "string", "description": "Search query for prompt name, description, or tags", "required": True},
                    "category": {"type": "string", "description": "Filter by prompt category", "required": False},
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 10, "required": False}
                }
            },
            {
                "name": "get_prompt",
                "description": "Retrieve a specific prompt by ID with full details",
                "parameters": {
                    "prompt_id": {"type": "string", "description": "ID of the prompt to retrieve", "required": True}
                }
            },
            {
                "name": "suggest_prompts",
                "description": "Get context-aware prompt suggestions",
                "parameters": {
                    "context": {"type": "string", "description": "Context description for prompt suggestions (optional)", "required": False}
                }
            },
            {
                "name": "create_prompt",
                "description": "Create a new custom prompt",
                "parameters": {
                    "name": {"type": "string", "description": "Name of the prompt", "required": True},
                    "description": {"type": "string", "description": "Description of what the prompt does", "required": True},
                    "template": {"type": "string", "description": "The prompt template with variables in {variable} format", "required": True},
                    "category": {"type": "string", "description": "Prompt category", "default": "custom", "required": False},
                    "variables": {"type": "array", "description": "List of variable names used in the template", "required": False},
                    "tags": {"type": "array", "description": "Tags for categorizing and searching", "required": False}
                }
            },
            {
                "name": "generate_contextual_prompt",
                "description": "Generate a prompt based on current documentation context",
                "parameters": {
                    "task": {"type": "string", "description": "The task type (e.g., 'code_review', 'documentation', 'architecture_analysis')", "required": True},
                    "docs_query": {"type": "string", "description": "Query to find relevant documentation context", "required": True}
                }
            },
            {
                "name": "apply_prompt_with_context",
                "description": "Apply a prompt with documentation context automatically filled",
                "parameters": {
                    "prompt_id": {"type": "string", "description": "ID of the prompt to apply", "required": True},
                    "content": {"type": "string", "description": "Content to analyze (code, documentation, etc.)", "required": True},
                    "auto_fill_context": {"type": "boolean", "description": "Automatically fill context variables from documentation", "default": True, "required": False}
                }
            }
        ]

    def on_tool_select(self, event):
        """Handle tool selection"""
        tool_name = self.tool_var.get()
        tool = next((t for t in self.available_tools if t["name"] == tool_name), None)

        if tool:
            self.tool_desc_label.config(text=tool["description"])
            self.create_parameter_inputs(tool)

    def create_parameter_inputs(self, tool):
        """Create input widgets for tool parameters"""
        # Clear existing widgets
        for widget in self.params_scrollable_frame.winfo_children():
            widget.destroy()

        self.param_widgets = {}

        if not tool["parameters"]:
            ttk.Label(self.params_scrollable_frame, text="No parameters required").pack(pady=10)
            return

        row = 0
        for param_name, param_info in tool["parameters"].items():
            # Parameter label
            label_text = f"{param_name}"
            if param_info.get("required", False):
                label_text += " *"
            ttk.Label(self.params_scrollable_frame, text=label_text).grid(row=row, column=0, sticky="w", padx=5, pady=2)

            # Parameter input widget
            if param_info["type"] == "string":
                var = tk.StringVar()
                if "default" in param_info:
                    var.set(str(param_info["default"]))
                entry = ttk.Entry(self.params_scrollable_frame, textvariable=var, width=50)
                entry.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
                self.param_widgets[param_name] = var

            elif param_info["type"] == "integer":
                var = tk.StringVar()
                if "default" in param_info:
                    var.set(str(param_info["default"]))
                entry = ttk.Entry(self.params_scrollable_frame, textvariable=var, width=20)
                entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
                self.param_widgets[param_name] = var

            elif param_info["type"] == "boolean":
                var = tk.BooleanVar()
                if "default" in param_info:
                    var.set(param_info["default"])
                check = ttk.Checkbutton(self.params_scrollable_frame, variable=var)
                check.grid(row=row, column=1, sticky="w", padx=5, pady=2)
                self.param_widgets[param_name] = var

            elif param_info["type"] == "array":
                var = tk.StringVar()
                entry = ttk.Entry(self.params_scrollable_frame, textvariable=var, width=50)
                entry.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
                ttk.Label(self.params_scrollable_frame, text="(comma-separated)").grid(row=row, column=2, sticky="w", padx=5, pady=2)
                self.param_widgets[param_name] = var

            # Description tooltip
            if "description" in param_info:
                ttk.Label(self.params_scrollable_frame, text=param_info["description"],
                         font=("Arial", 8), foreground="gray").grid(row=row+1, column=0, columnspan=3, sticky="w", padx=5, pady=1)

            row += 2

        # Configure grid weights
        self.params_scrollable_frame.grid_columnconfigure(1, weight=1)

    def execute_tool(self):
        """Execute the selected tool with provided parameters"""
        tool_name = self.tool_var.get()
        if not tool_name:
            messagebox.showerror("Error", "Please select a tool first")
            return

        tool = next((t for t in self.available_tools if t["name"] == tool_name), None)
        if not tool:
            messagebox.showerror("Error", f"Tool not found: {tool_name}")
            return

        # Collect parameters
        arguments = {}
        for param_name, param_info in tool["parameters"].items():
            if param_name in self.param_widgets:
                widget = self.param_widgets[param_name]

                if param_info["type"] == "string":
                    value = widget.get().strip()
                    if param_info.get("required", False) and not value:
                        messagebox.showerror("Error", f"Required parameter '{param_name}' is empty")
                        return
                    if value:
                        arguments[param_name] = value

                elif param_info["type"] == "integer":
                    value_str = widget.get().strip()
                    if param_info.get("required", False) and not value_str:
                        messagebox.showerror("Error", f"Required parameter '{param_name}' is empty")
                        return
                    if value_str:
                        try:
                            arguments[param_name] = int(value_str)
                        except ValueError:
                            messagebox.showerror("Error", f"Invalid integer value for '{param_name}'")
                            return

                elif param_info["type"] == "boolean":
                    arguments[param_name] = widget.get()

                elif param_info["type"] == "array":
                    value_str = widget.get().strip()
                    if value_str:
                        arguments[param_name] = [item.strip() for item in value_str.split(",") if item.strip()]

        # Execute tool using MCP server (required - no fallback)
        try:
            self.status_var.set(f"Executing tool: {tool_name}...")
            self.tool_results_text.delete(1.0, tk.END)
            self.tool_results_text.insert(tk.END, f"Executing {tool_name}...\n\n")

            # Run the async tool call in a separate thread
            import concurrent.futures
            def run_async_tool():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(self.call_mcp_tool(tool_name, arguments))
                    return result
                finally:
                    loop.close()

            # Use ThreadPoolExecutor to run the async call
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async_tool)
                result = future.result(timeout=30)  # 30 second timeout

            self.tool_results_text.insert(tk.END, f"✅ Tool executed successfully!\n\n")
            self.tool_results_text.insert(tk.END, f"Result:\n{result}")
            self.status_var.set(f"Tool {tool_name} executed successfully")

        except concurrent.futures.TimeoutError:
            error_msg = f"❌ Tool execution timed out after 30 seconds"
            self.tool_results_text.insert(tk.END, error_msg)
            self.status_var.set(f"Timeout executing {tool_name}")
            messagebox.showerror("Tool Execution Timeout", error_msg)
        except Exception as e:
            error_msg = f"❌ Error executing tool {tool_name}: {str(e)}"
            self.tool_results_text.insert(tk.END, error_msg)
            self.status_var.set(f"Error executing {tool_name}")
            messagebox.showerror("Tool Execution Error", error_msg)

    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call the MCP server tool directly and return formatted result"""
        try:
            # Call the tool method directly on the MCP server instance
            if tool_name == "search_docs":
                query = arguments.get("query", "")
                doc_type = arguments.get("doc_type")
                limit = arguments.get("limit", 10)
                results = self.mcp_server.search_documents(query, doc_type, limit)
                
                response_text = f"Documentation Search Results for '{query}':\n\n"
                if results:
                    for i, result in enumerate(results, 1):
                        response_text += f"{i}. **{result['title']}** ({result['doc_type']})\n"
                        response_text += f"   Path: {result['path']}\n"
                        response_text += f"   Section: {result['section_title']}\n"
                        response_text += f"   Content: {result['content_snippet']}\n\n"
                else:
                    response_text += f"No results found for '{query}'"
                return response_text

            elif tool_name == "get_architecture_info":
                arch_info = self.mcp_server.get_architecture_info()
                response_text = "Architecture Documentation Summary:\n\n"
                if arch_info["architecture_documents"]:
                    for doc in arch_info["architecture_documents"]:
                        response_text += f"📋 **{doc['title']}**\n"
                        response_text += f"   Section: {doc['section_title']}\n"
                        response_text += f"   Content: {doc['content_snippet']}\n\n"
                else:
                    response_text += "No architecture documentation found."
                return response_text

            elif tool_name == "index_documentation":
                force = arguments.get("force", False)
                if force:
                    with sqlite3.connect(self.mcp_server.db_path) as conn:
                        conn.execute("DELETE FROM documents")
                        conn.execute("DELETE FROM search_index")
                result = await self.mcp_server.index_all_documents()
                response_text = "Documentation Indexing Results:\n\n"
                response_text += f"✅ Indexed documents: {result['indexed_count']}\n"
                response_text += f"❌ Errors: {result['error_count']}\n"
                response_text += f"📚 Total documents: {result['total_documents']}\n"
                return response_text

            elif tool_name == "search_prompts":
                query = arguments.get("query", "")
                category = arguments.get("category")
                limit = arguments.get("limit", 10)
                results = self.mcp_server.search_prompts(query, category, limit)
                
                response_text = f"Prompt Search Results for '{query}':\n\n"
                if results:
                    for i, result in enumerate(results, 1):
                        response_text += f"{i}. **{result['name']}** ({result['category']})\n"
                        response_text += f"   ID: {result['id']}\n"
                        response_text += f"   Description: {result['description']}\n"
                        response_text += f"   Usage: {result['usage_count']} times\n"
                        response_text += f"   Tags: {', '.join(result['tags'])}\n\n"
                else:
                    response_text += f"No prompts found for '{query}'"
                return response_text

            elif tool_name == "get_prompt":
                prompt_id = arguments.get("prompt_id", "")
                prompt = self.mcp_server.get_prompt(prompt_id)
                
                if prompt:
                    self.mcp_server.record_prompt_usage(prompt_id)
                    response_text = f"Prompt: **{prompt['name']}**\n\n"
                    response_text += f"**Description:** {prompt['description']}\n\n"
                    response_text += f"**Category:** {prompt['category']}\n\n"
                    response_text += f"**Variables:** {', '.join(prompt['variables'])}\n\n"
                    response_text += f"**Template:**\n```\n{prompt['template']}\n```\n\n"
                    response_text += f"**Usage Count:** {prompt['usage_count']}\n"
                    response_text += f"**Effectiveness Score:** {prompt['effectiveness_score']:.1f}/10\n"
                else:
                    response_text = f"Prompt not found: {prompt_id}"
                return response_text

            elif tool_name == "suggest_prompts":
                context = arguments.get("context", "")
                suggestions = self.mcp_server.suggest_prompts(context)
                
                response_text = "Suggested Prompts:\n\n"
                if suggestions:
                    for i, suggestion in enumerate(suggestions, 1):
                        response_text += f"{i}. **{suggestion['name']}** ({suggestion['category']})\n"
                        response_text += f"   ID: {suggestion['id']}\n"
                        response_text += f"   Description: {suggestion['description']}\n"
                        response_text += f"   Usage: {suggestion['usage_count']} times\n\n"
                else:
                    response_text += "No suggestions available."
                return response_text

            elif tool_name == "create_prompt":
                prompt_data = {
                    "name": arguments.get("name", ""),
                    "description": arguments.get("description", ""),
                    "template": arguments.get("template", ""),
                    "category": arguments.get("category", "custom"),
                    "variables": arguments.get("variables", []),
                    "tags": arguments.get("tags", [])
                }
                prompt_id = self.mcp_server.create_custom_prompt(prompt_data)
                response_text = f"✅ Created new prompt: **{prompt_data['name']}**\n\n"
                response_text += f"**ID:** {prompt_id}\n"
                response_text += f"**Category:** {prompt_data['category']}\n"
                response_text += f"**Variables:** {', '.join(prompt_data['variables'])}\n"
                response_text += f"**Tags:** {', '.join(prompt_data['tags'])}\n"
                return response_text

            elif tool_name == "generate_contextual_prompt":
                task = arguments.get("task", "")
                docs_query = arguments.get("docs_query", "")
                
                doc_results = self.mcp_server.search_documents(docs_query, limit=3)
                context_info = []
                for doc in doc_results:
                    context_info.append({
                        "title": doc["title"],
                        "content": doc["content_snippet"]
                    })
                
                contextual_template = f"""Based on the following project documentation:

    {chr(10).join([f"**{info['title']}**: {info['content']}" for info in context_info])}

    Please {task} the following content:
    {{content}}

    Consider the documented patterns, guidelines, and architecture when providing your analysis."""
                
                response_text = f"Generated Contextual Prompt for '{task}':\n\n"
                response_text += f"**Documentation Context Found:** {len(doc_results)} documents\n\n"
                response_text += f"**Generated Prompt Template:**\n```\n{contextual_template}\n```\n"
                return response_text

            elif tool_name == "apply_prompt_with_context":
                prompt_id = arguments.get("prompt_id", "")
                content = arguments.get("content", "")
                auto_fill = arguments.get("auto_fill_context", True)
                
                prompt = self.mcp_server.get_prompt(prompt_id)
                if not prompt:
                    return f"Prompt not found: {prompt_id}"
                
                template = prompt["template"]
                
                if auto_fill:
                    context_mappings = {
                        "architecture_info": "architecture patterns",
                        "coding_standards": "coding standards best practices",
                        "security_requirements": "security requirements guidelines",
                        "api_patterns": "api design patterns",
                        "testing_guidelines": "testing strategy guidelines",
                        "architecture_docs": "architecture patterns design",
                        "design_patterns": "design patterns microservice architecture",
                        "integration_guidelines": "integration patterns event-driven",
                        "scalability_requirements": "scalability performance requirements",
                        "implementation_code": "implementation patterns",
                        "event_driven_patterns": "event-driven architecture patterns",
                        "service_independence": "microservice independence patterns",
                        "kafka_patterns": "kafka integration patterns",
                        "security_guidelines": "security authentication",
                        "threat_model": "security threat model",
                        "compliance_requirements": "security compliance",
                        "coverage_requirements": "test coverage requirements",
                        "testing_framework": "testing framework patterns",
                        "quality_guidelines": "code quality guidelines",
                        "performance_requirements": "performance requirements optimization",
                        "existing_api_patterns": "api design patterns",
                        "architecture_style": "api architecture style",
                        "auth_method": "authentication authorization patterns"
                    }
                    
                    filled_template = template
                    for var in prompt["variables"]:
                        if var in context_mappings:
                            search_query = context_mappings[var]
                            doc_results = self.mcp_server.search_documents(search_query, limit=2)
                            if doc_results:
                                context_text = "\n".join([f"- {doc['content_snippet']}" for doc in doc_results])
                                filled_template = filled_template.replace(f"{{{var}}}", context_text)
                    
                    filled_template = filled_template.replace("{content}", content)
                    filled_template = filled_template.replace("{code_content}", content)
                    filled_template = filled_template.replace("{implementation_code}", content)
                    filled_template = filled_template.replace("{api_code}", content)
                else:
                    filled_template = template.replace("{content}", content)
                
                self.mcp_server.record_prompt_usage(prompt_id, context=f"Applied to content length: {len(content)}")
                response_text = f"Applied Prompt: **{prompt['name']}**\n\n"
                response_text += f"**Filled Prompt:**\n```\n{filled_template}\n```\n"
                return response_text

            else:
                return f"Unknown tool: {tool_name}"
                
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_stats(stats: Dict[str, Any]):
    """Print database statistics"""
    print_header("📊 DATABASE STATISTICS")

    print(f"📚 Documents: {stats['documents']['total_count']}")
    print(f"   Content Size: {stats['documents']['total_content_size_kb']} KB")

    print(f"🎯 Prompts: {stats['prompts']['total_count']}")
    print(f"   Total Usage: {stats['prompts']['total_usage']}")

    print(f"🔍 Search Index: {stats['search_index']['total_chunks']} chunks")

    print(f"📈 Usage Tracking: "
          f"{stats['usage_tracking']['total_usage_records']} records")


def print_documents(docs: List[Dict[str, Any]]):
    """Print list of documents"""
    print_header("📄 INDEXED DOCUMENTS")

    if not docs:
        print("No documents found.")
        return

    for i, doc in enumerate(docs, 1):
        print(f"{i}. 📄 {doc['title']}")
        print(f"   Path: {doc['path']}")
        print(f"   Type: {doc['doc_type']}")
        print(f"   Size: {doc['size_bytes']} bytes")
        print(f"   Modified: {doc['last_modified']}")
        print(f"   Relative Path: "
              f"{doc['metadata'].get('relative_path', 'N/A')}")
        print()


def print_prompts(prompts: List[Dict[str, Any]]):
    """Print list of prompts"""
    print_header("🎯 AVAILABLE PROMPTS")

    if not prompts:
        print("No prompts found.")
        return

    current_category = None
    for prompt in prompts:
        if prompt['category'] != current_category:
            if current_category is not None:
                print()
            print(f"📂 {prompt['category'].upper()}")
            current_category = prompt['category']

        print(f"  • {prompt['name']} (ID: {prompt['id']})")
        print(f"    Usage: {prompt['usage_count']} | Score: {prompt['effectiveness_score']:.1f}")
        print(f"    Tags: {', '.join(prompt['tags'])}")
        print(f"    {prompt['description']}")


def print_search_results(results: List[Dict[str, Any]], query: str):
    """Print search results"""
    print_header(f"🔍 SEARCH RESULTS FOR: '{query}'")

    if not results:
        print("No results found.")
        return

    for i, result in enumerate(results, 1):
        print(f"{i}. 📄 {result['title']} ({result['doc_type']})")
        print(f"   Section: {result['section_title']}")
        print(f"   Content: {result['content_snippet']}")
        print()


def print_architecture_info(arch_info: Dict[str, Any]):
    """Print architecture information"""
    print_header("🏗️ ARCHITECTURE INFORMATION")

    print(f"Found {arch_info['total_count']} architecture-related documents")
    print(f"Searched keywords: {', '.join(arch_info['keywords_searched'])}")
    print()

    if arch_info['architecture_documents']:
        for doc in arch_info['architecture_documents']:
            print(f"📋 {doc['title']} ({doc['doc_type']})")
            print(f"   Section: {doc['section_title']}")
            print(f"   Content: {doc['content_snippet']}")
            print()
    else:
        print("No architecture documentation found.")


def print_usage_stats(stats: List[Dict[str, Any]]):
    """Print prompt usage statistics"""
    print_header("📈 PROMPT USAGE STATISTICS")

    if not stats:
        print("No usage statistics available.")
        return

    print(f"{'Prompt':<30} {'Category':<15} {'Uses':<5} {'Avg Score':<10}")
    print("-" * 70)

    for stat in stats:
        name = stat['name'][:28] + "..." if len(stat['name']) > 28 else stat['name']
        print(f"{name:<30} {stat['category']:<15} {stat['usage_count']:<5} {stat['avg_effectiveness']:<10.1f}")


def interactive_mode(viewer: DocsPromptsViewer):
    """Run interactive mode"""
    print_header("🎯 DOCS-PROMPTS DATABASE VIEWER")
    print("Interactive mode - type 'help' for commands")

    while True:
        try:
            cmd = input("\n> ").strip().lower()

            if cmd == 'help':
                print("""
Available commands:
  stats        - Show database statistics
  docs         - List all indexed documents
  prompts      - List all prompts
  arch         - Show architecture information
  usage        - Show prompt usage statistics
  search <q>   - Search documents
  show-doc <path> - Show document details
  show-prompt <id> - Show prompt details
  categories   - List prompt categories
  help         - Show this help
  quit         - Exit
                """)

            elif cmd == 'stats':
                stats = viewer.get_database_stats()
                print_stats(stats)

            elif cmd == 'docs':
                docs = viewer.list_documents()
                print_documents(docs)

            elif cmd == 'prompts':
                prompts = viewer.list_prompts()
                print_prompts(prompts)

            elif cmd == 'arch':
                arch_info = viewer.get_architecture_info()
                print_architecture_info(arch_info)

            elif cmd == 'usage':
                stats = viewer.get_prompt_usage_stats()
                print_usage_stats(stats)

            elif cmd.startswith('search '):
                query = cmd[7:].strip()
                if query:
                    results = viewer.search_documents(query)
                    print_search_results(results, query)
                else:
                    print("Usage: search <query>")

            elif cmd.startswith('show-doc '):
                path = cmd[9:].strip()
                if path:
                    doc = viewer.show_document_details(path)
                    if doc:
                        print_header(f"📄 DOCUMENT DETAILS: {doc['title']}")
                        print(f"Path: {doc['path']}")
                        print(f"Type: {doc['doc_type']}")
                        print(f"Size: {len(doc['content'])} characters")
                        print(f"Sections: {len(doc['sections'])}")
                        print(f"Links: {len(doc['links'])}")
                        print(f"Code blocks: {len(doc['code_blocks'])}")
                        print(f"Last modified: {doc['last_modified']}")
                        print(f"Indexed at: {doc['indexed_at']}")
                        print(f"\nContent preview (first 500 chars):\n{doc['content'][:500]}...")
                    else:
                        print(f"Document not found: {path}")
                else:
                    print("Usage: show-doc <path>")

            elif cmd.startswith('show-prompt '):
                prompt_id = cmd[12:].strip()
                if prompt_id:
                    prompt = viewer.show_prompt_details(prompt_id)
                    if prompt:
                        print_header(f"🎯 PROMPT DETAILS: {prompt['name']}")
                        print(f"ID: {prompt['id']}")
                        print(f"Category: {prompt['category']}")
                        print(f"Description: {prompt['description']}")
                        print(f"Variables: {', '.join(prompt['variables'])}")
                        print(f"Tags: {', '.join(prompt['tags'])}")
                        print(f"Usage count: {prompt['usage_count']}")
                        print(f"Effectiveness: {prompt['effectiveness_score']:.1f}")
                        print(f"Created: {prompt['created_at']}")
                        print(f"Updated: {prompt['updated_at']}")
                        print(f"\nTemplate:\n{prompt['template']}")
                    else:
                        print(f"Prompt not found: {prompt_id}")
                else:
                    print("Usage: show-prompt <id>")

            elif cmd == 'categories':
                categories = viewer.get_categories()
                print_header("📂 PROMPT CATEGORIES")
                for cat in categories:
                    print(f"  • {cat}")

            elif cmd in ['quit', 'exit', 'q']:
                break

            else:
                print("Unknown command. Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Docs-Prompts Database Viewer")
    parser.add_argument("--db", default=".docs_prompts_index.db",
                       help="Path to the database file")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="Run in interactive mode")
    parser.add_argument("--gui", action="store_true",
                       help="Run in GUI mode")
    parser.add_argument("--stats", action="store_true",
                       help="Show database statistics")
    parser.add_argument("--docs", action="store_true",
                       help="List all documents")
    parser.add_argument("--prompts", action="store_true",
                       help="List all prompts")
    parser.add_argument("--arch", action="store_true",
                       help="Show architecture information")
    parser.add_argument("--usage", action="store_true",
                       help="Show usage statistics")
    parser.add_argument("--search", help="Search documents")

    args = parser.parse_args()

    viewer = DocsPromptsViewer(args.db)

    if args.gui:
        # Launch GUI
        gui = DocsPromptsGUI(viewer)
        gui.run()
    elif args.interactive:
        interactive_mode(viewer)
    elif args.stats:
        stats = viewer.get_database_stats()
        print_stats(stats)
    elif args.docs:
        docs = viewer.list_documents()
        print_documents(docs)
    elif args.prompts:
        prompts = viewer.list_prompts()
        print_prompts(prompts)
    elif args.arch:
        arch_info = viewer.get_architecture_info()
        print_architecture_info(arch_info)
    elif args.usage:
        stats = viewer.get_prompt_usage_stats()
        print_usage_stats(stats)
    elif args.search:
        results = viewer.search_documents(args.search)
        print_search_results(results, args.search)
    else:
        # Default: show stats
        stats = viewer.get_database_stats()
        print_stats(stats)
        print("\nUse --help for more options or --interactive for full interface")


if __name__ == "__main__":
    main()