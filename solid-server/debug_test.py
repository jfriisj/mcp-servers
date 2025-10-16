#!/usr/bin/env python3
"""
Debug script to test refactoring suggestions functionality
"""
import sys
import os
sys.path.insert(0, '/app/src')

from pathlib import Path
from application.suggest_refactoring import RefactoringOptions, SuggestRefactoringUseCase
from application.analyze_file import AnalyzeFileUseCase
from domain.analyzers.solid_analyzer import SolidAnalyzer
from infrastructure.parsers.python_parser import PythonASTParser

# Test the RefactoringOptions with string max_suggestions
def test_refactoring_options():
    print("=== Testing RefactoringOptions ===")
    
    # Test with integer (should work)
    options1 = RefactoringOptions(max_suggestions=5, priority_filter="all")
    print(f"Integer max_suggestions: {type(options1.max_suggestions)} = {options1.max_suggestions}")
    
    # Test with string (might cause issue)
    try:
        options2 = RefactoringOptions(max_suggestions="5", priority_filter="all")
        print(f"String max_suggestions: {type(options2.max_suggestions)} = {options2.max_suggestions}")
    except Exception as e:
        print(f"Error with string max_suggestions: {e}")
    
    print()

def test_slicing():
    print("=== Testing list slicing operations ===")
    test_list = ['a', 'b', 'c', 'd', 'e', 'f']
    
    # Test with int
    try:
        result = test_list[:5]
        print(f"test_list[:5] works: {result}")
    except Exception as e:
        print(f"Error with int slicing: {e}")
    
    # Test with string
    try:
        result = test_list[:"5"]
        print(f"test_list[:\"5\"] works: {result}")
    except Exception as e:
        print(f"Error with string slicing: {e}")
    
    print()

if __name__ == "__main__":
    test_refactoring_options()
    test_slicing()