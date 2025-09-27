"""
Database management for the Documentation and Prompts MCP Server
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import time

from models import DocumentInfo

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all database operations"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        logger.info(f"Initializing database at {self.db_path}")
        with sqlite3.connect(self.db_path) as conn:
            # Documents tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents
                (
                    path TEXT PRIMARY KEY,
                    title TEXT,
                    content TEXT,
                    sections TEXT,
                    metadata TEXT,
                    last_modified REAL,
                    file_hash TEXT,
                    doc_type TEXT,
                    links TEXT,
                    code_blocks TEXT,
                    indexed_at REAL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_index
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_path TEXT,
                    section_title TEXT,
                    content_chunk TEXT,
                    chunk_type TEXT,
                    FOREIGN KEY (doc_path) REFERENCES documents (path)
                )
            """)

            # Prompts tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompts
                (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    category TEXT,
                    template TEXT,
                    variables TEXT,
                    tags TEXT,
                    created_at REAL,
                    updated_at REAL,
                    usage_count INTEGER DEFAULT 0,
                    effectiveness_score REAL DEFAULT 0.0
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompt_usage
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id TEXT,
                    used_at REAL,
                    context TEXT,
                    effectiveness INTEGER,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id)
                )
            """)

            # Create indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_search_content ON search_index(content_chunk)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_doc_path ON search_index(doc_path)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_prompt_category ON prompts(category)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prompt_tags ON prompts(tags)")

    # Document operations
    def store_document(self, doc_info: DocumentInfo):
        """Store a document in the database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO documents
                (path, title, content, sections, metadata, last_modified, file_hash, doc_type, links, code_blocks, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    doc_info.path,
                    doc_info.title,
                    doc_info.content,
                    json.dumps(doc_info.sections),
                    json.dumps(doc_info.metadata),
                    doc_info.last_modified,
                    doc_info.file_hash,
                    doc_info.doc_type,
                    json.dumps(doc_info.links),
                    json.dumps(doc_info.code_blocks),
                    time.time(),
                ),
            )

            # Clear old search index entries
            conn.execute(
                "DELETE FROM search_index WHERE doc_path = ?", (doc_info.path,)
            )

            # Add to search index
            for section in doc_info.sections:
                conn.execute(
                    """
                    INSERT INTO search_index (doc_path, section_title, content_chunk, chunk_type)
                    VALUES (?, ?, ?, ?)
                """,
                    (doc_info.path, section["title"], section["content"], "section"),
                )

            for code_block in doc_info.code_blocks:
                conn.execute(
                    """
                    INSERT INTO search_index (doc_path, section_title, content_chunk, chunk_type)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        doc_info.path,
                        f"Code ({code_block['language']})",
                        code_block["content"],
                        "code",
                    ),
                )

    def get_document_hash(self, path: str) -> Optional[str]:
        """Get the stored hash for a document"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT file_hash FROM documents WHERE path = ?", (path,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def search_documents(
        self, query: str, doc_type: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search documents using text matching"""
        with sqlite3.connect(self.db_path) as conn:
            sql = """
                SELECT DISTINCT d.path, d.title, d.doc_type, d.metadata,
                                s.section_title, s.content_chunk, s.chunk_type
                FROM documents d
                JOIN search_index s ON d.path = s.doc_path
                WHERE (s.content_chunk LIKE ? OR d.title LIKE ?)
            """
            params = [f"%{query}%", f"%{query}%"]

            if doc_type:
                sql += " AND d.doc_type = ?"
                params.append(doc_type)

            sql += " ORDER BY (CASE WHEN d.title LIKE ? THEN 1 ELSE 2 END), d.title LIMIT ?"
            params.extend([f"%{query}%", limit])

            cursor = conn.execute(sql, params)
            results = []

            for row in cursor.fetchall():
                results.append(
                    {
                        "path": row[0],
                        "title": row[1],
                        "doc_type": row[2],
                        "metadata": json.loads(row[3]),
                        "section_title": row[4],
                        "content_snippet": (
                            row[5][:200] + "..." if len(row[5]) > 200 else row[5]
                        ),
                        "chunk_type": row[6],
                    }
                )

            return results

    def get_document_count(self) -> int:
        """Get total number of indexed documents"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM documents")
            return cursor.fetchone()[0]

    def clear_documents(self):
        """Clear all documents and search index"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM documents")
            conn.execute("DELETE FROM search_index")

    # Prompt operations
    def store_prompt(self, prompt_data: Dict[str, Any]):
        """Store a prompt in the database"""
        current_time = time.time()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO prompts
                (id, name, description, category, template, variables, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    prompt_data["id"],
                    prompt_data["name"],
                    prompt_data["description"],
                    prompt_data["category"],
                    prompt_data["template"],
                    json.dumps(prompt_data.get("variables", [])),
                    json.dumps(prompt_data.get("tags", [])),
                    current_time,
                    current_time,
                ),
            )

    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific prompt by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, name, description, category, template, variables, tags,
                       created_at, updated_at, usage_count, effectiveness_score
                FROM prompts WHERE id = ?
            """,
                (prompt_id,),
            )

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
                    "created_at": result[7],
                    "updated_at": result[8],
                    "usage_count": result[9],
                    "effectiveness_score": result[10],
                }
            return None

    def search_prompts(
        self, query: str, category: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search prompts by keyword or category"""
        with sqlite3.connect(self.db_path) as conn:
            sql = """
                SELECT id, name, description, category, tags, usage_count, effectiveness_score
                FROM prompts
                WHERE (name LIKE ? OR description LIKE ? OR tags LIKE ?)
            """
            params = [f"%{query}%", f"%{query}%", f"%{query}%"]

            if category:
                sql += " AND category = ?"
                params.append(category)

            sql += " ORDER BY usage_count DESC, effectiveness_score DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(sql, params)
            results = []

            for row in cursor.fetchall():
                results.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "category": row[3],
                        "tags": json.loads(row[4]),
                        "usage_count": row[5],
                        "effectiveness_score": row[6],
                    }
                )

            return results

    def get_prompts_by_category(
        self, category: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get prompts by category"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, name, description, tags, usage_count, effectiveness_score
                FROM prompts WHERE category = ?
                ORDER BY usage_count DESC, effectiveness_score DESC LIMIT ?
            """,
                (category, limit),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "category": category,
                        "tags": json.loads(row[3]),
                        "usage_count": row[4],
                        "effectiveness_score": row[5],
                    }
                )

            return results

    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Get all prompts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, name, description, category, tags, usage_count, effectiveness_score
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
                        "tags": json.loads(row[4]),
                        "usage_count": row[5],
                        "effectiveness_score": row[6],
                    }
                )

            return prompts

    def get_popular_prompts(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get popular prompts by usage"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, name, description, category, usage_count, effectiveness_score
                FROM prompts ORDER BY usage_count DESC, effectiveness_score DESC LIMIT ?
            """,
                (limit,),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "category": row[3],
                        "usage_count": row[4],
                        "effectiveness_score": row[5],
                    }
                )

            return results

    def record_prompt_usage(
        self, prompt_id: str, context: str = "", effectiveness: int = 5
    ):
        """Record prompt usage for analytics"""
        with sqlite3.connect(self.db_path) as conn:
            # Record usage
            conn.execute(
                """
                INSERT INTO prompt_usage (prompt_id, used_at, context, effectiveness)
                VALUES (?, ?, ?, ?)
            """,
                (prompt_id, time.time(), context, effectiveness),
            )

            # Update prompt statistics
            conn.execute(
                """
                UPDATE prompts
                SET usage_count = usage_count + 1,
                    effectiveness_score = (SELECT AVG(effectiveness) FROM prompt_usage WHERE prompt_id = ?)
                WHERE id = ?
            """,
                (prompt_id, prompt_id),
            )

    def get_usage_stats(self) -> List[Dict[str, Any]]:
        """Get usage statistics for all prompts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT p.id, p.name, p.category, p.usage_count, p.effectiveness_score,
                       COUNT(pu.id) as total_uses,
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
                        "effectiveness_score": row[4],
                        "total_uses": row[5],
                        "avg_effectiveness": row[6] or 0,
                    }
                )

            return stats

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all indexed documents"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT path, title, doc_type, metadata, last_modified,
                       file_hash
                FROM documents ORDER BY path
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
                })
            
            return documents
