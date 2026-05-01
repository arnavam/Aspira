import numpy as np
import logging
import os

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Document

from logger_config import get_logger

# Define logger for corpus debugging
corpus_logger = get_logger("corpus_debug")
corpus_logger.setLevel(logging.DEBUG)

# File handler for corpus debug - if user wants a specific file
# Ensuring the directory exists
os.makedirs("log", exist_ok=True)
c_handler = logging.FileHandler('log/corpus_debug.log', encoding='utf-8')
c_handler.setLevel(logging.DEBUG)
c_formatter = logging.Formatter('%(asctime)s - %(message)s')
c_handler.setFormatter(c_formatter)

if not corpus_logger.hasHandlers():
    corpus_logger.addHandler(c_handler)


def split_text_into_chunks(text, max_tokens=1024):
    from textblob import TextBlob

    blob = TextBlob(text)
    sentences = [str(sentence).strip() for sentence in blob.sentences]

    chunks = []
    current_chunk = []
    current_length = 0
    max_words_per_chunk = max_tokens * 3 // 4  # approximate word limit

    for sentence in sentences:
        sentence_length = len(sentence.split())
        # If adding this sentence exceeds chunk limit, start a new chunk
        if current_length + sentence_length > max_words_per_chunk and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.append(sentence)
        current_length += sentence_length

    # Add the last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def retrieve_relevant_chunks(chunks: list, query: str, top_k: int = 5) -> list:
    """Retrieve relevant chunks using Vector RAG."""
    from L_llamaindex_rag import VectorRAGBuilder

    rag_builder = VectorRAGBuilder()
    rag_builder.create_index(chunks)

    results = rag_builder.retrieve(query, top_k=top_k)
    relevant = [item["chunk"] for item in results] if results else chunks
    return relevant


def textrank(text, source_link=None):
    import networkx as nx
    from sklearn.metrics.pairwise import cosine_similarity
    from model_cache import get_spacy
    nlp = get_spacy()
    if not text:
        return {}

    doc = nlp(text)
    sentences = list(doc.sents)

    sentence_vectors = [sent.vector for sent in sentences]

    sim_matrix = cosine_similarity(sentence_vectors)
    nx_graph = nx.from_numpy_array(sim_matrix)

    scores = nx.pagerank(nx_graph)

    ranked = sorted(((str(sent), scores[i]) for i, sent in enumerate(
        sentences)), key=lambda item: item[1], reverse=True)

    top_sent = dict(ranked[:int(len(ranked)*0.4)])

    # Log to corpus debug logger
    if source_link:
        corpus_logger.debug(f"\n\n=== SOURCE: {source_link} ===")
        for sentence in top_sent.keys():
            corpus_logger.debug(f"{sentence}")
        corpus_logger.debug("----------------------------------")

    return top_sent


def summrize(text, max_tokens=200):
    from model_cache import get_summarizer

    summarizer = get_summarizer()
    # long_text = """
    # Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term "artificial intelligence" is often used to describe machines (or computers) that mimic "cognitive" functions that humans associate with the human mind, such as "learning" and "problem solving." ...
    # """  # Make sure this text is long enough to exceed the token limit
    chunks = split_text_into_chunks(text, max_tokens)
    summaries = [summarizer(chunk, max_length=len(chunk.split())//2, min_length=len(
        chunk.split())//4, do_sample=False)[0]['summary_text'] for chunk in chunks]
    print('f')

    return summaries


if __name__ == '__main__':
    large_text = """
        Wikipedia is a free online encyclopedia, created and edited by volunteers around the world and hosted by the Wikimedia Foundation.
        The 30 million articles in English have about 5 million editors, and more than 500 million articles exist in all languages.
        Content is written collaboratively by largely anonymous volunteers who write without pay.
        Anyone with internet access can write and make changes to Wikipedia articles, except in limited cases where editing is restricted to prevent disruption or vandalism.
        """

    chunks = split_text_into_chunks(large_text, max_tokens=50)
    print(f"Total chunks: {len(chunks)}{type(chunks)}")
    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i}:\n{chunk}")
    sent = textrank(large_text)
