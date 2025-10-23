"""
Universal Content Discovery System - Sources Module

This module provides integration with various academic and web sources
for content discovery and data collection.
"""

from .academic_sources import AcademicSourceManager
from .web_sources import WebSourceManager
from .content_fetcher import ContentFetcher

__all__ = [
    'AcademicSourceManager',
    'WebSourceManager', 
    'ContentFetcher'
]
