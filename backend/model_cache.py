"""
Model Cache - Centralized lazy loading for expensive ML models.
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


def initialize_all_models():
    """Eagerly load all NLP models into memory."""
    get_spacy()

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
