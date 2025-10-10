"""
Intelligent Search Suggestion Engine for Study Buddy GUI Application.

Provides intelligent search suggestions, autocomplete functionality, and
query expansion based on document content analysis and user search patterns.

Part of Task 14, Phase 1: Advanced Search Enhancement
Architecture: Clean Architecture Layer 2 (Business Logic)
SOLID Compliance: Single Responsibility, Dependency Inversion via interfaces
"""

import asyncio
import re
from typing import Dict, List, Set, Optional, Tuple, Any, Callable
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class SearchSuggestion:
    """Represents a single search suggestion with metadata."""
    text: str
    suggestion_type: str  # "completion", "related", "recent", "popular"
    relevance_score: float
    frequency: int = 0
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.last_used is None:
            self.last_used = datetime.now()


@dataclass
class QueryAnalysis:
    """Analysis results for a search query."""
    tokens: List[str]
    partial_token: str
    query_type: str  # "phrase", "boolean", "wildcard", "fuzzy"
    suggestions: List[SearchSuggestion]
    completions: List[str]


class SuggestionStrategy(ABC):
    """Abstract strategy for generating different types of suggestions."""
    
    @abstractmethod
    async def generate_suggestions(self, query: str, context: Dict[str, Any]) -> List[SearchSuggestion]:
        """Generate suggestions based on query and context."""
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """Get strategy priority (higher = more important)."""
        pass


class CompletionStrategy(SuggestionStrategy):
    """Strategy for auto-completing partial words."""
    
    def __init__(self, vocabulary: Set[str]):
        self.vocabulary = vocabulary
        self.trie = self._build_trie()
    
    def _build_trie(self) -> Dict:
        """Build trie structure for efficient prefix matching."""
        trie = {}
        for word in self.vocabulary:
            current = trie
            for char in word.lower():
                if char not in current:
                    current[char] = {}
                current = current[char]
            current['$'] = word  # Mark end of word
        return trie
    
    async def generate_suggestions(self, query: str, context: Dict[str, Any]) -> List[SearchSuggestion]:
        """Generate auto-completion suggestions."""
        suggestions = []
        
        if not query.strip():
            return suggestions
        
        # Get last partial word for completion
        words = query.strip().split()
        if not words:
            return suggestions
        
        last_word = words[-1].lower()
        if len(last_word) < 2:  # Only suggest for 2+ characters
            return suggestions
        
        # Find completions using trie
        completions = self._find_completions(last_word, max_suggestions=10)
        
        for completion in completions:
            # Calculate relevance based on length similarity and position
            relevance = self._calculate_completion_relevance(last_word, completion)
            
            suggestions.append(SearchSuggestion(
                text=completion,
                suggestion_type="completion",
                relevance_score=relevance,
                metadata={"partial_word": last_word}
            ))
        
        return suggestions
    
    def _find_completions(self, prefix: str, max_suggestions: int = 10) -> List[str]:
        """Find word completions using trie traversal."""
        completions = []
        current = self.trie
        
        # Navigate to prefix position in trie
        for char in prefix:
            if char not in current:
                return completions  # No completions found
            current = current[char]
        
        # Collect all completions from this position
        self._collect_words(current, prefix, completions, max_suggestions)
        return completions[:max_suggestions]
    
    def _collect_words(self, node: Dict, prefix: str, results: List[str], max_results: int) -> None:
        """Recursively collect words from trie node."""
        if len(results) >= max_results:
            return
        
        if '$' in node:
            results.append(node['$'])
        
        for char, child_node in node.items():
            if char != '$' and len(results) < max_results:
                self._collect_words(child_node, prefix + char, results, max_results)
    
    def _calculate_completion_relevance(self, partial: str, completion: str) -> float:
        """Calculate relevance score for completion."""
        if not partial or not completion:
            return 0.0
        
        # Base score: how much of the word is already typed
        base_score = len(partial) / len(completion)
        
        # Bonus for exact prefix match
        if completion.lower().startswith(partial.lower()):
            base_score += 0.3
        
        # Penalty for very long completions
        if len(completion) > len(partial) * 3:
            base_score *= 0.8
        
        return min(base_score, 1.0)
    
    def get_priority(self) -> int:
        return 90  # High priority for completions
    
    def update_vocabulary(self, new_words: Set[str]) -> None:
        """Update vocabulary and rebuild trie."""
        self.vocabulary.update(new_words)
        self.trie = self._build_trie()
        logger.info("Updated vocabulary with %d new words", len(new_words))


