"""
Topic-based chunking strategy for research papers.

Uses semantic analysis and keyword clustering to create topically coherent chunks
that group related concepts and research themes together. Optimized for thematic
analysis in systematic literature reviews.
"""

import re
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

from ..domain.models import AcademicChunk, ResearchPaper
from .base_academic_strategy import BaseAcademicStrategy


class TopicBasedStrategy(BaseAcademicStrategy):
    """
    Chunks research papers based on topic coherence and semantic clustering.

    This strategy creates chunks that group semantically related content together,
    making them ideal for:
    - Thematic analysis across papers
    - Concept clustering in systematic reviews
    - Research theme identification
    - Content-based similarity analysis

    Features:
    - Keyword-based topic detection
    - Semantic coherence scoring
    - Academic domain terminology recognition
    - Research theme clustering
    - Contextual topic boundaries
    """

    # Academic and research-specific keyword categories
    RESEARCH_KEYWORDS = {
        'methodology': [
            'method', 'methodology', 'approach', 'technique', 'procedure', 'protocol',
            'design', 'framework', 'model', 'algorithm', 'analysis', 'evaluation',
            'assessment', 'measurement', 'survey', 'experiment', 'study', 'research',
            'investigation', 'examination', 'exploration', 'observation'
        ],
        'data_analysis': [
            'data', 'dataset', 'statistics', 'statistical', 'analysis', 'regression',
            'correlation', 'significant', 'p-value', 'confidence', 'variance',
            'distribution', 'sample', 'population', 'variable', 'factor', 'measure',
            'metric', 'indicator', 'parameter', 'coefficient', 'test', 'hypothesis'
        ],
        'results_findings': [
            'result', 'finding', 'outcome', 'effect', 'impact', 'influence',
            'relationship', 'association', 'difference', 'comparison', 'trend',
            'pattern', 'evidence', 'support', 'demonstrate', 'show', 'indicate',
            'suggest', 'reveal', 'discover', 'identify', 'observe', 'detect'
        ],
        'theory_concept': [
            'theory', 'concept', 'principle', 'hypothesis', 'assumption', 'premise',
            'proposition', 'notion', 'idea', 'framework', 'paradigm', 'model',
            'construct', 'definition', 'characteristic', 'property', 'attribute',
            'feature', 'aspect', 'dimension', 'component', 'element', 'factor'
        ],
        'quality_validity': [
            'quality', 'validity', 'reliability', 'accuracy', 'precision', 'bias',
            'limitation', 'strength', 'weakness', 'advantage', 'disadvantage',
            'benefit', 'risk', 'challenge', 'issue', 'problem', 'concern',
            'consideration', 'implication', 'consequence', 'recommendation'
        ]
    }

    # Minimum and maximum chunk parameters
    MIN_CHUNK_WORDS = 100
    MAX_CHUNK_WORDS = 600
    MIN_TOPIC_COHERENCE = 0.3
    SEMANTIC_WINDOW_SIZE = 50  # Words to consider for topic coherence

    def can_chunk(self, paper: ResearchPaper, content: str) -> bool:
        """
        Check if paper has sufficient topical diversity for topic-based chunking.

        Args:
            paper: Research paper metadata
            content: Paper text content

        Returns:
            True if paper has diverse topics suitable for thematic chunking
        """
        if not content:
            return False

        # Analyze keyword distribution across different topic categories
        keywords_by_category = self._extract_keywords_by_category(content)
        
        # Require presence in at least 3 different topic categories
        active_categories = sum(1 for keywords in keywords_by_category.values() if keywords)
        
        if active_categories < 3:
            return False

        # Check for topic distribution throughout the document
        # Split document into quarters and check each has some topical content
        content_quarters = self._split_into_quarters(content)
        quarters_with_topics = 0
        
        for quarter in content_quarters:
            quarter_keywords = self._extract_all_keywords(quarter)
            if len(quarter_keywords) >= 10:  # At least 10 relevant keywords
                quarters_with_topics += 1
        
        # Require topics distributed across at least 3/4 of document
        return quarters_with_topics >= 3

    def chunk(self, paper: ResearchPaper, content: str) -> List[AcademicChunk]:
        """
        Create topic-based chunks from the research paper.

        Args:
            paper: Research paper metadata
            content: Paper text content

        Returns:
            List of topically coherent academic chunks

        Raises:
            ValueError: If paper cannot be chunked by topic analysis
        """
        if not content:
            raise ValueError("Paper has no content")

        # Extract topics and their positions throughout the document
        topic_segments = self._identify_topic_segments(content)
        
        if not topic_segments:
            raise ValueError("No coherent topic segments found")

        # Create chunks based on topic boundaries
        chunks = self._create_topic_chunks(content, topic_segments)
        
        if not chunks:
            raise ValueError("Could not create topic-based chunks")

        # Process and enrich chunks
        processed_chunks = []
        for i, chunk_data in enumerate(chunks):
            content_text, start_pos, topics, coherence_score = chunk_data
            
            # Calculate position ratio
            position_ratio = start_pos / len(content) if len(content) > 0 else 0.0
            
            # Extract title from topic or content
            title = self._extract_topic_title(content_text, topics)
            
            # Detect section type
            section_type = self._detect_section_type(title, content_text, position_ratio)
            
            # Count citations, figures, tables
            citation_count = self._count_citations(content_text)
            figure_count, table_count = self._count_figures_tables(content_text)
            
            # Extract research elements and semantic tags
            research_elements = self._extract_research_elements(content_text, section_type)
            semantic_tags = self._generate_semantic_tags(content_text, section_type)
            
            # Add topic-specific semantic tags
            semantic_tags.extend(self._extract_topic_semantic_tags(topics))

            # Create academic chunk
            chunk = AcademicChunk(
                paper_id=paper.id or 0,
                chunk_index=i,
                content=content_text.strip(),
                section_type=section_type,
                title=self._clean_title(title),
                word_count=self._calculate_word_count(content_text),
                citation_count=citation_count,
                figure_count=figure_count,
                table_count=table_count,
                research_elements=research_elements,
                semantic_tags=list(set(semantic_tags)),  # Remove duplicates
                metadata={
                    "strategy": "topic_based",
                    "start_position": start_pos,
                    "position_ratio": position_ratio,
                    "primary_topics": topics[:3],  # Top 3 topics
                    "topic_coherence_score": coherence_score,
                    "keyword_density": len(self._extract_all_keywords(content_text)) / max(1, self._calculate_word_count(content_text)),
                    "dominant_category": self._get_dominant_topic_category(topics),
                    "topic_diversity": len(set(topic.split('_')[0] for topic in topics if '_' in topic)),
                    "semantic_richness": len(set(semantic_tags))
                }
            )

            # Calculate confidence score (enhanced with topic coherence)
            base_confidence = self._calculate_confidence_score(chunk)
            topic_bonus = min(0.2, coherence_score * 0.3)  # Up to 0.2 bonus for high coherence
            chunk.confidence_score = min(1.0, base_confidence + topic_bonus)
            
            processed_chunks.append(chunk)

        return processed_chunks

    def _extract_keywords_by_category(self, content: str) -> Dict[str, List[str]]:
        """Extract keywords organized by research category."""
        content_lower = content.lower()
        keywords_by_category = {}
        
        for category, keyword_list in self.RESEARCH_KEYWORDS.items():
            found_keywords = []
            for keyword in keyword_list:
                if keyword in content_lower:
                    # Count frequency
                    count = len(re.findall(rf'\b{re.escape(keyword)}\b', content_lower))
                    found_keywords.extend([keyword] * count)
            keywords_by_category[category] = found_keywords
        
        return keywords_by_category

    def _extract_all_keywords(self, content: str) -> List[str]:
        """Extract all research keywords from content."""
        all_keywords = []
        keywords_by_category = self._extract_keywords_by_category(content)
        
        for keywords in keywords_by_category.values():
            all_keywords.extend(keywords)
        
        return all_keywords

    def _split_into_quarters(self, content: str) -> List[str]:
        """Split content into quarters for distribution analysis."""
        content_length = len(content)
        quarter_size = content_length // 4
        
        quarters = []
        for i in range(4):
            start = i * quarter_size
            end = start + quarter_size if i < 3 else content_length
            quarters.append(content[start:end])
        
        return quarters

    def _identify_topic_segments(self, content: str) -> List[Tuple[int, int, List[str], float]]:
        """
        Identify coherent topic segments in the content.

        Returns:
            List of (start_pos, end_pos, topics, coherence_score) tuples
        """
        # Split content into sentences for analysis
        sentences = re.split(r'[.!?]+\s+', content)
        if not sentences:
            return []

        segments = []
        current_start = 0
        current_sentences = []
        current_topics = []
        
        for i, sentence in enumerate(sentences):
            sentence_keywords = self._extract_all_keywords(sentence)
            sentence_topics = self._classify_sentence_topics(sentence)
            
            # Calculate position in original content
            sentence_start = content.find(sentence, current_start)
            if sentence_start == -1:
                sentence_start = current_start
            
            # Check if we should start a new segment
            if (self._should_start_new_topic_segment(current_sentences, sentence, current_topics, sentence_topics) or
                len(current_sentences) >= 20):  # Max sentences per segment
                
                # Finalize current segment
                if current_sentences and len(current_sentences) >= 3:
                    segment_start = content.find(current_sentences[0], current_start)
                    segment_end = sentence_start
                    segment_content = content[segment_start:segment_end]
                    
                    if self._calculate_word_count(segment_content) >= self.MIN_CHUNK_WORDS:
                        coherence = self._calculate_topic_coherence(current_sentences)
                        if coherence >= self.MIN_TOPIC_COHERENCE:
                            segments.append((segment_start, segment_end, current_topics.copy(), coherence))
                
                # Start new segment
                current_sentences = [sentence]
                current_topics = sentence_topics.copy()
                current_start = sentence_start
            else:
                # Add to current segment
                current_sentences.append(sentence)
                current_topics.extend(sentence_topics)
            
            # Update position
            current_start = sentence_start + len(sentence)

        # Handle final segment
        if current_sentences and len(current_sentences) >= 3:
            segment_start = content.find(current_sentences[0], current_start - sum(len(s) for s in current_sentences))
            segment_content = content[segment_start:]
            
            if self._calculate_word_count(segment_content) >= self.MIN_CHUNK_WORDS:
                coherence = self._calculate_topic_coherence(current_sentences)
                if coherence >= self.MIN_TOPIC_COHERENCE:
                    segments.append((segment_start, len(content), current_topics, coherence))

        return segments

    def _classify_sentence_topics(self, sentence: str) -> List[str]:
        """Classify the main topics present in a sentence."""
        topics = []
        keywords_by_category = self._extract_keywords_by_category(sentence)
        
        for category, keywords in keywords_by_category.items():
            if keywords:
                # Weight by frequency
                topic_strength = len(keywords) / max(1, len(sentence.split()))
                topics.extend([category] * max(1, int(topic_strength * 10)))
        
        return topics

    def _should_start_new_topic_segment(self, current_sentences: List[str], new_sentence: str, 
                                      current_topics: List[str], new_topics: List[str]) -> bool:
        """Determine if a new topic segment should be started."""
        if not current_sentences:
            return False
        
        # Calculate topic overlap
        current_topic_set = set(current_topics)
        new_topic_set = set(new_topics)
        
        if not current_topic_set or not new_topic_set:
            return len(current_sentences) > 10  # Segment by length if no clear topics
        
        overlap = len(current_topic_set & new_topic_set) / len(current_topic_set | new_topic_set)
        
        # Start new segment if topic overlap is low
        return overlap < 0.4

    def _calculate_topic_coherence(self, sentences: List[str]) -> float:
        """Calculate topic coherence score for a group of sentences."""
        if not sentences:
            return 0.0
        
        # Extract keywords from all sentences
        all_keywords = []
        for sentence in sentences:
            all_keywords.extend(self._extract_all_keywords(sentence))
        
        if not all_keywords:
            return 0.0
        
        # Calculate keyword frequency distribution
        keyword_counts = Counter(all_keywords)
        total_keywords = len(all_keywords)
        
        # Calculate coherence as normalized entropy
        entropy = 0.0
        for count in keyword_counts.values():
            prob = count / total_keywords
            if prob > 0:
                entropy -= prob * (prob ** 0.5)  # Modified entropy for coherence
        
        # Normalize to 0-1 range
        max_entropy = len(keyword_counts) ** 0.5 if keyword_counts else 1
        coherence = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 0.0
        
        return max(0.0, min(1.0, coherence))

    def _create_topic_chunks(self, content: str, segments: List[Tuple[int, int, List[str], float]]) -> List[Tuple[str, int, List[str], float]]:
        """Create chunks from topic segments."""
        chunks = []
        
        for start_pos, end_pos, topics, coherence in segments:
            chunk_content = content[start_pos:end_pos]
            
            # Ensure chunk is within size limits
            word_count = self._calculate_word_count(chunk_content)
            
            if word_count < self.MIN_CHUNK_WORDS:
                continue  # Skip too-small chunks
            
            if word_count > self.MAX_CHUNK_WORDS:
                # Split large chunks while preserving topic coherence
                sub_chunks = self._split_large_chunk(chunk_content, start_pos, topics, coherence)
                chunks.extend(sub_chunks)
            else:
                # Get most common topics
                topic_counts = Counter(topics)
                dominant_topics = [topic for topic, count in topic_counts.most_common(5)]
                chunks.append((chunk_content, start_pos, dominant_topics, coherence))
        
        return chunks

    def _split_large_chunk(self, content: str, start_pos: int, topics: List[str], coherence: float) -> List[Tuple[str, int, List[str], float]]:
        """Split a large chunk while preserving topic coherence."""
        sentences = re.split(r'[.!?]+\s+', content)
        if len(sentences) < 4:
            return [(content, start_pos, topics, coherence)]  # Can't split further
        
        # Split roughly in half
        mid_point = len(sentences) // 2
        
        first_half = '. '.join(sentences[:mid_point]) + '.'
        second_half = '. '.join(sentences[mid_point:]) + '.'
        
        # Calculate positions
        second_start = start_pos + len(first_half)
        
        # Recalculate topics and coherence for each half
        first_topics = self._classify_sentence_topics(first_half)
        second_topics = self._classify_sentence_topics(second_half)
        
        first_coherence = self._calculate_topic_coherence(sentences[:mid_point])
        second_coherence = self._calculate_topic_coherence(sentences[mid_point:])
        
        chunks = []
        if self._calculate_word_count(first_half) >= self.MIN_CHUNK_WORDS:
            chunks.append((first_half, start_pos, first_topics, first_coherence))
        
        if self._calculate_word_count(second_half) >= self.MIN_CHUNK_WORDS:
            chunks.append((second_half, second_start, second_topics, second_coherence))
        
        return chunks

    def _extract_topic_title(self, content: str, topics: List[str]) -> str:
        """Extract or generate a title based on content and topics."""
        # Try to find section headers in content
        lines = content.split('\n')
        for line in lines[:3]:
            line = line.strip()
            if (line and len(line.split()) <= 8 and 
                any(char.isupper() for char in line) and
                not line.endswith('.')):
                return line
        
        # Generate title from dominant topics
        if topics:
            topic_counts = Counter(topics)
            dominant_topic = topic_counts.most_common(1)[0][0]
            
            # Convert topic category to readable title
            topic_titles = {
                'methodology': 'Methodology and Approach',
                'data_analysis': 'Data Analysis and Statistics',
                'results_findings': 'Results and Findings',
                'theory_concept': 'Theory and Concepts',
                'quality_validity': 'Quality and Validity'
            }
            
            if dominant_topic in topic_titles:
                return topic_titles[dominant_topic]
        
        # Fallback: use first sentence
        sentences = re.split(r'[.!?]+\s+', content)
        first_sentence = sentences[0].strip() if sentences else content[:100]
        return first_sentence[:100] + "..." if len(first_sentence) > 100 else first_sentence

    def _get_dominant_topic_category(self, topics: List[str]) -> str:
        """Get the dominant topic category."""
        if not topics:
            return "general"
        
        topic_counts = Counter(topics)
        return topic_counts.most_common(1)[0][0]

    def _extract_topic_semantic_tags(self, topics: List[str]) -> List[str]:
        """Extract semantic tags based on topic analysis."""
        tags = []
        
        topic_counts = Counter(topics)
        
        # Add tags based on topic diversity
        if len(set(topics)) > 3:
            tags.append("multi_topic")
        
        # Add tags based on dominant categories
        for topic, count in topic_counts.most_common(2):
            if topic == 'methodology':
                tags.append("methods_focus")
            elif topic == 'data_analysis':
                tags.append("analysis_heavy")
            elif topic == 'results_findings':
                tags.append("results_section")
            elif topic == 'theory_concept':
                tags.append("theoretical")
            elif topic == 'quality_validity':
                tags.append("quality_assessment")
        
        return tags

    def get_strategy_name(self) -> str:
        """Get the name of this chunking strategy."""
        return "topic_based"