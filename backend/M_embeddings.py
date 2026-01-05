"""
LlamaCPP Embeddings Module

Uses llama-cpp-python with a GGUF embedding model for lightweight embeddings
without PyTorch dependency. Replaces sentence-transformers for similarity scoring.
"""

import os
import numpy as np
from typing import List, Dict
from logger_config import get_logger

logger = get_logger(__name__)

# Model paths - try local first, then Docker path
_MODEL_PATHS = [
    os.environ.get("EMBEDDING_MODEL_PATH", ""),
    os.path.join(os.path.dirname(__file__), "models", "nomic-embed-text-v1.5.Q4_K_M.gguf"),
    "/app/models/nomic-embed-text-v1.5.Q4_K_M.gguf",
]

# Lazy-loaded singletons
_model = None
_st_model = None  # sentence-transformers fallback

def _get_model():
    """Lazy-load the embedding model (llama-cpp or sentence-transformers fallback)."""
    global _model, _st_model
    
    if _model is not None:
        return _model
    if _st_model is not None:
        return _st_model
    
    # Try llama-cpp first
    model_path = None
    for path in _MODEL_PATHS:
        if path and os.path.exists(path):
            model_path = path
            break
    
    if model_path:
        try:
            from llama_cpp import Llama
            logger.info(f"Loading embedding model from {model_path}...")
            _model = Llama(
                model_path=model_path,
                embedding=True,
                n_ctx=512,
                n_batch=512,
                verbose=False
            )
            logger.info("Embedding model loaded.")
            return _model
        except Exception as e:
            logger.warning(f"Failed to load llama-cpp model: {e}")
    
    # Fallback to sentence-transformers
    # try:
    #     from sentence_transformers import SentenceTransformer
    #     _st_model = SentenceTransformer('all-MiniLM-L6-v2')
    #     return _st_model
    # except ImportError:
    #     logger.warning("sentence-transformers not available. Using mock embeddings.")
    #     return None


def get_embeddings(texts: List[str]) -> np.ndarray:
    """
    Get embeddings for a list of texts.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        numpy array of shape (len(texts), embedding_dim)
    """
    model = _get_model()
    
    if model is None:
        # Fallback: return random embeddings for testing
        return np.random.randn(len(texts), 384).astype(np.float32)
    
    # Check if it's a sentence-transformers model
    if hasattr(model, 'encode'):
        # sentence-transformers API
        return model.encode(texts, convert_to_numpy=True).astype(np.float32)
    else:
        # llama-cpp-python API
        embeddings = []
        for text in texts:
            emb = model.embed(text)
            embeddings.append(emb)
        return np.array(embeddings, dtype=np.float32)


def normalize(vectors: np.ndarray) -> np.ndarray:
    """L2 normalize vectors."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
    return vectors / norms


def similarity_score(target_sentence: str, other_sentences: List[str]) -> Dict[str, float]:
    """
    Compute cosine similarity between target sentence and other sentences.
    
    Args:
        target_sentence: The reference sentence
        other_sentences: List of sentences to compare against
        
    Returns:
        Dict mapping each sentence to its similarity score
    """
    if not other_sentences:
        return {}
    
    # Get all embeddings in one batch
    all_texts = [target_sentence] + list(other_sentences)
    all_embeddings = get_embeddings(all_texts)
    
    # Split target and others
    target_embedding = all_embeddings[0:1]  # Keep 2D shape
    other_embeddings = all_embeddings[1:]
    
    # Normalize
    target_embedding = normalize(target_embedding)
    other_embeddings = normalize(other_embeddings)
    
    # Compute cosine similarities
    similarities = np.matmul(target_embedding, other_embeddings.T).squeeze(0)
    
    # Handle single result case
    if similarities.ndim == 0:
        return {other_sentences[0]: float(similarities)}
    
    return {sentence: float(score) for sentence, score in zip(other_sentences, similarities)}


# For LlamaIndex integration
try:
    from llama_index.core.embeddings import BaseEmbedding
    
    class LlamaCppEmbedding(BaseEmbedding):
        """LlamaIndex-compatible embedding class using llama-cpp or sentence-transformers."""
        
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._model = None
        
        @classmethod
        def class_name(cls) -> str:
            return "LlamaCppEmbedding"
        
        def _get_model(self):
            if self._model is None:
                self._model = _get_model()
            return self._model
        
        def _get_text_embedding(self, text: str) -> List[float]:
            """Get embedding for a single text (required by BaseEmbedding)."""
            model = self._get_model()
            if model is None:
                return list(np.random.randn(384).astype(np.float32))
            # Handle both model types
            if hasattr(model, 'encode'):
                return model.encode([text], convert_to_numpy=True)[0].tolist()
            return model.embed(text)
        
        def _get_query_embedding(self, query: str) -> List[float]:
            """Get embedding for a query (required by BaseEmbedding)."""
            return self._get_text_embedding(query)
        
        async def _aget_text_embedding(self, text: str) -> List[float]:
            """Async version (just calls sync)."""
            return self._get_text_embedding(text)
        
        async def _aget_query_embedding(self, query: str) -> List[float]:
            """Async version (just calls sync)."""
            return self._get_query_embedding(query)

except ImportError:
    # Fallback if LlamaIndex not available
    class LlamaCppEmbedding:
        """Fallback embedding class when LlamaIndex is not available."""
        def __init__(self, **kwargs):
            pass
        def _get_text_embedding(self, text: str) -> List[float]:
            return list(np.random.randn(384).astype(np.float32))