class RelatedTermsStrategy(SuggestionStrategy):
    """Strategy for suggesting semantically related terms."""
    
    def __init__(self):
        self.term_associations: Dict[str, Counter] = defaultdict(Counter)
        self.document_terms: Dict[int, Set[str]] = {}
    
    async def generate_suggestions(self, query: str, context: Dict[str, Any]) -> List[SearchSuggestion]:
        """Generate related term suggestions."""
        suggestions = []
        
        query_terms = set(self._extract_terms(query))
        if not query_terms:
            return suggestions
        
        # Find terms that frequently appear with query terms
        related_terms = Counter()
        
        for term in query_terms:
            if term in self.term_associations:
                for related_term, count in self.term_associations[term].items():
                    if related_term not in query_terms:  # Don't suggest terms already in query
                        related_terms[related_term] += count
        
        # Create suggestions from most frequent related terms
        for term, frequency in related_terms.most_common(8):
            relevance = min(frequency / 100.0, 1.0)  # Normalize frequency
            
            suggestions.append(SearchSuggestion(
                text=f"{query} {term}",
                suggestion_type="related",
                relevance_score=relevance,
                frequency=frequency,
                metadata={"related_term": term}
            ))
        
        return suggestions
    
    def _extract_terms(self, text: str) -> List[str]:
        """Extract meaningful terms from text."""
        # Simple tokenization - could be enhanced with NLP
        words = re.findall(r'\b\w{3,}\b', text.lower())  # Words with 3+ characters
        return [word for word in words if not self._is_stopword(word)]
    
    def _is_stopword(self, word: str) -> bool:
        """Check if word is a common stopword."""
        stopwords = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'throughout', 'within'
        }
        return word in stopwords
    
    def add_document_content(self, document_id: int, content: str) -> None:
        """Add document content to build term associations."""
        terms = set(self._extract_terms(content))
        self.document_terms[document_id] = terms
        
        # Build co-occurrence associations
        for term1 in terms:
            for term2 in terms:
                if term1 != term2:
                    self.term_associations[term1][term2] += 1
        
        logger.debug("Added %d terms from document %d", len(terms), document_id)
    
    def get_priority(self) -> int:
        return 70  # Medium-high priority for related terms


class PopularSearchStrategy(SuggestionStrategy):
    """Strategy for suggesting popular/frequent searches."""
    
    def __init__(self):
        self.search_history: Counter = Counter()
        self.recent_searches: List[Tuple[str, datetime]] = []
        self.max_recent = 100
    
    async def generate_suggestions(self, query: str, context: Dict[str, Any]) -> List[SearchSuggestion]:
        """Generate suggestions based on popular searches."""
        suggestions = []
        
        query_lower = query.lower().strip()
        
        # Find searches that start with or contain the query
        matching_searches = []
        
        for search, count in self.search_history.items():
            search_lower = search.lower()
            
            if query_lower and query_lower in search_lower:
                # Calculate relevance based on match type and frequency
                if search_lower.startswith(query_lower):
                    relevance = 0.8 + (count / max(self.search_history.values() or [1]))
                else:
                    relevance = 0.6 + (count / max(self.search_history.values() or [1]))
                
                matching_searches.append((search, count, relevance))
        
        # Sort by relevance and take top results
        matching_searches.sort(key=lambda x: x[2], reverse=True)
        
        for search, frequency, relevance in matching_searches[:6]:
            if search.lower() != query_lower:  # Don't suggest exact match
                suggestions.append(SearchSuggestion(
                    text=search,
                    suggestion_type="popular",
                    relevance_score=min(relevance, 1.0),
                    frequency=frequency,
                    metadata={"match_type": "popular"}
                ))
        
        return suggestions
    
    def record_search(self, query: str) -> None:
        """Record a search query for popularity tracking."""
        if not query or len(query.strip()) < 2:
            return
        
        normalized_query = query.strip()
        self.search_history[normalized_query] += 1
        
        # Add to recent searches
        now = datetime.now()
        self.recent_searches.append((normalized_query, now))
        
        # Trim recent searches to max size
        if len(self.recent_searches) > self.max_recent:
            self.recent_searches = self.recent_searches[-self.max_recent:]
        
        logger.debug("Recorded search: '%s' (total: %d)", normalized_query, self.search_history[normalized_query])
    
    def get_recent_searches(self, limit: int = 10) -> List[SearchSuggestion]:
        """Get recent search queries as suggestions."""
        suggestions = []
        
        # Get unique recent searches (most recent first)
        seen = set()
        recent_unique = []
        
        for query, timestamp in reversed(self.recent_searches):
            if query not in seen:
                seen.add(query)
                recent_unique.append((query, timestamp))
                if len(recent_unique) >= limit:
                    break
        
        # Convert to suggestions
        for i, (query, timestamp) in enumerate(recent_unique):
            # More recent searches get higher relevance
            relevance = 1.0 - (i * 0.1)
            
            suggestions.append(SearchSuggestion(
                text=query,
                suggestion_type="recent",
                relevance_score=max(relevance, 0.1),
                last_used=timestamp,
                metadata={"rank": i + 1}
            ))
        
        return suggestions
    
    def get_priority(self) -> int:
        return 60  # Medium priority for popular searches


