"""
LlamaIndex PropertyGraph Module for Aspira

Extracts entities and relationships from document chunks,
builds a knowledge graph, and exports to JSON.

Supports multiple extractors:
- "spacy": Fast, local, no API calls (default)
- "groq": Better relationship extraction (requires API)
"""

import glob
import json
import logging
import os
from typing import Optional
from M_embeddings import similarity_score


from logger_config import get_logger

logger = get_logger(__name__)

# =============================================================================
# Knowledge Graph File Management
# =============================================================================


def get_next_run_id() -> int:
    """Find next available run ID for knowledge graph file."""
    existing = glob.glob("log/knowledge_map_*.json")
    if not existing:
        return 1
    numbers = []
    for f in existing:
        try:
            num = int(f.replace("log/knowledge_map_", "").replace(".json", ""))
            numbers.append(num)
        except ValueError:
            pass
    return max(numbers) + 1 if numbers else 1


def get_knowledge_graph_filepath() -> str:
    """Get the current session's knowledge graph filepath."""
    run_id = get_next_run_id()
    return f"log/knowledge_map_{run_id}.json"


# Note: LlamaIndex imports commented out for now (using spaCy-based extraction)
# To switch to LLM-based extraction, uncomment and install llama-index-llms-groq
# from llama_index.core import Document, PropertyGraphIndex
# from llama_index.core.indices.property_graph import SimpleLLMPathExtractor


