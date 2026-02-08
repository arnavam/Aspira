"""
Model Cache - Centralized lazy loading for expensive ML models.

This module provides cached singleton instances of ML models to avoid
reloading them on every function call. Models are loaded once on first
use and reused thereafter.

Usage:
    from model_cache import get_spacy, get_keybert

    nlp = get_spacy()  # First call loads, subsequent calls reuse
"""

import os
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# Cached Model Instances
# =============================================================================

_SPACY_MODEL = None
_KEYBERT_MODEL = None
_SUMMARIZER = None


def get_keybert():
    """
    Lazy-load KeyBERT model once, reuse forever.
    
    Returns:
        KeyBERT: The loaded KeyBERT model
    """
    global _KEYBERT_MODEL
    if _KEYBERT_MODEL is None:
        from keybert import KeyBERT
        logger.info("Loading KeyBERT model...")
        _KEYBERT_MODEL = KeyBERT()
        logger.info("KeyBERT model loaded successfully")
    return _KEYBERT_MODEL

