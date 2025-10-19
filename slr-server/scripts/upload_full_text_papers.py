#!/usr/bin/env python3
"""
Upload full-text papers from data/papers directory.

This script uploads all PDF papers from the data/papers directory with the
option to replace existing papers that only have abstracts.

Features:
- Batch uploads all 54 papers
- Detects and replaces existing papers with full-text versions
- Tracks upload progress and errors
- Generates detailed upload report
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.container import Container
from src.repositories.base_repository import DuplicateEntityError, RepositoryError


def get_paper_files():
    """Get all PDF files from data/papers directory."""
    papers_dir = project_root / "data" / "papers"
    if not papers_dir.exists():
        print(f"❌ Papers directory not found: {papers_dir}")
        return []
    
    pdf_files = sorted(papers_dir.glob("*.pdf"))
    return pdf_files


def upload_papers():
    """Upload all full-text papers."""
    # Initialize container
    container = Container()
    document_service = container.get_document_service()
    
    # Get all paper files
    paper_files = get_paper_files()
    print(f"\n📚 Found {len(paper_files)} PDF files to process\n")
    
    if not paper_files:
        print("❌ No PDF files found in data/papers directory")
        return
    
    # Track results
    results = {
        "uploaded": [],
        "updated": [],
        "errors": [],
        "skipped": []
    }
    
    total = len(paper_files)
    
    # Upload each paper
    for idx, pdf_file in enumerate(paper_files, 1):
        print(f"\n[{idx}/{total}] Processing: {pdf_file.name}")
        
        try:
            # Upload with full-text override
            paper, is_new = document_service.upload_paper_with_full_text(
                file_path=str(pdf_file),
                tags=["full-text", "real-time-translation"],
                auto_extract_metadata=True,
                replace_existing=True
            )
            
            if is_new:
                print(f"    ✅ Created: ID {paper.id}")
                results["uploaded"].append({
                    "id": paper.id,
                    "title": paper.title,
                    "file": pdf_file.name
                })
            else:
                print(f"    ✏️  Updated: ID {paper.id}")
                results["updated"].append({
                    "id": paper.id,
                    "title": paper.title,
                    "file": pdf_file.name
                })
                
        except DuplicateEntityError as e:
            print(f"    ⚠️  Duplicate detected: {str(e)[:80]}...")
            results["skipped"].append({
                "file": pdf_file.name,
                "reason": "Duplicate",
                "error": str(e)[:100]
            })
            
        except RepositoryError as e:
            print(f"    ❌ Repository error: {str(e)[:80]}...")
            results["errors"].append({
                "file": pdf_file.name,
                "error": str(e)[:200]
            })
            
        except Exception as e:
            print(f"    ❌ Error: {str(e)[:80]}...")
            results["errors"].append({
                "file": pdf_file.name,
                "error": str(e)[:200]
            })
    
    # Print summary
    print("\n" + "="*70)
    print("📊 UPLOAD SUMMARY")
    print("="*70)
    print(f"✅ Newly Uploaded: {len(results['uploaded'])}")
    print(f"✏️  Updated with Full-Text: {len(results['updated'])}")
    print(f"⚠️  Skipped: {len(results['skipped'])}")
    print(f"❌ Errors: {len(results['errors'])}")
    print(f"📈 Total Processed: {len(results['uploaded']) + len(results['updated']) + len(results['skipped']) + len(results['errors'])}/{total}")
    
    # Show details if there were updates
    if results["updated"]:
        print(f"\n📝 Updated Papers (with full-text replacement):")
        for item in results["updated"][:10]:
            print(f"   • ID {item['id']}: {item['title'][:60]}...")
        if len(results["updated"]) > 10:
            print(f"   ... and {len(results['updated']) - 10} more")
    
    # Show details if there were errors
    if results["errors"]:
        print(f"\n❌ Error Details:")
        for item in results["errors"][:5]:
            print(f"   • {item['file']}: {item['error'][:80]}...")
        if len(results["errors"]) > 5:
            print(f"   ... and {len(results['errors']) - 5} more")
    
    # Save detailed report
    report_file = project_root / "scripts" / f"upload_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Detailed report saved: {report_file}")
    
    return results


if __name__ == "__main__":
    print("\n🚀 Full-Text Paper Upload Process")
    print("="*70)
    upload_papers()
    print("\n✨ Process complete!")
