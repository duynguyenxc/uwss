#!/usr/bin/env python3
"""
Test script for Data Processing Only

This script tests the data processing functionality without PostgreSQL.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from uwss.database.data_processor import DataProcessor
from uwss.database.data_models import SourceType, DocumentType, ContentType
from uwss.intelligence.keyword_discovery import KeywordDiscoveryEngine


def test_data_processing():
    """Test data processing functionality."""
    print("Testing Data Processing...")
    
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
    
    print(f"Academic document processed: {academic_doc.metadata.title}")
    print(f"  Authors: {academic_doc.metadata.authors}")
    print(f"  DOI: {academic_doc.metadata.doi}")
    print(f"  Quality score: {academic_doc.metadata.quality_score:.2f}")
    print(f"  Relevance score: {academic_doc.metadata.relevance_score:.2f}")
    print(f"  Confidence score: {academic_doc.metadata.confidence_score:.2f}")
    print(f"  Word count: {academic_doc.metadata.word_count}")
    print(f"  Keywords: {academic_doc.metadata.keywords[:5]}")
    print(f"  Subject areas: {academic_doc.subject_areas}")
    print(f"  Research fields: {academic_doc.research_fields}")
    print(f"  Methodologies: {academic_doc.methodologies}")
    
    # Test web document processing
    web_doc = processor.process_web_document(
        title="Concrete Corrosion Discussion in Civil Engineering Forum",
        content="Discussion about concrete corrosion in civil engineering forums. Users share experiences with reinforced concrete deterioration and maintenance strategies.",
        url="https://example.com/forum/post/123",
        source_type=SourceType.FORUM,
    )
    
    print(f"\nWeb document processed: {web_doc.metadata.title}")
    print(f"  Domain: {web_doc.domain}")
    print(f"  Quality score: {web_doc.metadata.quality_score:.2f}")
    print(f"  Relevance score: {web_doc.metadata.relevance_score:.2f}")
    print(f"  Content category: {web_doc.content_category}")
    print(f"  Sentiment: {web_doc.sentiment}")
    print(f"  Readability score: {web_doc.readability_score:.2f}")
    
    return academic_doc, web_doc


def test_keyword_integration():
    """Test keyword discovery integration."""
    print("\nTesting Keyword Discovery Integration...")
    
    # Initialize keyword discovery
    keyword_engine = KeywordDiscoveryEngine()
    topic = "reinforced concrete deterioration"
    keywords = keyword_engine.discover_keywords(topic, max_keywords=20)
    
    print(f"Discovered {len(keywords)} keywords for topic: '{topic}'")
    
    # Show top keywords
    for i, kw in enumerate(keywords[:10]):
        print(f"  {i+1}. {kw.keyword} ({kw.category}) - {kw.confidence:.2f}")
    
    return keywords


def test_integrated_workflow():
    """Test integrated workflow without database."""
    print("\nTesting Integrated Workflow...")
    
    # Step 1: Keyword Discovery
    print("Step 1: Keyword Discovery")
    keyword_engine = KeywordDiscoveryEngine()
    topic = "reinforced concrete deterioration"
    keywords = keyword_engine.discover_keywords(topic, max_keywords=20)
    print(f"  Discovered {len(keywords)} keywords")
    
    # Step 2: Data Processing
    print("Step 2: Data Processing")
    processor = DataProcessor()
    
    # Process multiple documents
    documents = []
    for i in range(3):
        doc = processor.process_academic_document(
            title=f"Research Paper {i+1}: Concrete Deterioration Study",
            authors=[f"Author {i+1}", f"Co-author {i+1}"],
            abstract=f"Abstract for research paper {i+1} on concrete deterioration",
            content=f"Content for research paper {i+1} focusing on reinforced concrete deterioration mechanisms",
            url=f"https://example.com/paper{i+1}.pdf",
            source_type=SourceType.ACADEMIC
        )
        documents.append(doc)
    
    print(f"  Processed {len(documents)} documents")
    
    # Show results
    for i, doc in enumerate(documents):
        print(f"  Document {i+1}:")
        print(f"    Title: {doc.metadata.title}")
        print(f"    Quality: {doc.metadata.quality_score:.2f}")
        print(f"    Relevance: {doc.metadata.relevance_score:.2f}")
        print(f"    Keywords: {len(doc.metadata.keywords)}")
    
    return documents


def main():
    """Run all tests."""
    print("Universal Web Crawling System - Data Processing Tests")
    print("=" * 60)
    
    try:
        # Test data processing
        academic_doc, web_doc = test_data_processing()
        
        # Test keyword integration
        keywords = test_keyword_integration()
        
        # Test integrated workflow
        documents = test_integrated_workflow()
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("Data processing working")
        print("Keyword discovery working")
        print("Integrated workflow working")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
