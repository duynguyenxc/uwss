"""
Data Models for Universal Web Crawling System

This module defines the data models for storing academic and web documents
with standardized metadata.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


class DocumentType(Enum):
    """Document type enumeration."""
    ACADEMIC_PAPER = "academic_paper"
    CONFERENCE_PAPER = "conference_paper"
    JOURNAL_ARTICLE = "journal_article"
    PREPRINT = "preprint"
    THESIS = "thesis"
    REPORT = "report"
    BOOK = "book"
    CHAPTER = "chapter"
    WEB_ARTICLE = "web_article"
    BLOG_POST = "blog_post"
    NEWS_ARTICLE = "news_article"
    FORUM_POST = "forum_post"
    TECHNICAL_DOCUMENT = "technical_document"
    GOVERNMENT_REPORT = "government_report"
    PATENT = "patent"
    STANDARD = "standard"
    OTHER = "other"


class ContentType(Enum):
    """Content type enumeration."""
    PDF = "pdf"
    HTML = "html"
    DOCX = "docx"
    TXT = "txt"
    XML = "xml"
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"
    PPTX = "pptx"
    OTHER = "other"


class SourceType(Enum):
    """Source type enumeration."""
    ACADEMIC = "academic"
    GOVERNMENT = "government"
    PROFESSIONAL = "professional"
    SOCIAL = "social"
    TECHNICAL = "technical"
    NEWS = "news"
    BLOG = "blog"
    FORUM = "forum"
    DATABASE = "database"
    REPOSITORY = "repository"
    OTHER = "other"


@dataclass
class Metadata:
    """Standardized metadata for documents."""
    # Core identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    keywords: List[str] = field(default_factory=list)
    
    # Publication information
    publication_date: Optional[datetime] = None
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    venue: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    
    # Identifiers
    doi: Optional[str] = None
    pmid: Optional[str] = None
    arxiv_id: Optional[str] = None
    isbn: Optional[str] = None
    issn: Optional[str] = None
    
    # Source information
    url: str = ""
    source_url: str = ""
    source_type: SourceType = SourceType.OTHER
    source_name: str = ""
    
    # Content information
    content_type: ContentType = ContentType.OTHER
    document_type: DocumentType = DocumentType.OTHER
    language: str = "en"
    word_count: int = 0
    page_count: int = 0
    
    # Quality metrics
    relevance_score: float = 0.0
    quality_score: float = 0.0
    confidence_score: float = 0.0
    
    # Processing information
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    
    # File information
    file_path: Optional[str] = None
    file_size: int = 0
    file_hash: Optional[str] = None
    download_url: Optional[str] = None
    
    # Additional metadata
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    # Access information
    access_level: str = "public"  # public, restricted, private
    license: Optional[str] = None
    copyright: Optional[str] = None
    
    # Quality control
    is_duplicate: bool = False
    is_processed: bool = False
    is_verified: bool = False
    error_message: Optional[str] = None


@dataclass
class AcademicDocument:
    """Academic document with full metadata."""
    metadata: Metadata
    
    # Content
    content: str = ""
    full_text: str = ""
    summary: str = ""
    
    # Academic specific
    citations: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    funding: List[str] = field(default_factory=list)
    acknowledgments: str = ""
    
    # Research metrics
    citation_count: int = 0
    download_count: int = 0
    view_count: int = 0
    
    # Academic classification
    subject_areas: List[str] = field(default_factory=list)
    research_fields: List[str] = field(default_factory=list)
    methodologies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.metadata.id,
            'title': self.metadata.title,
            'authors': self.metadata.authors,
            'abstract': self.metadata.abstract,
            'keywords': self.metadata.keywords,
            'publication_date': self.metadata.publication_date,
            'publication_year': self.metadata.publication_year,
            'journal': self.metadata.journal,
            'venue': self.metadata.venue,
            'doi': self.metadata.doi,
            'url': self.metadata.url,
            'source_type': self.metadata.source_type.value,
            'content_type': self.metadata.content_type.value,
            'document_type': self.metadata.document_type.value,
            'language': self.metadata.language,
            'word_count': self.metadata.word_count,
            'relevance_score': self.metadata.relevance_score,
            'quality_score': self.metadata.quality_score,
            'content': self.content,
            'full_text': self.full_text,
            'citations': self.citations,
            'references': self.references,
            'citation_count': self.citation_count,
            'subject_areas': self.subject_areas,
            'created_at': self.metadata.created_at,
            'updated_at': self.metadata.updated_at
        }


@dataclass
class WebDocument:
    """Web document with full metadata."""
    metadata: Metadata
    
    # Content
    content: str = ""
    html_content: str = ""
    text_content: str = ""
    
    # Web specific
    domain: str = ""
    path: str = ""
    query_params: Dict[str, str] = field(default_factory=dict)
    
    # Social metrics
    likes: int = 0
    shares: int = 0
    comments: int = 0
    views: int = 0
    
    # Web classification
    content_category: str = ""
    sentiment: str = ""
    readability_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.metadata.id,
            'title': self.metadata.title,
            'authors': self.metadata.authors,
            'abstract': self.metadata.abstract,
            'keywords': self.metadata.keywords,
            'publication_date': self.metadata.publication_date,
            'url': self.metadata.url,
            'source_type': self.metadata.source_type.value,
            'content_type': self.metadata.content_type.value,
            'document_type': self.metadata.document_type.value,
            'language': self.metadata.language,
            'word_count': self.metadata.word_count,
            'relevance_score': self.metadata.relevance_score,
            'quality_score': self.metadata.quality_score,
            'content': self.content,
            'html_content': self.html_content,
            'domain': self.domain,
            'likes': self.likes,
            'shares': self.shares,
            'comments': self.comments,
            'content_category': self.content_category,
            'created_at': self.metadata.created_at,
            'updated_at': self.metadata.updated_at
        }


def create_metadata(
    title: str,
    authors: List[str] = None,
    abstract: str = "",
    keywords: List[str] = None,
    url: str = "",
    source_type: SourceType = SourceType.OTHER,
    content_type: ContentType = ContentType.OTHER,
    document_type: DocumentType = DocumentType.OTHER,
    **kwargs
) -> Metadata:
    """Create metadata object with default values."""
    return Metadata(
        title=title,
        authors=authors or [],
        abstract=abstract,
        keywords=keywords or [],
        url=url,
        source_type=source_type,
        content_type=content_type,
        document_type=document_type,
        **kwargs
    )


def create_academic_document(
    title: str,
    authors: List[str] = None,
    abstract: str = "",
    content: str = "",
    **kwargs
) -> AcademicDocument:
    """Create academic document with metadata."""
    # Remove source_type from kwargs if present
    kwargs.pop('source_type', None)
    
    metadata = create_metadata(
        title=title,
        authors=authors or [],
        abstract=abstract,
        source_type=SourceType.ACADEMIC,
        document_type=DocumentType.ACADEMIC_PAPER,
        **kwargs
    )
    return AcademicDocument(metadata=metadata, content=content)


def create_web_document(
    title: str,
    content: str = "",
    url: str = "",
    source_type: SourceType = SourceType.TECHNICAL,
    **kwargs
) -> WebDocument:
    """Create web document with metadata."""
    # Remove source_type from kwargs if present
    kwargs.pop('source_type', None)
    
    metadata = create_metadata(
        title=title,
        url=url,
        source_type=source_type,
        document_type=DocumentType.BLOG_POST,
        **kwargs
    )
    return WebDocument(metadata=metadata, content=content)
