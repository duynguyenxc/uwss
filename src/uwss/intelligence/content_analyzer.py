"""
Content Analysis Engine

This module provides intelligent content analysis capabilities
including content type detection, metadata extraction, and quality assessment.
"""

import re
import mimetypes
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ContentAnalysis:
    """Represents the result of content analysis."""
    content_type: str
    file_extension: str
    mime_type: str
    is_text: bool
    is_structured: bool
    language: str
    word_count: int
    quality_score: float
    metadata: Dict[str, Any]


class ContentAnalyzer:
    """
    Intelligent content analyzer that detects content types,
    extracts metadata, and assesses content quality.
    """
    
    def __init__(self):
        """Initialize the content analyzer."""
        self.supported_types = {
            'pdf': ['application/pdf'],
            'html': ['text/html'],
            'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            'doc': ['application/msword'],
            'txt': ['text/plain'],
            'csv': ['text/csv'],
            'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
            'pptx': ['application/vnd.openxmlformats-officedocument.presentationml.presentation']
        }
        
        self.language_patterns = {
            'english': r'[a-zA-Z]',
            'french': r'[àâäéèêëïîôöùûüÿç]',
            'german': r'[äöüß]',
            'spanish': r'[ñáéíóúü]',
            'russian': r'[а-яё]',
            'chinese': r'[\u4e00-\u9fff]',
            'japanese': r'[\u3040-\u309f\u30a0-\u30ff]',
            'korean': r'[\uac00-\ud7af]'
        }
    
    def analyze_content(self, file_path: Optional[Path] = None, 
                       content: Optional[str] = None,
                       url: Optional[str] = None) -> ContentAnalysis:
        """
        Analyze content and return detailed analysis.
        
        Args:
            file_path: Path to the file to analyze
            content: Raw content text
            url: URL of the content
            
        Returns:
            ContentAnalysis object with analysis results
        """
        # Detect content type
        content_type, file_extension, mime_type = self._detect_content_type(
            file_path, content, url
        )
        
        # Check if content is text-based
        is_text = self._is_text_content(content_type, mime_type)
        
        # Check if content is structured
        is_structured = self._is_structured_content(content_type, content)
        
        # Detect language
        language = self._detect_language(content) if content else 'unknown'
        
        # Count words
        word_count = self._count_words(content) if content else 0
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            content_type, content, word_count, file_path
        )
        
        # Extract metadata
        metadata = self._extract_metadata(file_path, content, url)
        
        return ContentAnalysis(
            content_type=content_type,
            file_extension=file_extension,
            mime_type=mime_type,
            is_text=is_text,
            is_structured=is_structured,
            language=language,
            word_count=word_count,
            quality_score=quality_score,
            metadata=metadata
        )
    
    def _detect_content_type(self, file_path: Optional[Path], 
                           content: Optional[str], url: Optional[str]) -> Tuple[str, str, str]:
        """Detect content type based on file path, content, or URL."""
        # Try file path first
        if file_path and file_path.exists():
            extension = file_path.suffix.lower()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            content_type = self._extension_to_type(extension)
            return content_type, extension, mime_type or 'unknown'
        
        # Try URL
        if url:
            url_lower = url.lower()
            if url_lower.endswith('.pdf'):
                return 'pdf', '.pdf', 'application/pdf'
            elif url_lower.endswith('.html') or url_lower.endswith('.htm'):
                return 'html', '.html', 'text/html'
            elif url_lower.endswith('.docx'):
                return 'docx', '.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif url_lower.endswith('.doc'):
                return 'doc', '.doc', 'application/msword'
            elif url_lower.endswith('.txt'):
                return 'txt', '.txt', 'text/plain'
            elif url_lower.endswith('.csv'):
                return 'csv', '.csv', 'text/csv'
            elif url_lower.endswith('.xlsx'):
                return 'xlsx', '.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif url_lower.endswith('.pptx'):
                return 'pptx', '.pptx', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        
        # Try content analysis
        if content:
            if content.startswith('%PDF'):
                return 'pdf', '.pdf', 'application/pdf'
            elif '<html' in content.lower() or '<!doctype html' in content.lower():
                return 'html', '.html', 'text/html'
            elif content.startswith('PK\x03\x04'):  # ZIP-based formats
                return 'docx', '.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        # Default to text
        return 'txt', '.txt', 'text/plain'
    
    def _extension_to_type(self, extension: str) -> str:
        """Convert file extension to content type."""
        extension_map = {
            '.pdf': 'pdf',
            '.html': 'html',
            '.htm': 'html',
            '.docx': 'docx',
            '.doc': 'doc',
            '.txt': 'txt',
            '.csv': 'csv',
            '.xlsx': 'xlsx',
            '.xls': 'xls',
            '.pptx': 'pptx',
            '.ppt': 'ppt'
        }
        return extension_map.get(extension, 'unknown')
    
    def _is_text_content(self, content_type: str, mime_type: str) -> bool:
        """Check if content is text-based."""
        text_types = ['txt', 'html', 'csv']
        text_mimes = ['text/', 'application/json', 'application/xml']
        
        return (content_type in text_types or 
                any(mime_type.startswith(prefix) for prefix in text_mimes))
    
    def _is_structured_content(self, content_type: str, content: Optional[str]) -> bool:
        """Check if content is structured (has clear organization)."""
        if not content:
            return False
        
        structured_indicators = [
            r'<title>',  # HTML title
            r'<h[1-6]>',  # HTML headings
            r'<section>',  # HTML sections
            r'<article>',  # HTML articles
            r'^\d+\.',  # Numbered lists
            r'^\*',  # Bullet points
            r'^\s*[A-Z][a-z]+:',  # Key-value pairs
            r'^\s*##',  # Markdown headings
            r'^\s*###',  # Markdown subheadings
        ]
        
        for pattern in structured_indicators:
            if re.search(pattern, content, re.MULTILINE):
                return True
        
        return False
    
    def _detect_language(self, content: str) -> str:
        """Detect the primary language of the content."""
        if not content:
            return 'unknown'
        
        # Sample first 1000 characters for language detection
        sample = content[:1000]
        
        language_scores = {}
        for language, pattern in self.language_patterns.items():
            matches = len(re.findall(pattern, sample))
            language_scores[language] = matches
        
        if not language_scores:
            return 'unknown'
        
        # Return language with highest score
        return max(language_scores.items(), key=lambda x: x[1])[0]
    
    def _count_words(self, content: str) -> int:
        """Count words in content."""
        if not content:
            return 0
        
        # Remove HTML tags for word counting
        clean_content = re.sub(r'<[^>]+>', ' ', content)
        
        # Split by whitespace and count
        words = clean_content.split()
        return len(words)
    
    def _calculate_quality_score(self, content_type: str, content: Optional[str], 
                                word_count: int, file_path: Optional[Path]) -> float:
        """Calculate content quality score."""
        quality_factors = []
        
        # Content length factor
        if word_count > 1000:
            quality_factors.append(0.9)
        elif word_count > 500:
            quality_factors.append(0.7)
        elif word_count > 100:
            quality_factors.append(0.5)
        elif word_count > 50:
            quality_factors.append(0.3)
        else:
            quality_factors.append(0.1)
        
        # Content type factor
        type_scores = {
            'pdf': 0.9,
            'docx': 0.8,
            'html': 0.7,
            'txt': 0.6,
            'csv': 0.5,
            'xlsx': 0.4,
            'pptx': 0.3
        }
        quality_factors.append(type_scores.get(content_type, 0.5))
        
        # File size factor (if available)
        if file_path and file_path.exists():
            file_size = file_path.stat().st_size
            if file_size > 1000000:  # > 1MB
                quality_factors.append(0.8)
            elif file_size > 100000:  # > 100KB
                quality_factors.append(0.6)
            elif file_size > 10000:  # > 10KB
                quality_factors.append(0.4)
            else:
                quality_factors.append(0.2)
        
        # Content structure factor
        if content and self._is_structured_content(content_type, content):
            quality_factors.append(0.8)
        else:
            quality_factors.append(0.5)
        
        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
    
    def _extract_metadata(self, file_path: Optional[Path], 
                         content: Optional[str], url: Optional[str]) -> Dict[str, Any]:
        """Extract metadata from content."""
        metadata = {}
        
        # File metadata
        if file_path and file_path.exists():
            stat = file_path.stat()
            metadata.update({
                'file_size': stat.st_size,
                'file_name': file_path.name,
                'file_path': str(file_path),
                'created_time': stat.st_ctime,
                'modified_time': stat.st_mtime
            })
        
        # URL metadata
        if url:
            metadata['source_url'] = url
        
        # Content metadata
        if content:
            # Extract title from HTML
            title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            if title_match:
                metadata['title'] = title_match.group(1).strip()
            
            # Extract meta description
            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
            if desc_match:
                metadata['description'] = desc_match.group(1).strip()
            
            # Extract meta keywords
            keywords_match = re.search(r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
            if keywords_match:
                metadata['keywords'] = keywords_match.group(1).strip()
        
        return metadata
    
    def get_processing_strategy(self, analysis: ContentAnalysis) -> str:
        """Get recommended processing strategy for the content."""
        if analysis.content_type == 'pdf':
            return 'pdf_extraction'
        elif analysis.content_type == 'html':
            return 'html_parsing'
        elif analysis.content_type in ['docx', 'doc']:
            return 'document_processing'
        elif analysis.content_type == 'csv':
            return 'tabular_processing'
        elif analysis.content_type == 'xlsx':
            return 'spreadsheet_processing'
        else:
            return 'text_processing'
    
    def is_processable(self, analysis: ContentAnalysis) -> bool:
        """Check if content can be processed."""
        return (analysis.is_text and 
                analysis.word_count > 10 and 
                analysis.quality_score > 0.3)


def main():
    """Test the content analyzer."""
    analyzer = ContentAnalyzer()
    
    # Test with sample content
    test_content = """
    <html>
    <head>
        <title>Reinforced Concrete Deterioration Study</title>
        <meta name="description" content="A comprehensive study on reinforced concrete deterioration">
        <meta name="keywords" content="concrete, deterioration, corrosion, durability">
    </head>
    <body>
        <h1>Introduction</h1>
        <p>This paper investigates the deterioration of reinforced concrete structures.</p>
        <h2>Methodology</h2>
        <p>The study uses advanced analytical techniques to assess concrete degradation.</p>
    </body>
    </html>
    """
    
    analysis = analyzer.analyze_content(content=test_content)
    
    print(f"Content Type: {analysis.content_type}")
    print(f"Is Text: {analysis.is_text}")
    print(f"Is Structured: {analysis.is_structured}")
    print(f"Language: {analysis.language}")
    print(f"Word Count: {analysis.word_count}")
    print(f"Quality Score: {analysis.quality_score:.2f}")
    print(f"Processing Strategy: {analyzer.get_processing_strategy(analysis)}")


if __name__ == "__main__":
    main()
