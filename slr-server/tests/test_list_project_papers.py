"""
Test list_project_papers functionality.
"""

import sqlite3
from pathlib import Path

def test_list_project_papers():
    """Test listing papers for a project."""
    
    print("=" * 70)
    print("TEST: list_project_papers")
    print("=" * 70)
    print()
    
    db_path = Path(__file__).parent / "database" / "slr_database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get existing project
    cursor.execute("SELECT id, name FROM slr_projects LIMIT 1")
    project = cursor.fetchone()
    
    if not project:
        print("❌ No projects found. Create a project first.")
        conn.close()
        return False
    
    project_id, project_name = project
    print(f"✅ Testing with project: {project_name} (ID: {project_id})")
    print()
    
    # Check papers for this project
    cursor.execute("""
        SELECT COUNT(*) FROM research_papers 
        WHERE project_id = ?
    """, (project_id,))
    
    paper_count = cursor.fetchone()[0]
    print(f"📊 Papers in project: {paper_count}")
    
    if paper_count == 0:
        print("ℹ️  No papers in project yet (expected for new implementation)")
    else:
        # Show some papers
        cursor.execute("""
            SELECT id, title, screening_status 
            FROM research_papers 
            WHERE project_id = ?
            LIMIT 5
        """, (project_id,))
        
        papers = cursor.fetchall()
        print(f"\n📚 Sample papers:")
        for paper_id, title, status in papers:
            status_str = status if status else "no status"
            print(f"  • [{paper_id}] {title[:60]}... ({status_str})")
    
    conn.close()
    
    print()
    print("✅ Database query works. Ready to test MCP tool.")
    print()
    print("Next: Test via MCP server:")
    print(f"  Tool: list_project_papers")
    print(f"  Args: {{ \"project_name\": \"{project_name}\" }}")
    
    return True

if __name__ == "__main__":
    test_list_project_papers()
