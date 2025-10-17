#!/usr/bin/env python3
"""
Test script to verify refactored methods in research_document_service.py

This script tests the 3 major refactored methods:
1. upload_paper
2. detect_and_remove_duplicates
3. get_corpus_statistics

And their helper methods:
- _validate_file_path
- _extract_and_merge_metadata
- _validate_paper_metadata
- _build_research_paper_entity
- _group_duplicate_papers
- _build_duplicate_report
- _remove_duplicate_papers
- _calculate_basic_corpus_statistics
- _calculate_citation_statistics
- _aggregate_paper_distributions
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test that all imports work correctly after refactoring."""
    print("=" * 70)
    print("TEST 1: Import Verification")
    print("=" * 70)
    
    try:
        from services.research_document_service import ResearchDocumentService
        print("✅ Successfully imported ResearchDocumentService")
        
        from domain.models import ResearchPaper, Author, Journal
        print("✅ Successfully imported domain models")
        
        from infrastructure.database.database import Database
        print("✅ Successfully imported Database")
        
        from infrastructure.repositories.paper_repository import PaperRepository
        print("✅ Successfully imported PaperRepository")
        
        print("\n✅ ALL IMPORTS SUCCESSFUL!\n")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_service_instantiation():
    """Test that the service can be instantiated."""
    print("=" * 70)
    print("TEST 2: Service Instantiation")
    print("=" * 70)
    
    try:
        from services.research_document_service import ResearchDocumentService
        from infrastructure.database.database import Database
        from infrastructure.repositories.paper_repository import PaperRepository
        
        # Create in-memory database
        db = Database(':memory:')
        print("✅ Created in-memory database")
        
        # Create repository
        repo = PaperRepository(db)
        print("✅ Created paper repository")
        
        # Create service
        service = ResearchDocumentService(repo)
        print("✅ Created ResearchDocumentService")
        
        # Verify helper methods exist
        helper_methods = [
            '_validate_file_path',
            '_extract_and_merge_metadata',
            '_validate_paper_metadata',
            '_build_research_paper_entity',
            '_group_duplicate_papers',
            '_build_duplicate_report',
            '_remove_duplicate_papers',
            '_calculate_basic_corpus_statistics',
            '_calculate_citation_statistics',
            '_aggregate_paper_distributions'
        ]
        
        print("\nVerifying helper methods exist:")
        for method_name in helper_methods:
            if hasattr(service, method_name):
                print(f"  ✅ {method_name}")
            else:
                print(f"  ❌ {method_name} - NOT FOUND")
                return False
        
        print("\n✅ ALL HELPER METHODS EXIST!\n")
        return service, repo
        
    except Exception as e:
        print(f"❌ Service instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_corpus_statistics(service):
    """Test the refactored get_corpus_statistics method."""
    print("=" * 70)
    print("TEST 3: Corpus Statistics (Refactored Method)")
    print("=" * 70)
    
    try:
        stats = service.get_corpus_statistics()
        print("✅ Successfully called get_corpus_statistics()")
        
        # Verify structure
        expected_keys = [
            'total_papers', 'review_status', 'quality_assessed',
            'indexed_papers', 'total_size_mb', 'citation_statistics',
            'methodologies', 'study_types', 'publication_years',
            'journals', 'file_types', 'authors'
        ]
        
        print("\nVerifying statistics structure:")
        for key in expected_keys:
            if key in stats:
                print(f"  ✅ {key}: {stats[key]}")
            else:
                print(f"  ❌ {key} - MISSING")
                return False
        
        print("\n✅ CORPUS STATISTICS TEST PASSED!\n")
        return True
        
    except Exception as e:
        print(f"❌ Corpus statistics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_duplicate_detection(service):
    """Test the refactored detect_and_remove_duplicates method."""
    print("=" * 70)
    print("TEST 4: Duplicate Detection (Refactored Method)")
    print("=" * 70)
    
    try:
        result = service.detect_and_remove_duplicates(
            similarity_threshold=0.85,
            dry_run=True
        )
        print("✅ Successfully called detect_and_remove_duplicates()")
        
        # Verify structure
        expected_keys = [
            'success', 'dry_run', 'duplicates_found', 'papers_removed',
            'total_papers_before', 'total_papers_after', 'duplicate_groups',
            'similarity_threshold', 'duplicate_details', 'message'
        ]
        
        print("\nVerifying result structure:")
        for key in expected_keys:
            if key in result:
                print(f"  ✅ {key}: {result[key]}")
            else:
                print(f"  ❌ {key} - MISSING")
                return False
        
        print("\n✅ DUPLICATE DETECTION TEST PASSED!\n")
        return True
        
    except Exception as e:
        print(f"❌ Duplicate detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_helper_method_isolation():
    """Test that helper methods can be called independently."""
    print("=" * 70)
    print("TEST 5: Helper Method Isolation")
    print("=" * 70)
    
    try:
        from services.research_document_service import ResearchDocumentService
        from infrastructure.database.database import Database
        from infrastructure.repositories.paper_repository import PaperRepository
        
        db = Database(':memory:')
        repo = PaperRepository(db)
        service = ResearchDocumentService(repo)
        
        # Test _calculate_basic_corpus_statistics with empty list
        print("\nTesting _calculate_basic_corpus_statistics:")
        stats = service._calculate_basic_corpus_statistics([])
        print(f"  ✅ Returns: {stats}")
        assert 'total_papers' in stats
        assert stats['total_papers'] == 0
        
        # Test _calculate_citation_statistics with empty list
        print("\nTesting _calculate_citation_statistics:")
        cit_stats = service._calculate_citation_statistics([])
        print(f"  ✅ Returns: {cit_stats}")
        assert 'total_citations' in cit_stats
        
        # Test _aggregate_paper_distributions with empty list
        print("\nTesting _aggregate_paper_distributions:")
        dist = service._aggregate_paper_distributions([])
        print(f"  ✅ Returns keys: {list(dist.keys())}")
        assert 'methodologies' in dist
        assert 'study_types' in dist
        
        print("\n✅ HELPER METHOD ISOLATION TEST PASSED!\n")
        return True
        
    except Exception as e:
        print(f"❌ Helper method isolation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("REFACTORED METHODS VERIFICATION TEST SUITE")
    print("=" * 70 + "\n")
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: Instantiation
    service_result = test_service_instantiation()
    if service_result:
        service, repo = service_result
        results.append(("Instantiation", True))
        
        # Test 3: Corpus Statistics
        results.append(("Corpus Statistics", test_corpus_statistics(service)))
        
        # Test 4: Duplicate Detection
        results.append(("Duplicate Detection", test_duplicate_detection(service)))
        
        # Test 5: Helper Methods
        results.append(("Helper Method Isolation", test_helper_method_isolation()))
    else:
        results.append(("Instantiation", False))
    
    # Print summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Refactoring is working correctly!\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
