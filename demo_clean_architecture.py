"""
Demo: Clean Architecture SOLID Server
=====================================
Demonstrates the refactored SOLID server using Clean Architecture.
This is the composition root where dependencies are wired together.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "solid-server" / "src"))

# Domain layer
from domain.models import SolidPrinciple

# Application layer  
from application.analyze_file import AnalyzeFileUseCase
from application.analyze_directory import (
    AnalyzeDirectoryUseCase,
    DirectoryFilters
)
from application.generate_report import (
    GenerateReportUseCase,
    ReportOptions
)
from application.suggest_refactoring import (
    SuggestRefactoringUseCase,
    RefactoringOptions
)

# Infrastructure layer
from infrastructure.analyzers.ast_analyzer import ASTAnalyzer
from infrastructure.analyzers.principle_checkers import (
    SRPChecker,
    OCPChecker,
    LSPChecker,
    ISPChecker,
    DIPChecker
)
from infrastructure.formatters.text_formatter import TextFormatter


async def main():
    """Demonstrate the clean architecture in action"""
    
    print("\n" + "=" * 70)
    print("CLEAN ARCHITECTURE SOLID SERVER DEMO")
    print("=" * 70)
    
    # ========================================
    # COMPOSITION ROOT - Dependency Injection
    # ========================================
    print("\n🔧 Setting up dependencies...")
    
    # 1. Create principle checkers
    checkers = [
        SRPChecker(),  # Single Responsibility
        OCPChecker(),  # Open-Closed
        LSPChecker(),  # Liskov Substitution
        ISPChecker(),  # Interface Segregation
        DIPChecker(),  # Dependency Inversion
    ]
    print(f"  ✅ Created {len(checkers)} principle checkers")
    
    # 2. Create analyzer with checkers (Dependency Injection)
    analyzer = ASTAnalyzer(checkers)
    print("  ✅ Created ASTAnalyzer with checkers")
    
    # 3. Create formatter
    formatter = TextFormatter()
    print("  ✅ Created TextFormatter")
    
    # 4. Create use cases with their dependencies (DI)
    analyze_file_uc = AnalyzeFileUseCase(analyzer)
    analyze_directory_uc = AnalyzeDirectoryUseCase(analyzer)
    generate_report_uc = GenerateReportUseCase(formatter)
    suggest_refactoring_uc = SuggestRefactoringUseCase()
    print("  ✅ Created 4 use cases")
    
    print("\n✅ Architecture assembled successfully!")
    print("   Dependencies flow: Presentation → Application → Domain")
    print("   Infrastructure implements Domain interfaces")
    
    # ========================================
    # DEMO 1: Analyze Single File
    # ========================================
    print("\n" + "=" * 70)
    print("DEMO 1: Analyze Single File")
    print("=" * 70)
    
    test_file = Path(__file__).parent / "solid-server" / "src" / "main.py"
    print(f"\nAnalyzing: {test_file.name}")
    
    try:
        report = analyze_file_uc.execute(test_file)
        output = formatter.format_file_report(report)
        print(output)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # ========================================
    # DEMO 2: Analyze Directory
    # ========================================
    print("\n" + "=" * 70)
    print("DEMO 2: Analyze Directory")
    print("=" * 70)
    
    src_dir = Path(__file__).parent / "solid-server" / "src"
    print(f"\nAnalyzing directory: {src_dir}")
    
    try:
        filters = DirectoryFilters(
            max_files=10,
            exclude_patterns=["__pycache__", ".git", "test_"]
        )
        
        reports = analyze_directory_uc.execute(src_dir, filters)
        print(f"\n✅ Analyzed {len(reports)} files")
        
        # Generate comprehensive report
        report_options = ReportOptions(
            include_suggestions=True,
            output_format="text"
        )
        output = generate_report_uc.execute(reports, report_options)
        print(output)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # ========================================
    # DEMO 3: Refactoring Suggestions
    # ========================================
    print("\n" + "=" * 70)
    print("DEMO 3: Refactoring Suggestions")
    print("=" * 70)
    
    try:
        refactor_options = RefactoringOptions(
            max_suggestions=5,
            priority_filter="all"
        )
        
        suggestions = suggest_refactoring_uc.execute(
            reports,
            refactor_options
        )
        output = formatter.format_suggestions(suggestions)
        print(output)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # ========================================
    # ARCHITECTURE BENEFITS
    # ========================================
    print("\n" + "=" * 70)
    print("ARCHITECTURE BENEFITS")
    print("=" * 70)
    print("""
✅ Single Responsibility Principle
   - Each class has one reason to change
   - AnalyzeFileUseCase: only coordinates file analysis
   - SRPChecker: only checks SRP violations
   - TextFormatter: only formats to text

✅ Open-Closed Principle
   - New checkers can be added without modifying ASTAnalyzer
   - New formatters can be added without modifying use cases
   - System is open for extension, closed for modification

✅ Liskov Substitution Principle
   - All IPrincipleChecker implementations are substitutable
   - All IFormatter implementations are substitutable
   - Interfaces define clear contracts

✅ Interface Segregation Principle
   - IAnalyzer: focused interface for file analysis
   - IPrincipleChecker: focused interface for principle checking
   - IFormatter: focused interface for formatting

✅ Dependency Inversion Principle
   - Use cases depend on abstractions (interfaces)
   - High-level policies don't depend on low-level details
   - Dependencies point inward toward domain
    """)
    
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print("\nThe SOLID server now practices what it preaches! 🎉")


if __name__ == "__main__":
    asyncio.run(main())
