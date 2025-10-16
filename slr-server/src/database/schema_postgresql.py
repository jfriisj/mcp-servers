"""
PostgreSQL-specific schema creation for SLR MCP Server.
Handles PostgreSQL-specific data types and syntax.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def create_tables_postgresql(conn: Any) -> None:
    """Create PostgreSQL tables with proper data types and constraints."""
    
    cursor = conn.cursor()
    
    # Projects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            description TEXT,
            research_question TEXT,
            research_domain VARCHAR(200),
            team_lead VARCHAR(200),
            team_members TEXT,
            estimated_timeline_weeks INTEGER,
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Papers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            authors TEXT,
            publication_year INTEGER,
            doi VARCHAR(200),
            abstract TEXT,
            content TEXT,
            file_path VARCHAR(500),
            tags TEXT,
            indexed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Chunks table for semantic search
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id SERIAL PRIMARY KEY,
            paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            chunk_type VARCHAR(100),
            section_title VARCHAR(300),
            start_page INTEGER,
            end_page INTEGER,
            metadata JSONB,
            embedding BYTEA,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Quality assessments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_assessments (
            id SERIAL PRIMARY KEY,
            paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
            reviewer_id VARCHAR(200) NOT NULL,
            assessment_framework VARCHAR(50) DEFAULT 'PRISMA',
            criteria JSONB,
            scores JSONB,
            overall_score DECIMAL(4,2),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(paper_id, reviewer_id)
        )
    """)
    
    # Screening decisions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screening_decisions (
            id SERIAL PRIMARY KEY,
            project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
            paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
            reviewer_id VARCHAR(200) NOT NULL,
            stage VARCHAR(50) NOT NULL,
            decision VARCHAR(20) NOT NULL,
            reason TEXT,
            exclusion_criteria TEXT,
            confidence_level DECIMAL(3,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, paper_id, reviewer_id, stage)
        )
    """)
    
    # Citations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS citations (
            id SERIAL PRIMARY KEY,
            citing_paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
            cited_paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
            citation_context TEXT,
            citation_type VARCHAR(50),
            page_number INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(citing_paper_id, cited_paper_id)
        )
    """)
    
    # Hypotheses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hypotheses (
            id SERIAL PRIMARY KEY,
            paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
            hypothesis_text TEXT NOT NULL,
            hypothesis_type VARCHAR(20) DEFAULT 'explicit',
            section VARCHAR(100),
            confidence_score DECIMAL(3,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Evidence synthesis table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_synthesis (
            id SERIAL PRIMARY KEY,
            synthesis_title VARCHAR(300) NOT NULL,
            paper_ids JSONB NOT NULL,
            synthesis_method VARCHAR(50) DEFAULT 'narrative',
            outcome_measures TEXT,
            results JSONB,
            confidence_level VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_title ON papers USING gin(to_tsvector('english', title))")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_authors ON papers USING gin(to_tsvector('english', authors))")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_publication_year ON papers(publication_year)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_paper_id ON chunks(paper_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_content ON chunks USING gin(to_tsvector('english', content))")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_assessments_paper_id ON quality_assessments(paper_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_screening_decisions_project_paper ON screening_decisions(project_id, paper_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_citations_citing_paper ON citations(citing_paper_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_citations_cited_paper ON citations(cited_paper_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hypotheses_paper_id ON hypotheses(paper_id)")
    
    # Create triggers for updated_at timestamps
    cursor.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)
    
    # Apply triggers to relevant tables
    for table in ['projects', 'papers']:
        cursor.execute(f"""
            DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};
            CREATE TRIGGER update_{table}_updated_at
                BEFORE UPDATE ON {table}
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column()
        """)
    
    conn.commit()
    logger.info("PostgreSQL tables and indexes created successfully")