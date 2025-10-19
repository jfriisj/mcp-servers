#!/usr/bin/env python3
"""
Test PDF extraction for Phase 2
"""

import sys
from pathlib import Path

# Absolute path to slr-server root
SLR_SERVER_ROOT = Path(__file__).parent.parent.absolute()

sys.path.insert(0, str(SLR_SERVER_ROOT / "src"))

from src.container import Container


def test_pdf_extraction():
    """Test creating project from PDF file"""
    print("=" * 80)
    print("TESTING: Create Project from PDF")
    print("=" * 80)
    print()
    
    database_path = str(SLR_SERVER_ROOT / "database" / "slr_database.db")
    container = Container(database_path=database_path)
    project_service = container.get_project_service()
    
    # Test with existing PDF
    pdf_path = "projects/test.pdf"
    project_name = "test-pdf-project"
    
    print(f"📄 PDF File: {pdf_path}")
    print(f"📝 Project Name: {project_name}")
    print()
    
    try:
        print("Creating project from PDF...")
        project = project_service.create_project_from_file(
            project_name=project_name,
            file_path=pdf_path,
            description="Test project from PDF",
            extract_metadata=True
        )
        
        print("✅ Project created successfully!")
        print()
        print(f"ID: {project.id}")
        print(f"Name: {project.name}")
        print(f"Display Name: {project.display_name}")
        print(f"Description: {project.description[:100]}...")
        print(f"Research Questions: {len(project.research_questions)} found")
        for i, rq in enumerate(project.research_questions[:3], 1):
            print(f"  RQ{i}: {rq[:80]}...")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_pdf_extraction()
    sys.exit(0 if success else 1)
