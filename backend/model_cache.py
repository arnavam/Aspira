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

def get_spacy():
    """
    Lazy-load spaCy model once, reuse forever.

    Returns:
        Language: The loaded spaCy model
    """
    global _SPACY_MODEL
    if _SPACY_MODEL is None:
        import spacy
        logger.info("Loading spaCy model...")
        try:
            _SPACY_MODEL = spacy.load("en_core_web_md")
        except OSError:
            logger.warning("en_core_web_md not found. Attempting to download...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_md"], check=True)
            _SPACY_MODEL = spacy.load("en_core_web_md")
        logger.info("spaCy model loaded successfully")
    return _SPACY_MODEL
