#!/usr/bin/env python3
"""Batch index all papers with PDF files."""

import sys
import os
import sqlite3
from pathlib import Path

# Absolute path to slr-server root
SLR_SERVER_ROOT = Path(__file__).parent.parent.absolute()

def batch_index_all_pdfs():
    """Index all papers with PDF files."""
    
    # Get database path with absolute path
    db_path = str(SLR_SERVER_ROOT / "database" / "slr_database.db")
    
    # Get all paper IDs with PDF files
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT id FROM research_papers 
        WHERE file_path IS NOT NULL AND file_type = 'pdf'
        ORDER BY id DESC
    ''')
    
    paper_ids = [row[0] for row in cursor.fetchall()]
    db.close()
    
    print(f"Found {len(paper_ids)} papers with PDF files")
    print(f"Paper IDs: {', '.join(map(str, paper_ids[:10]))}..." if len(paper_ids) > 10 else f"Paper IDs: {paper_ids}")
    
    # Now try to import and use the indexing service
    try:
        # Import as package
        from src.container import Container
        from src.services.academic_chunking_service import IndexingStrategy
        
        container = Container(database_path="database/slr_database.db")
        paper_repo = container.get_paper_repository()
        indexing_service = container.get_chunking_service()
        
        print("\nStarting batch indexing...\n")
        
        success_count = 0
        fail_count = 0
        total_chunks = 0
        
        for i, paper_id in enumerate(paper_ids, 1):
            try:
                paper = paper_repo.get_by_id(paper_id)
                if not paper or not paper.file_path:
                    print(f"[{i}/{len(paper_ids)}] Paper {paper_id}: Skipped (no file)")
                    fail_count += 1
                    continue
                
                chunks = indexing_service.index_paper(paper_id, IndexingStrategy.HYBRID)
                success_count += 1
                total_chunks += len(chunks)
                
                title_short = paper.title[:50] if paper.title else "N/A"
                print(f"[{i}/{len(paper_ids)}] Paper {paper_id}: {len(chunks)} chunks | {title_short}")
                
                if i % 10 == 0:
                    print(f"  Progress: {success_count}/{i} indexed successfully")
                    
            except Exception as e:
                fail_count += 1
                print(f"[{i}/{len(paper_ids)}] Paper {paper_id}: ERROR - {str(e)[:60]}")
        
        print(f"\n{'='*60}")
        print(f"INDEXING COMPLETE!")
        print(f"{'='*60}")
        print(f"Total papers: {len(paper_ids)}")
        print(f"Successfully indexed: {success_count}")
        print(f"Failed: {fail_count}")
        print(f"Total chunks created: {total_chunks}")
        print(f"Average chunks per paper: {total_chunks / success_count if success_count > 0 else 0:.1f}")
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    batch_index_all_pdfs()
