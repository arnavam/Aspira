"""
LlamaIndex Vector RAG Module for Aspira

Uses LlamaIndex to create a vector store from text chunks and retrieve
relevant context for question generation.
"""

import os
import logging
import warnings
from typing import List, Dict

# Suppress warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", message=".*unpickleable.*")
warnings.filterwarnings("ignore", category=UserWarning, module="llama_index")
logging.getLogger("root").setLevel(logging.ERROR)

# Try to import LlamaIndex components
try:
    from llama_index.core import Document, VectorStoreIndex, Settings
    from M_embeddings import LlamaCppEmbedding
    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False
    print("Warning: LlamaIndex not found. Please install: pip install llama-index")

logger = logging.getLogger(__name__)

class VectorRAGBuilder:
    """Builds a vector index and retrieves relevant chunks."""
    
    def __init__(self):
        """Initialize the RAG builder."""
        self.index = None
        
        if LLAMA_INDEX_AVAILABLE:
            # Configure embedding model (uses llama-cpp-python)
            Settings.embed_model = LlamaCppEmbedding()
            # We don't need an LLM for vector retrieval, just embeddings
            Settings.llm = None 
    
    def create_index(self, chunks: List[str]):
        """
        Create a vector index from text chunks.
        
        Args:
            chunks: List of text strings to index
        """
        if not LLAMA_INDEX_AVAILABLE:
            logger.error("LlamaIndex not available. Cannot create index.")
            return

        if not chunks:
            logger.warning("No chunks provided for indexing.")
            return

        # Create Documents
        documents = [Document(text=chunk) for chunk in chunks]
        
        # Create Index (this builds the vector store in memory)
        logger.info(f"Creating vector index for {len(documents)} documents...")
        self.index = VectorStoreIndex.from_documents(documents)
        logger.info("Vector index created.")
    
    def create_index_parallel(self, texts: List[str], num_workers: int = 4):
        """
        Create index with parallel chunking and embedding using IngestionPipeline.
        
        Args:
            texts: List of raw text strings (will be chunked automatically)
            num_workers: Number of parallel workers for ingestion
        """
        if not LLAMA_INDEX_AVAILABLE:
            logger.error("LlamaIndex not available. Cannot create index.")
            return
        
        if not texts:
            logger.warning("No texts provided for indexing.")
            return
        
        from llama_index.core.ingestion import IngestionPipeline
        from llama_index.core.node_parser import SentenceSplitter
        
        # Create pipeline with chunking + embedding
        pipeline = IngestionPipeline(
            transformations=[
                SentenceSplitter(chunk_size=512, chunk_overlap=50),
                Settings.embed_model,
            ]
        )
        
        # Create documents from raw texts
        documents = [Document(text=text) for text in texts]
        
        # Run pipeline in parallel
        logger.info(f"Running parallel ingestion for {len(documents)} documents with {num_workers} workers...")
        nodes = pipeline.run(documents=documents, num_workers=num_workers)
        
        # Create index from nodes
        self.index = VectorStoreIndex(nodes)
        logger.info(f"Vector index created with {len(nodes)} nodes.")
        
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: The search query (usually user answer)
            top_k: Number of chunks to retrieve
            
        Returns:
            List of dicts: [{"chunk": text, "score": float}, ...]
        """
        if not self.index:
            logger.warning("Index not created. Returning empty list.")
            return []
            
        # Create retriever
        retriever = self.index.as_retriever(similarity_top_k=top_k)
        
        # Retrieve nodes
        nodes = retriever.retrieve(query)
        
        results = []
        for node in nodes:
            results.append({
                "chunk": node.text,
                "score": node.score
            })
            
        return results

# Fallback implementation if LlamaIndex is strictly not available but user wants "simulated" RAG
# (We already have this in the main file via compute_similarity, but this file is specific for LlamaIndex)
