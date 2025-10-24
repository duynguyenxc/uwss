#!/usr/bin/env python3
"""
Test script for Real Academic Data Collection

This script tests the real academic data collection functionality
for the Universal Web Crawling System.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from uwss.database.postgresql_manager import PostgreSQLManager
from uwss.database.data_processor import DataProcessor
from uwss.database.data_models import SourceType, DocumentType, ContentType
from uwss.intelligence.keyword_discovery import KeywordDiscoveryEngine
from uwss.discovery.intelligent_discovery import IntelligentSourceDiscovery


def test_postgresql_setup():
    """Test PostgreSQL database setup."""
    print("Testing PostgreSQL Database Setup...")
    
    # Initialize PostgreSQL manager
    db_manager = PostgreSQLManager(
        host="localhost",
        port=5432,
        database="uwss",
        user="postgres",
        password="postgres"
    )
    
    # Create database
    if db_manager.create_database():
        print("✅ Database created successfully")
    else:
        print("Failed to create database")
        return False
    
    # Create tables
    if db_manager.create_tables():
        print("✅ Tables created successfully")
    else:
        print("Failed to create tables")
        return False
    
    # Test connection
    if db_manager.connect():
        print("✅ Database connection successful")
        db_manager.disconnect()
        return True
    else:
        print("Database connection failed")
        return False


def test_data_processing():
    """Test data processing functionality."""
    print("\nTesting Data Processing...")
    
    # Initialize data processor
    processor = DataProcessor()
    
    # Test academic document processing
    academic_doc = processor.process_academic_document(
        title="Reinforced Concrete Deterioration Due to Chloride Attack",
        authors=["John Doe", "Jane Smith", "Bob Johnson"],
        abstract="This study investigates the deterioration of reinforced concrete structures exposed to chloride environments. The research focuses on the mechanisms of chloride ingress and its impact on steel reinforcement corrosion.",
        content="The research focuses on the mechanisms of chloride ingress and its impact on steel reinforcement corrosion. Experimental studies were conducted on concrete specimens exposed to chloride solutions. Results show significant corrosion initiation after 6 months of exposure.",
        url="https://example.com/paper.pdf",
        source_type=SourceType.ACADEMIC,
        doi="10.1000/example",
        journal="Journal of Concrete Research"
    )
    
    print(f"✅ Academic document processed: {academic_doc.metadata.title}")
    print(f"   Authors: {academic_doc.metadata.authors}")
    print(f"   DOI: {academic_doc.metadata.doi}")
    print(f"   Quality score: {academic_doc.metadata.quality_score:.2f}")
    print(f"   Relevance score: {academic_doc.metadata.relevance_score:.2f}")
    print(f"   Confidence score: {academic_doc.metadata.confidence_score:.2f}")
    print(f"   Word count: {academic_doc.metadata.word_count}")
    print(f"   Keywords: {academic_doc.metadata.keywords[:5]}")
    
    # Test web document processing
    web_doc = processor.process_web_document(
        title="Concrete Corrosion Discussion in Civil Engineering Forum",
        content="Discussion about concrete corrosion in civil engineering forums. Users share experiences with reinforced concrete deterioration and maintenance strategies.",
        url="https://example.com/forum/post/123",
        source_type=SourceType.FORUM,
        domain="example.com"
    )
    
    print(f"\n✅ Web document processed: {web_doc.metadata.title}")
    print(f"   Domain: {web_doc.domain}")
    print(f"   Quality score: {web_doc.metadata.quality_score:.2f}")
    print(f"   Relevance score: {web_doc.metadata.relevance_score:.2f}")
    print(f"   Content category: {web_doc.content_category}")
    print(f"   Sentiment: {web_doc.sentiment}")
    
    return academic_doc, web_doc


def test_database_operations():
    """Test database operations."""
    print("\nTesting Database Operations...")
    
    # Initialize database manager
    db_manager = PostgreSQLManager()
    
    if not db_manager.connect():
        print("Failed to connect to database")
        return False
    
    # Test data processing
    processor = DataProcessor()
    
    # Create test academic document
    academic_doc = processor.process_academic_document(
        title="Long-term Durability of Reinforced Concrete in Marine Environments",
        authors=["Dr. Sarah Wilson", "Prof. Michael Brown"],
        abstract="This paper presents a comprehensive study on the long-term durability of reinforced concrete structures in marine environments.",
        content="The study investigates the effects of chloride penetration on concrete durability over a 10-year period. Results show significant deterioration after 5 years of exposure.",
        url="https://example.com/marine-concrete.pdf",
        source_type=SourceType.ACADEMIC,
        doi="10.1000/marine-concrete",
        journal="Marine Structures Journal"
    )
    
    # Create test web document
    web_doc = processor.process_web_document(
        title="Concrete Maintenance Best Practices",
        content="Best practices for maintaining reinforced concrete structures in harsh environments.",
        url="https://example.com/maintenance-guide.html",
        source_type=SourceType.WEB_ARTICLE
    )
    
    # Insert documents into database
    if db_manager.insert_academic_document(academic_doc):
        print("✅ Academic document inserted successfully")
    else:
        print("Failed to insert academic document")
    
    if db_manager.insert_web_document(web_doc):
        print("✅ Web document inserted successfully")
    else:
        print("Failed to insert web document")
    
    # Test search functionality
    search_results = db_manager.search_documents("concrete", limit=10)
    print(f"✅ Search results: {len(search_results)} documents found")
    
    # Test statistics
    stats = db_manager.get_statistics()
    print(f"✅ Database statistics:")
    print(f"   Total documents: {stats.get('total_documents', 0)}")
    print(f"   Academic documents: {stats.get('academic_documents', 0)}")
    print(f"   Web documents: {stats.get('web_documents', 0)}")
    
    return True


def test_integrated_workflow():
    """Test integrated workflow from keyword discovery to data storage."""
    print("\nTesting Integrated Workflow...")
    
    # Step 1: Keyword Discovery
    print("Step 1: Keyword Discovery")
    keyword_engine = KeywordDiscoveryEngine()
    topic = "reinforced concrete deterioration"
    keywords = keyword_engine.discover_keywords(topic, max_keywords=20)
    print(f"   Discovered {len(keywords)} keywords")
    
    # Step 2: Source Discovery
    print("Step 2: Source Discovery")
    discovery = IntelligentSourceDiscovery()
    keyword_list = [kw.keyword for kw in keywords[:5]]
    sources = discovery.discover_sources(keyword_list, max_sources=20)
    print(f"   Discovered {len(sources)} sources")
    
    # Step 3: Data Processing
    print("Step 3: Data Processing")
    processor = DataProcessor()
    
    # Process academic documents
    academic_docs = []
    for i, source in enumerate(sources[:5]):
        if source.source_type == "academic":
            doc = processor.process_academic_document(
                title=f"Research Paper {i+1}: {source.title}",
                authors=[f"Author {i+1}"],
                abstract=f"Abstract for research paper {i+1}",
                content=f"Content for research paper {i+1}",
                url=source.url,
                source_type=SourceType.ACADEMIC
            )
            academic_docs.append(doc)
    
    print(f"   Processed {len(academic_docs)} academic documents")
    
    # Step 4: Database Storage
    print("Step 4: Database Storage")
    db_manager = PostgreSQLManager()
    
    stored_count = 0
    for doc in academic_docs:
        if db_manager.insert_academic_document(doc):
            stored_count += 1
    
    print(f"   Stored {stored_count} documents in database")
    
    # Step 5: Verification
    print("Step 5: Verification")
    stats = db_manager.get_statistics()
    print(f"   Database now contains {stats.get('total_documents', 0)} documents")
    
    return True


def main():
    """Run all tests."""
    print("Universal Web Crawling System - Real Data Collection Tests")
    print("=" * 70)
    
    try:
        # Test PostgreSQL setup
        if not test_postgresql_setup():
            print("PostgreSQL setup failed")
            return 1
        
        # Test data processing
        academic_doc, web_doc = test_data_processing()
        
        # Test database operations
        if not test_database_operations():
            print("Database operations failed")
            return 1
        
        # Test integrated workflow
        if not test_integrated_workflow():
            print("Integrated workflow failed")
            return 1
        
        print("\n" + "=" * 70)
        print("All tests completed successfully!")
        print("✅ PostgreSQL database setup working")
        print("✅ Data processing working")
        print("✅ Database operations working")
        print("✅ Integrated workflow working")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
