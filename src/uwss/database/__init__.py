"""
Universal Web Crawling System - Database Module

This module provides database integration capabilities for storing
and managing academic data with full metadata.
"""

from .postgresql_manager import PostgreSQLManager
from .data_models import AcademicDocument, WebDocument, Metadata
from .data_processor import DataProcessor

__all__ = [
    'PostgreSQLManager',
    'AcademicDocument', 
    'WebDocument',
    'Metadata',
    'DataProcessor'
]
