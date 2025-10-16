#!/usr/bin/env python3
"""
Debug script to test paper indexing functionality.
"""

import sqlite3
import os
import sys
from pathlib import Path

def check_paper_content():
    """Check if papers have extractable content."""
    db_path = 'database/slr_database.db'
    
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📊 **Paper Content Analysis:**")
    print("=" * 60)
    
    cursor.execute("""
        SELECT id, title, file_path, file_type, abstract, total_words
        FROM research_papers 
        ORDER BY id
    """)
    
    for row in cursor.fetchall():
        paper_id, title, file_path, file_type, abstract, total_words = row
        
        print(f"\n📄 Paper {paper_id}: {title[:50]}...")
        print(f"   File: {file_path} ({file_type})")
        print(f"   Total Words: {total_words}")
        print(f"   Abstract: {'✅ Yes' if abstract else '❌ No'}")
        
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"   File Exists: ✅ Yes ({file_size} bytes)")
            
            # Test content extraction for PDF
            if file_type == 'pdf':
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(file_path)
                    page_count = len(doc)
                    if page_count > 0:
                        text_sample = doc[0].get_text()[:200]
                        print(f"   PDF Pages: {page_count}")
                        print(f"   Content Sample: {text_sample}...")
                    doc.close()
                except Exception as e:
                    print(f"   PDF Error: {e}")
            elif file_type == 'bib':
                # For BibTeX files, we should use abstract + metadata
                print(f"   BibTeX File: Uses metadata/abstract for indexing")
        else:
            print(f"   File Exists: ❌ No")
    
    conn.close()

def simulate_indexing():
    """Simulate the indexing process for abstract-only papers."""
    print(f"\n🧪 **Simulating Abstract-Based Indexing:**")
    print("=" * 60)
    
    db_path = 'database/slr_database.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get papers with abstracts but no full text
    cursor.execute("""
        SELECT id, title, abstract, file_type
        FROM research_papers 
        WHERE abstract IS NOT NULL AND abstract != ''
        ORDER BY id
    """)
    
    papers_with_abstracts = cursor.fetchall()
    
    for paper_id, title, abstract, file_type in papers_with_abstracts:
        print(f"\n📋 Paper {paper_id}: {title[:40]}...")
        print(f"   File Type: {file_type}")
        print(f"   Abstract Length: {len(abstract)} chars")
        
        # Simulate chunking based on abstract + metadata
        content_parts = []
        content_parts.append(f"Title: {title}")
        content_parts.append(f"Abstract: {abstract}")
        
        total_content = "\n\n".join(content_parts)
        print(f"   Total Indexable Content: {len(total_content)} chars")
        
        # Simple chunking simulation
        if len(total_content) > 100:  # Minimum content for chunking
            print(f"   ✅ Can be indexed ({len(total_content)} chars available)")
        else:
            print(f"   ❌ Insufficient content for indexing")
    
    conn.close()

if __name__ == "__main__":
    print("🔍 **SLR Paper Indexing Debug Analysis**")
    print("=" * 70)
    
    check_paper_content()
    simulate_indexing()