"""
Database Adapter for GUI Direct Access

This module provides direct database access for the GUI when MCP connection
is not available. It implements the same interface as the MCP client but 
queries the SQLite database directly.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class DirectDatabaseAdapter:
    """
    Direct database access adapter for GUI.
    
    Provides the same interface as MCP client but queries database directly.
    Use this when MCP server HTTP connection is not available.
    """
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(str(self.db_path))
    
    def list_documents(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        List all documents in the database.
        
        Returns:
            Dictionary matching MCP response format
        """
        try:
            with self.get_connection() as db:
                cursor = db.cursor()
                
                # Get total count
                cursor.execute("SELECT COUNT(*) FROM documents")
                total = cursor.fetchone()[0]
                
                # Get documents with pagination
                cursor.execute("""
                    SELECT id, title, file_type, indexed, summarized, 
                           total_pages, total_words, tags, upload_date
                    FROM documents 
                    ORDER BY upload_date DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                documents = []
                for row in cursor.fetchall():
                    doc_id, title, file_type, indexed, summarized, total_pages, total_words, tags, upload_date = row
                    
                    documents.append({
                        "document_id": doc_id,
                        "title": title,
                        "file_type": file_type,
                        "indexed": bool(indexed),
                        "summarized": bool(summarized),
                        "total_pages": total_pages,
                        "total_words": total_words,
                        "tags": json.loads(tags) if tags else [],
                        "upload_date": upload_date
                    })
                
                return {
                    "documents": documents,
                    "pagination": {
                        "limit": limit,
                        "offset": offset,
                        "total": total,
                        "has_more": (offset + limit) < total
                    }
                }
        
        except Exception as e:
            self.logger.error(f"Error listing documents: {e}")
            return {
                "documents": [],
                "pagination": {"limit": limit, "offset": offset, "total": 0, "has_more": False}
            }
    
    def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID."""
        try:
            with self.get_connection() as db:
                cursor = db.cursor()
                
                cursor.execute("""
                    SELECT id, title, file_type, indexed, summarized,
                           total_pages, total_words, tags, upload_date, file_path
                    FROM documents 
                    WHERE id = ?
                """, (document_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                doc_id, title, file_type, indexed, summarized, total_pages, total_words, tags, upload_date, file_path = row
                
                return {
                    "document_id": doc_id,
                    "title": title,
                    "file_type": file_type,
                    "indexed": bool(indexed),
                    "summarized": bool(summarized),
                    "total_pages": total_pages,
                    "total_words": total_words,
                    "tags": json.loads(tags) if tags else [],
                    "upload_date": upload_date,
                    "file_path": file_path
                }
        
        except Exception as e:
            self.logger.error(f"Error getting document {document_id}: {e}")
            return None
    
    def get_document_structure(self, document_id: int) -> Dict[str, Any]:
        """Get document structure (chunks)."""
        try:
            with self.get_connection() as db:
                cursor = db.cursor()
                
                # Get document info
                cursor.execute("SELECT title, indexed FROM documents WHERE id = ?", (document_id,))
                doc_row = cursor.fetchone()
                if not doc_row:
                    return {"success": False, "error": "Document not found"}
                
                title, indexed = doc_row
                
                if not indexed:
                    return {
                        "document_id": document_id,
                        "document_title": title,
                        "indexed": False,
                        "chunks": []
                    }
                
                # Get chunks
                cursor.execute("""
                    SELECT id, chunk_index, chunk_type, title, word_count, metadata
                    FROM chunks 
                    WHERE document_id = ?
                    ORDER BY chunk_index
                """, (document_id,))
                
                chunks = []
                for row in cursor.fetchall():
                    chunk_id, chunk_index, chunk_type, chunk_title, word_count, metadata = row
                    
                    chunks.append({
                        "chunk_id": chunk_id,
                        "chunk_index": chunk_index,
                        "chunk_type": chunk_type or "auto",
                        "title": chunk_title or f"Chunk {chunk_index + 1}",
                        "word_count": word_count or 0,
                        "metadata": json.loads(metadata) if metadata else {}
                    })
                
                return {
                    "document_id": document_id,
                    "document_title": title,
                    "indexed": True,
                    "chunks": chunks
                }
        
        except Exception as e:
            self.logger.error(f"Error getting document structure {document_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_chunk_content(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        """Get chunk content."""
        try:
            with self.get_connection() as db:
                cursor = db.cursor()
                
                cursor.execute("""
                    SELECT c.id, c.document_id, c.chunk_index, c.title, 
                           c.content, c.word_count, c.metadata,
                           d.title as document_title
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE c.id = ?
                """, (chunk_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                chunk_id, doc_id, chunk_index, title, content, word_count, metadata, doc_title = row
                
                return {
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "chunk_index": chunk_index,
                    "title": title or f"Chunk {chunk_index + 1}",
                    "content": content,
                    "word_count": word_count or len(content.split()) if content else 0,
                    "metadata": json.loads(metadata) if metadata else {},
                    "document_title": doc_title
                }
        
        except Exception as e:
            self.logger.error(f"Error getting chunk content {chunk_id}: {e}")
            return None
    
    def search_documents(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search documents using FTS."""
        try:
            with self.get_connection() as db:
                cursor = db.cursor()
                
                # Search in chunks_fts
                cursor.execute("""
                    SELECT cf.chunk_id, cf.document_id, cf.title as chunk_title,
                           d.title as document_title,
                           substr(cf.content, 1, 200) as excerpt
                    FROM chunks_fts cf
                    JOIN documents d ON cf.document_id = d.id
                    WHERE chunks_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (query, limit))
                
                results = []
                for row in cursor.fetchall():
                    chunk_id, doc_id, chunk_title, doc_title, excerpt = row
                    
                    results.append({
                        "document_id": doc_id,
                        "title": doc_title,
                        "chunk_id": chunk_id,
                        "chunk_title": chunk_title,
                        "match_excerpt": excerpt + "..." if len(excerpt) >= 200 else excerpt,
                        "relevance_score": 1.0  # FTS doesn't provide scores directly
                    })
                
                return {
                    "total_results": len(results),
                    "results": results
                }
        
        except Exception as e:
            self.logger.error(f"Error searching documents: {e}")
            return {"total_results": 0, "results": []}

    def list_summaries(self, document_id: Optional[int] = None, chunk_id: Optional[int] = None, limit: int = 20) -> Dict[str, Any]:
        """List summaries with optional filtering."""
        try:
            with self.get_connection() as db:
                cursor = db.cursor()
                
                query = """
                    SELECT s.id, s.document_id, s.chunk_id, s.summary_type, 
                           s.summary_content, s.word_count, s.model_name, 
                           s.generation_date, s.metadata,
                           d.title as document_title,
                           c.title as chunk_title
                    FROM summaries s
                    LEFT JOIN documents d ON s.document_id = d.id
                    LEFT JOIN chunks c ON s.chunk_id = c.id
                    WHERE 1=1
                """
                params = []
                
                if document_id is not None:
                    query += " AND (s.document_id = ? OR (s.chunk_id IN (SELECT id FROM chunks WHERE document_id = ?)))"
                    params.extend([document_id, document_id])
                
                if chunk_id is not None:
                    query += " AND s.chunk_id = ?"
                    params.append(chunk_id)
                
                query += " ORDER BY s.generation_date DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                
                summaries = []
                for row in cursor.fetchall():
                    summary_id, doc_id, ch_id, summary_type, content, word_count, model_name, gen_date, metadata, doc_title, chunk_title = row
                    
                    summaries.append({
                        "summary_id": summary_id,
                        "document_id": doc_id,
                        "chunk_id": ch_id,
                        "summary_type": summary_type,
                        "summary_content": content,
                        "word_count": word_count or len(content.split()) if content else 0,
                        "model_name": model_name,
                        "generation_date": gen_date,
                        "metadata": json.loads(metadata) if metadata else {},
                        "document_title": doc_title,
                        "chunk_title": chunk_title
                    })
                
                return {
                    "summaries": summaries,
                    "total": len(summaries)
                }
                
        except Exception as e:
            logging.error(f"Failed to list summaries: {e}")
            return {"summaries": [], "total": 0, "error": str(e)}

    def get_summary(self, summary_id: Optional[int] = None, document_id: Optional[int] = None, chunk_id: Optional[int] = None, summary_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a specific summary by various criteria."""
        try:
            with self.get_connection() as db:
                cursor = db.cursor()
                
                if summary_id is not None:
                    # Get by summary ID
                    cursor.execute("""
                        SELECT s.id, s.document_id, s.chunk_id, s.summary_type, 
                               s.summary_content, s.word_count, s.model_name, 
                               s.generation_date, s.metadata,
                               d.title as document_title,
                               c.title as chunk_title
                        FROM summaries s
                        LEFT JOIN documents d ON s.document_id = d.id
                        LEFT JOIN chunks c ON s.chunk_id = c.id
                        WHERE s.id = ?
                    """, (summary_id,))
                elif document_id is not None and chunk_id is None:
                    # Get document-level summary
                    cursor.execute("""
                        SELECT s.id, s.document_id, s.chunk_id, s.summary_type, 
                               s.summary_content, s.word_count, s.model_name, 
                               s.generation_date, s.metadata,
                               d.title as document_title,
                               c.title as chunk_title
                        FROM summaries s
                        LEFT JOIN documents d ON s.document_id = d.id
                        LEFT JOIN chunks c ON s.chunk_id = c.id
                        WHERE s.document_id = ? AND s.chunk_id IS NULL AND s.summary_type = ?
                    """, (document_id, summary_type or 'standard'))
                elif chunk_id is not None:
                    # Get chunk-level summary
                    cursor.execute("""
                        SELECT s.id, s.document_id, s.chunk_id, s.summary_type, 
                               s.summary_content, s.word_count, s.model_name, 
                               s.generation_date, s.metadata,
                               d.title as document_title,
                               c.title as chunk_title
                        FROM summaries s
                        LEFT JOIN documents d ON s.document_id = d.id
                        LEFT JOIN chunks c ON s.chunk_id = c.id
                        WHERE s.chunk_id = ? AND s.summary_type = ?
                    """, (chunk_id, summary_type or 'standard'))
                else:
                    return None
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                summary_id, doc_id, ch_id, summary_type, content, word_count, model_name, gen_date, metadata, doc_title, chunk_title = row
                
                return {
                    "summary_id": summary_id,
                    "document_id": doc_id,
                    "chunk_id": ch_id,
                    "summary_type": summary_type,
                    "summary_content": content,
                    "word_count": word_count or len(content.split()) if content else 0,
                    "model_name": model_name,
                    "generation_date": gen_date,
                    "metadata": json.loads(metadata) if metadata else {},
                    "document_title": doc_title,
                    "chunk_title": chunk_title
                }
                
        except Exception as e:
            logging.error(f"Failed to get summary: {e}")
            return None

    def save_summary(self, document_id: Optional[int] = None, chunk_id: Optional[int] = None, summary_type: str = "standard", 
                    summary_content: str = "", model_name: str = "", metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Save a new summary or update existing one."""
        try:
            with self.get_connection() as db:
                cursor = db.cursor()
                
                # Validate parameters
                if not summary_content:
                    raise ValueError("Summary content cannot be empty")
                
                if not ((document_id is not None and chunk_id is None) or (document_id is None and chunk_id is not None)):
                    raise ValueError("Must provide either document_id or chunk_id, but not both")
                
                word_count = len(summary_content.split())
                metadata_json = json.dumps(metadata) if metadata else "{}"
                
                # Check if summary already exists
                if document_id is not None:
                    cursor.execute("""
                        SELECT id FROM summaries 
                        WHERE document_id = ? AND chunk_id IS NULL AND summary_type = ?
                    """, (document_id, summary_type))
                else:
                    cursor.execute("""
                        SELECT id FROM summaries 
                        WHERE chunk_id = ? AND summary_type = ?
                    """, (chunk_id, summary_type))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing summary
                    cursor.execute("""
                        UPDATE summaries 
                        SET summary_content = ?, word_count = ?, model_name = ?, 
                            generation_date = CURRENT_TIMESTAMP, metadata = ?
                        WHERE id = ?
                    """, (summary_content, word_count, model_name, metadata_json, existing[0]))
                    summary_id = existing[0]
                else:
                    # Create new summary
                    cursor.execute("""
                        INSERT INTO summaries (document_id, chunk_id, summary_type, summary_content, 
                                             word_count, model_name, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (document_id, chunk_id, summary_type, summary_content, 
                          word_count, model_name, metadata_json))
                    summary_id = cursor.lastrowid
                
                db.commit()
                
                # Return the created/updated summary
                return self.get_summary(summary_id=summary_id)
                
        except Exception as e:
            logging.error(f"Failed to save summary: {e}")
            return None

    def delete_summary(self, summary_id: int) -> bool:
        """Delete a summary."""
        try:
            with self.get_connection() as db:
                cursor = db.cursor()
                cursor.execute("DELETE FROM summaries WHERE id = ?", (summary_id,))
                db.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logging.error(f"Failed to delete summary: {e}")
            return False


def get_database_adapter() -> DirectDatabaseAdapter:
    """
    Get database adapter instance.
    
    Returns:
        DirectDatabaseAdapter configured for Study Buddy database
    """
    # Use the same database path as MCP server
    db_path = Path(__file__).parent.parent / "mcp-server" / "src" / "data" / "study_buddy.db"
    
    return DirectDatabaseAdapter(str(db_path))