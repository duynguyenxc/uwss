"""
Relevance Scoring Engine

This module provides intelligent relevance scoring for content
based on keyword matching, semantic analysis, and content quality.
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RelevanceScore:
    """Represents a relevance score with breakdown."""
    total_score: float  # 0.0 to 1.0
    keyword_score: float
    title_score: float
    abstract_score: float
    content_score: float
    quality_score: float
    matched_keywords: List[str]
    confidence: float


class RelevanceScorer:
    """
    Intelligent relevance scorer that evaluates content relevance
    based on multiple criteria.
    """
    
    def __init__(self, keywords: List[str], weights: Optional[Dict[str, float]] = None):
        """
        Initialize the relevance scorer.
        
        Args:
            keywords: List of keywords to match against
            weights: Custom weights for scoring components
        """
        self.keywords = [kw.lower() for kw in keywords]
        self.weights = weights or {
            'keyword': 0.3,
            'title': 0.4,
            'abstract': 0.25,
            'content': 0.05
        }
        
        # Compile keyword patterns for efficient matching
        self.keyword_patterns = self._compile_keyword_patterns()
    
    def _compile_keyword_patterns(self) -> List[re.Pattern]:
        """Compile keyword patterns for efficient matching."""
        patterns = []
        for keyword in self.keywords:
            # Create case-insensitive pattern
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            patterns.append(pattern)
        return patterns
    
    def score_content(self, title: str = "", abstract: str = "", 
                     content: str = "", metadata: Optional[Dict] = None) -> RelevanceScore:
        """
        Score content relevance based on multiple criteria.
        
        Args:
            title: Document title
            abstract: Document abstract
            content: Full content text
            metadata: Additional metadata
            
        Returns:
            RelevanceScore object with detailed breakdown
        """
        # Calculate individual scores
        keyword_score = self._calculate_keyword_score(title, abstract, content)
        title_score = self._calculate_title_score(title)
        abstract_score = self._calculate_abstract_score(abstract)
        content_score = self._calculate_content_score(content)
        quality_score = self._calculate_quality_score(title, abstract, content, metadata)
        
        # Calculate weighted total score
        total_score = (
            keyword_score * self.weights['keyword'] +
            title_score * self.weights['title'] +
            abstract_score * self.weights['abstract'] +
            content_score * self.weights['content']
        )
        
        # Find matched keywords
        matched_keywords = self._find_matched_keywords(title, abstract, content)
        
        # Calculate confidence based on multiple factors
        confidence = self._calculate_confidence(
            total_score, matched_keywords, quality_score
        )
        
        return RelevanceScore(
            total_score=total_score,
            keyword_score=keyword_score,
            title_score=title_score,
            abstract_score=abstract_score,
            content_score=content_score,
            quality_score=quality_score,
            matched_keywords=matched_keywords,
            confidence=confidence
        )
    
    def _calculate_keyword_score(self, title: str, abstract: str, content: str) -> float:
        """Calculate keyword matching score."""
        text = f"{title} {abstract} {content}".lower()
        
        matches = 0
        for pattern in self.keyword_patterns:
            if pattern.search(text):
                matches += 1
        
        # Normalize by number of keywords
        if not self.keywords:
            return 0.0
        
        return min(matches / len(self.keywords), 1.0)
    
    def _calculate_title_score(self, title: str) -> float:
        """Calculate title relevance score."""
        if not title:
            return 0.0
        
        title_lower = title.lower()
        matches = 0
        
        for keyword in self.keywords:
            if keyword in title_lower:
                matches += 1
        
        # Higher score for more keyword matches in title
        return min(matches / len(self.keywords), 1.0) if self.keywords else 0.0
    
    def _calculate_abstract_score(self, abstract: str) -> float:
        """Calculate abstract relevance score."""
        if not abstract:
            return 0.0
        
        abstract_lower = abstract.lower()
        matches = 0
        
        for keyword in self.keywords:
            if keyword in abstract_lower:
                matches += 1
        
        # Normalize by abstract length and keyword count
        if not self.keywords:
            return 0.0
        
        base_score = min(matches / len(self.keywords), 1.0)
        
        # Boost score for high keyword density
        keyword_density = matches / max(len(abstract.split()), 1)
        density_boost = min(keyword_density * 0.5, 0.3)
        
        return min(base_score + density_boost, 1.0)
    
    def _calculate_content_score(self, content: str) -> float:
        """Calculate content relevance score."""
        if not content:
            return 0.0
        
        content_lower = content.lower()
        matches = 0
        
        for keyword in self.keywords:
            if keyword in content_lower:
                matches += 1
        
        if not self.keywords:
            return 0.0
        
        # Lower weight for content since it's less reliable
        base_score = min(matches / len(self.keywords), 1.0)
        
        # Boost for keyword frequency in content
        total_keywords = sum(content_lower.count(keyword) for keyword in self.keywords)
        frequency_boost = min(total_keywords / max(len(content.split()), 1) * 0.1, 0.2)
        
        return min(base_score + frequency_boost, 1.0)
    
    def _calculate_quality_score(self, title: str, abstract: str, 
                                content: str, metadata: Optional[Dict]) -> float:
        """Calculate content quality score."""
        quality_factors = []
        
        # Title quality
        if title and len(title) > 10:
            quality_factors.append(0.8)
        elif title:
            quality_factors.append(0.4)
        else:
            quality_factors.append(0.0)
        
        # Abstract quality
        if abstract and len(abstract) > 50:
            quality_factors.append(0.9)
        elif abstract and len(abstract) > 20:
            quality_factors.append(0.6)
        elif abstract:
            quality_factors.append(0.3)
        else:
            quality_factors.append(0.0)
        
        # Content quality
        if content and len(content) > 100:
            quality_factors.append(0.8)
        elif content and len(content) > 50:
            quality_factors.append(0.5)
        elif content:
            quality_factors.append(0.2)
        else:
            quality_factors.append(0.0)
        
        # Metadata quality
        if metadata:
            metadata_score = 0.0
            if metadata.get('authors'):
                metadata_score += 0.3
            if metadata.get('year'):
                metadata_score += 0.2
            if metadata.get('venue'):
                metadata_score += 0.2
            if metadata.get('doi'):
                metadata_score += 0.3
            quality_factors.append(metadata_score)
        
        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
    
    def _find_matched_keywords(self, title: str, abstract: str, content: str) -> List[str]:
        """Find which keywords were matched."""
        text = f"{title} {abstract} {content}".lower()
        matched = []
        
        for keyword in self.keywords:
            if keyword in text:
                matched.append(keyword)
        
        return matched
    
    def _calculate_confidence(self, total_score: float, matched_keywords: List[str], 
                            quality_score: float) -> float:
        """Calculate confidence in the relevance score."""
        # Base confidence from total score
        confidence = total_score
        
        # Boost for multiple keyword matches
        if len(matched_keywords) > 1:
            confidence += 0.1 * min(len(matched_keywords), 5)
        
        # Boost for high quality content
        confidence += quality_score * 0.2
        
        # Penalty for very low scores
        if total_score < 0.2:
            confidence *= 0.5
        
        return min(confidence, 1.0)
    
    def is_relevant(self, score: RelevanceScore, threshold: float = 0.6) -> bool:
        """Check if content is relevant based on threshold."""
        return score.total_score >= threshold
    
    def get_relevance_level(self, score: RelevanceScore) -> str:
        """Get human-readable relevance level."""
        if score.total_score >= 0.9:
            return "Very High"
        elif score.total_score >= 0.8:
            return "High"
        elif score.total_score >= 0.6:
            return "Medium"
        elif score.total_score >= 0.4:
            return "Low"
        else:
            return "Very Low"


def main():
    """Test the relevance scorer."""
    # Test keywords
    keywords = [
        "reinforced concrete", "deterioration", "corrosion", "durability",
        "steel reinforcement", "chloride attack", "carbonation"
    ]
    
    scorer = RelevanceScorer(keywords)
    
    # Test content
    test_content = {
        "title": "Reinforced Concrete Deterioration Due to Chloride Attack",
        "abstract": "This paper investigates the deterioration of reinforced concrete structures due to chloride-induced corrosion of steel reinforcement.",
        "content": "The study focuses on the mechanisms of chloride attack and its impact on concrete durability."
    }
    
    score = scorer.score_content(**test_content)
    
    print(f"Relevance Score: {score.total_score:.3f}")
    print(f"Confidence: {score.confidence:.3f}")
    print(f"Matched Keywords: {score.matched_keywords}")
    print(f"Relevance Level: {scorer.get_relevance_level(score)}")


if __name__ == "__main__":
    main()
