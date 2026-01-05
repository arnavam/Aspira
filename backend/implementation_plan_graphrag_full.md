# GraphRAG Integration for Knowledge Graph Extraction

Implement a lightweight GraphRAG system that extracts entities and relationships from scraped interview content, building a knowledge graph that shows connections between the user's answer, relevant document chunks, topics, and generated questions.

## Proposed Changes

### New Module: Graph RAG

#### [NEW] [K_graph_rag.py](file:///Users/arnav/Code/AI_interviewer/backend/K_graph_rag.py)

Create a new module that uses Groq LLM to extract a knowledge graph from text:

```python
# Key components:
1. EntityExtractor - Uses Groq to extract entities (topics, skills, roles, concepts)
2. RelationshipExtractor - Uses Groq to extract relationships between entities
3. KnowledgeGraph - NetworkX-based graph to store and query entities
4. export_to_json() - Converts graph to JSON for frontend visualization
```

**Output JSON structure:**
```json
{
  "nodes": [
    {"id": "user_answer", "type": "answer", "content": "..."},
    {"id": "chunk_1", "type": "document", "content": "..."},
    {"id": "machine_learning", "type": "topic", "content": "..."},
    {"id": "q_1", "type": "question", "content": "..."}
  ],
  "edges": [
    {"source": "user_answer", "target": "chunk_1", "relation": "matches"},
    {"source": "chunk_1", "target": "machine_learning", "relation": "contains_topic"},
    {"source": "machine_learning", "target": "q_1", "relation": "generates_question"}
  ]
}
```

---

### Integration Points

#### [MODIFY] [aspira_groq.py](file:///Users/arnav/Code/AI_interviewer/backend/aspira_groq.py)

1. **Import the new module:**
   ```python
   from K_graph_rag import KnowledgeGraphBuilder
   ```

2. **Update `AgentState`** to include knowledge graph:
   ```python
   class AgentState(TypedDict):
       # ... existing fields ...
       knowledge_graph: dict  # JSON representation of the graph
   ```

3. **Modify `perform_search_node`** to build knowledge graph:
   - After collecting corpus, call `KnowledgeGraphBuilder`
   - Extract entities from chunks using Groq
   - Build relationships between answer → chunks → topics → questions
   - Store JSON in `state["knowledge_graph"]`

4. **Update `respond_node`** to return the knowledge graph JSON

---

## Dependencies

```
networkx>=3.0  # For graph operations (lightweight, no Neo4j needed)
```

> [!NOTE]
> We're using NetworkX instead of Neo4j/LangChain's `LLMGraphTransformer` to keep the solution lightweight and avoid additional database setup. The LLM-based entity extraction achieves similar results.

---

## Verification Plan

### Manual Verification

1. Run terminal mode:
   ```bash
   python aspira_groq.py --terminal
   ```

2. Enter an answer like: `I want to become a machine learning engineer`

3. Check the log file `log/aspira.log` for:
   - `Building knowledge graph...` message
   - Entity extraction results
   - Relationship building steps

4. After the question is generated, verify the knowledge graph JSON is printed or logged (we'll add a debug output)

5. Validate JSON structure contains:
   - User answer node
   - Document chunk nodes
   - Topic/entity nodes extracted from chunks
   - Question nodes
   - Edges connecting them with appropriate relation types

> [!IMPORTANT]
> Since this is a new feature without existing tests, manual verification is required. The terminal mode provides interactive testing capability.
