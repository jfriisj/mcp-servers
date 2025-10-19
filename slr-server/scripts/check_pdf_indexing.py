#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path

# Absolute path to database and data
SLR_SERVER_ROOT = Path(__file__).parent.parent.absolute()
db_path = str(SLR_SERVER_ROOT / "database" / "slr_database.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get papers with chunks
cursor.execute('SELECT COUNT(DISTINCT paper_id) FROM chunks')
papers_indexed = cursor.fetchone()[0]

# Get total chunks
cursor.execute('SELECT COUNT(*) FROM chunks')
total_chunks = cursor.fetchone()[0]

# Get papers that have existing PDFs in data/papers/
cursor.execute("SELECT id, title, file_path FROM research_papers WHERE file_path IS NOT NULL AND file_path != ''")
papers = cursor.fetchall()

papers_dir = SLR_SERVER_ROOT / "data" / "papers"
actual_pdfs = set(f.name for f in papers_dir.glob('*.pdf'))

# Find paper IDs with existing PDFs
paper_ids_with_pdfs = set()
for paper_id, title, file_path in papers:
    if file_path:
        filename = Path(file_path).name
        if filename in actual_pdfs:
            paper_ids_with_pdfs.add(paper_id)

# Get papers with chunks
cursor.execute('SELECT DISTINCT paper_id FROM chunks ORDER BY paper_id')
papers_with_chunks = set(row[0] for row in cursor.fetchall())

# Find which ones are indexed
indexed_with_pdfs = papers_with_chunks & paper_ids_with_pdfs
not_indexed_with_pdfs = paper_ids_with_pdfs - papers_with_chunks

print(f'Total PDF files: {len(actual_pdfs)}')
print(f'Papers in DB with these PDFs: {len(paper_ids_with_pdfs)}')
print(f'\nIndexing Status:')
print(f'  OK Indexed: {len(indexed_with_pdfs)}')
print(f'  NOT indexed: {len(not_indexed_with_pdfs)}')
print(f'  Total chunks: {total_chunks}')

print(f'\nPapers NOT yet indexed:')
for paper_id in sorted(not_indexed_with_pdfs):
    cursor.execute("SELECT title FROM research_papers WHERE id = ?", (paper_id,))
    result = cursor.fetchone()
    if result:
        print(f'  - ID {paper_id}: {result[0][:60]}...')

conn.close()
