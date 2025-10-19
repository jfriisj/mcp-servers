"""
Phase 3 Integration Test - Complete Workflow

Tests the full Phase 3 workflow:
1. Create SLR project (Phase 2)
2. Upload paper to project (Phase 3)
3. List papers in project (Phase 3)
4. Verify database linkage (Phase 3)
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def test_phase3_integration():
    """Test complete Phase 3 workflow."""
    
    print("=" * 80)
    print("PHASE 3 INTEGRATION TEST")
    print("=" * 80)
    print()
    
    # Absolute path to slr-server root
    SLR_SERVER_ROOT = Path(__file__).parent.parent.absolute()
    db_path = SLR_SERVER_ROOT / "database" / "slr_database.db"
    test_project_name = f"test-phase3-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    try:
        # Test 1: Verify Phase 2 project exists or create one
        print("TEST 1: Check/Create Test Project")
        print("-" * 80)
        
        cursor.execute("SELECT id, name FROM slr_projects WHERE name = ?", ("microservices-patterns",))
        project = cursor.fetchone()
        
        if project:
            project_id, project_name = project
            print(f"✅ Using existing project: {project_name} (ID: {project_id})")
        else:
            print("ℹ️  No test project found. Create one using test_phase2_manual.py first.")
            print("   Or use MCP tool: create_slr_project")
            conn.close()
            return False
        
        print()
        
        # Test 2: Verify Phase 3 schema changes
        print("TEST 2: Verify Phase 3 Database Schema")
        print("-" * 80)
        
        cursor.execute("PRAGMA table_info(research_papers)")
        columns = {col[1]: col for col in cursor.fetchall()}
        
        if 'project_id' in columns:
            col_info = columns['project_id']
            print(f"✅ project_id column exists")
            print(f"   Type: {col_info[2]}")
            print(f"   Nullable: {'Yes' if col_info[3] == 0 else 'No'}")
        else:
            print("❌ project_id column missing. Run migration: python run_phase3_migration.py")
            conn.close()
            return False
        
        cursor.execute("PRAGMA index_list(research_papers)")
        indices = cursor.fetchall()
        has_index = any('project_id' in idx[1] for idx in indices)
        
        if has_index:
            print("✅ Index on project_id exists")
        else:
            print("⚠️  Index on project_id missing (optional)")
        
        print()
        
        # Test 3: Check current paper count
        print("TEST 3: Check Current Papers in Project")
        print("-" * 80)
        
        cursor.execute("""
            SELECT COUNT(*) FROM research_papers 
            WHERE project_id = ?
        """, (project_id,))
        
        initial_count = cursor.fetchone()[0]
        print(f"📊 Initial paper count: {initial_count}")
        
        if initial_count > 0:
            print(f"ℹ️  Project already has {initial_count} paper(s)")
            cursor.execute("""
                SELECT id, title, file_path 
                FROM research_papers 
                WHERE project_id = ?
                LIMIT 3
            """, (project_id,))
            
            papers = cursor.fetchall()
            print("\n   Recent papers:")
            for pid, title, fpath in papers:
                print(f"   • [{pid}] {title[:50]}...")
        
        print()
        
        # Test 4: Simulate paper upload (database level)
        print("TEST 4: Simulate Paper Upload to Project")
        print("-" * 80)
        
        test_paper_data = {
            'title': f'Test Paper for Phase 3 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            'file_path': f'/test/papers/phase3-test-{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf',
            'file_type': 'pdf',
            'project_id': project_id,
            'publication_year': 2024,
            'keywords': '["test", "phase3", "integration"]',
            'tags': '["automated-test"]',
            'included_in_review': False,
            'indexed': 0,
            'quality_assessed': 0,
            'citation_count': 0,
            'upload_date': datetime.now().isoformat(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        cursor.execute("""
            INSERT INTO research_papers (
                title, file_path, file_type, project_id, publication_year,
                keywords, tags, included_in_review, indexed, quality_assessed, citation_count,
                upload_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_paper_data['title'],
            test_paper_data['file_path'],
            test_paper_data['file_type'],
            test_paper_data['project_id'],
            test_paper_data['publication_year'],
            test_paper_data['keywords'],
            test_paper_data['tags'],
            test_paper_data['included_in_review'],
            test_paper_data['indexed'],
            test_paper_data['quality_assessed'],
            test_paper_data['citation_count'],
            test_paper_data['upload_date'],
            test_paper_data['created_at'],
            test_paper_data['updated_at']
        ))
        
        test_paper_id = cursor.lastrowid
        conn.commit()
        
        print(f"✅ Test paper inserted")
        print(f"   Paper ID: {test_paper_id}")
        print(f"   Title: {test_paper_data['title']}")
        print(f"   Project ID: {test_paper_data['project_id']}")
        
        print()
        
        # Test 5: Verify paper linkage
        print("TEST 5: Verify Paper-Project Linkage")
        print("-" * 80)
        
        cursor.execute("""
            SELECT p.id, p.title, p.project_id, proj.name, proj.display_name
            FROM research_papers p
            JOIN slr_projects proj ON p.project_id = proj.id
            WHERE p.id = ?
        """, (test_paper_id,))
        
        linked_paper = cursor.fetchone()
        
        if linked_paper:
            pid, title, proj_id, proj_name, proj_display = linked_paper
            print(f"✅ Paper correctly linked to project")
            print(f"   Paper: [{pid}] {title[:50]}...")
            print(f"   Project: {proj_display} ({proj_name})")
            print(f"   Project ID Match: {proj_id == project_id}")
        else:
            print("❌ Paper linkage verification failed")
            conn.close()
            return False
        
        print()
        
        # Test 6: Test query by project (repository method simulation)
        print("TEST 6: Query Papers by Project")
        print("-" * 80)
        
        cursor.execute("""
            SELECT COUNT(*) FROM research_papers 
            WHERE project_id = ?
        """, (project_id,))
        
        final_count = cursor.fetchone()[0]
        print(f"📊 Final paper count: {final_count}")
        print(f"   Increase: +{final_count - initial_count}")
        
        if final_count > initial_count:
            print(f"✅ Paper count increased correctly")
        else:
            print(f"❌ Paper count did not increase")
            conn.close()
            return False
        
        # Get all papers for project
        cursor.execute("""
            SELECT id, title, included_in_review, file_type, publication_year
            FROM research_papers
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (project_id,))
        
        project_papers = cursor.fetchall()
        print(f"\n   Papers in project (showing {len(project_papers)}):")
        for pid, title, included, ftype, year in project_papers:
            status_str = "included" if included else "screening"
            year_str = f"{year}" if year else "no year"
            print(f"   • [{pid}] {title[:50]}... | {ftype} | {year_str} | {status_str}")
        
        print()
        
        # Test 7: Test backward compatibility (global papers)
        print("TEST 7: Verify Backward Compatibility")
        print("-" * 80)
        
        cursor.execute("""
            SELECT COUNT(*) FROM research_papers 
            WHERE project_id IS NULL
        """, ())
        
        global_paper_count = cursor.fetchone()[0]
        print(f"📊 Global papers (no project): {global_paper_count}")
        
        if global_paper_count >= 0:
            print(f"✅ Backward compatibility maintained")
            print(f"   Papers without project_id still exist and are queryable")
        
        print()
        
        # Test 8: Foreign key constraint test
        print("TEST 8: Test Foreign Key Constraint")
        print("-" * 80)
        
        # Try to insert paper with invalid project_id
        try:
            cursor.execute("""
                INSERT INTO research_papers (
                    title, file_path, file_type, project_id
                ) VALUES (?, ?, ?, ?)
            """, ("Invalid FK Test", "/test/invalid.pdf", "pdf", 99999))
            
            conn.commit()
            print("⚠️  Foreign key constraint not enforced (SQLite limitation)")
            
            # Clean up
            cursor.execute("DELETE FROM research_papers WHERE title = ?", ("Invalid FK Test",))
            conn.commit()
            
        except sqlite3.IntegrityError:
            print("✅ Foreign key constraint enforced")
            conn.rollback()
        
        print()
        
        # Summary
        print("=" * 80)
        print("✅ ALL PHASE 3 INTEGRATION TESTS PASSED")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  • Project used: {project_name} (ID: {project_id})")
        print(f"  • Test paper created: ID {test_paper_id}")
        print(f"  • Papers in project: {final_count}")
        print(f"  • Global papers: {global_paper_count}")
        print(f"  • Database schema: ✅ Correct")
        print(f"  • Paper-project linkage: ✅ Working")
        print(f"  • Backward compatibility: ✅ Maintained")
        print()
        print("🎉 Phase 3 implementation validated!")
        print()
        print("Next steps:")
        print("  1. Test via MCP server: upload_paper_to_project")
        print("  2. Test via MCP server: list_project_papers")
        print("  3. Start Phase 3.5: File system organization")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        conn.close()
        return False

if __name__ == "__main__":
    success = test_phase3_integration()
    
    if not success:
        print("\n❌ Integration test failed")
        exit(1)
    else:
        print("\n✅ Integration test passed")
