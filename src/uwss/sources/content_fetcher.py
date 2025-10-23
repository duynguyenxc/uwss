"""
Content Fetcher

This module provides content fetching and processing capabilities
for various content types including PDF, HTML, and other formats.
"""

import requests
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import hashlib
import time
import mimetypes

logger = logging.getLogger(__name__)


@dataclass
class FetchedContent:
    """Represents fetched content with metadata."""
    url: str
    content_type: str
    file_path: Optional[Path]
    content: Optional[str]
    file_size: int
    mime_type: str
    checksum: str
    fetch_time: float
    success: bool
    error_message: Optional[str]


class ContentFetcher:
    """
    Content fetcher for downloading and processing various content types.
    
    Technologies used:
    - requests: HTTP requests for content downloading
    - hashlib: Content integrity verification
    - mimetypes: Content type detection
    - Rate limiting: Respectful content fetching
    - Error handling: Robust error recovery
    - Content validation: Quality assurance
    """
    
    def __init__(self, download_dir: Path = Path("data/files")):
        """Initialize the content fetcher."""
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_delay = 1.0  # Minimum delay between requests
        
        # Content type handlers
        self.content_handlers = {
            'application/pdf': self._handle_pdf,
            'text/html': self._handle_html,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': self._handle_docx,
            'application/msword': self._handle_doc,
            'text/plain': self._handle_text,
            'text/csv': self._handle_csv
        }
    
    def fetch_content(self, url: str, content_type: Optional[str] = None) -> FetchedContent:
        """
        Fetch content from URL.
        
        Args:
            url: URL to fetch content from
            content_type: Expected content type (optional)
            
        Returns:
            FetchedContent object with results
        """
        start_time = time.time()
        
        try:
            self._rate_limit()
            
            # Download content
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Detect content type
            detected_type = self._detect_content_type(response, content_type)
            
            # Generate file path
            file_path = self._generate_file_path(url, detected_type)
            
            # Save content
            content, file_size = self._save_content(response, file_path)
            
            # Calculate checksum
            checksum = self._calculate_checksum(content)
            
            # Process content based on type
            processed_content = self._process_content(content, detected_type)
            
            fetch_time = time.time() - start_time
            
            return FetchedContent(
                url=url,
                content_type=detected_type,
                file_path=file_path,
                content=processed_content,
                file_size=file_size,
                mime_type=detected_type,
                checksum=checksum,
                fetch_time=fetch_time,
                success=True,
                error_message=None
            )
            
        except Exception as e:
            fetch_time = time.time() - start_time
            logger.error(f"Failed to fetch content from {url}: {e}")
            
            return FetchedContent(
                url=url,
                content_type=content_type or "unknown",
                file_path=None,
                content=None,
                file_size=0,
                mime_type=content_type or "unknown",
                checksum="",
                fetch_time=fetch_time,
                success=False,
                error_message=str(e)
            )
    
    def _detect_content_type(self, response: requests.Response, expected_type: Optional[str]) -> str:
        """Detect content type from response."""
        # Check Content-Type header
        content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
        
        if content_type and content_type != 'application/octet-stream':
            return content_type
        
        # Check file extension
        url_path = response.url.split('/')[-1]
        mime_type, _ = mimetypes.guess_type(url_path)
        
        if mime_type:
            return mime_type
        
        # Use expected type if provided
        if expected_type:
            return expected_type
        
        # Default to unknown
        return 'application/octet-stream'
    
    def _generate_file_path(self, url: str, content_type: str) -> Path:
        """Generate file path for downloaded content."""
        # Extract filename from URL
        filename = url.split('/')[-1]
        if not filename or '.' not in filename:
            # Generate filename based on content type
            extension = self._get_extension_from_mime_type(content_type)
            filename = f"content_{hashlib.md5(url.encode()).hexdigest()[:8]}{extension}"
        
        return self.download_dir / filename
    
    def _get_extension_from_mime_type(self, mime_type: str) -> str:
        """Get file extension from MIME type."""
        extension_map = {
            'application/pdf': '.pdf',
            'text/html': '.html',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/msword': '.doc',
            'text/plain': '.txt',
            'text/csv': '.csv',
            'application/json': '.json'
        }
        return extension_map.get(mime_type, '.bin')
    
    def _save_content(self, response: requests.Response, file_path: Path) -> Tuple[bytes, int]:
        """Save content to file and return content and size."""
        content = b""
        file_size = 0
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    content += chunk
                    file_size += len(chunk)
        
        return content, file_size
    
    def _calculate_checksum(self, content: bytes) -> str:
        """Calculate SHA256 checksum of content."""
        return hashlib.sha256(content).hexdigest()
    
    def _process_content(self, content: bytes, content_type: str) -> Optional[str]:
        """Process content based on type."""
        handler = self.content_handlers.get(content_type)
        if handler:
            return handler(content)
        return None
    
    def _handle_pdf(self, content: bytes) -> str:
        """Handle PDF content (simplified)."""
        # In a real implementation, you would use PyPDF2 or pdfplumber
        # For now, return a placeholder
        return f"PDF content ({len(content)} bytes) - [PDF processing not implemented]"
    
    def _handle_html(self, content: bytes) -> str:
        """Handle HTML content."""
        try:
            # Decode HTML content
            html_text = content.decode('utf-8', errors='ignore')
            
            # Simple text extraction (in real implementation, use BeautifulSoup)
            # Remove HTML tags
            import re
            text = re.sub(r'<[^>]+>', ' ', html_text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
        except Exception as e:
            logger.error(f"Failed to process HTML content: {e}")
            return f"HTML content ({len(content)} bytes) - [HTML processing failed]"
    
    def _handle_docx(self, content: bytes) -> str:
        """Handle DOCX content (simplified)."""
        # In a real implementation, you would use python-docx
        return f"DOCX content ({len(content)} bytes) - [DOCX processing not implemented]"
    
    def _handle_doc(self, content: bytes) -> str:
        """Handle DOC content (simplified)."""
        # In a real implementation, you would use python-docx2txt
        return f"DOC content ({len(content)} bytes) - [DOC processing not implemented]"
    
    def _handle_text(self, content: bytes) -> str:
        """Handle text content."""
        try:
            return content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Failed to decode text content: {e}")
            return f"Text content ({len(content)} bytes) - [Text decoding failed]"
    
    def _handle_csv(self, content: bytes) -> str:
        """Handle CSV content."""
        try:
            return content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Failed to decode CSV content: {e}")
            return f"CSV content ({len(content)} bytes) - [CSV decoding failed]"
    
    def _rate_limit(self):
        """Implement rate limiting to be respectful to servers."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_fetch_stats(self, results: List[FetchedContent]) -> Dict[str, Any]:
        """Get statistics about fetch results."""
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        
        total_size = sum(r.file_size for r in results if r.success)
        avg_size = total_size / successful if successful > 0 else 0
        
        total_time = sum(r.fetch_time for r in results)
        avg_time = total_time / total if total > 0 else 0
        
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "total_size": total_size,
            "avg_size": avg_size,
            "total_time": total_time,
            "avg_time": avg_time
        }
    
    def export_results(self, results: List[FetchedContent], output_path: Path) -> None:
        """Export fetch results to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        export_data = []
        for result in results:
            export_data.append({
                "url": result.url,
                "content_type": result.content_type,
                "file_path": str(result.file_path) if result.file_path else None,
                "file_size": result.file_size,
                "mime_type": result.mime_type,
                "checksum": result.checksum,
                "fetch_time": result.fetch_time,
                "success": result.success,
                "error_message": result.error_message
            })
        
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(results)} fetch results to {output_path}")


def main():
    """Test the content fetcher."""
    fetcher = ContentFetcher()
    
    # Test URLs
    test_urls = [
        "https://example.com/document.pdf",
        "https://example.com/article.html",
        "https://example.com/data.csv"
    ]
    
    # Fetch content
    results = []
    for url in test_urls:
        result = fetcher.fetch_content(url)
        results.append(result)
        print(f"Fetched {url}: {'Success' if result.success else 'Failed'}")
    
    # Show statistics
    stats = fetcher.get_fetch_stats(results)
    print(f"\nFetch Statistics:")
    print(f"Total: {stats['total']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success Rate: {stats['success_rate']:.2%}")
    print(f"Total Size: {stats['total_size']} bytes")
    print(f"Average Size: {stats['avg_size']:.0f} bytes")
    print(f"Average Time: {stats['avg_time']:.2f} seconds")
    
    # Export results
    fetcher.export_results(results, Path("data/export/fetch_results.json"))


if __name__ == "__main__":
    main()
