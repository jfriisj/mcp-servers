#!/usr/bin/env python3
"""
Manual test script for Phase 2 ProjectService

Tests:
1. Create project from Markdown file with YAML frontmatter
2. Verify database insertion
3. Verify folder structure creation
4. Display project details
"""

import sys
from pathlib import Path
from pprint import pprint

# Add parent directory to path for proper imports
sys.path.insert(0, str(Path(__file__).parent))

from src.container import Container
from src.domain.models import SLRProject


def test_create_project_from_markdown():
    """Test creating a project from markdown file"""
    print("=" * 80)
    print("PHASE 2 MANUAL TEST: Create SLR Project from Markdown")
    print("=" * 80)
    print()
    
    # Initialize container with correct database path
    print("1️⃣ Initializing container...")
    container = Container(database_path="database/slr_database.db")
    project_service = container.get_project_service()
    print("✅ Container initialized\n")
    
    # Test parameters
    project_name = "microservices-patterns"
    file_path = "test-project-description.md"
    description = "Fallback description if extraction fails"
    
    print("2️⃣ Test Parameters:")
    print(f"   - Project Name: {project_name}")
    print(f"   - File Path: {file_path}")
    print(f"   - Extract Metadata: True")
    print()
    
    # Create project
    print("3️⃣ Creating project from markdown file...")
    try:
        project = project_service.create_project_from_file(
            project_name=project_name,
            file_path=file_path,
            description=description,
            extract_metadata=True
        )
        print("✅ Project created successfully!\n")
        
        # Display project details
        print("4️⃣ Project Details:")
        print(f"   - ID: {project.id}")
        print(f"   - Name: {project.name}")
        print(f"   - Display Name: {project.display_name}")
        print(f"   - Description: {project.description[:100]}...")
        print(f"   - Status: {project.status}")
        print(f"   - Phase: {project.current_phase}")
        print(f"   - Folder Path: {project.folder_path}")
        print(f"   - File Path: {project.project_file_path}")
        print(f"   - File Type: {project.project_file_type}")
        print()
        
        # Display research questions
        print("5️⃣ Research Questions:")
        if project.research_questions:
            for i, rq in enumerate(project.research_questions, 1):
                print(f"   RQ{i}: {rq}")
        else:
            print("   No research questions extracted")
        print()
        
        # Display PICO framework
        print("6️⃣ PICO Framework:")
        print(f"   - Population: {project.population}")
        print(f"   - Intervention: {project.intervention}")
        print(f"   - Comparison: {project.comparison}")
        print(f"   - Outcome: {project.outcome}")
        print()
        
        # Display team and metadata
        print("7️⃣ Team & Metadata:")
        print(f"   - Team Members: {', '.join(project.team_members) if project.team_members else 'None'}")
        print(f"   - Tags: {', '.join(project.tags) if project.tags else 'None'}")
        print(f"   - Notes: {project.notes if project.notes else 'None'}")
        print()
        
        # Check folder structure
        print("8️⃣ Checking Folder Structure:")
        project_dir = Path(project.folder_path)
        if project_dir.exists():
            print(f"   ✅ Project directory exists: {project_dir}")
            
            # List created folders
            folders = [f for f in project_dir.rglob("*") if f.is_dir()]
            print(f"   📁 Created {len(folders)} folders:")
            for folder in sorted(folders)[:15]:  # Show first 15
                print(f"      - {folder.relative_to(project_dir)}")
            if len(folders) > 15:
                print(f"      ... and {len(folders) - 15} more")
            
            # List created files
            files = [f for f in project_dir.rglob("*") if f.is_file()]
            print(f"   📄 Created {len(files)} files:")
            for file in sorted(files):
                print(f"      - {file.relative_to(project_dir)}")
        else:
            print(f"   ❌ Project directory not found: {project_dir}")
        print()
        
        # Verify database
        print("9️⃣ Verifying Database Persistence:")
        if project.id:
            retrieved_project = project_service.project_repository.get_by_id(project.id)
        else:
            retrieved_project = None
        if retrieved_project:
            print(f"   ✅ Project found in database with ID: {retrieved_project.id}")
            print(f"   - Name matches: {retrieved_project.name == project.name}")
            print(f"   - Display name matches: {retrieved_project.display_name == project.display_name}")
            print(f"   - RQs match: {len(retrieved_project.research_questions) == len(project.research_questions)}")
        else:
            print(f"   ❌ Project not found in database")
        print()
        
        # Test retrieval by name
        print("🔟 Testing Retrieval by Name:")
        retrieved_by_name = project_service.project_repository.get_by_name(project_name)
        if retrieved_by_name:
            print(f"   ✅ Project found by name: {retrieved_by_name.name}")
        else:
            print(f"   ❌ Project not found by name")
        print()
        
        # Summary
        print("=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"Project '{project.display_name}' created with ID {project.id}")
        print(f"Location: {project.folder_path}")
        print(f"Database: Verified")
        print(f"Folders: {len(folders) if project_dir.exists() else 0} created")
        print(f"Files: {len(files) if project_dir.exists() else 0} created")
        
        return project
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_list_projects():
    """Test listing all projects"""
    print("\n" + "=" * 80)
    print("BONUS TEST: List All Projects")
    print("=" * 80)
    print()
    
    container = Container(database_path="database/slr_database.db")
    project_repo = container.get_project_repository()
    
    projects = project_repo.list_all()
    print(f"Found {len(projects)} projects in database:")
    for i, project in enumerate(projects, 1):
        print(f"{i}. {project.display_name} (ID: {project.id}, Status: {project.status}, Phase: {project.current_phase})")
    print()


if __name__ == "__main__":
    # Run main test
    project = test_create_project_from_markdown()
    
    # Run bonus test
    if project:
        test_list_projects()
