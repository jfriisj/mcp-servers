#!/usr/bin/env python3
"""Test script to verify indexing fix works."""

import sys
from pathlib import Path

# Absolute path to slr-server root
SLR_SERVER_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(SLR_SERVER_ROOT / 'src'))

from container import Container
from services.academic_chunking_service import IndexingStrategy

# Initialize container
database_path = str(SLR_SERVER_ROOT / "database" / "slr_database.db")
container = Container(database_path=database_path)
paper_repo = container.get_paper_repository()
indexing_service = container.get_chunking_service()

# Get papers with PDFs (test a few)
papers_to_test = [451, 375, 23, 505, 504]  # Mix of recently fixed and newly uploaded

print(f"Testing indexing on {len(papers_to_test)} papers...\n")

results = {}
for paper_id in papers_to_test:
    try:
        paper = paper_repo.get_by_id(paper_id)
        if not paper:
            print(f"Paper {paper_id}: Not found")
            continue
        
        if not paper.file_path:
            print(f"Paper {paper_id}: No file_path")
            continue
        
        chunks = indexing_service.index_paper(paper_id, IndexingStrategy.HYBRID)
        results[paper_id] = len(chunks)
        title = paper.title[:40] if paper.title else "N/A"
        print(f"Paper {paper_id} ({title}...): {len(chunks)} chunks")
        
    except Exception as e:
        print(f"Paper {paper_id}: Error - {str(e)[:80]}")

print(f"\nSummary:")
print(f"  Successfully indexed: {len([r for r in results.values() if r > 0])}")
print(f"  Total chunks created: {sum(results.values())}")

