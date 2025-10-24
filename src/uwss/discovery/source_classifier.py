"""
Source Classifier

This module provides intelligent source classification capabilities
for automatically categorizing discovered sources.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Represents the result of source classification."""
    source_type: str
    confidence: float
    features: List[str]
    reasoning: str


class SourceClassifier:
    """
    Intelligent source classifier that automatically categorizes
    discovered sources into appropriate types.
    
    Technologies used:
    - Pattern matching: Regular expressions for domain analysis
    - Feature extraction: URL, title, description analysis
    - Confidence scoring: Statistical confidence in classification
    - Machine learning: Future enhancement for better accuracy
    """
    
    def __init__(self):
        """Initialize the source classifier."""
        
        # Academic source patterns
        self.academic_patterns = {
            'domains': [
                r'\.edu$', r'\.ac\.', r'university', r'college', r'institute',
                r'scholar', r'research', r'journal', r'conference', r'proceedings'
            ],
            'keywords': [
                'university', 'college', 'institute', 'research', 'study',
                'journal', 'conference', 'proceedings', 'academic', 'scholar',
                'paper', 'thesis', 'dissertation', 'publication'
            ],
            'publishers': [
                'ieee', 'acm', 'springer', 'elsevier', 'wiley', 'taylor',
                'pubmed', 'crossref', 'arxiv', 'researchgate', 'academia'
            ]
        }
        
        # Government source patterns
        self.government_patterns = {
            'domains': [
                r'\.gov$', r'\.mil$', r'federal', r'government', r'national',
                r'department', r'agency', r'administration', r'bureau'
            ],
            'keywords': [
                'government', 'federal', 'national', 'department', 'agency',
                'administration', 'bureau', 'public', 'official', 'regulation',
                'policy', 'standard', 'guideline', 'report'
            ],
            'agencies': [
                'fhwa', 'dot', 'nist', 'nsf', 'epa', 'usda', 'doe', 'dhs',
                'doi', 'commerce', 'transportation', 'highway'
            ]
        }
        
        # Professional source patterns
        self.professional_patterns = {
            'domains': [
                r'\.org$', r'association', r'society', r'institute', r'foundation'
            ],
            'keywords': [
                'association', 'society', 'institute', 'foundation', 'professional',
                'engineering', 'construction', 'concrete', 'steel', 'reinforcement',
                'building', 'infrastructure', 'civil', 'structural'
            ],
            'organizations': [
                'aci', 'asce', 'pci', 'precast', 'post-tensioning', 'concrete',
                'steel', 'reinforcement', 'building', 'construction'
            ]
        }
        
        # Social source patterns
        self.social_patterns = {
            'domains': [
                r'reddit', r'linkedin', r'twitter', r'facebook', r'youtube',
                r'github', r'stackoverflow', r'quora', r'medium', r'blog'
            ],
            'keywords': [
                'discussion', 'forum', 'post', 'comment', 'reply', 'thread',
                'social', 'community', 'network', 'professional', 'career'
            ],
            'platforms': [
                'reddit', 'linkedin', 'twitter', 'facebook', 'youtube',
                'github', 'stackoverflow', 'quora', 'medium'
            ]
        }
        
        # Technical source patterns
        self.technical_patterns = {
            'domains': [
                r'\.com$', r'\.net$', r'\.io$', r'blog', r'news', r'article'
            ],
            'keywords': [
                'technical', 'engineering', 'construction', 'building',
                'materials', 'concrete', 'steel', 'reinforcement', 'design',
                'analysis', 'calculation', 'method', 'technique'
            ],
            'content_types': [
                'blog', 'news', 'article', 'tutorial', 'guide', 'manual',
                'documentation', 'specification', 'standard'
            ]
        }
    
    def classify_source(self, url: str, title: str = "", description: str = "") -> ClassificationResult:
        """
        Classify a source based on URL, title, and description.
        
        Args:
            url: Source URL
            title: Source title
            description: Source description
            
        Returns:
            ClassificationResult with classification details
        """
        # Extract features
        features = self._extract_features(url, title, description)
        
        # Calculate scores for each source type
        scores = {
            'academic': self._calculate_academic_score(features),
            'government': self._calculate_government_score(features),
            'professional': self._calculate_professional_score(features),
            'social': self._calculate_social_score(features),
            'technical': self._calculate_technical_score(features)
        }
        
        # Find best classification
        best_type = max(scores.items(), key=lambda x: x[1])
        source_type = best_type[0]
        confidence = best_type[1]
        
        # Generate reasoning
        reasoning = self._generate_reasoning(features, source_type, confidence)
        
        return ClassificationResult(
            source_type=source_type,
            confidence=confidence,
            features=features,
            reasoning=reasoning
        )
    
    def _extract_features(self, url: str, title: str, description: str) -> List[str]:
        """Extract features from URL, title, and description."""
        features = []
        
        # Extract domain features
        domain = urlparse(url).netloc.lower()
        features.append(f"domain:{domain}")
        
        # Extract path features
        path = urlparse(url).path.lower()
        features.append(f"path:{path}")
        
        # Extract URL keywords
        url_text = url.lower()
        for keyword in self._extract_keywords(url_text):
            features.append(f"url_keyword:{keyword}")
        
        # Extract title keywords
        title_text = title.lower()
        for keyword in self._extract_keywords(title_text):
            features.append(f"title_keyword:{keyword}")
        
        # Extract description keywords
        desc_text = description.lower()
        for keyword in self._extract_keywords(desc_text):
            features.append(f"desc_keyword:{keyword}")
        
        return features
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""
        # Simple keyword extraction (in a real implementation, use NLP)
        words = re.findall(r'\b\w+\b', text)
        
        # Filter for relevant keywords
        relevant_keywords = []
        for word in words:
            if len(word) > 3 and word.isalpha():
                relevant_keywords.append(word)
        
        return relevant_keywords
    
    def _calculate_academic_score(self, features: List[str]) -> float:
        """Calculate academic classification score."""
        score = 0.0
        
        # Check domain patterns
        for pattern in self.academic_patterns['domains']:
            for feature in features:
                if re.search(pattern, feature):
                    score += 0.3
                    break
        
        # Check keyword patterns
        for keyword in self.academic_patterns['keywords']:
            for feature in features:
                if keyword in feature:
                    score += 0.2
        
        # Check publisher patterns
        for publisher in self.academic_patterns['publishers']:
            for feature in features:
                if publisher in feature:
                    score += 0.4
        
        return min(score, 1.0)
    
    def _calculate_government_score(self, features: List[str]) -> float:
        """Calculate government classification score."""
        score = 0.0
        
        # Check domain patterns
        for pattern in self.government_patterns['domains']:
            for feature in features:
                if re.search(pattern, feature):
                    score += 0.4
                    break
        
        # Check keyword patterns
        for keyword in self.government_patterns['keywords']:
            for feature in features:
                if keyword in feature:
                    score += 0.2
        
        # Check agency patterns
        for agency in self.government_patterns['agencies']:
            for feature in features:
                if agency in feature:
                    score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_professional_score(self, features: List[str]) -> float:
        """Calculate professional classification score."""
        score = 0.0
        
        # Check domain patterns
        for pattern in self.professional_patterns['domains']:
            for feature in features:
                if re.search(pattern, feature):
                    score += 0.3
                    break
        
        # Check keyword patterns
        for keyword in self.professional_patterns['keywords']:
            for feature in features:
                if keyword in feature:
                    score += 0.2
        
        # Check organization patterns
        for org in self.professional_patterns['organizations']:
            for feature in features:
                if org in feature:
                    score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_social_score(self, features: List[str]) -> float:
        """Calculate social classification score."""
        score = 0.0
        
        # Check domain patterns
        for pattern in self.social_patterns['domains']:
            for feature in features:
                if re.search(pattern, feature):
                    score += 0.4
                    break
        
        # Check keyword patterns
        for keyword in self.social_patterns['keywords']:
            for feature in features:
                if keyword in feature:
                    score += 0.2
        
        # Check platform patterns
        for platform in self.social_patterns['platforms']:
            for feature in features:
                if platform in feature:
                    score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_technical_score(self, features: List[str]) -> float:
        """Calculate technical classification score."""
        score = 0.0
        
        # Check domain patterns
        for pattern in self.technical_patterns['domains']:
            for feature in features:
                if re.search(pattern, feature):
                    score += 0.2
                    break
        
        # Check keyword patterns
        for keyword in self.technical_patterns['keywords']:
            for feature in features:
                if keyword in feature:
                    score += 0.3
        
        # Check content type patterns
        for content_type in self.technical_patterns['content_types']:
            for feature in features:
                if content_type in feature:
                    score += 0.2
        
        return min(score, 1.0)
    
    def _generate_reasoning(self, features: List[str], source_type: str, confidence: float) -> str:
        """Generate reasoning for classification."""
        reasoning_parts = []
        
        if source_type == 'academic':
            reasoning_parts.append("Academic source detected based on:")
            for feature in features:
                if 'domain:' in feature and any(pattern in feature for pattern in self.academic_patterns['domains']):
                    reasoning_parts.append(f"- Academic domain: {feature}")
                if 'url_keyword:' in feature and any(keyword in feature for keyword in self.academic_patterns['keywords']):
                    reasoning_parts.append(f"- Academic keyword: {feature}")
        
        elif source_type == 'government':
            reasoning_parts.append("Government source detected based on:")
            for feature in features:
                if 'domain:' in feature and any(pattern in feature for pattern in self.government_patterns['domains']):
                    reasoning_parts.append(f"- Government domain: {feature}")
                if 'url_keyword:' in feature and any(keyword in feature for keyword in self.government_patterns['keywords']):
                    reasoning_parts.append(f"- Government keyword: {feature}")
        
        elif source_type == 'professional':
            reasoning_parts.append("Professional source detected based on:")
            for feature in features:
                if 'domain:' in feature and any(pattern in feature for pattern in self.professional_patterns['domains']):
                    reasoning_parts.append(f"- Professional domain: {feature}")
                if 'url_keyword:' in feature and any(keyword in feature for keyword in self.professional_patterns['keywords']):
                    reasoning_parts.append(f"- Professional keyword: {feature}")
        
        elif source_type == 'social':
            reasoning_parts.append("Social source detected based on:")
            for feature in features:
                if 'domain:' in feature and any(pattern in feature for pattern in self.social_patterns['domains']):
                    reasoning_parts.append(f"- Social domain: {feature}")
                if 'url_keyword:' in feature and any(keyword in feature for keyword in self.social_patterns['keywords']):
                    reasoning_parts.append(f"- Social keyword: {feature}")
        
        elif source_type == 'technical':
            reasoning_parts.append("Technical source detected based on:")
            for feature in features:
                if 'domain:' in feature and any(pattern in feature for pattern in self.technical_patterns['domains']):
                    reasoning_parts.append(f"- Technical domain: {feature}")
                if 'url_keyword:' in feature and any(keyword in feature for keyword in self.technical_patterns['keywords']):
                    reasoning_parts.append(f"- Technical keyword: {feature}")
        
        reasoning_parts.append(f"Confidence: {confidence:.2f}")
        
        return "\n".join(reasoning_parts)
    
    def classify_multiple_sources(self, sources: List[Dict]) -> List[ClassificationResult]:
        """Classify multiple sources."""
        results = []
        
        for source in sources:
            url = source.get('url', '')
            title = source.get('title', '')
            description = source.get('description', '')
            
            result = self.classify_source(url, title, description)
            results.append(result)
        
        return results
    
    def get_classification_stats(self, results: List[ClassificationResult]) -> Dict[str, int]:
        """Get statistics about classifications."""
        stats = {}
        for result in results:
            source_type = result.source_type
            stats[source_type] = stats.get(source_type, 0) + 1
        return stats


def main():
    """Test the source classifier."""
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
        }
    ]
    
    # Classify sources
    results = classifier.classify_multiple_sources(test_sources)
    
    print("Source Classification Results:")
    for i, result in enumerate(results):
        print(f"\nSource {i+1}:")
        print(f"  Type: {result.source_type}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Reasoning: {result.reasoning}")
    
    # Show statistics
    stats = classifier.get_classification_stats(results)
    print(f"\nClassification Statistics:")
    for source_type, count in stats.items():
        print(f"  {source_type}: {count}")


if __name__ == "__main__":
    main()
