#!/usr/bin/env python3
import sqlite3
from pathlib import Path

# Absolute path to database
SLR_SERVER_ROOT = Path(__file__).parent.parent.absolute()
db_path = str(SLR_SERVER_ROOT / "database" / "slr_database.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get papers with PDFs
cursor.execute('SELECT COUNT(*) FROM research_papers WHERE file_path IS NOT NULL')
papers_with_pdf = cursor.fetchone()[0]

# Get papers that are indexed
cursor.execute('SELECT COUNT(*) FROM research_papers WHERE indexed = 1')
indexed_papers = cursor.fetchone()[0]

# Get total chunks
cursor.execute('SELECT COUNT(*) FROM chunks')
total_chunks = cursor.fetchone()[0]

# Get papers with chunks
cursor.execute('SELECT COUNT(DISTINCT paper_id) FROM chunks')
papers_with_chunks = cursor.fetchone()[0]

print(f'Papers with PDFs: {papers_with_pdf}')
print(f'Papers marked as indexed: {indexed_papers}')
print(f'Papers with chunks in database: {papers_with_chunks}')
print(f'Total chunks: {total_chunks}')

if papers_with_pdf > 0:
    print(f'\n📊 Indexing Progress:')
    print(f'  • Chunks per paper (average): {total_chunks // papers_with_chunks if papers_with_chunks > 0 else 0}')
    print(f'  • Papers yet to index: {papers_with_pdf - papers_with_chunks}')

conn.close()
