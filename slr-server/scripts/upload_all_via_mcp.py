#!/usr/bin/env python3
"""
Upload all PDF documents using the SLR MCP tools.
This script will:
1. Initialize the database
2. Upload all PDFs from data/papers/
3. Index all papers
"""

import asyncio
import sys
from pathlib import Path
from typing import List

# Absolute path to slr-server root
SLR_SERVER_ROOT = Path(__file__).parent.parent.absolute()

# Add src to Python path
sys.path.insert(0, str(SLR_SERVER_ROOT / "src"))

from src.container import initialize_application
from src.domain.models import ResearchPaper
from src.services.research_document_service import ResearchDocumentService


async def upload_all_pdfs():
    """Upload all PDFs using MCP tools."""
    try:
        print("=" * 80)
        print("🚀 UPLOADING ALL DOCUMENTS VIA MCP TOOLS")
        print("=" * 80)
        
        # Initialize the application with fresh database
        print("\n1️⃣ Initializing application...")
        db_path = str(SLR_SERVER_ROOT / "database" / "slr_database.db")
        container = await initialize_application(database_path=db_path)
        print("✅ Application initialized\n")
        
        # Get the PDF files
        papers_dir = SLR_SERVER_ROOT / "data" / "papers"
        pdf_files = sorted(papers_dir.glob("*.pdf"))
        
        print(f"2️⃣ Found {len(pdf_files)} PDF files to upload")
        print(f"   Location: {papers_dir}\n")
        
        # Get service
        doc_service = container.get_document_service()
        
        # Upload each PDF
        uploaded_count = 0
        failed_count = 0
        errors = []
        
        print("3️⃣ Uploading documents...\n")
        
        for i, pdf_file in enumerate(pdf_files, 1):
            try:
                print(f"   [{i}/{len(pdf_files)}] Uploading: {pdf_file.name[:60]}...", end=" ")
                
                # Use the document service to upload
                result = doc_service.upload_paper(
                    file_path=str(pdf_file)
                )
                
                if result:
                    uploaded_count += 1
                    print(f"✅ (ID: {result.id})")
                else:
                    print("⚠️ No result returned")
                    failed_count += 1
                    
            except Exception as e:
                print(f"❌ Error: {str(e)[:80]}")
                failed_count += 1
                errors.append((pdf_file.name, str(e)))
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 UPLOAD SUMMARY")
        print("=" * 80)
        print(f"\n✅ Successfully uploaded: {uploaded_count}/{len(pdf_files)}")
        print(f"❌ Failed: {failed_count}/{len(pdf_files)}")
        
        if errors:
            print(f"\n⚠️ Errors encountered:")
            for filename, error in errors[:5]:  # Show first 5 errors
                print(f"   • {filename}: {error[:60]}...")
            if len(errors) > 5:
                print(f"   ... and {len(errors) - 5} more errors")
        
        # Check database
        paper_repo = container.get_paper_repository()
        papers = paper_repo.list_all()
        print(f"\n📂 Papers in database: {len(papers)}")
        
        if len(papers) > 0:
            print("\n4️⃣ Now indexing all papers...\n")
            
            # Index all papers
            chunking_service = container.get_chunking_service()
            indexed_count = 0
            indexing_errors = []
            
            for i, paper in enumerate(papers, 1):
                if not paper.id or not paper.file_path:
                    continue
                    
                try:
                    print(f"   [{i}/{len(papers)}] Indexing paper {paper.id}...", end=" ")
                    chunks = chunking_service.index_paper(paper.id)
                    indexed_count += 1
                    print(f"✅ ({len(chunks)} chunks)")
                except Exception as e:
                    print(f"⚠️ Error: {str(e)[:60]}")
                    indexing_errors.append((paper.id, str(e)))
            
            # Final summary
            print("\n" + "=" * 80)
            print("📊 INDEXING SUMMARY")
            print("=" * 80)
            print(f"\n✅ Successfully indexed: {indexed_count}/{len(papers)}")
            print(f"⚠️ Failed: {len(indexing_errors)}/{len(papers)}")
            
            # Get chunk stats
            chunk_repo = container.get_chunk_repository()
            all_chunks = chunk_repo.list_all()
            print(f"\n📈 Total chunks created: {len(all_chunks)}")
            
            if len(all_chunks) > 0:
                avg_chunks = len(all_chunks) / indexed_count if indexed_count > 0 else 0
                print(f"   Average chunks per paper: {avg_chunks:.1f}")
        
        print("\n" + "=" * 80)
        print("✅ COMPLETE!")
        print("=" * 80)
        return 0
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(upload_all_pdfs()))
