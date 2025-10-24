"""
Intelligent Crawling Engine

This module provides intelligent crawling capabilities that automatically
crawls content from discovered sources with appropriate strategies.
"""

import requests
import time
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class CrawledContent:
    """Represents crawled content with metadata."""
    url: str
    title: str
    content: str
    content_type: str
    source_type: str
    metadata: Dict[str, Any]
    crawl_time: float
    success: bool
    error_message: Optional[str]


class IntelligentCrawlingEngine:
    """
    Intelligent crawling engine that automatically crawls content
    from discovered sources with appropriate strategies.
    
    Technologies used:
    - requests: HTTP requests for content crawling
    - BeautifulSoup: HTML parsing for content extraction
    - Strategy pattern: Different crawling strategies for different source types
    - Rate limiting: Respectful crawling
    - Error handling: Robust error recovery
    - Content analysis: Automatic content type detection
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the intelligent crawling engine."""
        self.config = config or {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_delay = 1.0  # Minimum delay between requests
        
        # Crawling strategies
        self.strategies = {
            'academic': self._crawl_academic_source,
            'government': self._crawl_government_source,
            'professional': self._crawl_professional_source,
            'social': self._crawl_social_source,
            'technical': self._crawl_technical_source
        }
    
    def crawl_sources(self, sources: List[Any], max_content: int = 100) -> List[CrawledContent]:
        """
        Crawl content from discovered sources.
        
        Args:
            sources: List of DiscoveredSource objects
            max_content: Maximum number of content items to crawl
            
        Returns:
            List of CrawledContent objects
        """
        logger.info(f"Starting intelligent crawling for {len(sources)} sources")
        
        crawled_content = []
        
        for source in sources:
            try:
                # Choose appropriate strategy based on source type
                strategy = self.strategies.get(source.source_type, self._crawl_generic_source)
                
                # Crawl content using chosen strategy
                content = strategy(source)
                
                if content:
                    crawled_content.append(content)
                    
                    if len(crawled_content) >= max_content:
                        break
                        
            except Exception as e:
                logger.error(f"Failed to crawl source {source.url}: {e}")
                # Create error content
                error_content = CrawledContent(
                    url=source.url,
                    title=f"Error crawling {source.title}",
                    content="",
                    content_type="error",
                    source_type=source.source_type,
                    metadata={"error": str(e)},
                    crawl_time=0.0,
                    success=False,
                    error_message=str(e)
                )
                crawled_content.append(error_content)
        
        logger.info(f"Crawled {len(crawled_content)} content items")
        return crawled_content
    
    def _crawl_academic_source(self, source: Any) -> Optional[CrawledContent]:
        """Crawl academic source with academic-specific strategy."""
        start_time = time.time()
        
        try:
            self._rate_limit()
            response = self.session.get(source.url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract academic-specific content
            title = self._extract_academic_title(soup)
            content = self._extract_academic_content(soup)
            metadata = self._extract_academic_metadata(soup)
            
            crawl_time = time.time() - start_time
            
            return CrawledContent(
                url=source.url,
                title=title,
                content=content,
                content_type="academic",
                source_type=source.source_type,
                metadata=metadata,
                crawl_time=crawl_time,
                success=True,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Failed to crawl academic source {source.url}: {e}")
            return None
    
    def _crawl_government_source(self, source: Any) -> Optional[CrawledContent]:
        """Crawl government source with government-specific strategy."""
        start_time = time.time()
        
        try:
            self._rate_limit()
            response = self.session.get(source.url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract government-specific content
            title = self._extract_government_title(soup)
            content = self._extract_government_content(soup)
            metadata = self._extract_government_metadata(soup)
            
            crawl_time = time.time() - start_time
            
            return CrawledContent(
                url=source.url,
                title=title,
                content=content,
                content_type="government",
                source_type=source.source_type,
                metadata=metadata,
                crawl_time=crawl_time,
                success=True,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Failed to crawl government source {source.url}: {e}")
            return None
    
    def _crawl_professional_source(self, source: Any) -> Optional[CrawledContent]:
        """Crawl professional source with professional-specific strategy."""
        start_time = time.time()
        
        try:
            self._rate_limit()
            response = self.session.get(source.url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract professional-specific content
            title = self._extract_professional_title(soup)
            content = self._extract_professional_content(soup)
            metadata = self._extract_professional_metadata(soup)
            
            crawl_time = time.time() - start_time
            
            return CrawledContent(
                url=source.url,
                title=title,
                content=content,
                content_type="professional",
                source_type=source.source_type,
                metadata=metadata,
                crawl_time=crawl_time,
                success=True,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Failed to crawl professional source {source.url}: {e}")
            return None
    
    def _crawl_social_source(self, source: Any) -> Optional[CrawledContent]:
        """Crawl social source with social-specific strategy."""
        start_time = time.time()
        
        try:
            self._rate_limit()
            response = self.session.get(source.url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract social-specific content
            title = self._extract_social_title(soup)
            content = self._extract_social_content(soup)
            metadata = self._extract_social_metadata(soup)
            
            crawl_time = time.time() - start_time
            
            return CrawledContent(
                url=source.url,
                title=title,
                content=content,
                content_type="social",
                source_type=source.source_type,
                metadata=metadata,
                crawl_time=crawl_time,
                success=True,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Failed to crawl social source {source.url}: {e}")
            return None
    
    def _crawl_technical_source(self, source: Any) -> Optional[CrawledContent]:
        """Crawl technical source with technical-specific strategy."""
        start_time = time.time()
        
        try:
            self._rate_limit()
            response = self.session.get(source.url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract technical-specific content
            title = self._extract_technical_title(soup)
            content = self._extract_technical_content(soup)
            metadata = self._extract_technical_metadata(soup)
            
            crawl_time = time.time() - start_time
            
            return CrawledContent(
                url=source.url,
                title=title,
                content=content,
                content_type="technical",
                source_type=source.source_type,
                metadata=metadata,
                crawl_time=crawl_time,
                success=True,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Failed to crawl technical source {source.url}: {e}")
            return None
    
    def _crawl_generic_source(self, source: Any) -> Optional[CrawledContent]:
        """Crawl generic source with generic strategy."""
        start_time = time.time()
        
        try:
            self._rate_limit()
            response = self.session.get(source.url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract generic content
            title = self._extract_generic_title(soup)
            content = self._extract_generic_content(soup)
            metadata = self._extract_generic_metadata(soup)
            
            crawl_time = time.time() - start_time
            
            return CrawledContent(
                url=source.url,
                title=title,
                content=content,
                content_type="generic",
                source_type=source.source_type,
                metadata=metadata,
                crawl_time=crawl_time,
                success=True,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Failed to crawl generic source {source.url}: {e}")
            return None
    
    # Content extraction methods for different source types
    
    def _extract_academic_title(self, soup: BeautifulSoup) -> str:
        """Extract title from academic source."""
        # Try different title selectors for academic sources
        title_selectors = [
            'h1.title', 'h1.article-title', 'h1.paper-title',
            'h1', 'title', '.title', '.article-title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                return element.get_text().strip()
        
        return "Academic Content"
    
    def _extract_academic_content(self, soup: BeautifulSoup) -> str:
        """Extract content from academic source."""
        # Try different content selectors for academic sources
        content_selectors = [
            '.abstract', '.article-content', '.paper-content',
            '.content', 'main', 'article'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return soup.get_text().strip()
    
    def _extract_academic_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from academic source."""
        metadata = {}
        
        # Extract authors
        authors = []
        author_elements = soup.select('.author, .authors, [class*="author"]')
        for element in author_elements:
            authors.append(element.get_text().strip())
        metadata['authors'] = authors
        
        # Extract publication date
        date_elements = soup.select('.date, .published, [class*="date"]')
        if date_elements:
            metadata['publication_date'] = date_elements[0].get_text().strip()
        
        # Extract journal/venue
        venue_elements = soup.select('.journal, .venue, [class*="journal"]')
        if venue_elements:
            metadata['venue'] = venue_elements[0].get_text().strip()
        
        return metadata
    
    def _extract_government_title(self, soup: BeautifulSoup) -> str:
        """Extract title from government source."""
        title_selectors = ['h1', 'title', '.title', '.page-title']
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                return element.get_text().strip()
        
        return "Government Content"
    
    def _extract_government_content(self, soup: BeautifulSoup) -> str:
        """Extract content from government source."""
        content_selectors = ['.content', 'main', 'article', '.main-content']
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return soup.get_text().strip()
    
    def _extract_government_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from government source."""
        metadata = {}
        
        # Extract agency
        agency_elements = soup.select('.agency, .department, [class*="agency"]')
        if agency_elements:
            metadata['agency'] = agency_elements[0].get_text().strip()
        
        # Extract document type
        doc_type_elements = soup.select('.document-type, .type, [class*="type"]')
        if doc_type_elements:
            metadata['document_type'] = doc_type_elements[0].get_text().strip()
        
        return metadata
    
    def _extract_professional_title(self, soup: BeautifulSoup) -> str:
        """Extract title from professional source."""
        title_selectors = ['h1', 'title', '.title', '.post-title']
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                return element.get_text().strip()
        
        return "Professional Content"
    
    def _extract_professional_content(self, soup: BeautifulSoup) -> str:
        """Extract content from professional source."""
        content_selectors = ['.content', 'main', 'article', '.post-content']
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return soup.get_text().strip()
    
    def _extract_professional_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from professional source."""
        metadata = {}
        
        # Extract author
        author_elements = soup.select('.author, .byline, [class*="author"]')
        if author_elements:
            metadata['author'] = author_elements[0].get_text().strip()
        
        # Extract post date
        date_elements = soup.select('.date, .published, [class*="date"]')
        if date_elements:
            metadata['post_date'] = date_elements[0].get_text().strip()
        
        return metadata
    
    def _extract_social_title(self, soup: BeautifulSoup) -> str:
        """Extract title from social source."""
        title_selectors = ['h1', 'title', '.title', '.post-title']
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                return element.get_text().strip()
        
        return "Social Content"
    
    def _extract_social_content(self, soup: BeautifulSoup) -> str:
        """Extract content from social source."""
        content_selectors = ['.content', 'main', 'article', '.post-content']
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return soup.get_text().strip()
    
    def _extract_social_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from social source."""
        metadata = {}
        
        # Extract author
        author_elements = soup.select('.author, .username, [class*="author"]')
        if author_elements:
            metadata['author'] = author_elements[0].get_text().strip()
        
        # Extract post date
        date_elements = soup.select('.date, .timestamp, [class*="date"]')
        if date_elements:
            metadata['post_date'] = date_elements[0].get_text().strip()
        
        return metadata
    
    def _extract_technical_title(self, soup: BeautifulSoup) -> str:
        """Extract title from technical source."""
        title_selectors = ['h1', 'title', '.title', '.article-title']
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                return element.get_text().strip()
        
        return "Technical Content"
    
    def _extract_technical_content(self, soup: BeautifulSoup) -> str:
        """Extract content from technical source."""
        content_selectors = ['.content', 'main', 'article', '.article-content']
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return soup.get_text().strip()
    
    def _extract_technical_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from technical source."""
        metadata = {}
        
        # Extract author
        author_elements = soup.select('.author, .byline, [class*="author"]')
        if author_elements:
            metadata['author'] = author_elements[0].get_text().strip()
        
        # Extract publication date
        date_elements = soup.select('.date, .published, [class*="date"]')
        if date_elements:
            metadata['publication_date'] = date_elements[0].get_text().strip()
        
        return metadata
    
    def _extract_generic_title(self, soup: BeautifulSoup) -> str:
        """Extract title from generic source."""
        title_element = soup.find('title')
        if title_element:
            return title_element.get_text().strip()
        
        h1_element = soup.find('h1')
        if h1_element:
            return h1_element.get_text().strip()
        
        return "Generic Content"
    
    def _extract_generic_content(self, soup: BeautifulSoup) -> str:
        """Extract content from generic source."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        return soup.get_text().strip()
    
    def _extract_generic_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from generic source."""
        metadata = {}
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            metadata['description'] = meta_desc.get('content', '')
        
        # Extract meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            metadata['keywords'] = meta_keywords.get('content', '')
        
        return metadata
    
    def _rate_limit(self):
        """Implement rate limiting to be respectful to web sources."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_crawling_stats(self, content: List[CrawledContent]) -> Dict[str, Any]:
        """Get statistics about crawled content."""
        total = len(content)
        successful = sum(1 for c in content if c.success)
        failed = total - successful
        
        total_time = sum(c.crawl_time for c in content)
        avg_time = total_time / total if total > 0 else 0
        
        source_types = {}
        for c in content:
            source_type = c.source_type
            source_types[source_type] = source_types.get(source_type, 0) + 1
        
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "total_time": total_time,
            "avg_time": avg_time,
            "source_types": source_types
        }
    
    def export_content(self, content: List[CrawledContent], output_path: Path) -> None:
        """Export crawled content to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        export_data = []
        for c in content:
            export_data.append({
                "url": c.url,
                "title": c.title,
                "content": c.content,
                "content_type": c.content_type,
                "source_type": c.source_type,
                "metadata": c.metadata,
                "crawl_time": c.crawl_time,
                "success": c.success,
                "error_message": c.error_message
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(content)} content items to {output_path}")


def main():
    """Test the intelligent crawling engine."""
    # This would be used with actual DiscoveredSource objects
    # For testing, we'll create mock sources
    pass


if __name__ == "__main__":
    main()
