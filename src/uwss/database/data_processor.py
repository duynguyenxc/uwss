"""
Data Processor for Universal Web Crawling System

This module provides data processing capabilities for academic and web documents
including content extraction, metadata standardization, and quality control.
"""

import hashlib
import mimetypes
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json
import re

from .data_models import (
    AcademicDocument, WebDocument, Metadata, 
    DocumentType, SourceType, ContentType,
    create_academic_document, create_web_document
)

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Data processor for academic and web documents.
    
    Technologies used:
    - hashlib: Content integrity verification
    - mimetypes: Content type detection
    - Regular expressions: Text processing and extraction
    - JSON processing: Metadata serialization
    - File handling: Content processing and storage
    """
    
    def __init__(self):
        """Initialize data processor."""
        self.supported_content_types = {
            'application/pdf': ContentType.PDF,
            'text/html': ContentType.HTML,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ContentType.DOCX,
            'text/plain': ContentType.TXT,
            'application/xml': ContentType.XML,
            'text/xml': ContentType.XML,
            'application/json': ContentType.JSON,
            'text/csv': ContentType.CSV,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ContentType.XLSX,
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': ContentType.PPTX
        }
    
    def process_academic_document(self, 
                                  title: str,
                                  authors: List[str],
                                  abstract: str = "",
                                  content: str = "",
                                  url: str = "",
                                  source_type: SourceType = SourceType.ACADEMIC,
                                  **kwargs) -> AcademicDocument:
        """Process academic document and create standardized metadata."""
        try:
            # Create academic document
            document = create_academic_document(
                title=title,
                authors=authors,
                abstract=abstract,
                content=content,
                url=url,
                source_type=source_type,
                **kwargs
            )
            
            # Process metadata
            self._process_metadata(document.metadata, content)
            
            # Extract academic-specific information
            self._extract_academic_info(document)
            
            # Calculate quality metrics
            self._calculate_quality_metrics(document)
            
            # Generate file hash
            document.metadata.file_hash = self._generate_file_hash(content)
            
            logger.info(f"Processed academic document: {title}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to process academic document: {e}")
            raise
    
    def process_web_document(self,
                           title: str,
                           content: str,
                           url: str,
                           source_type: SourceType = SourceType.TECHNICAL,
                           **kwargs) -> WebDocument:
        """Process web document and create standardized metadata."""
        try:
            # Create web document
            document = create_web_document(
                title=title,
                content=content,
                url=url,
                source_type=source_type,
                **kwargs
            )
            
            # Process metadata
            self._process_metadata(document.metadata, content)
            
            # Extract web-specific information
            self._extract_web_info(document)
            
            # Calculate quality metrics
            self._calculate_quality_metrics(document)
            
            # Generate file hash
            document.metadata.file_hash = self._generate_file_hash(content)
            
            logger.info(f"Processed web document: {title}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to process web document: {e}")
            raise
    
    def _process_metadata(self, metadata: Metadata, content: str):
        """Process and standardize metadata."""
        # Detect content type from URL
        if metadata.url:
            content_type = self._detect_content_type_from_url(metadata.url)
            if content_type:
                metadata.content_type = content_type
        
        # Extract publication date
        if not metadata.publication_date:
            metadata.publication_date = self._extract_publication_date(content)
            if metadata.publication_date:
                metadata.publication_year = metadata.publication_date.year
        
        # Extract keywords if not provided
        if not metadata.keywords:
            metadata.keywords = self._extract_keywords(content)
        
        # Calculate word count
        metadata.word_count = len(content.split()) if content else 0
        
        # Detect language
        if not metadata.language or metadata.language == "en":
            metadata.language = self._detect_language(content)
        
        # Extract tags and categories
        metadata.tags = self._extract_tags(content)
        metadata.categories = self._extract_categories(content)
        metadata.topics = self._extract_topics(content)
    
    def _extract_academic_info(self, document: AcademicDocument):
        """Extract academic-specific information."""
        content = document.content
        
        # Extract citations
        document.citations = self._extract_citations(content)
        
        # Extract references
        document.references = self._extract_references(content)
        
        # Extract funding information
        document.funding = self._extract_funding(content)
        
        # Extract acknowledgments
        document.acknowledgments = self._extract_acknowledgments(content)
        
        # Extract subject areas
        document.subject_areas = self._extract_subject_areas(content)
        
        # Extract research fields
        document.research_fields = self._extract_research_fields(content)
        
        # Extract methodologies
        document.methodologies = self._extract_methodologies(content)
        
        # Calculate citation count
        document.citation_count = len(document.citations)
    
    def _extract_web_info(self, document: WebDocument):
        """Extract web-specific information."""
        content = document.content
        
        # Extract domain from URL
        if document.metadata.url:
            from urllib.parse import urlparse
            parsed_url = urlparse(document.metadata.url)
            document.domain = parsed_url.netloc
            document.path = parsed_url.path
        
        # Extract social metrics (if available in content)
        document.likes = self._extract_social_metric(content, 'likes')
        document.shares = self._extract_social_metric(content, 'shares')
        document.comments = self._extract_social_metric(content, 'comments')
        document.views = self._extract_social_metric(content, 'views')
        
        # Classify content category
        document.content_category = self._classify_content_category(content)
        
        # Analyze sentiment
        document.sentiment = self._analyze_sentiment(content)
        
        # Calculate readability score
        document.readability_score = self._calculate_readability(content)
    
    def _calculate_quality_metrics(self, document):
        """Calculate quality metrics for document."""
        metadata = document.metadata
        
        # Relevance score (based on keyword matching)
        metadata.relevance_score = self._calculate_relevance_score(
            metadata.title, metadata.abstract, metadata.keywords
        )
        
        # Quality score (based on content quality indicators)
        content = document.content if hasattr(document, 'content') else ""
        metadata.quality_score = self._calculate_quality_score(
            metadata.title, metadata.abstract, content, metadata.word_count
        )
        
        # Confidence score (based on metadata completeness)
        metadata.confidence_score = self._calculate_confidence_score(metadata)
    
    def _detect_content_type_from_url(self, url: str) -> Optional[ContentType]:
        """Detect content type from URL."""
        if not url:
            return None
        
        # Get MIME type from URL
        mime_type, _ = mimetypes.guess_type(url)
        if mime_type:
            return self.supported_content_types.get(mime_type, ContentType.OTHER)
        
        # Fallback to file extension
        if url.lower().endswith('.pdf'):
            return ContentType.PDF
        elif url.lower().endswith('.html') or url.lower().endswith('.htm'):
            return ContentType.HTML
        elif url.lower().endswith('.docx'):
            return ContentType.DOCX
        elif url.lower().endswith('.txt'):
            return ContentType.TXT
        elif url.lower().endswith('.xml'):
            return ContentType.XML
        elif url.lower().endswith('.json'):
            return ContentType.JSON
        elif url.lower().endswith('.csv'):
            return ContentType.CSV
        elif url.lower().endswith('.xlsx'):
            return ContentType.XLSX
        elif url.lower().endswith('.pptx'):
            return ContentType.PPTX
        
        return ContentType.OTHER
    
    def _extract_publication_date(self, content: str) -> Optional[datetime]:
        """Extract publication date from content."""
        if not content:
            return None
        
        # Common date patterns
        date_patterns = [
            r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b',  # YYYY-MM-DD
            r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b',  # MM-DD-YYYY
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{4}\b'  # Just year
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    # Try to parse the first match
                    date_str = matches[0] if isinstance(matches[0], str) else '-'.join(matches[0])
                    return datetime.strptime(date_str, '%Y-%m-%d')
                except:
                    continue
        
        return None
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content."""
        if not content:
            return []
        
        # Simple keyword extraction (in a real implementation, use NLP)
        words = re.findall(r'\b\w+\b', content.lower())
        
        # Filter for relevant keywords (length > 3, not common words)
        common_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'man', 'men', 'put', 'say', 'she', 'too', 'use'}
        
        keywords = []
        for word in words:
            if len(word) > 3 and word not in common_words:
                keywords.append(word)
        
        # Return top 10 keywords
        return keywords[:10]
    
    def _detect_language(self, content: str) -> str:
        """Detect language of content."""
        if not content:
            return "en"
        
        # Simple language detection based on common words
        english_words = ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had']
        spanish_words = ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se']
        french_words = ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir']
        
        content_lower = content.lower()
        
        english_count = sum(1 for word in english_words if word in content_lower)
        spanish_count = sum(1 for word in spanish_words if word in content_lower)
        french_count = sum(1 for word in french_words if word in content_lower)
        
        if english_count > spanish_count and english_count > french_count:
            return "en"
        elif spanish_count > french_count:
            return "es"
        elif french_count > 0:
            return "fr"
        else:
            return "en"
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract tags from content."""
        # Simple tag extraction (in a real implementation, use NLP)
        tags = []
        
        # Look for common academic tags
        academic_tags = ['research', 'study', 'analysis', 'experiment', 'method', 'result', 'conclusion', 'data', 'model', 'theory']
        
        content_lower = content.lower()
        for tag in academic_tags:
            if tag in content_lower:
                tags.append(tag)
        
        return tags
    
    def _extract_categories(self, content: str) -> List[str]:
        """Extract categories from content."""
        # Simple category extraction
        categories = []
        
        # Look for domain-specific categories
        domain_categories = {
            'engineering': ['engineering', 'structural', 'civil', 'mechanical'],
            'science': ['science', 'physics', 'chemistry', 'biology'],
            'technology': ['technology', 'computer', 'software', 'digital'],
            'medicine': ['medical', 'health', 'clinical', 'treatment']
        }
        
        content_lower = content.lower()
        for category, keywords in domain_categories.items():
            if any(keyword in content_lower for keyword in keywords):
                categories.append(category)
        
        return categories
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract topics from content."""
        # Simple topic extraction
        topics = []
        
        # Look for specific topics related to reinforced concrete
        concrete_topics = [
            'reinforced concrete', 'concrete deterioration', 'corrosion', 'durability',
            'chloride attack', 'carbonation', 'freeze-thaw', 'steel reinforcement',
            'service life', 'maintenance', 'repair', 'strengthening'
        ]
        
        content_lower = content.lower()
        for topic in concrete_topics:
            if topic in content_lower:
                topics.append(topic)
        
        return topics
    
    def _extract_citations(self, content: str) -> List[str]:
        """Extract citations from content."""
        # Simple citation extraction
        citations = []
        
        # Look for citation patterns
        citation_patterns = [
            r'\[(\d+)\]',  # [1], [2], etc.
            r'\([A-Za-z]+\s+\d{4}\)',  # (Author 2023)
            r'\b[A-Z][a-z]+\s+et\s+al\.\s+\d{4}\b'  # Author et al. 2023
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, content)
            citations.extend(matches)
        
        return citations
    
    def _extract_references(self, content: str) -> List[str]:
        """Extract references from content."""
        # Simple reference extraction
        references = []
        
        # Look for reference patterns
        reference_patterns = [
            r'^\d+\.\s+.*$',  # 1. Reference text
            r'^\[.*\]$'  # [Reference text]
        ]
        
        lines = content.split('\n')
        for line in lines:
            for pattern in reference_patterns:
                if re.match(pattern, line.strip()):
                    references.append(line.strip())
                    break
        
        return references
    
    def _extract_funding(self, content: str) -> List[str]:
        """Extract funding information from content."""
        # Simple funding extraction
        funding = []
        
        # Look for funding patterns
        funding_patterns = [
            r'funded\s+by\s+([^.]*)',
            r'supported\s+by\s+([^.]*)',
            r'grant\s+([^.]*)',
            r'NSF\s+([^.]*)',
            r'NIH\s+([^.]*)'
        ]
        
        for pattern in funding_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            funding.extend(matches)
        
        return funding
    
    def _extract_acknowledgments(self, content: str) -> str:
        """Extract acknowledgments from content."""
        # Look for acknowledgment section
        acknowledgment_patterns = [
            r'acknowledgments?[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'acknowledgements?[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)'
        ]
        
        for pattern in acknowledgment_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_subject_areas(self, content: str) -> List[str]:
        """Extract subject areas from content."""
        # Simple subject area extraction
        subject_areas = []
        
        # Look for subject area keywords
        area_keywords = {
            'civil engineering': ['civil', 'structural', 'construction', 'infrastructure'],
            'materials science': ['materials', 'concrete', 'steel', 'composite'],
            'chemistry': ['chemistry', 'chemical', 'reaction', 'molecule'],
            'physics': ['physics', 'mechanical', 'force', 'stress']
        }
        
        content_lower = content.lower()
        for area, keywords in area_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                subject_areas.append(area)
        
        return subject_areas
    
    def _extract_research_fields(self, content: str) -> List[str]:
        """Extract research fields from content."""
        # Simple research field extraction
        research_fields = []
        
        # Look for research field keywords
        field_keywords = {
            'structural engineering': ['structural', 'beam', 'column', 'bridge'],
            'materials engineering': ['materials', 'properties', 'characterization'],
            'corrosion science': ['corrosion', 'rust', 'oxidation', 'electrochemical'],
            'durability studies': ['durability', 'aging', 'degradation', 'service life']
        }
        
        content_lower = content.lower()
        for field, keywords in field_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                research_fields.append(field)
        
        return research_fields
    
    def _extract_methodologies(self, content: str) -> List[str]:
        """Extract methodologies from content."""
        # Simple methodology extraction
        methodologies = []
        
        # Look for methodology keywords
        method_keywords = {
            'experimental': ['experiment', 'test', 'laboratory', 'specimen'],
            'numerical': ['simulation', 'model', 'finite element', 'computation'],
            'analytical': ['analysis', 'calculation', 'formula', 'equation'],
            'field study': ['field', 'monitoring', 'inspection', 'survey']
        }
        
        content_lower = content.lower()
        for method, keywords in method_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                methodologies.append(method)
        
        return methodologies
    
    def _extract_social_metric(self, content: str, metric: str) -> int:
        """Extract social metric from content."""
        # Simple social metric extraction
        metric_patterns = {
            'likes': [r'(\d+)\s+likes?', r'liked\s+(\d+)'],
            'shares': [r'(\d+)\s+shares?', r'shared\s+(\d+)'],
            'comments': [r'(\d+)\s+comments?', r'commented\s+(\d+)'],
            'views': [r'(\d+)\s+views?', r'viewed\s+(\d+)']
        }
        
        patterns = metric_patterns.get(metric, [])
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 0
    
    def _classify_content_category(self, content: str) -> str:
        """Classify content category."""
        # Simple content category classification
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['research', 'study', 'analysis', 'experiment']):
            return 'research'
        elif any(word in content_lower for word in ['news', 'report', 'announcement']):
            return 'news'
        elif any(word in content_lower for word in ['blog', 'opinion', 'personal']):
            return 'blog'
        elif any(word in content_lower for word in ['forum', 'discussion', 'comment']):
            return 'forum'
        else:
            return 'other'
    
    def _analyze_sentiment(self, content: str) -> str:
        """Analyze sentiment of content."""
        # Simple sentiment analysis
        positive_words = ['good', 'excellent', 'positive', 'success', 'improve', 'benefit']
        negative_words = ['bad', 'poor', 'negative', 'fail', 'problem', 'issue']
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_readability(self, content: str) -> float:
        """Calculate readability score."""
        if not content:
            return 0.0
        
        # Simple readability calculation
        words = content.split()
        sentences = content.split('.')
        
        if len(sentences) == 0:
            return 0.0
        
        avg_words_per_sentence = len(words) / len(sentences)
        avg_syllables_per_word = sum(self._count_syllables(word) for word in words) / len(words)
        
        # Simple readability formula
        readability = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
        return max(0.0, min(100.0, readability))
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word."""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
        
        if word.endswith('e'):
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _calculate_relevance_score(self, title: str, abstract: str, keywords: List[str]) -> float:
        """Calculate relevance score."""
        # Simple relevance calculation
        target_keywords = [
            'reinforced concrete', 'deterioration', 'corrosion', 'durability',
            'chloride', 'carbonation', 'steel reinforcement', 'concrete'
        ]
        
        text = f"{title} {abstract}".lower()
        keyword_matches = sum(1 for keyword in target_keywords if keyword in text)
        
        return min(1.0, keyword_matches / len(target_keywords))
    
    def _calculate_quality_score(self, title: str, abstract: str, content: str, word_count: int) -> float:
        """Calculate quality score."""
        score = 0.0
        
        # Title quality
        if title and len(title) > 10:
            score += 0.2
        
        # Abstract quality
        if abstract and len(abstract) > 50:
            score += 0.3
        
        # Content quality
        if content and word_count > 100:
            score += 0.3
        
        # Word count quality
        if word_count > 500:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_confidence_score(self, metadata: Metadata) -> float:
        """Calculate confidence score based on metadata completeness."""
        score = 0.0
        
        # Required fields
        if metadata.title:
            score += 0.2
        if metadata.authors:
            score += 0.2
        if metadata.url:
            score += 0.2
        if metadata.publication_date:
            score += 0.1
        if metadata.abstract:
            score += 0.1
        if metadata.keywords:
            score += 0.1
        if metadata.doi:
            score += 0.1
        
        return min(1.0, score)
    
    def _generate_file_hash(self, content: str) -> str:
        """Generate SHA256 hash for content."""
        if not content:
            return ""
        
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


def main():
    """Test data processor."""
    processor = DataProcessor()
    
    # Test academic document processing
    academic_doc = processor.process_academic_document(
        title="Reinforced Concrete Deterioration Due to Chloride Attack",
        authors=["John Doe", "Jane Smith"],
        abstract="This study investigates the deterioration of reinforced concrete structures exposed to chloride environments.",
        content="The research focuses on the mechanisms of chloride ingress and its impact on steel reinforcement corrosion.",
        url="https://example.com/paper.pdf",
        source_type=SourceType.ACADEMIC
    )
    
    print(f"Academic document processed: {academic_doc.metadata.title}")
    print(f"Quality score: {academic_doc.metadata.quality_score}")
    print(f"Relevance score: {academic_doc.metadata.relevance_score}")
    
    # Test web document processing
    web_doc = processor.process_web_document(
        title="Concrete Corrosion Discussion",
        content="Discussion about concrete corrosion in civil engineering forums.",
        url="https://example.com/forum/post",
        source_type=SourceType.FORUM
    )
    
    print(f"Web document processed: {web_doc.metadata.title}")
    print(f"Quality score: {web_doc.metadata.quality_score}")
    print(f"Relevance score: {web_doc.metadata.relevance_score}")


if __name__ == "__main__":
    main()
