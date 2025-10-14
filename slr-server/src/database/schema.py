"""
Database schema management and initialization for SLR MCP Server.

This module implements Clean Architecture Layer 4 infrastructure for database
schema creation, migration, and management following SOLID principles and FTS5
search setup for academic research entities.
"""

import logging

from .connection import DatabaseConnection


class SchemaManager:
    """
    Database schema management for Systematic Literature Review application.

    This class follows the Single Responsibility Principle (SRP) by handling
    only database schema operations and initialization. It provides:

    - Schema creation and initialization for academic entities
    - FTS5 full-text search index setup for papers and citations
    - Schema version management and migration support
    - Table creation with proper academic research constraints
    - Index optimization for research workflows

    Clean Architecture Layer 4: Infrastructure
    - No dependencies on business logic or application layers
    - Pure infrastructure concern for database schema
    - Can be tested independently with in-memory databases
    """

    # Current schema version for migration tracking
    SCHEMA_VERSION = 1

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize schema manager with database connection.

        Args:
            db_connection: Database connection manager instance
        """
        self.db = db_connection
        self.logger = logging.getLogger(__name__)

    def initialize_schema(self) -> None:
        """
        Initialize complete database schema with all tables and indexes.

        Creates all necessary tables, indexes, and FTS5 search tables
        in the correct order respecting foreign key dependencies.

        Raises:
            sqlite3.Error: If schema creation fails
        """
        try:
            with self.db.transaction() as conn:
                cursor = conn.cursor()

                # Create tables in dependency order
                self._create_papers_table(cursor)
                self._create_authors_table(cursor)
                self._create_paper_authors_table(cursor)
                self._create_journals_table(cursor)
                self._create_citations_table(cursor)
                self._create_chunks_table(cursor)
                self._create_quality_assessments_table(cursor)
                self._create_research_questions_table(cursor)
                self._create_research_hypotheses_table(cursor)
                self._create_evidence_items_table(cursor)
                self._create_synthesis_results_table(cursor)

                # Create FTS5 search indexes
                self._create_search_indexes(cursor)

                # Create additional indexes for performance
                self._create_performance_indexes(cursor)

                # Initialize schema metadata
                self._initialize_metadata(cursor)

                self.logger.info("Database schema initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize schema: {e}")
            raise

    def _create_papers_table(self, cursor) -> None:
        """
        Create papers table with academic metadata and constraints.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                doi TEXT UNIQUE,
                abstract TEXT,
                publication_year INTEGER CHECK (
                    publication_year IS NULL OR 
                    (publication_year >= 1800 AND publication_year <= 2030)
                ),
                journal_id INTEGER,
                volume TEXT,
                issue TEXT,
                pages TEXT,
                url TEXT,
                arxiv_id TEXT,
                pubmed_id TEXT,
                file_path TEXT,
                file_type TEXT CHECK (
                    file_type IS NULL OR 
                    file_type IN ('pdf', 'txt', 'html', 'xml', 'docx')
                ),
                language TEXT DEFAULT 'en',
                keywords TEXT DEFAULT '[]',  -- JSON array of strings
                research_areas TEXT DEFAULT '[]',  -- JSON array of research areas
                methodology TEXT,  -- Research methodology description
                study_type TEXT CHECK (
                    study_type IS NULL OR
                    study_type IN (
                        'experimental', 'observational', 'review', 'meta-analysis',
                        'case-study', 'survey', 'qualitative', 'mixed-methods'
                    )
                ),
                sample_size INTEGER CHECK (sample_size IS NULL OR sample_size >= 0),
                participant_demographics TEXT,  -- JSON object for demographics
                inclusion_criteria TEXT,
                exclusion_criteria TEXT,
                outcome_measures TEXT,  -- JSON array of outcome measures
                statistical_methods TEXT,  -- JSON array of statistical methods used
                funding_sources TEXT,  -- JSON array of funding information
                conflicts_of_interest TEXT,
                ethical_approval BOOLEAN,
                data_availability TEXT,
                supplementary_materials TEXT,  -- JSON array of supplementary file paths
                notes TEXT,
                tags TEXT DEFAULT '[]',  -- JSON array of user tags
                indexed BOOLEAN DEFAULT 0,
                quality_assessed BOOLEAN DEFAULT 0,
                included_in_review BOOLEAN DEFAULT 1,
                exclusion_reason TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (journal_id) REFERENCES journals(id) ON DELETE SET NULL,
                
                -- Ensure valid DOI format if provided
                CHECK (doi IS NULL OR LENGTH(doi) >= 10),
                
                -- Ensure valid file path if provided
                CHECK (file_path IS NULL OR LENGTH(file_path) > 0)
            )
        """
        )

        self.logger.debug("Papers table created")

    def _create_authors_table(self, cursor) -> None:
        """
        Create authors table for researcher information.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                orcid TEXT UNIQUE,
                email TEXT,
                affiliation TEXT,
                department TEXT,
                country TEXT,
                h_index INTEGER CHECK (h_index IS NULL OR h_index >= 0),
                citation_count INTEGER CHECK (citation_count IS NULL OR citation_count >= 0),
                research_areas TEXT DEFAULT '[]',  -- JSON array of research areas
                expertise_keywords TEXT DEFAULT '[]',  -- JSON array of expertise keywords
                homepage_url TEXT,
                google_scholar_url TEXT,
                researchgate_url TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- Ensure valid ORCID format if provided
                CHECK (orcid IS NULL OR orcid GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][X0-9]')
            )
        """
        )

        self.logger.debug("Authors table created")

    def _create_paper_authors_table(self, cursor) -> None:
        """
        Create paper-author relationship table.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS paper_authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                author_position INTEGER NOT NULL CHECK (author_position > 0),
                is_corresponding BOOLEAN DEFAULT 0,
                contribution_statement TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
                FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE,
                
                -- Unique constraint for paper-author-position combination
                UNIQUE(paper_id, author_id),
                UNIQUE(paper_id, author_position)
            )
        """
        )

        self.logger.debug("Paper-authors relationship table created")

    def _create_journals_table(self, cursor) -> None:
        """
        Create journals table for publication venues.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS journals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                issn TEXT,
                e_issn TEXT,
                publisher TEXT,
                impact_factor REAL CHECK (impact_factor IS NULL OR impact_factor >= 0),
                h5_index INTEGER CHECK (h5_index IS NULL OR h5_index >= 0),
                sjr_score REAL CHECK (sjr_score IS NULL OR sjr_score >= 0),
                quartile TEXT CHECK (
                    quartile IS NULL OR quartile IN ('Q1', 'Q2', 'Q3', 'Q4')
                ),
                subject_areas TEXT DEFAULT '[]',  -- JSON array of subject areas
                open_access BOOLEAN DEFAULT 0,
                homepage_url TEXT,
                submission_guidelines_url TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- Ensure valid ISSN format if provided
                CHECK (issn IS NULL OR issn GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][X0-9]'),
                CHECK (e_issn IS NULL OR e_issn GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][X0-9]')
            )
        """
        )

        self.logger.debug("Journals table created")

    def _create_citations_table(self, cursor) -> None:
        """
        Create citations table for paper references.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS citations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                citing_paper_id INTEGER NOT NULL,
                cited_paper_id INTEGER,  -- NULL for external citations
                citation_text TEXT,
                citation_context TEXT,  -- Surrounding text context
                page_number INTEGER,
                section TEXT,  -- Section where citation appears
                citation_type TEXT DEFAULT 'reference' CHECK (
                    citation_type IN ('reference', 'background', 'method', 'comparison', 'criticism')
                ),
                external_title TEXT,  -- For citations not in our database
                external_authors TEXT,
                external_year INTEGER,
                external_journal TEXT,
                external_doi TEXT,
                external_url TEXT,
                sentiment TEXT CHECK (
                    sentiment IS NULL OR sentiment IN ('positive', 'neutral', 'negative')
                ),
                relevance_score REAL CHECK (
                    relevance_score IS NULL OR (relevance_score >= 0.0 AND relevance_score <= 1.0)
                ),
                extraction_method TEXT DEFAULT 'manual' CHECK (
                    extraction_method IN ('manual', 'automated', 'semi-automated')
                ),
                confidence_score REAL CHECK (
                    confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)
                ),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (citing_paper_id) REFERENCES papers(id) ON DELETE CASCADE,
                FOREIGN KEY (cited_paper_id) REFERENCES papers(id) ON DELETE SET NULL,

                -- Ensure either internal or external citation information
                CHECK (
                    (cited_paper_id IS NOT NULL) OR 
                    (external_title IS NOT NULL AND external_authors IS NOT NULL)
                )
            )
        """
        )

        self.logger.debug("Citations table created")

    def _create_chunks_table(self, cursor) -> None:
        """
        Create chunks table for paper content segmentation.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_type TEXT DEFAULT 'section' CHECK (
                    chunk_type IN (
                        'title', 'abstract', 'introduction', 'methodology', 'results',
                        'discussion', 'conclusion', 'references', 'section', 'paragraph',
                        'figure', 'table', 'equation', 'citation'
                    )
                ),
                section_title TEXT,
                content TEXT NOT NULL,
                start_page INTEGER,
                end_page INTEGER,
                word_count INTEGER CHECK (word_count >= 0),
                semantic_keywords TEXT DEFAULT '[]',  -- JSON array of extracted keywords
                research_concepts TEXT DEFAULT '[]',  -- JSON array of research concepts
                methodology_elements TEXT DEFAULT '[]',  -- JSON array of methodology elements
                statistical_results TEXT DEFAULT '{}',  -- JSON object for statistical data
                figures_tables TEXT DEFAULT '[]',  -- JSON array of figure/table references
                citations_mentioned TEXT DEFAULT '[]',  -- JSON array of citation IDs in this chunk
                quality_indicators TEXT DEFAULT '{}',  -- JSON object for quality metrics
                embedding_vector TEXT,  -- Serialized embedding for semantic search
                metadata TEXT DEFAULT '{}',  -- JSON object for chunk-specific metadata
                indexed_for_search BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
                UNIQUE(paper_id, chunk_index),

                -- Ensure valid page numbers
                CHECK (start_page IS NULL OR start_page > 0),
                CHECK (end_page IS NULL OR end_page > 0),
                CHECK (start_page IS NULL OR end_page IS NULL OR end_page >= start_page)
            )
        """
        )

        self.logger.debug("Chunks table created")

    def _create_quality_assessments_table(self, cursor) -> None:
        """
        Create quality assessments table for systematic review quality evaluation.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS quality_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER NOT NULL,
                framework TEXT NOT NULL CHECK (
                    framework IN ('prisma', 'strobe', 'consort', 'quadas', 'casp', 'custom')
                ),
                reviewer_id TEXT NOT NULL,
                overall_score REAL NOT NULL CHECK (overall_score >= 0.0 AND overall_score <= 100.0),
                risk_of_bias TEXT DEFAULT 'unknown' CHECK (
                    risk_of_bias IN ('low', 'moderate', 'high', 'unclear', 'unknown')
                ),
                study_design_score REAL CHECK (study_design_score IS NULL OR (study_design_score >= 0.0 AND study_design_score <= 100.0)),
                methodology_score REAL CHECK (methodology_score IS NULL OR (methodology_score >= 0.0 AND methodology_score <= 100.0)),
                data_quality_score REAL CHECK (data_quality_score IS NULL OR (data_quality_score >= 0.0 AND data_quality_score <= 100.0)),
                reporting_score REAL CHECK (reporting_score IS NULL OR (reporting_score >= 0.0 AND reporting_score <= 100.0)),
                statistical_analysis_score REAL CHECK (statistical_analysis_score IS NULL OR (statistical_analysis_score >= 0.0 AND statistical_analysis_score <= 100.0)),
                criterion_scores TEXT DEFAULT '{}',  -- JSON object for detailed criterion scores
                strengths TEXT,
                limitations TEXT,
                recommendations TEXT,
                reviewer_notes TEXT,
                assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                grade_level TEXT CHECK (
                    grade_level IS NULL OR grade_level IN ('very_low', 'low', 'moderate', 'high')
                ),
                confidence_level REAL CHECK (
                    confidence_level IS NULL OR (confidence_level >= 0.0 AND confidence_level <= 100.0)
                ),
                inter_rater_reliability REAL CHECK (
                    inter_rater_reliability IS NULL OR (inter_rater_reliability >= 0.0 AND inter_rater_reliability <= 1.0)
                ),
                consensus_reached BOOLEAN DEFAULT 0,
                final_decision TEXT CHECK (
                    final_decision IS NULL OR final_decision IN ('include', 'exclude', 'review', 'unclear')
                ),
                exclusion_reasons TEXT DEFAULT '[]',  -- JSON array of exclusion reasons
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
                
                -- Allow multiple assessments by different reviewers for same paper
                UNIQUE(paper_id, reviewer_id, framework)
            )
        """
        )

        self.logger.debug("Quality assessments table created")

    def _create_research_questions_table(self, cursor) -> None:
        """
        Create research questions table for systematic review questions.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS research_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                framework TEXT NOT NULL DEFAULT 'pico' CHECK (
                    framework IN ('pico', 'spider', 'picots', 'spice', 'custom')
                ),
                population TEXT,  -- PICO: Population/Patient
                intervention TEXT,  -- PICO: Intervention
                comparison TEXT,  -- PICO: Comparison/Control
                outcome TEXT,  -- PICO: Outcome
                time_frame TEXT,  -- PICOTS: Time
                setting TEXT,  -- SPIDER: Setting
                perspective TEXT,  -- SPIDER: Perspective
                phenomenon_of_interest TEXT,  -- SPIDER: Phenomenon of Interest
                design TEXT,  -- SPIDER: Design
                evaluation TEXT,  -- SPIDER: Evaluation
                research_type TEXT,  -- SPIDER: Research type
                question_type TEXT DEFAULT 'primary' CHECK (
                    question_type IN ('primary', 'secondary', 'exploratory')
                ),
                importance_level TEXT DEFAULT 'moderate' CHECK (
                    importance_level IN ('critical', 'important', 'moderate', 'low')
                ),
                search_strategy TEXT,
                inclusion_criteria TEXT DEFAULT '[]',  -- JSON array
                exclusion_criteria TEXT DEFAULT '[]',  -- JSON array
                validation_status TEXT DEFAULT 'draft' CHECK (
                    validation_status IN ('draft', 'validated', 'finalized', 'archived')
                ),
                validation_score REAL CHECK (
                    validation_score IS NULL OR (validation_score >= 0.0 AND validation_score <= 100.0)
                ),
                validation_feedback TEXT,
                review_protocol_section TEXT,
                related_papers TEXT DEFAULT '[]',  -- JSON array of paper IDs
                keywords_used TEXT DEFAULT '[]',  -- JSON array of search keywords
                databases_searched TEXT DEFAULT '[]',  -- JSON array of databases
                search_results_count INTEGER CHECK (search_results_count IS NULL OR search_results_count >= 0),
                papers_included_count INTEGER CHECK (papers_included_count IS NULL OR papers_included_count >= 0),
                last_search_date TIMESTAMP,
                notes TEXT,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        self.logger.debug("Research questions table created")

    def _create_research_hypotheses_table(self, cursor) -> None:
        """
        Create research hypotheses table for hypothesis testing.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS research_hypotheses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                research_question_id INTEGER,
                hypothesis_text TEXT NOT NULL,
                hypothesis_type TEXT NOT NULL DEFAULT 'primary' CHECK (
                    hypothesis_type IN ('primary', 'secondary', 'null', 'alternative')
                ),
                direction TEXT DEFAULT 'directional' CHECK (
                    direction IN ('directional', 'non-directional', 'one-tailed', 'two-tailed')
                ),
                statistical_test TEXT,
                significance_level REAL DEFAULT 0.05 CHECK (
                    significance_level > 0.0 AND significance_level < 1.0
                ),
                variables TEXT DEFAULT '[]',  -- JSON array of variables involved
                dependent_variable TEXT,
                independent_variables TEXT DEFAULT '[]',  -- JSON array
                confounding_variables TEXT DEFAULT '[]',  -- JSON array
                population_studied TEXT,
                sample_size_required INTEGER CHECK (sample_size_required IS NULL OR sample_size_required > 0),
                effect_size_expected REAL,
                power_analysis TEXT,  -- JSON object for power analysis details
                testing_status TEXT DEFAULT 'proposed' CHECK (
                    testing_status IN ('proposed', 'testing', 'tested', 'supported', 'rejected', 'inconclusive')
                ),
                evidence_papers TEXT DEFAULT '[]',  -- JSON array of paper IDs providing evidence
                test_results TEXT DEFAULT '{}',  -- JSON object for statistical test results
                p_value REAL CHECK (p_value IS NULL OR (p_value >= 0.0 AND p_value <= 1.0)),
                confidence_interval TEXT,  -- e.g., "95% CI: [0.2, 0.8]"
                effect_size_observed REAL,
                conclusion TEXT,
                limitations TEXT,
                reviewer_id TEXT,
                review_date TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (research_question_id) REFERENCES research_questions(id) ON DELETE SET NULL
            )
        """
        )

        self.logger.debug("Research hypotheses table created")

    def _create_evidence_items_table(self, cursor) -> None:
        """
        Create evidence items table for extracted evidence.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER NOT NULL,
                hypothesis_id INTEGER,
                chunk_id INTEGER,
                evidence_text TEXT NOT NULL,
                evidence_type TEXT NOT NULL CHECK (
                    evidence_type IN (
                        'statistical', 'qualitative', 'quantitative', 'observational',
                        'experimental', 'meta-analysis', 'systematic_review', 'expert_opinion'
                    )
                ),
                strength TEXT DEFAULT 'moderate' CHECK (
                    strength IN ('very_strong', 'strong', 'moderate', 'weak', 'very_weak')
                ),
                quality TEXT DEFAULT 'moderate' CHECK (
                    quality IN ('very_high', 'high', 'moderate', 'low', 'very_low')
                ),
                relevance REAL DEFAULT 0.5 CHECK (relevance >= 0.0 AND relevance <= 1.0),
                supporting BOOLEAN,  -- TRUE if supports hypothesis, FALSE if contradicts
                effect_size REAL,
                confidence_interval TEXT,
                statistical_significance REAL CHECK (
                    statistical_significance IS NULL OR (statistical_significance >= 0.0 AND statistical_significance <= 1.0)
                ),
                sample_size INTEGER CHECK (sample_size IS NULL OR sample_size > 0),
                study_design TEXT,
                population_characteristics TEXT,
                outcome_measures TEXT DEFAULT '[]',  -- JSON array
                methodological_quality TEXT DEFAULT 'moderate' CHECK (
                    methodological_quality IN ('excellent', 'good', 'moderate', 'poor', 'very_poor')
                ),
                risk_of_bias TEXT DEFAULT 'unclear' CHECK (
                    risk_of_bias IN ('low', 'moderate', 'high', 'unclear')
                ),
                grade_rating TEXT CHECK (
                    grade_rating IS NULL OR grade_rating IN ('very_low', 'low', 'moderate', 'high')
                ),
                extraction_method TEXT DEFAULT 'manual' CHECK (
                    extraction_method IN ('manual', 'automated', 'semi-automated')
                ),
                extractor_id TEXT,
                extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verification_status TEXT DEFAULT 'pending' CHECK (
                    verification_status IN ('pending', 'verified', 'disputed', 'rejected')
                ),
                verifier_id TEXT,
                verification_date TIMESTAMP,
                notes TEXT,
                metadata TEXT DEFAULT '{}',  -- JSON object for additional metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
                FOREIGN KEY (hypothesis_id) REFERENCES research_hypotheses(id) ON DELETE SET NULL,
                FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE SET NULL
            )
        """
        )

        self.logger.debug("Evidence items table created")

    def _create_synthesis_results_table(self, cursor) -> None:
        """
        Create synthesis results table for meta-analysis and evidence synthesis.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS synthesis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                research_question_id INTEGER,
                synthesis_type TEXT NOT NULL CHECK (
                    synthesis_type IN ('meta-analysis', 'narrative', 'thematic', 'mixed-methods', 'network')
                ),
                title TEXT NOT NULL,
                description TEXT,
                papers_included TEXT DEFAULT '[]',  -- JSON array of paper IDs
                evidence_items_included TEXT DEFAULT '[]',  -- JSON array of evidence item IDs
                total_participants INTEGER CHECK (total_participants IS NULL OR total_participants >= 0),
                number_of_studies INTEGER CHECK (number_of_studies IS NULL OR number_of_studies >= 0),
                pooled_effect_size REAL,
                effect_size_ci TEXT,  -- Confidence interval for effect size
                heterogeneity_i2 REAL CHECK (heterogeneity_i2 IS NULL OR (heterogeneity_i2 >= 0.0 AND heterogeneity_i2 <= 100.0)),
                heterogeneity_p_value REAL CHECK (heterogeneity_p_value IS NULL OR (heterogeneity_p_value >= 0.0 AND heterogeneity_p_value <= 1.0)),
                tau_squared REAL CHECK (tau_squared IS NULL OR tau_squared >= 0.0),
                statistical_model TEXT CHECK (
                    statistical_model IS NULL OR statistical_model IN ('fixed-effects', 'random-effects', 'mixed-effects')
                ),
                statistical_method TEXT,  -- e.g., "Inverse variance", "Mantel-Haenszel"
                subgroup_analyses TEXT DEFAULT '[]',  -- JSON array of subgroup analysis results
                sensitivity_analyses TEXT DEFAULT '[]',  -- JSON array of sensitivity analysis results
                publication_bias_assessment TEXT DEFAULT '{}',  -- JSON object for bias assessment
                funnel_plot_data TEXT,  -- JSON data for funnel plot
                egger_test_p_value REAL CHECK (egger_test_p_value IS NULL OR (egger_test_p_value >= 0.0 AND egger_test_p_value <= 1.0)),
                grade_assessment TEXT DEFAULT '{}',  -- JSON object for GRADE assessment
                certainty_of_evidence TEXT CHECK (
                    certainty_of_evidence IS NULL OR certainty_of_evidence IN ('very_low', 'low', 'moderate', 'high')
                ),
                clinical_significance TEXT,
                policy_implications TEXT,
                research_gaps TEXT DEFAULT '[]',  -- JSON array of identified research gaps
                recommendations TEXT DEFAULT '[]',  -- JSON array of recommendations
                limitations TEXT,
                conclusions TEXT,
                forest_plot_data TEXT,  -- JSON data for forest plot
                analysis_software TEXT,  -- Software used for analysis
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                analyst_id TEXT,
                peer_reviewer_id TEXT,
                review_status TEXT DEFAULT 'draft' CHECK (
                    review_status IN ('draft', 'under_review', 'revised', 'final', 'published')
                ),
                notes TEXT,
                metadata TEXT DEFAULT '{}',  -- JSON object for additional metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (research_question_id) REFERENCES research_questions(id) ON DELETE SET NULL
            )
        """
        )

        self.logger.debug("Synthesis results table created")

    def _create_search_indexes(self, cursor) -> None:
        """
        Create FTS5 full-text search indexes for efficient academic searching.

        Args:
            cursor: Database cursor for executing statements
        """
        # FTS5 index for papers (title, abstract, keywords)
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
                paper_id UNINDEXED,
                title,
                abstract,
                keywords,
                content='',
                content_rowid='id'
            )
        """
        )

        # FTS5 index for chunks (section titles and content)
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                chunk_id UNINDEXED,
                paper_id UNINDEXED,
                section_title,
                content,
                research_concepts,
                content='',
                content_rowid='id'
            )
        """
        )

        # FTS5 index for authors
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS authors_fts USING fts5(
                author_id UNINDEXED,
                name,
                affiliation,
                research_areas,
                content='',
                content_rowid='id'
            )
        """
        )

        # FTS5 index for research questions
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS research_questions_fts USING fts5(
                question_id UNINDEXED,
                question_text,
                population,
                intervention,
                outcome,
                content='',
                content_rowid='id'
            )
        """
        )

        # Create triggers to maintain FTS5 indexes
        self._create_fts_triggers(cursor)

        self.logger.debug("FTS5 search indexes created")

    def _create_fts_triggers(self, cursor) -> None:
        """
        Create triggers to automatically maintain FTS5 indexes.

        Args:
            cursor: Database cursor for executing statements
        """
        # Papers FTS triggers
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS papers_fts_insert AFTER INSERT ON papers
            BEGIN
                INSERT INTO papers_fts(paper_id, title, abstract, keywords)
                VALUES (NEW.id, NEW.title, NEW.abstract, NEW.keywords);
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS papers_fts_delete AFTER DELETE ON papers
            BEGIN
                DELETE FROM papers_fts WHERE paper_id = OLD.id;
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS papers_fts_update AFTER UPDATE ON papers
            BEGIN
                UPDATE papers_fts
                SET title = NEW.title, abstract = NEW.abstract, keywords = NEW.keywords
                WHERE paper_id = NEW.id;
            END
        """
        )

        # Chunks FTS triggers
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS chunks_fts_insert AFTER INSERT ON chunks
            BEGIN
                INSERT INTO chunks_fts(chunk_id, paper_id, section_title, content, research_concepts)
                VALUES (NEW.id, NEW.paper_id, NEW.section_title, NEW.content, NEW.research_concepts);
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS chunks_fts_delete AFTER DELETE ON chunks
            BEGIN
                DELETE FROM chunks_fts WHERE chunk_id = OLD.id;
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS chunks_fts_update AFTER UPDATE ON chunks
            BEGIN
                UPDATE chunks_fts
                SET section_title = NEW.section_title, content = NEW.content, 
                    research_concepts = NEW.research_concepts
                WHERE chunk_id = NEW.id;
            END
        """
        )

        # Authors FTS triggers
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS authors_fts_insert AFTER INSERT ON authors
            BEGIN
                INSERT INTO authors_fts(author_id, name, affiliation, research_areas)
                VALUES (NEW.id, NEW.name, NEW.affiliation, NEW.research_areas);
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS authors_fts_delete AFTER DELETE ON authors
            BEGIN
                DELETE FROM authors_fts WHERE author_id = OLD.id;
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS authors_fts_update AFTER UPDATE ON authors
            BEGIN
                UPDATE authors_fts
                SET name = NEW.name, affiliation = NEW.affiliation, research_areas = NEW.research_areas
                WHERE author_id = NEW.id;
            END
        """
        )

        # Research questions FTS triggers
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS research_questions_fts_insert AFTER INSERT ON research_questions
            BEGIN
                INSERT INTO research_questions_fts(question_id, question_text, population, intervention, outcome)
                VALUES (NEW.id, NEW.question_text, NEW.population, NEW.intervention, NEW.outcome);
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS research_questions_fts_delete AFTER DELETE ON research_questions
            BEGIN
                DELETE FROM research_questions_fts WHERE question_id = OLD.id;
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS research_questions_fts_update AFTER UPDATE ON research_questions
            BEGIN
                UPDATE research_questions_fts
                SET question_text = NEW.question_text, population = NEW.population,
                    intervention = NEW.intervention, outcome = NEW.outcome
                WHERE question_id = NEW.id;
            END
        """
        )

        self.logger.debug("FTS5 triggers created")

    def _create_performance_indexes(self, cursor) -> None:
        """
        Create additional indexes for query performance optimization.

        Args:
            cursor: Database cursor for executing statements
        """
        # Paper indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(publication_year)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_papers_journal ON papers(journal_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_papers_study_type ON papers(study_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_papers_indexed ON papers(indexed)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_papers_included ON papers(included_in_review)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_papers_upload_date ON papers(upload_date)"
        )

        # Author indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_authors_name ON authors(name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_authors_orcid ON authors(orcid)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_authors_affiliation ON authors(affiliation)"
        )

        # Paper-author indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_paper_authors_paper ON paper_authors(paper_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_paper_authors_author ON paper_authors(author_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_paper_authors_position ON paper_authors(author_position)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_paper_authors_corresponding ON paper_authors(is_corresponding)"
        )

        # Citation indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_citations_citing ON citations(citing_paper_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_citations_cited ON citations(cited_paper_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_citations_type ON citations(citation_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_citations_doi ON citations(external_doi)"
        )

        # Chunk indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_paper ON chunks(paper_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_type ON chunks(chunk_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_paper_index ON chunks(paper_id, chunk_index)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_indexed ON chunks(indexed_for_search)"
        )

        # Quality assessment indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_quality_paper ON quality_assessments(paper_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_quality_framework ON quality_assessments(framework)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_quality_reviewer ON quality_assessments(reviewer_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_quality_score ON quality_assessments(overall_score)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_quality_bias ON quality_assessments(risk_of_bias)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_quality_decision ON quality_assessments(final_decision)"
        )

        # Research question indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_research_questions_framework ON research_questions(framework)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_research_questions_type ON research_questions(question_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_research_questions_status ON research_questions(validation_status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_research_questions_created_by ON research_questions(created_by)"
        )

        # Hypothesis indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_hypotheses_question ON research_hypotheses(research_question_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_hypotheses_type ON research_hypotheses(hypothesis_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_hypotheses_status ON research_hypotheses(testing_status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_hypotheses_reviewer ON research_hypotheses(reviewer_id)"
        )

        # Evidence indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_evidence_paper ON evidence_items(paper_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_evidence_hypothesis ON evidence_items(hypothesis_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_evidence_chunk ON evidence_items(chunk_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence_items(evidence_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_evidence_strength ON evidence_items(strength)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_evidence_supporting ON evidence_items(supporting)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_evidence_extractor ON evidence_items(extractor_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_evidence_status ON evidence_items(verification_status)"
        )

        # Synthesis indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_synthesis_question ON synthesis_results(research_question_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_synthesis_type ON synthesis_results(synthesis_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_synthesis_analyst ON synthesis_results(analyst_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_synthesis_status ON synthesis_results(review_status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_synthesis_certainty ON synthesis_results(certainty_of_evidence)"
        )

        self.logger.debug("Performance indexes created")

    def _initialize_metadata(self, cursor) -> None:
        """
        Initialize schema metadata and version tracking.

        Args:
            cursor: Database cursor for executing statements
        """
        # Create metadata table for schema versioning
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Insert schema version
        cursor.execute(
            """
            INSERT OR REPLACE INTO schema_metadata (key, value)
            VALUES ('schema_version', ?), ('initialized_at', CURRENT_TIMESTAMP)
        """,
            (str(self.SCHEMA_VERSION),),
        )

        self.logger.debug(
            f"Schema metadata initialized (version {self.SCHEMA_VERSION})"
        )

    def get_schema_version(self) -> int:
        """
        Get current schema version from database.

        Returns:
            Schema version number, 0 if not initialized
        """
        try:
            cursor = self.db.execute(
                "SELECT value FROM schema_metadata WHERE key = 'schema_version'"
            )
            result = cursor.fetchone()
            return int(result[0]) if result else 0
        except Exception:
            return 0

    def verify_schema(self) -> bool:
        """
        Verify that database schema is properly initialized.

        Returns:
            True if schema is valid, False otherwise
        """
        try:
            required_tables = [
                "papers",
                "authors", 
                "paper_authors",
                "journals",
                "citations",
                "chunks",
                "quality_assessments",
                "research_questions",
                "research_hypotheses",
                "evidence_items",
                "synthesis_results",
                "schema_metadata",
            ]
            required_fts_tables = [
                "papers_fts",
                "chunks_fts",
                "authors_fts",
                "research_questions_fts",
            ]

            cursor = self.db.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """
            )

            existing_tables = {row[0] for row in cursor.fetchall()}

            # Check all required tables exist
            missing_tables = (
                set(required_tables + required_fts_tables) - existing_tables
            )
            if missing_tables:
                self.logger.error(f"Missing tables: {missing_tables}")
                return False

            # Check schema version
            current_version = self.get_schema_version()
            if current_version != self.SCHEMA_VERSION:
                self.logger.error(
                    f"Schema version mismatch: {current_version} != {self.SCHEMA_VERSION}"
                )
                return False

            self.logger.info("Schema verification successful")
            return True

        except Exception as e:
            self.logger.error(f"Schema verification failed: {e}")
            return False

    def drop_schema(self) -> None:
        """
        Drop all schema objects (for testing/cleanup).

        WARNING: This will delete all data!

        Raises:
            sqlite3.Error: If schema deletion fails
        """
        try:
            with self.db.transaction() as conn:
                cursor = conn.cursor()

                # Drop FTS tables first
                fts_tables = ["papers_fts", "chunks_fts", "authors_fts", "research_questions_fts"]
                for table in fts_tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")

                # Drop main tables in reverse dependency order
                main_tables = [
                    "synthesis_results",
                    "evidence_items", 
                    "research_hypotheses",
                    "research_questions",
                    "quality_assessments",
                    "chunks",
                    "citations",
                    "paper_authors",
                    "papers",
                    "authors",
                    "journals",
                    "schema_metadata",
                ]
                for table in main_tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")

                self.logger.warning("All schema objects dropped")

        except Exception as e:
            self.logger.error(f"Failed to drop schema: {e}")
            raise


async def create_tables(db_connection: DatabaseConnection) -> None:
    """
    Initialize database tables using SchemaManager.
    
    Args:
        db_connection: Database connection instance
    """
    schema_manager = SchemaManager(db_connection)
    schema_manager.initialize_schema()
