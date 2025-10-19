#!/usr/bin/env python3
"""
Test error handling for Phase 2
"""

import sys
from pathlib import Path

# Absolute path to slr-server root
SLR_SERVER_ROOT = Path(__file__).parent.parent.absolute()

sys.path.insert(0, str(SLR_SERVER_ROOT / "src"))

from src.container import Container
from src.repositories.base_repository import DuplicateEntityError


def test_duplicate_project_name():
    """Test that duplicate project names are properly rejected"""
    print("=" * 80)
    print("TESTING: Duplicate Project Name Error Handling")
    print("=" * 80)
    print()
    
    database_path = str(SLR_SERVER_ROOT / "database" / "slr_database.db")
    container = Container(database_path=database_path)
    project_service = container.get_project_service()
    
    project_name = "duplicate-test-project"
    
    try:
        # Create first project
        print(f"1️⃣ Creating project '{project_name}'...")
        project1 = project_service.create_project_manual(
            project_name=project_name,
            display_name="Duplicate Test",
            description="First project",
        )
        print(f"✅ First project created (ID: {project1.id})")
        print()
        
        # Try to create duplicate
        print(f"2️⃣ Attempting to create duplicate project '{project_name}'...")
        try:
            project2 = project_service.create_project_manual(
                project_name=project_name,
                display_name="Duplicate Test 2",
                description="Second project - should fail",
            )
            print("❌ FAILURE: Duplicate was allowed!")
            return False
            
        except DuplicateEntityError as e:
            print(f"✅ SUCCESS: Duplicate correctly rejected!")
            print(f"   Error message: {str(e)}")
            print()
            return True
            
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_invalid_file_path():
    """Test handling of non-existent file"""
    print("=" * 80)
    print("TESTING: Invalid File Path Error Handling")
    print("=" * 80)
    print()
    
    database_path = str(SLR_SERVER_ROOT / "database" / "slr_database.db")
    container = Container(database_path=database_path)
    project_service = container.get_project_service()
    
    try:
        print("Attempting to create project from non-existent file...")
        project = project_service.create_project_from_file(
            project_name="invalid-file-project",
            file_path="nonexistent-file.md",
            description="Should fail",
        )
        print("❌ FAILURE: Invalid file was accepted!")
        return False
        
    except Exception as e:
        print(f"✅ SUCCESS: Invalid file correctly rejected!")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)[:100]}...")
        print()
        return True


if __name__ == "__main__":
    print("Running Error Handling Tests")
    print("=" * 80)
    print()
    
    test1_passed = test_duplicate_project_name()
    test2_passed = test_invalid_file_path()
    
    print()
    print("=" * 80)
    print("TEST RESULTS:")
    print(f"  Duplicate project name: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  Invalid file path: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("=" * 80)
    
    all_passed = test1_passed and test2_passed
    sys.exit(0 if all_passed else 1)
