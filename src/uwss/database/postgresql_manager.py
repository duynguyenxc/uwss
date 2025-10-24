"""
PostgreSQL Database Manager

This module provides PostgreSQL database integration for storing
and managing academic and web documents with full metadata.
"""

import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path

from .data_models import AcademicDocument, WebDocument, Metadata, DocumentType, SourceType, ContentType

logger = logging.getLogger(__name__)


class PostgreSQLManager:
    """
    PostgreSQL database manager for Universal Web Crawling System.
    
    Technologies used:
    - psycopg2: PostgreSQL adapter for Python
    - JSONB: Flexible storage for metadata
    - Connection pooling: Efficient database connections
    - Transaction management: ACID compliance
    - Full-text search: PostgreSQL full-text search capabilities
    """
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 5432,
                 database: str = "uwss",
                 user: str = "postgres",
                 password: str = "postgres"):
        """Initialize PostgreSQL manager."""
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None
        
    def connect(self) -> bool:
        """Connect to PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            logger.info(f"Connected to PostgreSQL database: {self.database}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from PostgreSQL database."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Disconnected from PostgreSQL database")
    
    def create_database(self) -> bool:
        """Create database if it doesn't exist."""
        try:
            # Connect to default postgres database
            temp_conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database="postgres",
                user=self.user,
                password=self.password
            )
            temp_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            temp_cursor = temp_conn.cursor()
            
            # Check if database exists
            temp_cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.database,)
            )
            
            if not temp_cursor.fetchone():
                # Create database
                temp_cursor.execute(f"CREATE DATABASE {self.database}")
                logger.info(f"Created database: {self.database}")
            else:
                logger.info(f"Database already exists: {self.database}")
            
            temp_cursor.close()
            temp_conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return False
    
    def create_tables(self) -> bool:
        """Create database tables."""
        try:
            if not self.connect():
                return False
            
            # Create academic_documents table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS academic_documents (
                    id UUID PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors JSONB,
                    abstract TEXT,
                    keywords JSONB,
                    publication_date TIMESTAMP,
                    publication_year INTEGER,
                    journal TEXT,
                    venue TEXT,
                    volume TEXT,
                    issue TEXT,
                    pages TEXT,
                    doi TEXT UNIQUE,
                    pmid TEXT,
                    arxiv_id TEXT,
                    isbn TEXT,
                    issn TEXT,
                    url TEXT NOT NULL,
                    source_url TEXT,
                    source_type TEXT,
                    source_name TEXT,
                    content_type TEXT,
                    document_type TEXT,
                    language TEXT DEFAULT 'en',
                    word_count INTEGER DEFAULT 0,
                    page_count INTEGER DEFAULT 0,
                    relevance_score FLOAT DEFAULT 0.0,
                    quality_score FLOAT DEFAULT 0.0,
                    confidence_score FLOAT DEFAULT 0.0,
                    content TEXT,
                    full_text TEXT,
                    summary TEXT,
                    citations JSONB,
                    references JSONB,
                    funding JSONB,
                    acknowledgments TEXT,
                    citation_count INTEGER DEFAULT 0,
                    download_count INTEGER DEFAULT 0,
                    view_count INTEGER DEFAULT 0,
                    subject_areas JSONB,
                    research_fields JSONB,
                    methodologies JSONB,
                    file_path TEXT,
                    file_size INTEGER DEFAULT 0,
                    file_hash TEXT,
                    download_url TEXT,
                    tags JSONB,
                    categories JSONB,
                    topics JSONB,
                    custom_fields JSONB,
                    access_level TEXT DEFAULT 'public',
                    license TEXT,
                    copyright TEXT,
                    is_duplicate BOOLEAN DEFAULT FALSE,
                    is_processed BOOLEAN DEFAULT FALSE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    last_accessed TIMESTAMP
                )
            """)
            
            # Create web_documents table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS web_documents (
                    id UUID PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors JSONB,
                    abstract TEXT,
                    keywords JSONB,
                    publication_date TIMESTAMP,
                    publication_year INTEGER,
                    url TEXT NOT NULL,
                    source_type TEXT,
                    source_name TEXT,
                    content_type TEXT,
                    document_type TEXT,
                    language TEXT DEFAULT 'en',
                    word_count INTEGER DEFAULT 0,
                    relevance_score FLOAT DEFAULT 0.0,
                    quality_score FLOAT DEFAULT 0.0,
                    confidence_score FLOAT DEFAULT 0.0,
                    content TEXT,
                    html_content TEXT,
                    text_content TEXT,
                    domain TEXT,
                    path TEXT,
                    query_params JSONB,
                    likes INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    content_category TEXT,
                    sentiment TEXT,
                    readability_score FLOAT DEFAULT 0.0,
                    file_path TEXT,
                    file_size INTEGER DEFAULT 0,
                    file_hash TEXT,
                    download_url TEXT,
                    tags JSONB,
                    categories JSONB,
                    topics JSONB,
                    custom_fields JSONB,
                    access_level TEXT DEFAULT 'public',
                    license TEXT,
                    copyright TEXT,
                    is_duplicate BOOLEAN DEFAULT FALSE,
                    is_processed BOOLEAN DEFAULT FALSE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    last_accessed TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_academic_documents_title 
                ON academic_documents USING gin(to_tsvector('english', title))
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_academic_documents_abstract 
                ON academic_documents USING gin(to_tsvector('english', abstract))
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_academic_documents_authors 
                ON academic_documents USING gin(authors)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_academic_documents_keywords 
                ON academic_documents USING gin(keywords)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_academic_documents_source_type 
                ON academic_documents(source_type)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_academic_documents_publication_year 
                ON academic_documents(publication_year)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_web_documents_title 
                ON web_documents USING gin(to_tsvector('english', title))
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_web_documents_content 
                ON web_documents USING gin(to_tsvector('english', content))
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_web_documents_domain 
                ON web_documents(domain)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_web_documents_source_type 
                ON web_documents(source_type)
            """)
            
            logger.info("Database tables created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False
        finally:
            self.disconnect()
    
    def insert_academic_document(self, document: AcademicDocument) -> bool:
        """Insert academic document into database."""
        try:
            if not self.connect():
                return False
            
            data = document.to_dict()
            
            self.cursor.execute("""
                INSERT INTO academic_documents (
                    id, title, authors, abstract, keywords, publication_date, publication_year,
                    journal, venue, volume, issue, pages, doi, pmid, arxiv_id, isbn, issn,
                    url, source_url, source_type, source_name, content_type, document_type,
                    language, word_count, page_count, relevance_score, quality_score, confidence_score,
                    content, full_text, summary, citations, references, funding, acknowledgments,
                    citation_count, download_count, view_count, subject_areas, research_fields,
                    methodologies, file_path, file_size, file_hash, download_url, tags, categories,
                    topics, custom_fields, access_level, license, copyright, is_duplicate,
                    is_processed, is_verified, error_message, created_at, updated_at, processed_at,
                    last_accessed
                ) VALUES (
                    %(id)s, %(title)s, %(authors)s, %(abstract)s, %(keywords)s, %(publication_date)s,
                    %(publication_year)s, %(journal)s, %(venue)s, %(volume)s, %(issue)s, %(pages)s,
                    %(doi)s, %(pmid)s, %(arxiv_id)s, %(isbn)s, %(issn)s, %(url)s, %(source_url)s,
                    %(source_type)s, %(source_name)s, %(content_type)s, %(document_type)s,
                    %(language)s, %(word_count)s, %(page_count)s, %(relevance_score)s,
                    %(quality_score)s, %(confidence_score)s, %(content)s, %(full_text)s, %(summary)s,
                    %(citations)s, %(references)s, %(funding)s, %(acknowledgments)s,
                    %(citation_count)s, %(download_count)s, %(view_count)s, %(subject_areas)s,
                    %(research_fields)s, %(methodologies)s, %(file_path)s, %(file_size)s,
                    %(file_hash)s, %(download_url)s, %(tags)s, %(categories)s, %(topics)s,
                    %(custom_fields)s, %(access_level)s, %(license)s, %(copyright)s,
                    %(is_duplicate)s, %(is_processed)s, %(is_verified)s, %(error_message)s,
                    %(created_at)s, %(updated_at)s, %(processed_at)s, %(last_accessed)s
                )
            """, data)
            
            logger.info(f"Inserted academic document: {document.metadata.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert academic document: {e}")
            return False
        finally:
            self.disconnect()
    
    def insert_web_document(self, document: WebDocument) -> bool:
        """Insert web document into database."""
        try:
            if not self.connect():
                return False
            
            data = document.to_dict()
            
            self.cursor.execute("""
                INSERT INTO web_documents (
                    id, title, authors, abstract, keywords, publication_date, publication_year,
                    url, source_type, source_name, content_type, document_type, language,
                    word_count, relevance_score, quality_score, confidence_score, content,
                    html_content, text_content, domain, path, query_params, likes, shares,
                    comments, views, content_category, sentiment, readability_score,
                    file_path, file_size, file_hash, download_url, tags, categories, topics,
                    custom_fields, access_level, license, copyright, is_duplicate, is_processed,
                    is_verified, error_message, created_at, updated_at, processed_at, last_accessed
                ) VALUES (
                    %(id)s, %(title)s, %(authors)s, %(abstract)s, %(keywords)s, %(publication_date)s,
                    %(publication_year)s, %(url)s, %(source_type)s, %(source_name)s,
                    %(content_type)s, %(document_type)s, %(language)s, %(word_count)s,
                    %(relevance_score)s, %(quality_score)s, %(confidence_score)s, %(content)s,
                    %(html_content)s, %(text_content)s, %(domain)s, %(path)s, %(query_params)s,
                    %(likes)s, %(shares)s, %(comments)s, %(views)s, %(content_category)s,
                    %(sentiment)s, %(readability_score)s, %(file_path)s, %(file_size)s,
                    %(file_hash)s, %(download_url)s, %(tags)s, %(categories)s, %(topics)s,
                    %(custom_fields)s, %(access_level)s, %(license)s, %(copyright)s,
                    %(is_duplicate)s, %(is_processed)s, %(is_verified)s, %(error_message)s,
                    %(created_at)s, %(updated_at)s, %(processed_at)s, %(last_accessed)s
                )
            """, data)
            
            logger.info(f"Inserted web document: {document.metadata.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert web document: {e}")
            return False
        finally:
            self.disconnect()
    
    def search_documents(self, 
                        query: str,
                        document_type: str = "academic",
                        limit: int = 100,
                        offset: int = 0) -> List[Dict[str, Any]]:
        """Search documents using full-text search."""
        try:
            if not self.connect():
                return []
            
            table_name = "academic_documents" if document_type == "academic" else "web_documents"
            
            self.cursor.execute(f"""
                SELECT * FROM {table_name}
                WHERE to_tsvector('english', title || ' ' || COALESCE(abstract, '') || ' ' || COALESCE(content, '')) 
                @@ plainto_tsquery('english', %s)
                ORDER BY relevance_score DESC, quality_score DESC
                LIMIT %s OFFSET %s
            """, (query, limit, offset))
            
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []
        finally:
            self.disconnect()
    
    def get_document_by_id(self, document_id: str, document_type: str = "academic") -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        try:
            if not self.connect():
                return None
            
            table_name = "academic_documents" if document_type == "academic" else "web_documents"
            
            self.cursor.execute(f"""
                SELECT * FROM {table_name} WHERE id = %s
            """, (document_id,))
            
            result = self.cursor.fetchone()
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Failed to get document by ID: {e}")
            return None
        finally:
            self.disconnect()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            if not self.connect():
                return {}
            
            # Academic documents count
            self.cursor.execute("SELECT COUNT(*) as count FROM academic_documents")
            academic_count = self.cursor.fetchone()['count']
            
            # Web documents count
            self.cursor.execute("SELECT COUNT(*) as count FROM web_documents")
            web_count = self.cursor.fetchone()['count']
            
            # Source type distribution
            self.cursor.execute("""
                SELECT source_type, COUNT(*) as count 
                FROM academic_documents 
                GROUP BY source_type
            """)
            academic_sources = dict(self.cursor.fetchall())
            
            self.cursor.execute("""
                SELECT source_type, COUNT(*) as count 
                FROM web_documents 
                GROUP BY source_type
            """)
            web_sources = dict(self.cursor.fetchall())
            
            # Year distribution
            self.cursor.execute("""
                SELECT publication_year, COUNT(*) as count 
                FROM academic_documents 
                WHERE publication_year IS NOT NULL 
                GROUP BY publication_year 
                ORDER BY publication_year DESC 
                LIMIT 10
            """)
            year_distribution = dict(self.cursor.fetchall())
            
            return {
                'total_documents': academic_count + web_count,
                'academic_documents': academic_count,
                'web_documents': web_count,
                'academic_sources': academic_sources,
                'web_sources': web_sources,
                'year_distribution': year_distribution
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
        finally:
            self.disconnect()
    
    def cleanup_duplicates(self) -> int:
        """Remove duplicate documents based on URL and title."""
        try:
            if not self.connect():
                return 0
            
            # Remove duplicates from academic_documents
            self.cursor.execute("""
                DELETE FROM academic_documents 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM academic_documents 
                    GROUP BY url, title
                )
            """)
            academic_removed = self.cursor.rowcount
            
            # Remove duplicates from web_documents
            self.cursor.execute("""
                DELETE FROM web_documents 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM web_documents 
                    GROUP BY url, title
                )
            """)
            web_removed = self.cursor.rowcount
            
            total_removed = academic_removed + web_removed
            logger.info(f"Removed {total_removed} duplicate documents")
            return total_removed
            
        except Exception as e:
            logger.error(f"Failed to cleanup duplicates: {e}")
            return 0
        finally:
            self.disconnect()


def main():
    """Test PostgreSQL manager."""
    # Initialize manager
    db_manager = PostgreSQLManager()
    
    # Create database
    if db_manager.create_database():
        print("Database created successfully")
    
    # Create tables
    if db_manager.create_tables():
        print("Tables created successfully")
    
    # Test connection
    if db_manager.connect():
        print("Connection successful")
        db_manager.disconnect()
    
    # Get statistics
    stats = db_manager.get_statistics()
    print(f"Database statistics: {stats}")


if __name__ == "__main__":
    main()
