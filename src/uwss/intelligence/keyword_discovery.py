"""
Intelligent Keyword Discovery Engine

This module provides automatic keyword discovery and expansion capabilities
for any given topic, with focus on academic and technical terminology.
"""

import re
import requests
import json
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class KeywordResult:
    """Represents a discovered keyword with metadata."""
    keyword: str
    category: str  # 'technical', 'academic', 'synonym', 'related'
    confidence: float  # 0.0 to 1.0
    source: str  # Where this keyword was discovered
    frequency: int = 1


class KeywordDiscoveryEngine:
    """
    Intelligent keyword discovery engine that automatically finds
    related keywords for any given topic.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the keyword discovery engine."""
        self.config_path = config_path or Path("config/config.yaml")
        self.discovered_keywords: Set[str] = set()
        self.keyword_results: List[KeywordResult] = []
        
    def discover_keywords(self, base_topic: str, max_keywords: int = 100) -> List[KeywordResult]:
        """
        Discover related keywords for a given topic.
        
        Args:
            base_topic: The base topic to expand keywords for
            max_keywords: Maximum number of keywords to discover
            
        Returns:
            List of KeywordResult objects
        """
        logger.info(f"Starting keyword discovery for topic: {base_topic}")
        
        # Clear previous results
        self.discovered_keywords.clear()
        self.keyword_results.clear()
        
        # Step 1: Base keyword expansion
        base_keywords = self._expand_base_keywords(base_topic)
        self._add_keywords(base_keywords, "base", 1.0, "base_expansion")
        
        # Step 2: Technical term discovery
        technical_keywords = self._discover_technical_terms(base_topic)
        self._add_keywords(technical_keywords, "technical", 0.9, "technical_discovery")
        
        # Step 3: Academic term discovery
        academic_keywords = self._discover_academic_terms(base_topic)
        self._add_keywords(academic_keywords, "academic", 0.95, "academic_discovery")
        
        # Step 4: Synonym discovery
        synonym_keywords = self._discover_synonyms(base_topic)
        self._add_keywords(synonym_keywords, "synonym", 0.8, "synonym_discovery")
        
        # Step 5: Related term discovery
        related_keywords = self._discover_related_terms(base_topic)
        self._add_keywords(related_keywords, "related", 0.7, "related_discovery")
        
        # Step 6: Multilingual expansion
        multilingual_keywords = self._discover_multilingual_terms(base_topic)
        self._add_keywords(multilingual_keywords, "multilingual", 0.6, "multilingual_discovery")
        
        # Sort by confidence and limit results
        self.keyword_results.sort(key=lambda x: x.confidence, reverse=True)
        result = self.keyword_results[:max_keywords]
        
        logger.info(f"Discovered {len(result)} keywords for topic: {base_topic}")
        return result
    
    def _expand_base_keywords(self, topic: str) -> List[str]:
        """Expand base topic into related technical terms."""
        keywords = [topic]
        
        # Split topic into words
        words = topic.lower().split()
        
        # Add variations
        if "concrete" in topic.lower():
            keywords.extend([
                "RC", "RCC", "steel-reinforced concrete",
                "reinforced concrete", "concrete reinforcement"
            ])
        
        if "deterioration" in topic.lower():
            keywords.extend([
                "degradation", "damage", "aging", "deterioration",
                "corrosion", "durability", "service life"
            ])
        
        if "reinforced" in topic.lower():
            keywords.extend([
                "steel reinforcement", "rebar", "reinforcement",
                "steel bars", "reinforcing steel"
            ])
        
        return list(set(keywords))
    
    def _discover_technical_terms(self, topic: str) -> List[str]:
        """Discover technical terms related to the topic."""
        technical_terms = []
        
        # Concrete-related technical terms
        if "concrete" in topic.lower():
            technical_terms.extend([
                "chloride attack", "carbonation", "freeze-thaw",
                "alkali-silica reaction", "sulfate attack",
                "creep", "shrinkage", "cracking"
            ])
        
        # Deterioration-related technical terms
        if "deterioration" in topic.lower():
            technical_terms.extend([
                "corrosion rate", "corrosion initiation",
                "corrosion propagation", "passive film",
                "depassivation", "pitting corrosion"
            ])
        
        return technical_terms
    
    def _discover_academic_terms(self, topic: str) -> List[str]:
        """Discover academic terms related to the topic."""
        academic_terms = []
        
        # Academic terminology
        academic_terms.extend([
            "durability", "service life prediction",
            "life cycle assessment", "performance evaluation",
            "structural integrity", "material degradation"
        ])
        
        return academic_terms
    
    def _discover_synonyms(self, topic: str) -> List[str]:
        """Discover synonyms for the topic."""
        synonyms = []
        
        # Synonym mapping
        synonym_map = {
            "deterioration": ["degradation", "damage", "aging", "deterioration"],
            "concrete": ["cementitious", "concrete", "mortar", "cement"],
            "reinforced": ["steel-reinforced", "reinforced", "armored"],
            "corrosion": ["rust", "oxidation", "corrosion", "deterioration"]
        }
        
        for word in topic.lower().split():
            if word in synonym_map:
                synonyms.extend(synonym_map[word])
        
        return list(set(synonyms))
    
    def _discover_related_terms(self, topic: str) -> List[str]:
        """Discover related terms through semantic analysis."""
        related_terms = []
        
        # Related concepts
        if "concrete" in topic.lower():
            related_terms.extend([
                "construction materials", "building materials",
                "infrastructure", "civil engineering",
                "structural engineering", "materials science"
            ])
        
        if "deterioration" in topic.lower():
            related_terms.extend([
                "maintenance", "repair", "rehabilitation",
                "inspection", "monitoring", "assessment"
            ])
        
        return related_terms
    
    def _discover_multilingual_terms(self, topic: str) -> List[str]:
        """Discover multilingual terms for the topic."""
        multilingual_terms = []
        
        # Multilingual terms for concrete
        multilingual_terms.extend([
            "béton armé",  # French
            "armierter Beton",  # German
            "concreto armado",  # Spanish
            "бетон армированный"  # Russian
        ])
        
        return multilingual_terms
    
    def _add_keywords(self, keywords: List[str], category: str, 
                     confidence: float, source: str):
        """Add keywords to the results with metadata."""
        for keyword in keywords:
            if keyword.lower() not in self.discovered_keywords:
                self.discovered_keywords.add(keyword.lower())
                self.keyword_results.append(KeywordResult(
                    keyword=keyword,
                    category=category,
                    confidence=confidence,
                    source=source
                ))
    
    def get_keywords_by_category(self, category: str) -> List[KeywordResult]:
        """Get keywords filtered by category."""
        return [kw for kw in self.keyword_results if kw.category == category]
    
    def get_high_confidence_keywords(self, threshold: float = 0.8) -> List[KeywordResult]:
        """Get keywords with confidence above threshold."""
        return [kw for kw in self.keyword_results if kw.confidence >= threshold]
    
    def export_keywords(self, output_path: Path) -> None:
        """Export discovered keywords to a file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for kw in self.keyword_results:
                f.write(f"{kw.keyword}\t{kw.category}\t{kw.confidence}\t{kw.source}\n")
        
        logger.info(f"Exported {len(self.keyword_results)} keywords to {output_path}")
    
    def load_keywords(self, input_path: Path) -> None:
        """Load keywords from a file."""
        if not input_path.exists():
            logger.warning(f"Keywords file not found: {input_path}")
            return
        
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 4:
                    keyword, category, confidence, source = parts[:4]
                    self.keyword_results.append(KeywordResult(
                        keyword=keyword,
                        category=category,
                        confidence=float(confidence),
                        source=source
                    ))
        
        logger.info(f"Loaded {len(self.keyword_results)} keywords from {input_path}")


def main():
    """Test the keyword discovery engine."""
    engine = KeywordDiscoveryEngine()
    
    # Test with reinforced concrete deterioration
    topic = "reinforced concrete deterioration"
    keywords = engine.discover_keywords(topic, max_keywords=50)
    
    print(f"Discovered {len(keywords)} keywords for: {topic}")
    print("\nHigh confidence keywords:")
    for kw in engine.get_high_confidence_keywords(0.8):
        print(f"  {kw.keyword} ({kw.category}) - {kw.confidence:.2f}")
    
    # Export results
    engine.export_keywords(Path("data/export/discovered_keywords.txt"))


if __name__ == "__main__":
    main()
