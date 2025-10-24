#!/usr/bin/env python3
"""
Test script for Intelligent Source Discovery

This script tests the intelligent source discovery and crawling functionality
for the Universal Content Discovery System.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from uwss.discovery.intelligent_discovery import IntelligentSourceDiscovery
from uwss.discovery.intelligent_crawling import IntelligentCrawlingEngine
from uwss.discovery.source_classifier import SourceClassifier
from uwss.intelligence.keyword_discovery import KeywordDiscoveryEngine


def test_intelligent_source_discovery():
    """Test the intelligent source discovery engine."""
    print("Testing Intelligent Source Discovery Engine...")
    
    # Initialize discovery engine
    discovery = IntelligentSourceDiscovery()
    
    # Test keywords from config.yaml
    keywords = [
        "reinforced concrete corrosion experiment",
        "long term durability concrete",
        "concrete chloride diffusion test",
        "reinforcement corrosion long duration exposure",
        "reinforced concrete half-cell potential experiment"
    ]
    
    # Discover sources
    print(f"Discovering sources for {len(keywords)} keywords...")
    sources = discovery.discover_sources(keywords, max_sources=50)
    
    print(f"Discovered {len(sources)} sources")
    
    # Show statistics
    stats = discovery.get_discovery_stats(sources)
    print(f"\nSource Discovery Statistics:")
    for source_type, count in stats.items():
        print(f"  {source_type}: {count} sources")
    
    # Show sample sources
    print(f"\nSample Discovered Sources:")
    for i, source in enumerate(sources[:5]):
        print(f"\nSource {i+1}:")
        print(f"  URL: {source.url}")
        print(f"  Domain: {source.domain}")
        print(f"  Type: {source.source_type}")
        print(f"  Title: {source.title}")
        print(f"  Confidence: {source.confidence:.2f}")
        print(f"  Priority: {source.priority}")
        print(f"  Matched Keywords: {source.keywords_matched}")
    
    # Export sources
    discovery.export_sources(sources, Path("data/export/discovered_sources.json"))
    print(f"\nExported sources to: data/export/discovered_sources.json")
    
    return sources


def test_source_classifier():
    """Test the source classifier."""
    print("\nTesting Source Classifier...")
    
    # Initialize classifier
    classifier = SourceClassifier()
    
    # Test sources
    test_sources = [
        {
            'url': 'https://scholar.google.com/scholar?q=concrete',
            'title': 'Research on Concrete Deterioration',
            'description': 'Academic study on reinforced concrete deterioration'
        },
        {
            'url': 'https://www.fhwa.dot.gov/research',
            'title': 'FHWA Research on Concrete',
            'description': 'Federal Highway Administration research on concrete'
        },
        {
            'url': 'https://www.reddit.com/r/civilengineering',
            'title': 'Civil Engineering Discussion',
            'description': 'Discussion about concrete in civil engineering'
        },
        {
            'url': 'https://www.concrete.org/publications',
            'title': 'ACI Concrete Publications',
            'description': 'American Concrete Institute publications'
        },
        {
            'url': 'https://github.com/concrete-analysis',
            'title': 'Concrete Analysis Repository',
            'description': 'GitHub repository for concrete analysis tools'
        }
    ]
    
    # Classify sources
    print(f"Classifying {len(test_sources)} test sources...")
    results = classifier.classify_multiple_sources(test_sources)
    
    print(f"\nSource Classification Results:")
    for i, result in enumerate(results):
        print(f"\nSource {i+1}:")
        print(f"  URL: {test_sources[i]['url']}")
        print(f"  Type: {result.source_type}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Features: {len(result.features)} features")
        print(f"  Reasoning: {result.reasoning[:100]}...")
    
    # Show statistics
    stats = classifier.get_classification_stats(results)
    print(f"\nClassification Statistics:")
    for source_type, count in stats.items():
        print(f"  {source_type}: {count}")
    
    return results


def test_intelligent_crawling():
    """Test the intelligent crawling engine."""
    print("\nTesting Intelligent Crawling Engine...")
    
    # Initialize crawling engine
    crawler = IntelligentCrawlingEngine()
    
    # Create mock sources for testing
    class MockSource:
        def __init__(self, url, source_type, title):
            self.url = url
            self.source_type = source_type
            self.title = title
    
    mock_sources = [
        MockSource("https://example.com/academic-paper", "academic", "Academic Paper"),
        MockSource("https://example.com/government-report", "government", "Government Report"),
        MockSource("https://example.com/professional-article", "professional", "Professional Article"),
        MockSource("https://example.com/social-post", "social", "Social Post"),
        MockSource("https://example.com/technical-blog", "technical", "Technical Blog")
    ]
    
    # Crawl sources
    print(f"Crawling {len(mock_sources)} mock sources...")
    crawled_content = crawler.crawl_sources(mock_sources, max_content=10)
    
    print(f"Crawled {len(crawled_content)} content items")
    
    # Show statistics
    stats = crawler.get_crawling_stats(crawled_content)
    print(f"\nCrawling Statistics:")
    print(f"  Total: {stats['total']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Success Rate: {stats['success_rate']:.2%}")
    print(f"  Total Time: {stats['total_time']:.2f} seconds")
    print(f"  Average Time: {stats['avg_time']:.2f} seconds")
    
    # Show source types
    print(f"\nSource Types:")
    for source_type, count in stats['source_types'].items():
        print(f"  {source_type}: {count}")
    
    # Show sample content
    print(f"\nSample Crawled Content:")
    for i, content in enumerate(crawled_content[:3]):
        print(f"\nContent {i+1}:")
        print(f"  URL: {content.url}")
        print(f"  Title: {content.title}")
        print(f"  Type: {content.content_type}")
        print(f"  Source Type: {content.source_type}")
        print(f"  Success: {content.success}")
        print(f"  Crawl Time: {content.crawl_time:.2f} seconds")
        if content.error_message:
            print(f"  Error: {content.error_message}")
    
    # Export content
    crawler.export_content(crawled_content, Path("data/export/crawled_content.json"))
    print(f"\nExported content to: data/export/crawled_content.json")
    
    return crawled_content


def test_integrated_workflow():
    """Test the integrated workflow."""
    print("\nTesting Integrated Workflow...")
    
    # Step 1: Keyword Discovery
    print("Step 1: Keyword Discovery")
    keyword_engine = KeywordDiscoveryEngine()
    topic = "reinforced concrete deterioration"
    keywords = keyword_engine.discover_keywords(topic, max_keywords=20)
    print(f"  Discovered {len(keywords)} keywords")
    
    # Step 2: Source Discovery
    print("Step 2: Source Discovery")
    discovery = IntelligentSourceDiscovery()
    keyword_list = [kw.keyword for kw in keywords[:5]]
    sources = discovery.discover_sources(keyword_list, max_sources=30)
    print(f"  Discovered {len(sources)} sources")
    
    # Step 3: Source Classification
    print("Step 3: Source Classification")
    classifier = SourceClassifier()
    source_data = [{'url': s.url, 'title': s.title, 'description': s.description} for s in sources]
    classifications = classifier.classify_multiple_sources(source_data)
    print(f"  Classified {len(classifications)} sources")
    
    # Step 4: Intelligent Crawling
    print("Step 4: Intelligent Crawling")
    crawler = IntelligentCrawlingEngine()
    crawled_content = crawler.crawl_sources(sources, max_content=20)
    print(f"  Crawled {len(crawled_content)} content items")
    
    # Show workflow results
    print(f"\nIntegrated Workflow Results:")
    print(f"  Keywords: {len(keywords)}")
    print(f"  Sources: {len(sources)}")
    print(f"  Classifications: {len(classifications)}")
    print(f"  Content: {len(crawled_content)}")
    
    # Show source type distribution
    source_stats = discovery.get_discovery_stats(sources)
    print(f"\nSource Type Distribution:")
    for source_type, count in source_stats.items():
        print(f"  {source_type}: {count}")
    
    # Show classification distribution
    classification_stats = classifier.get_classification_stats(classifications)
    print(f"\nClassification Distribution:")
    for source_type, count in classification_stats.items():
        print(f"  {source_type}: {count}")
    
    # Show crawling statistics
    crawling_stats = crawler.get_crawling_stats(crawled_content)
    print(f"\nCrawling Statistics:")
    print(f"  Success Rate: {crawling_stats['success_rate']:.2%}")
    print(f"  Average Time: {crawling_stats['avg_time']:.2f} seconds")
    
    return keywords, sources, classifications, crawled_content


def main():
    """Run all tests."""
    print("Universal Content Discovery System - Intelligent Discovery Tests")
    print("=" * 80)
    
    try:
        # Test intelligent source discovery
        sources = test_intelligent_source_discovery()
        
        # Test source classifier
        classifications = test_source_classifier()
        
        # Test intelligent crawling
        crawled_content = test_intelligent_crawling()
        
        # Test integrated workflow
        keywords, sources, classifications, crawled_content = test_integrated_workflow()
        
        print("\n" + "=" * 80)
        print("All tests completed successfully!")
        print(f"Keywords: {len(keywords)}")
        print(f"Sources: {len(sources)}")
        print(f"Classifications: {len(classifications)}")
        print(f"Content: {len(crawled_content)}")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
