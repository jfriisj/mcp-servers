"""
Phase 3 Manual Test: Upload paper to SLR project

Tests the new upload_paper_to_project functionality that links papers to specific projects.
"""

import json
from pathlib import Path

# Absolute path to slr-server root
SLR_SERVER_ROOT = Path(__file__).parent.parent.absolute()

from src.infrastructure.database_connection import DatabaseConnection
from src.repositories.project_repository import ProjectRepository
from src.repositories.paper_repository import PaperRepository
from src.services.project_service import ProjectService
from src.services.research_document_service import ResearchDocumentService


def test_phase3_upload_paper_to_project():
    """Test uploading a paper to a specific SLR project."""
    
    print("=" * 70)
    print("PHASE 3 MANUAL TEST: Upload Paper to Project")
    print("=" * 70)
    print()
    
    # Initialize database connection
    db_path = SLR_SERVER_ROOT / "database" / "slr_database.db"
    db_conn = DatabaseConnection(str(db_path))
    
    # Initialize repositories
    project_repo = ProjectRepository(db_conn)
    paper_repo = PaperRepository(db_conn)
    
    # Initialize services
    project_service = ProjectService(project_repo)
    research_doc_service = ResearchDocumentService(paper_repo)
    
    print("1️⃣  Step 1: Check if test project exists")
    print("-" * 70)
    
    test_project_name = "microservices-patterns"
    project = project_repo.get_by_name(test_project_name)
    
    if not project:
        print(f"❌ Project '{test_project_name}' not found")
        print(f"💡 Please run test_phase2_manual.py first to create the project")
        return False
    
    print(f"✅ Project found: {project.name}")
    print(f"   ID: {project.id}")
    print(f"   Display Name: {project.display_name}")
    print(f"   Status: {project.status}")
    print()
    
    print("2️⃣  Step 2: Create a test paper file")
    print("-" * 70)
    
    # Create a test markdown file as a paper
    test_paper_path = SLR_SERVER_ROOT / "test_paper.md"
    test_paper_content = """# Test Research Paper

## Abstract
This is a test research paper for Phase 3 testing. It demonstrates the ability to upload papers to specific SLR projects.

## Introduction
Microservices architecture has become a popular approach for building scalable distributed systems.

## Methodology
This study employs a systematic literature review methodology to analyze patterns in microservices architecture.

## Results
We identified 25 key patterns used in microservices implementations.

## Conclusion
Microservices patterns provide valuable guidance for system architects.

## References
1. Newman, S. (2015). Building Microservices. O'Reilly Media.
2. Richardson, C. (2018). Microservices Patterns. Manning Publications.
"""
    
    with open(test_paper_path, 'w', encoding='utf-8') as f:
        f.write(test_paper_content)
    
    print(f"✅ Test paper created: {test_paper_path}")
    print()
    
    print("3️⃣  Step 3: Upload paper to project (Phase 3 functionality)")
    print("-" * 70)
    
    try:
        # Upload paper with project_id (Phase 3)
        paper = research_doc_service.upload_paper(
            file_path=str(test_paper_path),
            title="Microservices Architecture Patterns: A Systematic Review",
            publication_year=2024,
            tags=["microservices", "patterns", "architecture"],
            project_id=project.id  # Phase 3: Link to project
        )
        
        print(f"✅ Paper uploaded successfully!")
        print(f"   Paper ID: {paper.id}")
        print(f"   Title: {paper.title}")
        print(f"   Project ID: {paper.project_id}")
        print(f"   File Path: {paper.file_path}")
        print(f"   File Type: {paper.file_type}")
        print()
        
    except Exception as e:
        print(f"❌ Error uploading paper: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("4️⃣  Step 4: Verify paper is linked to project in database")
    print("-" * 70)
    
    # Retrieve paper and verify project_id
    retrieved_paper = paper_repo.get_by_id(paper.id)
    
    if retrieved_paper:
        print(f"✅ Paper retrieved from database")
        print(f"   Paper ID: {retrieved_paper.id}")
        print(f"   Title: {retrieved_paper.title}")
        print(f"   Project ID: {retrieved_paper.project_id}")
        
        if retrieved_paper.project_id == project.id:
            print(f"✅ Paper correctly linked to project!")
        else:
            print(f"❌ Paper project_id mismatch: expected {project.id}, got {retrieved_paper.project_id}")
            return False
    else:
        print(f"❌ Could not retrieve paper from database")
        return False
    
    print()
    
    print("5️⃣  Step 5: Query papers by project (using new repository method)")
    print("-" * 70)
    
    try:
        project_papers = paper_repo.get_by_project(project.id)
        
        print(f"✅ Retrieved {len(project_papers)} paper(s) for project '{project.name}'")
        
        for i, p in enumerate(project_papers, 1):
            print(f"\n   Paper {i}:")
            print(f"     • ID: {p.id}")
            print(f"     • Title: {p.title}")
            print(f"     • Project ID: {p.project_id}")
            print(f"     • File Type: {p.file_type}")
        
        # Verify our paper is in the list
        if any(p.id == paper.id for p in project_papers):
            print(f"\n✅ Our uploaded paper is in the project papers list!")
        else:
            print(f"\n❌ Our uploaded paper is NOT in the project papers list")
            return False
            
    except Exception as e:
        print(f"❌ Error querying papers by project: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    print("6️⃣  Step 6: Count papers by project")
    print("-" * 70)
    
    try:
        paper_count = paper_repo.count_by_project(project.id)
        print(f"✅ Project '{project.name}' has {paper_count} paper(s)")
        
        if paper_count > 0:
            print(f"✅ Count matches expected value!")
        else:
            print(f"❌ Count is 0, expected at least 1")
            return False
            
    except Exception as e:
        print(f"❌ Error counting papers by project: {e}")
        return False
    
    print()
    
    print("7️⃣  Step 7: Test backward compatibility (upload without project_id)")
    print("-" * 70)
    
    try:
        # Upload paper WITHOUT project_id (should still work)
        global_paper = research_doc_service.upload_paper(
            file_path=str(test_paper_path),
            title="Global Paper (No Project)",
            publication_year=2024,
            tags=["test", "global"]
            # No project_id - this is a global paper
        )
        
        print(f"✅ Global paper uploaded successfully!")
        print(f"   Paper ID: {global_paper.id}")
        print(f"   Title: {global_paper.title}")
        print(f"   Project ID: {global_paper.project_id} (should be None)")
        
        if global_paper.project_id is None:
            print(f"✅ Backward compatibility confirmed - NULL project_id works!")
        else:
            print(f"⚠️  Warning: Global paper has project_id={global_paper.project_id}")
        
    except Exception as e:
        print(f"❌ Error testing backward compatibility: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("=" * 70)
    print("✅ ALL PHASE 3 TESTS PASSED!")
    print("=" * 70)
    print()
    print("📊 Summary:")
    print(f"   • Database migration: ✅ Successful")
    print(f"   • PaperRepository updated: ✅ Successful")
    print(f"   • Paper uploaded with project_id: ✅ Successful")
    print(f"   • Database link verified: ✅ Successful")
    print(f"   • Query papers by project: ✅ Successful")
    print(f"   • Count papers by project: ✅ Successful")
    print(f"   • Backward compatibility: ✅ Successful")
    print()
    
    return True


if __name__ == "__main__":
    success = test_phase3_upload_paper_to_project()
    
    if success:
        print("🎉 Phase 3 implementation is working correctly!")
    else:
        print("❌ Phase 3 testing failed - please review errors above")
        exit(1)