class SearchSuggestionEngine:
    """
    Intelligent search suggestion engine with multiple strategies.
    
    Responsibilities:
    - Generate intelligent search suggestions and auto-completions
    - Maintain search history and popularity tracking  
    - Provide contextual suggestions based on document content
    - Support multiple suggestion strategies with prioritization
    
    Architecture:
    - Uses Strategy pattern for different suggestion types
    - Maintains search analytics for intelligent suggestions
    - Integrates with document content for semantic suggestions
    - Follows Single Responsibility and Open/Closed principles
    """
    
    def __init__(self, mcp_client: Optional[Any] = None):
        """
        Initialize suggestion engine.
        
        Args:
            mcp_client: Optional MCP client for advanced features
        """
        self.mcp_client = mcp_client
        self.strategies: List[SuggestionStrategy] = []
        self.vocabulary: Set[str] = set()
        self.analytics_enabled = True
        
        # Initialize default strategies
        self._initialize_strategies()
        
        # Load existing data
        self._load_persistent_data()
        
        logger.info("SearchSuggestionEngine initialized with %d strategies", len(self.strategies))
    
    def _initialize_strategies(self) -> None:
        """Initialize suggestion strategies."""
        # Build initial vocabulary from common terms
        self.vocabulary = self._build_initial_vocabulary()
        
        # Add strategies in priority order
        self.strategies = [
            CompletionStrategy(self.vocabulary),
            RelatedTermsStrategy(),
            PopularSearchStrategy()
        ]
    
    def _build_initial_vocabulary(self) -> Set[str]:
        """Build initial vocabulary from common search terms."""
        common_terms = {
            # Document types
            'document', 'file', 'pdf', 'text', 'markdown', 'chapter', 'section',
            'page', 'paragraph', 'content', 'summary', 'abstract', 'introduction',
            
            # Academic terms
            'research', 'study', 'analysis', 'method', 'result', 'conclusion',
            'hypothesis', 'theory', 'experiment', 'data', 'figure', 'table',
            
            # Technical terms
            'algorithm', 'implementation', 'design', 'architecture', 'pattern',
            'framework', 'library', 'api', 'interface', 'class', 'function',
            
            # Common actions
            'create', 'update', 'delete', 'search', 'find', 'browse', 'view',
            'edit', 'save', 'export', 'import', 'share', 'organize'
        }
        return common_terms
    
    async def get_suggestions(
        self, 
        query: str, 
        max_suggestions: int = 10,
        context: Optional[Dict[str, Any]] = None
    ) -> List[SearchSuggestion]:
        """
        Get intelligent suggestions for search query.
        
        Args:
            query: Current search query (partial or complete)
            max_suggestions: Maximum number of suggestions to return
            context: Optional context information (current document, etc.)
            
        Returns:
            List of search suggestions ordered by relevance
        """
        if context is None:
            context = {}
        
        all_suggestions = []
        
        # Generate suggestions from all strategies
        for strategy in self.strategies:
            try:
                strategy_suggestions = await strategy.generate_suggestions(query, context)
                for suggestion in strategy_suggestions:
                    # Adjust relevance by strategy priority
                    suggestion.relevance_score *= (strategy.get_priority() / 100.0)
                    all_suggestions.append(suggestion)
            except Exception as e:
                logger.error("Error generating suggestions from %s: %s", type(strategy).__name__, e)
        
        # Remove duplicates and sort by relevance
        unique_suggestions = self._deduplicate_suggestions(all_suggestions)
        unique_suggestions.sort(key=lambda s: s.relevance_score, reverse=True)
        
        return unique_suggestions[:max_suggestions]
    
    def _deduplicate_suggestions(self, suggestions: List[SearchSuggestion]) -> List[SearchSuggestion]:
        """Remove duplicate suggestions, keeping the highest scoring ones."""
        seen_texts = set()
        unique_suggestions = []
        
        for suggestion in suggestions:
            if suggestion.text not in seen_texts:
                seen_texts.add(suggestion.text)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions
    
    async def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze search query and provide comprehensive suggestions.
        
        Args:
            query: Search query to analyze
            
        Returns:
            QueryAnalysis with tokens, suggestions, and completions
        """
        # Tokenize query
        tokens = query.strip().split()
        partial_token = tokens[-1] if tokens else ""
        
        # Determine query type
        query_type = self._determine_query_type(query)
        
        # Get suggestions
        suggestions = await self.get_suggestions(query)
        
        # Get completions for partial token
        completions = []
        if len(partial_token) >= 2:
            completion_strategy = next((s for s in self.strategies if isinstance(s, CompletionStrategy)), None)
            if completion_strategy:
                completion_suggestions = await completion_strategy.generate_suggestions(query, {})
                completions = [s.text for s in completion_suggestions]
        
        return QueryAnalysis(
            tokens=tokens,
            partial_token=partial_token,
            query_type=query_type,
            suggestions=suggestions,
            completions=completions
        )
    
    def _determine_query_type(self, query: str) -> str:
        """Determine the type of search query."""
        query = query.strip()
        
        if not query:
            return "empty"
        elif '"' in query:
            return "phrase"
        elif any(op in query.lower() for op in ['and', 'or', 'not', '+', '-']):
            return "boolean"
        elif '*' in query or '?' in query:
            return "wildcard"
        elif '~' in query:
            return "fuzzy"
        else:
            return "simple"
    
    def record_search_interaction(self, query: str, selected_suggestion: Optional[str] = None) -> None:
        """
        Record search interaction for analytics and improvement.
        
        Args:
            query: The search query that was executed
            selected_suggestion: Optional suggestion that was selected
        """
        if not self.analytics_enabled:
            return
        
        # Record with popular search strategy
        popular_strategy = next((s for s in self.strategies if isinstance(s, PopularSearchStrategy)), None)
        if popular_strategy:
            popular_strategy.record_search(query)
        
        # Update vocabulary with query terms
        new_terms = set(re.findall(r'\b\w{3,}\b', query.lower()))
        if new_terms:
            self.vocabulary.update(new_terms)
            
            # Update completion strategy vocabulary
            completion_strategy = next((s for s in self.strategies if isinstance(s, CompletionStrategy)), None)
            if completion_strategy:
                completion_strategy.update_vocabulary(new_terms)
        
        logger.debug("Recorded search interaction: query='%s', suggestion='%s'", query, selected_suggestion)
    
    def add_document_content(self, document_id: int, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add document content to improve suggestions.
        
        Args:
            document_id: Unique document identifier
            content: Document text content
            metadata: Optional document metadata
        """
        # Extract vocabulary from content
        content_terms = set(re.findall(r'\b\w{3,}\b', content.lower()))
        self.vocabulary.update(content_terms)
        
        # Update related terms strategy
        related_strategy = next((s for s in self.strategies if isinstance(s, RelatedTermsStrategy)), None)
        if related_strategy:
            related_strategy.add_document_content(document_id, content)
        
        # Update completion strategy
        completion_strategy = next((s for s in self.strategies if isinstance(s, CompletionStrategy)), None)
        if completion_strategy:
            completion_strategy.update_vocabulary(content_terms)
        
        logger.debug("Added document content: %d terms from document %d", len(content_terms), document_id)
    
    def get_recent_searches(self, limit: int = 10) -> List[SearchSuggestion]:
        """Get recent search queries for quick access."""
        popular_strategy = next((s for s in self.strategies if isinstance(s, PopularSearchStrategy)), None)
        if popular_strategy:
            return popular_strategy.get_recent_searches(limit)
        return []
    
    def add_custom_strategy(self, strategy: SuggestionStrategy) -> None:
        """
        Add custom suggestion strategy.
        
        Args:
            strategy: Custom suggestion strategy implementation
        """
        self.strategies.append(strategy)
        self.strategies.sort(key=lambda s: s.get_priority(), reverse=True)
        logger.info("Added custom suggestion strategy: %s", type(strategy).__name__)
    
    def _load_persistent_data(self) -> None:
        """Load persistent suggestion data from storage."""
        # This would load from file/database in a real implementation
        # For now, just log that we would load data
        logger.debug("Loading persistent suggestion data (placeholder)")
    
    def save_persistent_data(self) -> None:
        """Save suggestion data for persistence."""
        # This would save to file/database in a real implementation
        # For now, just log that we would save data
        logger.debug("Saving persistent suggestion data (placeholder)")
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary for monitoring and optimization."""
        popular_strategy = next((s for s in self.strategies if isinstance(s, PopularSearchStrategy)), None)
        
        summary = {
            "vocabulary_size": len(self.vocabulary),
            "strategies_count": len(self.strategies),
            "analytics_enabled": self.analytics_enabled
        }
        
        if popular_strategy:
            summary.update({
                "total_searches": sum(popular_strategy.search_history.values()),
                "unique_searches": len(popular_strategy.search_history),
                "recent_searches": len(popular_strategy.recent_searches)
            })
        
        return summary