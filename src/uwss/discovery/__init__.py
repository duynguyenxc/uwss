"""
Universal Content Discovery System - Discovery Module

This module provides intelligent source discovery and crawling capabilities
for the Universal Content Discovery System.
"""

from .intelligent_discovery import IntelligentSourceDiscovery
from .intelligent_crawling import IntelligentCrawlingEngine
from .source_classifier import SourceClassifier

__all__ = [
    'IntelligentSourceDiscovery',
    'IntelligentCrawlingEngine',
    'SourceClassifier'
]