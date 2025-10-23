#!/usr/bin/env python3
"""
Test script for Keyword Discovery Engine

This script tests the intelligent keyword discovery functionality
for the Universal Content Discovery System.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from uwss.intelligence.keyword_discovery import KeywordDiscoveryEngine
from uwss.intelligence.relevance_scorer import RelevanceScorer
from uwss.intelligence.content_analyzer import ContentAnalyzer


def test_keyword_discovery():
    """Test the keyword discovery engine."""
    print("Testing Keyword Discovery Engine...")
    
    # Initialize engine
    engine = KeywordDiscoveryEngine()
    
    # Test with reinforced concrete deterioration
    topic = "reinforced concrete deterioration"
    keywords = engine.discover_keywords(topic, max_keywords=50)
    
    print(f"\nResults for topic: '{topic}'")
    print(f"Total keywords discovered: {len(keywords)}")
    
    # Show results by category
    categories = {}
    for kw in keywords:
        if kw.category not in categories:
            categories[kw.category] = []
        categories[kw.category].append(kw)
    
    for category, kws in categories.items():
        print(f"\n{category.upper()} Keywords ({len(kws)}):")
        for kw in kws[:10]:  # Show top 10
            print(f"  - {kw.keyword} (confidence: {kw.confidence:.2f})")
    
    # Show high confidence keywords
    high_conf = engine.get_high_confidence_keywords(0.8)
    print(f"\nHigh Confidence Keywords ({len(high_conf)}):")
    for kw in high_conf:
        print(f"  - {kw.keyword} ({kw.category}) - {kw.confidence:.2f}")
    
    # Export results
    output_path = Path("data/export/discovered_keywords.txt")
    engine.export_keywords(output_path)
    print(f"\nExported keywords to: {output_path}")
    
    return keywords


def test_relevance_scorer():
    """Test the relevance scorer."""
    print("\nTesting Relevance Scorer...")
    
    # Test keywords
    keywords = [
        "reinforced concrete", "deterioration", "corrosion", "durability",
        "steel reinforcement", "chloride attack", "carbonation"
    ]
    
    scorer = RelevanceScorer(keywords)
    
    # Test content samples
    test_cases = [
        {
            "title": "Reinforced Concrete Deterioration Due to Chloride Attack",
            "abstract": "This paper investigates the deterioration of reinforced concrete structures due to chloride-induced corrosion of steel reinforcement.",
            "content": "The study focuses on the mechanisms of chloride attack and its impact on concrete durability."
        },
        {
            "title": "Machine Learning Applications in Healthcare",
            "abstract": "This paper presents machine learning techniques for medical diagnosis.",
            "content": "The study uses neural networks to analyze medical images."
        },
        {
            "title": "Concrete Durability and Service Life Prediction",
            "abstract": "This research examines the long-term durability of concrete structures and methods for predicting service life.",
            "content": "The paper discusses various deterioration mechanisms including corrosion, carbonation, and freeze-thaw cycles."
        }
    ]
    
    for i, test_content in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Title: {test_content['title']}")
        
        score = scorer.score_content(**test_content)
        
        print(f"  Relevance Score: {score.total_score:.3f}")
        print(f"  Confidence: {score.confidence:.3f}")
        print(f"  Matched Keywords: {score.matched_keywords}")
        print(f"  Relevance Level: {scorer.get_relevance_level(score)}")
        print(f"  Is Relevant: {scorer.is_relevant(score, 0.6)}")


def test_content_analyzer():
    """Test the content analyzer."""
    print("\nTesting Content Analyzer...")
    
    analyzer = ContentAnalyzer()
    
    # Test with sample HTML content
    test_content = """
    <html>
    <head>
        <title>Reinforced Concrete Deterioration Study</title>
        <meta name="description" content="A comprehensive study on reinforced concrete deterioration">
        <meta name="keywords" content="concrete, deterioration, corrosion, durability">
    </head>
    <body>
        <h1>Introduction</h1>
        <p>This paper investigates the deterioration of reinforced concrete structures due to various environmental factors.</p>
        <h2>Methodology</h2>
        <p>The study uses advanced analytical techniques to assess concrete degradation mechanisms including chloride attack, carbonation, and freeze-thaw cycles.</p>
        <h2>Results</h2>
        <p>The research shows that steel reinforcement corrosion is the primary cause of concrete deterioration in marine environments.</p>
    </body>
    </html>
    """
    
    analysis = analyzer.analyze_content(content=test_content)
    
    print(f"Content Type: {analysis.content_type}")
    print(f"File Extension: {analysis.file_extension}")
    print(f"MIME Type: {analysis.mime_type}")
    print(f"Is Text: {analysis.is_text}")
    print(f"Is Structured: {analysis.is_structured}")
    print(f"Language: {analysis.language}")
    print(f"Word Count: {analysis.word_count}")
    print(f"Quality Score: {analysis.quality_score:.2f}")
    print(f"Processing Strategy: {analyzer.get_processing_strategy(analysis)}")
    print(f"Is Processable: {analyzer.is_processable(analysis)}")
    
    # Show extracted metadata
    print(f"\nExtracted Metadata:")
    for key, value in analysis.metadata.items():
        print(f"  {key}: {value}")


def main():
    """Run all tests."""
    print("Universal Content Discovery System - Intelligence Module Tests")
    print("=" * 70)
    
    try:
        # Test keyword discovery
        keywords = test_keyword_discovery()
        
        # Test relevance scorer
        test_relevance_scorer()
        
        # Test content analyzer
        test_content_analyzer()
        
        print("\nAll tests completed successfully!")
        print(f"Discovered {len(keywords)} keywords for reinforced concrete deterioration")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
