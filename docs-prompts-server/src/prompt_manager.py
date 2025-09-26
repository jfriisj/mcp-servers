"""
Prompt management for the Documentation and Prompts MCP Server
"""
import logging
from typing import Dict, Any, List, Optional

from database import DatabaseManager

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages prompt operations"""

    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        self.db_manager = db_manager
        self.config = config
        self._ensure_default_prompts()

    def _ensure_default_prompts(self):
        """Ensure default prompts are loaded"""
        # Check if we have any prompts
        all_prompts = self.db_manager.get_all_prompts()
        if not all_prompts:
            self._create_default_prompts()

    def _create_default_prompts(self):
        """Create default prompts if they don't exist"""
        default_prompts = {
            "code_review": {
                "id": "code_review",
                "name": "Comprehensive Code Review",
                "description": "Review code for quality, security, and best practices",
                "category": "code-quality",
                "template": """Review the following code against the project's documented standards:

                Architecture Guidelines: {architecture_info}
                Coding Standards: {coding_standards}
                Security Requirements: {security_requirements}

                Code to Review:
                {code_content}

                Please analyze for:
                1. Adherence to documented architecture patterns
                2. Code quality and maintainability
                3. Security vulnerabilities
                4. Performance considerations
                5. Documentation completeness
                6. Test coverage adequacy

                Provide specific recommendations for improvements.""",
                "variables": ["architecture_info", "coding_standards", "security_requirements", "code_content"],
                "tags": ["review", "quality", "security", "best-practices"]
            },

            "api_documentation": {
                "id": "api_documentation",
                "name": "API Documentation Generator",
                "description": "Generate comprehensive API documentation",
                "category": "documentation",
                "template": """Generate API documentation based on the following:

                Existing API Patterns: {existing_api_patterns}
                Architecture Style: {architecture_style}
                Authentication Method: {auth_method}

                Code/Endpoints to Document:
                {api_code}

                Please include:
                - Clear endpoint descriptions
                - Request/response schemas with examples
                - Error handling and status codes
                - Authentication requirements
                - Rate limiting information
                - Usage examples in multiple languages
                - Integration guidelines""",
                "variables": ["existing_api_patterns", "architecture_style", "auth_method", "api_code"],
                "tags": ["api", "documentation", "openapi", "endpoints"]
            },

            "architecture_review": {
                "id": "architecture_review",
                "name": "Architecture Compliance Check",
                "description": "Validate implementation against architecture docs",
                "category": "architecture",
                "template": """Validate the following implementation against documented architecture:

                Architecture Documentation: {architecture_docs}
                Design Patterns: {design_patterns}
                Integration Guidelines: {integration_guidelines}
                Scalability Requirements: {scalability_requirements}

                Implementation to Review:
                {implementation_code}

                Please verify:
                1. Compliance with documented patterns
                2. Proper separation of concerns
                3. Integration point correctness
                4. Scalability and performance considerations
                5. Error handling strategy
                6. Monitoring and observability
                7. Security architecture adherence""",
                "variables": ["architecture_docs", "design_patterns", "integration_guidelines",
                             "scalability_requirements", "implementation_code"],
                "tags": ["architecture", "validation", "patterns", "scalability"]
            },

            "security_analysis": {
                "id": "security_analysis",
                "name": "Security Vulnerability Assessment",
                "description": "Comprehensive security analysis of code",
                "category": "security",
                "template": """Perform a security analysis based on documented security requirements:

                Security Guidelines: {security_guidelines}
                Threat Model: {threat_model}
                Compliance Requirements: {compliance_requirements}

                Code to Analyze:
                {code_content}

                Analyze for:
                1. Input validation and sanitization
                2. Authentication and authorization
                3. Data encryption and protection
                4. SQL injection vulnerabilities
                5. XSS and CSRF protection
                6. Secure communication protocols
                7. Logging and monitoring for security events
                8. Compliance with documented security standards

                Provide risk assessment and mitigation strategies.""",
                "variables": ["security_guidelines", "threat_model", "compliance_requirements", "code_content"],
                "tags": ["security", "vulnerability", "compliance", "risk-assessment"]
            },

            "test_generation": {
                "id": "test_generation",
                "name": "Test Strategy and Generation",
                "description": "Generate comprehensive test strategies and test code",
                "category": "testing",
                "template": """Generate test strategy and test code based on:

                Testing Guidelines: {testing_guidelines}
                Code Coverage Requirements: {coverage_requirements}
                Testing Framework: {testing_framework}

                Code to Test:
                {code_content}

                Please provide:
                1. Test strategy and approach
                2. Unit test cases with assertions
                3. Integration test scenarios
                4. Edge cases and error conditions
                5. Performance test considerations
                6. Mock and fixture requirements
                7. Test data setup and teardown
                8. Coverage goals and metrics""",
                "variables": ["testing_guidelines", "coverage_requirements", "testing_framework", "code_content"],
                "tags": ["testing", "unit-tests", "coverage", "test-strategy"]
            },

            "refactoring_analysis": {
                "id": "refactoring_analysis",
                "name": "Code Refactoring Recommendations",
                "description": "Analyze code for refactoring opportunities",
                "category": "refactoring",
                "template": """Analyze the following code for refactoring opportunities:

                Code Quality Guidelines: {quality_guidelines}
                Design Patterns: {design_patterns}
                Performance Requirements: {performance_requirements}

                Code to Refactor:
                {code_content}

                Please identify:
                1. Code smells and anti-patterns
                2. Duplicate code elimination opportunities
                3. Method and class extraction possibilities
                4. Performance optimization areas
                5. Design pattern application opportunities
                6. Dependency injection improvements
                7. Error handling enhancements
                8. Documentation and naming improvements

                Provide specific refactoring steps and expected benefits.""",
                "variables": ["quality_guidelines", "design_patterns", "performance_requirements", "code_content"],
                "tags": ["refactoring", "optimization", "code-quality", "patterns"]
            }
        }

        # Store default prompts in database
        for prompt_data in default_prompts.values():
            self.db_manager.store_prompt(prompt_data)

    def search_prompts(self, query: str, category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search prompts by keyword or category"""
        return self.db_manager.search_prompts(query, category, limit)

    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific prompt by ID"""
        return self.db_manager.get_prompt(prompt_id)

    def suggest_prompts(self, context: Optional[str] = None) -> List[Dict[str, Any]]:
        """Suggest prompts based on context"""
        # Simple implementation - can be enhanced with ML
        suggestions = []

        if context:
            # Analyze context for keywords
            context_lower = context.lower()

            # Map keywords to categories
            keyword_categories = {
                "review": ["code-quality"],
                "test": ["testing"],
                "api": ["api", "documentation"],
                "security": ["security"],
                "refactor": ["refactoring"],
                "architecture": ["architecture"],
                "document": ["documentation"]
            }

            relevant_categories = set()
            for keyword, categories in keyword_categories.items():
                if keyword in context_lower:
                    relevant_categories.update(categories)

            if relevant_categories:
                for category in relevant_categories:
                    category_prompts = self.get_prompts_by_category(category, limit=2)
                    suggestions.extend(category_prompts)

        # If no context-specific suggestions, return popular prompts
        if not suggestions:
            suggestions = self.db_manager.get_popular_prompts(limit=5)

        return suggestions

    def get_prompts_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get prompts by category"""
        return self.db_manager.get_prompts_by_category(category, limit)

    def create_custom_prompt(self, prompt_data: Dict[str, Any]) -> str:
        """Create a new custom prompt"""
        prompt_id = prompt_data.get("id", f"custom_{int(__import__('time').time())}")
        self.db_manager.store_prompt(prompt_data)
        return prompt_id

    def record_prompt_usage(self, prompt_id: str, context: str = "", effectiveness: int = 5):
        """Record prompt usage for analytics"""
        self.db_manager.record_prompt_usage(prompt_id, context, effectiveness)

    def get_usage_stats(self) -> List[Dict[str, Any]]:
        """Get usage statistics for all prompts"""
        return self.db_manager.get_usage_stats()