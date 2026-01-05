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


def get_spacy():
    """
    Lazy-load spaCy 'en_core_web_md' model once, reuse forever.
    
    Returns:
        spacy.Language: The loaded spaCy model
    """
    global _SPACY_MODEL
    if _SPACY_MODEL is None:
        import spacy
        logger.info("Loading spaCy model (en_core_web_md)...")
        try:
            _SPACY_MODEL = spacy.load("en_core_web_md")
        except OSError:
            logger.warning("spaCy model not found, downloading...")
            os.system("python -m spacy download en_core_web_md")
            _SPACY_MODEL = spacy.load("en_core_web_md")
        _SPACY_MODEL.max_length = 3000000
        logger.info("spaCy model loaded successfully")
    return _SPACY_MODEL


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


def get_summarizer():
    """
    Lazy-load HuggingFace BART summarization pipeline once, reuse forever.
    
    Returns:
        Pipeline: The loaded summarization pipeline
    """
    global _SUMMARIZER
    if _SUMMARIZER is None:
        from transformers import pipeline
        logger.info("Loading BART summarizer model...")
        _SUMMARIZER = pipeline("summarization", model="facebook/bart-large-cnn")
        logger.info("BART summarizer model loaded successfully")
    return _SUMMARIZER
