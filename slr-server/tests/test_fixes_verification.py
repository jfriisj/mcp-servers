#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test the upload fixes"""

import sys
from pathlib import Path

# Absolute path to slr-server root
SLR_SERVER_ROOT = Path(__file__).parent.parent.absolute()

sys.path.insert(0, str(SLR_SERVER_ROOT / 'src'))

from database.connection import DatabaseConnection
from repositories.paper_repository import PaperRepository
from services.research_document_service import ResearchDocumentService

db_conn = DatabaseConnection()
db = db_conn.connect()
repo = PaperRepository(db)
service = ResearchDocumentService(repo)

file_path = str(SLR_SERVER_ROOT / "data" / "papers" / "Primo_BibTeX_Export (6).bib")

try:
    result = service.upload_bibliography_batch(file_path=file_path)
    print(f"OK Success count: {result['success_count']}")
    print(f"FAIL count: {result['failure_count']}")
    print(f"Total: {result['total_entries']}")
    print(f"\n{result['summary']}")
    if result['skipped_entries']:
        print(f"\nFirst 5 failures:")
        for entry in result['skipped_entries'][:5]:
            print(f"  Entry {entry['entry_num']}: {entry['reason']}")
            print(f"    {entry['detail'][:100]}")
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
