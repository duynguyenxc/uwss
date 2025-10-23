#!/usr/bin/env python3
"""
Test script for Academic Sources Integration

This script tests the academic sources integration functionality
for the Universal Content Discovery System.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from uwss.sources.academic_sources import AcademicSourceManager
from uwss.sources.web_sources import WebSourceManager
from uwss.sources.content_fetcher import ContentFetcher
from uwss.intelligence.keyword_discovery import KeywordDiscoveryEngine
from uwss.intelligence.relevance_scorer import RelevanceScorer


def test_academic_sources():
    """Test the academic sources integration."""
    print("Testing Academic Sources Integration...")
    
    # Initialize academic source manager
    academic_manager = AcademicSourceManager()
    
    # Test keywords from config.yaml
    keywords = [
        "reinforced concrete corrosion experiment",
        "long term durability concrete",
        "concrete chloride diffusion test",
        "reinforcement corrosion long duration exposure",
        "reinforced concrete half-cell potential experiment"
    ]
    
    # Search academic sources
    print(f"\nSearching academic sources for {len(keywords)} keywords...")
    academic_results = academic_manager.search_academic_sources(keywords, max_results=30)
    
    print(f"Found {len(academic_results)} academic results")
    
    # Show results by source
    academic_stats = academic_manager.get_source_stats(academic_results)
    print(f"\nAcademic Sources Statistics:")
    for source, count in academic_stats.items():
        print(f"  {source}: {count} results")
    
    # Show sample results
    print(f"\nSample Academic Results:")
    for i, result in enumerate(academic_results[:3]):
        print(f"\nResult {i+1}:")
        print(f"  Title: {result.title}")
        print(f"  Authors: {', '.join(result.authors[:2])}...")
        print(f"  Source: {result.source}")
        print(f"  Year: {result.year}")
        print(f"  Venue: {result.venue}")
        print(f"  Open Access: {result.open_access}")
        print(f"  Relevance Score: {result.relevance_score:.2f}")
    
    # Export results
    academic_manager.export_results(academic_results, Path("data/export/academic_results.json"))
    print(f"\nExported academic results to: data/export/academic_results.json")
    
    return academic_results


def test_web_sources():
    """Test the web sources integration."""
    print("\nTesting Web Sources Integration...")
    
    # Initialize web source manager
    web_manager = WebSourceManager()
    
    # Test keywords
    keywords = [
        "reinforced concrete deterioration",
        "concrete corrosion",
        "steel reinforcement"
    ]
    
    # Search web sources
    print(f"Searching web sources for {len(keywords)} keywords...")
    web_results = web_manager.search_web_sources(keywords, max_results=20)
    
    print(f"Found {len(web_results)} web results")
    
    # Show results by source
    web_stats = web_manager.get_source_stats(web_results)
    print(f"\nWeb Sources Statistics:")
    for source, count in web_stats.items():
        print(f"  {source}: {count} results")
    
    # Show sample results
    print(f"\nSample Web Results:")
    for i, result in enumerate(web_results[:3]):
        print(f"\nResult {i+1}:")
        print(f"  Title: {result.title}")
        print(f"  Author: {result.author}")
        print(f"  Source: {result.source}")
        print(f"  Type: {result.post_type}")
        print(f"  Upvotes: {result.upvotes}")
        print(f"  Comments: {result.comments}")
        print(f"  Relevance Score: {result.relevance_score:.2f}")
    
    # Export results
    web_manager.export_results(web_results, Path("data/export/web_results.json"))
    print(f"\nExported web results to: data/export/web_results.json")
    
    return web_results


def test_content_fetcher():
    """Test the content fetcher."""
    print("\nTesting Content Fetcher...")
    
    # Initialize content fetcher
    fetcher = ContentFetcher()
    
    # Test URLs (mock URLs for testing)
    test_urls = [
        "https://example.com/concrete-paper.pdf",
        "https://example.com/construction-article.html",
        "https://example.com/engineering-data.csv"
    ]
    
    # Fetch content
    print(f"Fetching content from {len(test_urls)} URLs...")
    fetch_results = []
    
    for url in test_urls:
        result = fetcher.fetch_content(url)
        fetch_results.append(result)
        print(f"  {url}: {'Success' if result.success else 'Failed'}")
    
    # Show statistics
    stats = fetcher.get_fetch_stats(fetch_results)
    print(f"\nFetch Statistics:")
    print(f"  Total: {stats['total']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Success Rate: {stats['success_rate']:.2%}")
    print(f"  Total Size: {stats['total_size']} bytes")
    print(f"  Average Size: {stats['avg_size']:.0f} bytes")
    print(f"  Average Time: {stats['avg_time']:.2f} seconds")
    
    # Export results
    fetcher.export_results(fetch_results, Path("data/export/fetch_results.json"))
    print(f"\nExported fetch results to: data/export/fetch_results.json")
    
    return fetch_results


def test_integrated_workflow():
    """Test the integrated workflow."""
    print("\nTesting Integrated Workflow...")
    
    # Step 1: Keyword Discovery
    print("Step 1: Keyword Discovery")
    keyword_engine = KeywordDiscoveryEngine()
    topic = "reinforced concrete deterioration"
    keywords = keyword_engine.discover_keywords(topic, max_keywords=20)
    print(f"  Discovered {len(keywords)} keywords")
    
    # Step 2: Academic Sources
    print("Step 2: Academic Sources Search")
    academic_manager = AcademicSourceManager()
    academic_results = academic_manager.search_academic_sources([kw.keyword for kw in keywords[:5]], max_results=15)
    print(f"  Found {len(academic_results)} academic results")
    
    # Step 3: Web Sources
    print("Step 3: Web Sources Search")
    web_manager = WebSourceManager()
    web_results = web_manager.search_web_sources([kw.keyword for kw in keywords[:5]], max_results=10)
    print(f"  Found {len(web_results)} web results")
    
    # Step 4: Relevance Scoring
    print("Step 4: Relevance Scoring")
    scorer = RelevanceScorer([kw.keyword for kw in keywords])
    
    # Score academic results
    academic_scored = []
    for result in academic_results:
        score = scorer.score_content(
            title=result.title,
            abstract=result.abstract,
            content=""
        )
        academic_scored.append((result, score))
    
    # Score web results
    web_scored = []
    for result in web_results:
        score = scorer.score_content(
            title=result.title,
            abstract=result.content,
            content=""
        )
        web_scored.append((result, score))
    
    # Sort by relevance score
    academic_scored.sort(key=lambda x: x[1].total_score, reverse=True)
    web_scored.sort(key=lambda x: x[1].total_score, reverse=True)
    
    print(f"\nTop Academic Results:")
    for i, (result, score) in enumerate(academic_scored[:3]):
        print(f"  {i+1}. {result.title}")
        print(f"     Relevance: {score.total_score:.3f}")
        print(f"     Source: {result.source}")
    
    print(f"\nTop Web Results:")
    for i, (result, score) in enumerate(web_scored[:3]):
        print(f"  {i+1}. {result.title}")
        print(f"     Relevance: {score.total_score:.3f}")
        print(f"     Source: {result.source}")
    
    return academic_scored, web_scored


def main():
    """Run all tests."""
    print("Universal Content Discovery System - Academic Sources Integration Tests")
    print("=" * 80)
    
    try:
        # Test academic sources
        academic_results = test_academic_sources()
        
        # Test web sources
        web_results = test_web_sources()
        
        # Test content fetcher
        fetch_results = test_content_fetcher()
        
        # Test integrated workflow
        academic_scored, web_scored = test_integrated_workflow()
        
        print("\n" + "=" * 80)
        print("All tests completed successfully!")
        print(f"Academic Results: {len(academic_results)}")
        print(f"Web Results: {len(web_results)}")
        print(f"Fetch Results: {len(fetch_results)}")
        print(f"Integrated Workflow: Academic {len(academic_scored)}, Web {len(web_scored)}")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
