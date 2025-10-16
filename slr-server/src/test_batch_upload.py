#!/usr/bin/env python3
"""
Test script for batch BibTeX upload functionality.

This script tests the new batch upload feature by:
1. Connecting directly to the database
2. Using the batch upload service
3. Uploading all BibTeX files with full entry extraction
"""

import os
import sys
from pathlib import Path

# Add the slr-server directory to the Python path  
slr_root = Path(__file__).parent.parent
sys.path.insert(0, str(slr_root))

# Import required modules using the proper module path
from src.services.research_document_service import ResearchDocumentService
from src.repositories.paper_repository import PaperRepository
from src.database.connection import DatabaseConnection

def main():
        # Database setup - slr-server root is already defined above
        # slr_root = Path(__file__).parent.parent
        db_path = slr_root / "database" / "slr_production.db"
        print(f"📂 Using database: {db_path}")
        
        # Initialize database connection
        connection = DatabaseConnection(str(db_path))
        
        # Initialize repository and service
        paper_repository = PaperRepository(connection)
        document_service = ResearchDocumentService(paper_repository)
        
        # Find all BibTeX files
        papers_dir = slr_root / "papers"
        bib_files = sorted([f for f in papers_dir.glob("*.bib")])
        
        print(f"📚 Found {len(bib_files)} BibTeX files:")
        for file in bib_files:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                import re
                entries = re.findall(r'@\w+\{', content)
                print(f"  • {file.name}: {len(entries)} entries")
        
        # Get current paper count
        try:
            current_papers = paper_repository.list_all()
            print(f"\n📊 Current papers in database: {len(current_papers)}")
        except Exception as e:
            print(f"\n📊 Could not count current papers: {e}")
            current_papers = []
        
        total_uploaded = 0
        total_expected = 0
        
        # Process each BibTeX file
        for i, bib_file in enumerate(bib_files, 1):
            print(f"\n🔄 Processing file {i}/{len(bib_files)}: {bib_file.name}")
            
            try:
                # Count expected entries
                with open(bib_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    import re
                    entries = re.findall(r'@\w+\{', content)
                    expected_count = len(entries)
                    total_expected += expected_count
                
                # Use batch upload
                papers = document_service.upload_bibliography_batch(
                    file_path=str(bib_file),
                    tags=[f"primo-export-{i}", "speech-translation", "systematic-search"],
                    auto_extract_metadata=True
                )
                
                uploaded_count = len(papers)
                total_uploaded += uploaded_count
                
                print(f"✅ Successfully uploaded {uploaded_count}/{expected_count} papers")
                
                # Show first few titles
                for j, paper in enumerate(papers[:3]):
                    authors_str = ', '.join([author.name for author in paper.authors[:2]]) if paper.authors else 'No authors'
                    if len(paper.authors) > 2:
                        authors_str += f" et al. ({len(paper.authors)} authors)"
                    
                    print(f"   {j+1}. {paper.title[:60]}...")
                    print(f"      Authors: {authors_str}")
                    print(f"      Year: {paper.publication_year}")
                
                if uploaded_count > 3:
                    print(f"   ... and {uploaded_count - 3} more papers")
                
            except Exception as e:
                print(f"❌ Error processing {bib_file.name}: {e}")
                # Print full traceback for debugging
                import traceback
                traceback.print_exc()
        
        print(f"\n📈 Summary:")
        print(f"   Total files processed: {len(bib_files)}")
        print(f"   Total papers expected: {total_expected}")
        print(f"   Total papers uploaded: {total_uploaded}")
        print(f"   Success rate: {total_uploaded/total_expected*100:.1f}%" if total_expected > 0 else "   Success rate: N/A")
        
        # Final count
        try:
            final_papers = paper_repository.list_all()
            print(f"   Papers in database now: {len(final_papers)}")
            print(f"   New papers added: {len(final_papers) - len(current_papers)}")
        except Exception as e:
            print(f"   Could not get final count: {e}")

if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the slr-server directory")
        sys.exit(1)