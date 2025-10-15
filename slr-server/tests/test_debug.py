import asyncio
import sys
import os
from pathlib import Path

# Set up the path correctly
sys.path.insert(0, str(Path(__file__).parent / 'src'))
os.chdir(str(Path(__file__).parent / 'src'))

# Import with corrected path
from repositories.paper_repository import PaperRepository  
from database.connection import DatabaseConnection

def test_list_papers():
    try:
        print("Creating database connection...")
        db = DatabaseConnection("../slr_database.db")
        
        print("Creating paper repository...")
        repo = PaperRepository(db)
        
        print("Testing list_papers...")
        papers = repo.list_papers()
        print(f"Result: Found {len(papers)} papers")
        for paper in papers:
            print(f"  - {paper.title}")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print("Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_list_papers()