class KnowledgeGraphBuilder:

    """Builds and manages a knowledge graph from text chunks."""

    # Class-level LLM (lazy loaded)
    _llm = None

    def __init__(self, extractor_type: str = "spacy"):
        """
        Initialize the knowledge graph builder.

        Args:
            extractor_type: "spacy" (local NER) or "llm" (llama-cpp based)
        """
        import networkx as nx
        self.extractor_type = extractor_type
        self.graph = nx.DiGraph()
        self.nodes = []
        self.edges = []

        # Initialize LLM if needed
        if extractor_type == "llm" and KnowledgeGraphBuilder._llm is None:
            self._init_llm()

    @classmethod
    def _init_llm(cls):
        """Initialize llama-cpp LLM (lazy loading)."""
        from llama_cpp import Llama

        # Use llama-server's default model path or download a small model
        model_path = os.environ.get("LLAMA_MODEL_PATH")

        if model_path and os.path.exists(model_path):
            logger.info(f"Loading LLM from: {model_path}")
            cls._llm = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=4,
                verbose=False
            )
        else:
            # Download a small model from HuggingFace
            logger.info("Downloading small LLM model (Qwen2.5-0.5B)...")
            cls._llm = Llama.from_pretrained(
                repo_id="Qwen/Qwen2.5-0.5B-Instruct-GGUF",
                filename="qwen2.5-0.5b-instruct-q4_k_m.gguf",
                n_ctx=2048,
                n_threads=4,
                verbose=False
            )

    def extract_topics_spacy(self, text: str) -> list:
        """Extract topics/entities using spaCy NER."""
        import networkx as nx
        import torch
        import torch.nn.functional as F
        from model_cache import get_spacy

        nlp = get_spacy()
        doc = nlp(text)
        topics = []

        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART", "LAW", "LANGUAGE",
                              "EVENT", "FAC", "GPE", "NORP", "PERSON"]:
                topics.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })

        # Extract noun chunks as potential topics
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= 2:  # Multi-word phrases
                topics.append({
                    "text": chunk.text,
                    "label": "TOPIC",
                    "start": chunk.start_char,
                    "end": chunk.end_char
                })

        # Deduplicate by text
        seen = set()
        unique_topics = []
        for t in topics:
            if t["text"].lower() not in seen:
                seen.add(t["text"].lower())
                unique_topics.append(t)

        return unique_topics

    def extract_topics_llm(self, text: str) -> list:
        """Extract topics/entities using LLM (llama-cpp)."""
        if KnowledgeGraphBuilder._llm is None:
            logger.warning("LLM not available, falling back to spaCy")
            return self.extract_topics_spacy(text)

        prompt = f"""Extract key topics, entities, and concepts from this text.
Return as a JSON list of objects with "text" and "label" fields.
Labels should be: SKILL, ROLE, ORG, CONCEPT, TOOL, or TOPIC.

Text: {text[:500]}

Return ONLY valid JSON, no explanation. Example:
[{{"text": "machine learning", "label": "SKILL"}},
    {{"text": "Google", "label": "ORG"}}]

JSON:"""

        response = KnowledgeGraphBuilder._llm(
            prompt,
            max_tokens=200,
            temperature=0.1,
            stop=["\n\n", "```"]
        )

        result_text = response["choices"][0]["text"].strip()

        # Parse JSON
        import re
        # Find JSON array in response
        json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
        if json_match:
            topics_raw = json.loads(json_match.group())
            topics = [
                {"text": t.get("text", ""), "label": t.get("label", "TOPIC")}
                for t in topics_raw if t.get("text")
            ]
            return topics[:10]  # Limit to 10 topics

        return []  # No JSON match found

    def extract_topics(self, text: str) -> list:
        """Extract topics using the configured extractor."""
        if self.extractor_type == "llm":
            return self.extract_topics_llm(text)
        return self.extract_topics_spacy(text)

    def extract_relationships(self, text: str, entities: list = None) -> list:
        """
        Extract semantic relationships between entities using LLM.

        Returns:
            list: [{"source": "Python", "relation": "required_for", "target": "Data Science"}, ...]
        """
        if KnowledgeGraphBuilder._llm is None:
            return []

        # Get entities if not provided
        if not entities:
            topics = self.extract_topics(text)
            entities = [t["text"] for t in topics]

        if len(entities) < 2:
            return []

        entity_str = ", ".join(entities[:10])

        prompt = f"""Extract relationships between these entities from the context.

Context: "{text[:500]}"

Entities: {entity_str}

VALID RELATIONS: required_for, subset_of, used_in, enables, related_to

Return JSON array of relationships:
[{{"source": "entity1", "relation": "relation_type", "target": "entity2"}}]

Only include relationships clearly implied by the context. Return [] if none found.

JSON:"""

        try:
            response = KnowledgeGraphBuilder._llm(
                prompt,
                max_tokens=300,
                temperature=0.1,
                stop=["\n\n", "```"]
            )

            result_text = response["choices"][0]["text"].strip()

            # Parse JSON
            import re
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                relationships = json.loads(json_match.group())
                # Validate relationships
                valid_relations = ["required_for", "subset_of",
                                   "used_in", "enables", "related_to"]
                validated = []
                for rel in relationships:
                    if (rel.get("source") and rel.get("target") and
                            rel.get("relation") in valid_relations):
                        validated.append(rel)
                return validated[:10]  # Limit to 10 relationships

        except Exception as e:
            logger.warning(f"Relationship extraction failed: {e}")

        return []

    def get_related_context(self, concept: str, depth: int = 2) -> list:
        """
        Traverse graph to find related concepts using BFS.

        Args:
            concept: Starting concept to search from
            depth: How many hops to traverse

        Returns:
            list: Related node contents
        """
        if not self.graph.nodes():
            return []

        # Find node matching concept
        start_node = None
        for node_id, data in self.graph.nodes(data=True):
            if concept.lower() in str(data.get("content", "")).lower():
                start_node = node_id
                break

        if not start_node:
            return []

        # BFS traversal
        visited = set()
        queue = [(start_node, 0)]
        related_content = []

        while queue:
            node, d = queue.pop(0)
            if node in visited or d > depth:
                continue
            visited.add(node)

            node_data = self.graph.nodes[node]
            if node_data.get("content"):
                related_content.append({
                    "id": node,
                    "type": node_data.get("type"),
                    "content": node_data.get("content"),
                    "depth": d
                })

            # Add neighbors to queue
            for neighbor in self.graph.neighbors(node):
                if neighbor not in visited:
                    queue.append((neighbor, d + 1))

        return related_content

    def compute_similarity(self, text1: str, texts: list) -> dict:
        """Compute cosine similarity between text1 and a list of texts."""
        return similarity_score(text1, texts)

    def find_relevant_chunks(self, answer: str, chunks: list, threshold: float = 0.3) -> list:
        """Find chunks relevant to the user's answer."""
        if not chunks:
            return []

        similarities = self.compute_similarity(answer, chunks)
        relevant = [
            {"chunk": chunk, "similarity": score}
            for chunk, score in similarities.items()
            if score >= threshold
        ]

        # Sort by similarity (highest first)
        relevant.sort(key=lambda x: x["similarity"], reverse=True)

        return relevant

    def build_graph(self, answer: str, chunks: list, questions: list, session_id: int = None, source_urls: list = None, keywords: dict = None) -> dict:
        """
        Build the knowledge graph with hierarchy: Answer -> Keywords -> URLs -> Documents -> Topics -> Questions.
        """
        self.graph.clear()
        self.nodes = []
        self.edges = []

        # Use session_id to create unique node IDs
        prefix = f"s{session_id}_" if session_id else ""

        # 1. Answer Node (Level 0)
        answer_id = f"{prefix}answer"
        self.graph.add_node(answer_id, type="answer", content=answer[:200])
        self.nodes.append(
            {"id": answer_id, "type": "answer", "content": answer[:200]})

        # 2. Keywords Nodes (Level 1)
        # keywords is dict {word: score}
        keyword_ids = {}
        if keywords:
            for i, (kw, score) in enumerate(list(keywords.items())[:5]):
                kw_id = f"{prefix}kw_{i}"
                keyword_ids[kw] = kw_id

                self.graph.add_node(kw_id, type="keyword",
                                    content=kw, score=score)
                self.nodes.append(
                    {"id": kw_id, "type": "keyword", "content": kw, "score": score})

                # Edge: Answer -> Keyword
                self.graph.add_edge(answer_id, kw_id, relation="has_keyword")
                self.edges.append(
                    {"source": answer_id, "target": kw_id, "relation": "has_keyword"})

        # 3. Source URL Nodes (Level 2)
        url_ids = {}
        if source_urls:
            for i, url in enumerate(source_urls[:5]):
                url_id = f"{prefix}url_{i}"
                url_ids[url] = url_id

                # Use content for display
                self.graph.add_node(url_id, type="source", content=url)
                self.nodes.append(
                    {"id": url_id, "type": "source", "content": url, "url": url})

                # Edge: Keyword -> Source (Many-to-Many heuristic: link all top keywords to sources)
                # Ideally we know which keyword found which source, but for now we link all.
                for kw_id in keyword_ids.values():
                    self.graph.add_edge(kw_id, url_id, relation="found_source")
                    self.edges.append(
                        {"source": kw_id, "target": url_id, "relation": "found_source"})

        # 4. Document Nodes (Chunks) (Level 3)
        chunk_ids = []
        relevant_chunks = self.find_relevant_chunks(answer, chunks)

        for i, item in enumerate(relevant_chunks[:5]):
            chunk_id = f"{prefix}chunk_{i}"
            chunk_text = item["chunk"][:300]
            chunk_ids.append(chunk_id)

            self.graph.add_node(chunk_id, type="document", content=chunk_text)
            self.nodes.append(
                {"id": chunk_id, "type": "document", "content": chunk_text})

            # Edge: Source -> Document
            # Since we lost strict lineage, link generic Source -> Document
            # If no source_urls, link Answer -> Document as fallback
            if url_ids:
                # Link each doc to the first source (simplification) or all?
                # Let's link to the first source to avoid cluttered mesh, or random distribution.
                # User model: Source -> Document.
                # Let's link all sources to all documents? (A bit messy)
                # Let's link each document to the *first* source as a primary lineage visual.
                first_url_id = list(url_ids.values())[0]
                self.graph.add_edge(first_url_id, chunk_id,
                                    relation="contains_text")
                self.edges.append(
                    {"source": first_url_id, "target": chunk_id, "relation": "contains_text"})
            else:
                # Fallback if no URLs
                self.graph.add_edge(answer_id, chunk_id, relation="matches")
                self.edges.append(
                    {"source": answer_id, "target": chunk_id, "relation": "matches"})

        # 5. Topic Nodes (Level 4)
        topic_ids = {}
        for chunk_id, item in zip(chunk_ids, relevant_chunks[:5]):
            chunk_text = item["chunk"]
            chunk_topics = self.extract_topics(chunk_text)

            for topic in chunk_topics[:3]:
                if topic["text"] in topic_ids:
                    tid = topic_ids[topic["text"]]
                else:
                    tid = f"{prefix}topic_{len(topic_ids)}"
                    topic_ids[topic["text"]] = tid

                    self.graph.add_node(tid, type="topic",
                                        content=topic["text"])
                    self.nodes.append(
                        {"id": tid, "type": "topic", "content": topic["text"]})

                # Edge: Document -> Topic
                if not self.graph.has_edge(chunk_id, tid):
                    self.graph.add_edge(
                        chunk_id, tid, relation="mentions_topic")
                    self.edges.append(
                        {"source": chunk_id, "target": tid, "relation": "mentions_topic"})

        # 6. Question Nodes (Level 5)
        # Questions from Document/Topics
        # Ensure questions are not standalone
        all_topic_ids = list(topic_ids.values())

        for i, question in enumerate(questions[:5]):
            q_id = f"{prefix}question_{i}"

            self.graph.add_node(q_id, type="question", content=question)
            self.nodes.append(
                {"id": q_id, "type": "question", "content": question})

            # Find relevant topics
            q_topics = self.extract_topics(question)
            linked = False

            for qt in q_topics:
                if qt["text"] in topic_ids:
                    tid = topic_ids[qt["text"]]
                    self.graph.add_edge(tid, q_id, relation="asks_about")
                    self.edges.append(
                        {"source": tid, "target": q_id, "relation": "asks_about"})
                    linked = True

            # Fallback 1: if no specific topic matched, link to the first topic found in this turn
            if not linked and all_topic_ids:
                fallback_tid = all_topic_ids[0]
                self.graph.add_edge(fallback_tid, q_id,
                                    relation="asks_about_related")
                self.edges.append(
                    {"source": fallback_tid, "target": q_id, "relation": "asks_about_related"})
                linked = True

            # Fallback 2: if still not linked (no topics at all), link directly to the Answer node
            if not linked:
                self.graph.add_edge(answer_id, q_id, relation="next_question")
                self.edges.append(
                    {"source": answer_id, "target": q_id, "relation": "next_question"})

        return self.to_json()

    def to_json(self) -> dict:
        """Convert the graph to JSON format."""
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "summary": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "node_types": {
                    "answer": len([n for n in self.nodes if n["type"] == "answer"]),
                    "source": len([n for n in self.nodes if n["type"] == "source"]),
                    "topic": len([n for n in self.nodes if n["type"] == "topic"]),
                    "document": len([n for n in self.nodes if n["type"] == "document"]),
                    "question": len([n for n in self.nodes if n["type"] == "question"])
                }
            }
        }

    def save_to_file(self, filepath: str = "log/knowledge_map.json"):
        """Save the knowledge graph to a JSON file, appending to existing data."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Load existing data if file exists
        existing_data = {"nodes": [], "edges": []}
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        # Append new nodes and edges
        current_data = self.to_json()
        existing_data["nodes"].extend(current_data["nodes"])
        existing_data["edges"].extend(current_data["edges"])

        # Update summary
        existing_data["summary"] = {
            "total_nodes": len(existing_data["nodes"]),
            "total_edges": len(existing_data["edges"]),
            "node_types": {
                "answer": len([n for n in existing_data["nodes"] if n["type"] == "answer"]),
                "document": len([n for n in existing_data["nodes"] if n["type"] == "document"]),
                "topic": len([n for n in existing_data["nodes"] if n["type"] == "topic"]),
                "question": len([n for n in existing_data["nodes"] if n["type"] == "question"])
            }
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Knowledge map saved to {filepath}")
        return filepath

    def get_relevant_chunks_for_questions(self) -> list:
        """Return only the relevant chunks for question generation."""
        return [
            node["content"] for node in self.nodes
            if node["type"] == "document"
        ]

    def get_topics(self) -> list:
        """Return all extracted topics."""
        return [
            node["content"] for node in self.nodes
            if node["type"] == "topic"
        ]


# Convenience function for integration
# Convenience function for integration
def build_knowledge_graph(answer: str, chunks: list, questions: list,
                          save_path: str = "log/knowledge_map.json",
                          keywords: dict = None,
                          source_urls: list = None) -> dict:
    """
    Build a knowledge graph and save to file.

    Args:
        answer: User's answer text
        chunks: List of document chunks from search
        questions: Generated interview questions
        save_path: Path to save the JSON file
        keywords: Input keywords dict
        source_urls: List of source URLs

    Returns:
        dict: The knowledge graph as JSON
    """
    builder = KnowledgeGraphBuilder(extractor_type="spacy")
    graph_data = builder.build_graph(
        answer, chunks, questions, source_urls=source_urls, keywords=keywords)
    builder.save_to_file(save_path)

    return graph_data


def build_knowledge_graph_from_state(state: dict, chunks: list, questions: list,
                                      existing_graph: dict = None, turn_id: int = 0) -> dict:
    """
    Build a knowledge graph from LangGraph state, merging into an existing graph if provided.

    Args:
        state: AgentState dict with history, keywords, scraped_content, etc.
        chunks: List of document chunks (relevant_chunks or all_texts)
        questions: Generated interview questions
        existing_graph: Optional dict with 'nodes' and 'edges' from the DB to merge into.

    Returns:
        dict: The merged knowledge graph as JSON with 'stats' and 'data' keys.
    """
    # Extract answer from history
    history = state.get("history", [])
    answer = ""
    if history:
        last_msg = history[-1]
        answer = last_msg.replace("User: ", "") if last_msg.startswith(
            "User: ") else last_msg

    # Extract other fields from state
    keywords = state.get("keywords", {})
    scraped_content = state.get("scraped_content", {})
    source_urls = list(scraped_content.keys()) if scraped_content else []

    # Build new graph data for this turn
    builder = KnowledgeGraphBuilder(extractor_type="spacy")
    graph_data = builder.build_graph(
        answer=answer,
        chunks=chunks,
        questions=questions,
        source_urls=source_urls,
        keywords=keywords,
        session_id=turn_id
    )

    # Merge with existing graph if provided
    merged = {"nodes": [], "edges": []}
    if existing_graph and existing_graph.get("nodes"):
        merged["nodes"] = list(existing_graph["nodes"])
        merged["edges"] = list(existing_graph.get("edges", []))

    # Append new nodes and edges from this turn
    merged["nodes"].extend(graph_data.get("nodes", []))
    merged["edges"].extend(graph_data.get("edges", []))

    # Recalculate summary
    merged["summary"] = {
        "total_nodes": len(merged["nodes"]),
        "total_edges": len(merged["edges"]),
        "node_types": {
            "answer": len([n for n in merged["nodes"] if n.get("type") == "answer"]),
            "source": len([n for n in merged["nodes"] if n.get("type") == "source"]),
            "topic": len([n for n in merged["nodes"] if n.get("type") == "topic"]),
            "document": len([n for n in merged["nodes"] if n.get("type") == "document"]),
            "question": len([n for n in merged["nodes"] if n.get("type") == "question"]),
        }
    }

    logger.info(f"Knowledge graph merged: {merged['summary']}")

    return {
        "stats": merged.get("summary", {}),
        "data": merged
    }



if __name__ == "__main__":
    # Test the module
    test_answer = "I want to become a machine learning engineer at Google"
    test_chunks = [
        "Machine learning engineers design and implement ML models using Python and TensorFlow.",
        "Common interview questions for ML roles include explaining gradient descent.",
        "Data scientists analyze large datasets to find patterns.",
        "Software engineers write code and build applications."
    ]
    test_questions = [
        "What is your experience with neural networks?",
        "How do you handle overfitting in machine learning models?",
        "Explain the difference between supervised and unsupervised learning."
    ]

    result = build_knowledge_graph(test_answer, test_chunks, test_questions)
    print(json.dumps(result, indent=2))
