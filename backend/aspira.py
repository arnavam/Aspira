"""
Aspira Groq - Combined AI Interviewer with Groq LLM and LangGraph

This module merges aspira.py and search-agent.py functionalities:ent


- Uses Groq LLM (llama-3.3-70b-versatile) for intelligent responses
- Uses LangGraph for state machine workflow
- Preserves sentence-transformers for similarity scoring
- Hybrid query generation: keywords + message -> Groq -> search queries
"""

import heapq
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, TypedDict

# Suppress tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import numpy as np
from C_ans_checker import scoring
from D_keyword_generator import keyword_extraction
from F_Search_Engine import search
from G_Parser import Parse, scrape_webpage
from M_embeddings import similarity_score
from K_llamaindex_graph import build_knowledge_graph_from_state
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph

# Logging setup
from logger_config import get_logger

# Logging setup
logger = get_logger(__name__)

USE_KNOWLEDGE_GRAPH = os.environ.get("USE_KNOWLEDGE_GRAPH", "false").lower() == "true"
logger.debug(f"Knowledge graph enabled: {USE_KNOWLEDGE_GRAPH}")

# Token counting helper
try:
    import tiktoken
    _tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4/Llama tokenizer
except ImportError:
    _tokenizer = None
    logger.warning("tiktoken not installed, falling back to char-based estimation")


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken or fallback to char estimate."""
    if _tokenizer:
        return len(_tokenizer.encode(text))
    return len(text) // 4  # ~4 chars per token approximation


def truncate_to_token_limit(items: List[str], max_tokens: int, separator: str = "\n") -> str:
    """Truncate list of strings to fit within token limit, keeping most recent items."""
    result = []
    total_tokens = 0
    
    # Process from newest to oldest (reverse order)
    for item in reversed(items):
        item_tokens = count_tokens(item + separator)
        if total_tokens + item_tokens > max_tokens:
            break
        result.append(item)
        total_tokens += item_tokens
    
    # Reverse back to chronological order
    result.reverse()
    return separator.join(result)


# Initialize Groq LLM
llm = ChatGroq(
    temperature=0,
    model_name="llama-3.1-8b-instant",
    groq_api_key=os.environ.get("GROQ_API_KEY"),
)


start_time = time.perf_counter()


# =============================================================================
# LangGraph State Definition
# =============================================================================


class AgentState(TypedDict):
    # --- Persistent (saved by checkpointer) ---
    keywords: dict  # Accumulated keyword scores
    history: List[str]  # Conversation history
    user_id: str  # User identifier

    # --- Ephemeral (per-request) ---
    question: str  # Generated interviewer question (output)
    search_queries: List[str]  # Generated search queries
    scraped_content: dict  # {url: text} - keys are the links
    relevant_chunks: List[str]  # Retrieved chunks from RAG
    question_scores: dict  # {question: similarity_score}


# =============================================================================
# LangGraph Nodes
# =============================================================================


def handle_input_node(state: AgentState) -> AgentState:
    """Process user input (simple pass-through now)."""
    # Logic moved to extract_keywords_node to separate concerns
    history = state.get("history", [])
    if history:
        logger.info(f"Handling input: {history[-1][:50]}...")
    return state


def extract_keywords_node(state: AgentState) -> AgentState:
    """Enhance keywords with similarity scoring. Pure function - no DB calls."""
    current_kw = state.get("keywords", {})
    if not isinstance(current_kw, dict):
        current_kw = {}

    # Get answer from history
    history = state.get("history", [])
    answer = ""
    if history:
        last_msg = history[-1]
        answer = (
            last_msg.replace("User: ", "")
            if last_msg.startswith("User: ")
            else last_msg
        )

    # Extract keywords using aspira's keyword extraction
    new_keywords = keyword_extraction(answer)

    # Adding scoring to get noun_phrases
    try:
        subj, pol, noun_phrases = scoring(answer)
    except Exception as e:
        logger.warning(f"Scoring extraction failed: {e}")
        noun_phrases = []

    # Add noun phrases to new_keywords
    for phrase in noun_phrases:
        phrase_lower = phrase.lower()
        if phrase_lower not in new_keywords and len(phrase_lower) > 2:
            new_keywords[phrase_lower] = [0.1, 0.0]
    # ------------------------------------------

    question = "which job would you prefer?"

    # Reduce relevancy of old keywords
    if current_kw:
        current_kw = {
            key: [a / 2, b / 2]
            for key, (a, b) in current_kw.items()
            if isinstance((a, b), (list, tuple)) and len((a, b)) == 2
        }

    # Merge new keywords into current_kw
    if new_keywords:
        keys = list(new_keywords.keys())
        # Normalize scores to list
        scores = [v[0] if isinstance(v, list) else v for v in new_keywords.values()]

        sims = similarity_score(question, keys)

        for key, score in zip(keys, scores):
            sm = sims.get(key, 0)
            if key in current_kw:
                current_kw[key][0] += score
                current_kw[key][1] += sm
            else:
                current_kw[key] = [score, sm]

    # Sort by combined score
    sorted_scores = dict(
        sorted(
            current_kw.items(),
            key=lambda x: np.sqrt(max(0, x[1][0] * x[1][1]))
            if isinstance(x[1], list) and len(x[1]) == 2
            else 0,
            reverse=True,
        )
    )

    state["keywords"] = sorted_scores

    logger.info(
        "\n"
        + "\n".join(
            f"({score[0]:.2f}, {score[1]:.2f}):{key}"
            for key, score in sorted_scores.items()
            if isinstance(score, list)
        )
    )

    return state


def query_generation_node(state: AgentState) -> AgentState:
    """Decide if search is needed and generate queries using Groq."""
    import json

    history = state.get("history", [])
    answer = (
        history[-1].replace("User: ", "")
        if history and history[-1].startswith("User: ")
        else (history[-1] if history else "")
    )
    keywords = state.get("keywords", {})
    
    # Format conversation history with token limit (1500 tokens max)
    history_str = truncate_to_token_limit(history, max_tokens=1500)
    context = "\nCONVERSATION HISTORY\n" + history_str + "\n\n" if history_str else ""

    prompt = f"""Analyze this conversation and decide if web search is needed.


{context}


LATEST MESSAGE: "{answer}"

Respond with JSON only:
{{"skip": true, "reason": "nonsense"}} - if latest message is nonsense/greeting/vague/short
{{"skip": false, "queries": ["query1", "query2", "query3"]}} - if search needed

Generate search queries that are relevant to the ENTIRE conversation context, not just the latest message.

Examples:
"hello" -> {{"skip": true, "reason": "nonsense"}}
"I want to be a data scientist" -> {{"skip": false, "queries": ["data scientist interview questions", "data scientist skills", "data scientist career path"]}}

Respond with valid JSON only, no other text:"""

    response = llm.invoke(
        [
            {
                "role": "system",
                "content": "You are a JSON generator. Output only valid JSON, nothing else.",
            },
            {"role": "user", "content": prompt},
        ]
    )

    content = response.content.strip()
    logger.debug(f"Query generator response: {content}")

    # Skip if "nonsense" appears anywhere in LLM output
    if "nonsense" in content.lower():
        logger.info("Skipping search: detected 'nonsense' in LLM output")
        state["search_queries"] = []
        return state

    search_queries = []
    try:
        data = json.loads(content)

        if data.get("skip", False):
            reason = data.get("reason", "not needed")
            logger.info(f"Skipping search: {reason}")
        else:
            search_queries = data.get("queries", [])[:3]
            logger.info(f"Generated search queries: {search_queries}")

    except json.JSONDecodeError:
        # Fallback: try to extract queries from malformed response
        logger.warning(f"Failed to parse JSON, attempting fallback: {content}")
        lines = [
            l.strip().strip("\"'")
            for l in content.split("\n")
            if l.strip() and 5 < len(l.strip()) < 100
        ]
        search_queries = lines[:3]

    state["search_queries"] = search_queries
    return state


def search_and_process_node(state: AgentState) -> AgentState:
    """Parallel search+scrape with streaming, then LlamaIndex parallel ingestion."""
    search_queries = state.get("search_queries", [])
    history = state.get("history", [])
    answer = (
        history[-1].replace("User: ", "")
        if history and history[-1].startswith("User: ")
        else (history[-1] if history else "")
    )
    question = "which job would you prefer?"

    scraped_content = {}
    all_texts = []

    # Perform search + scrape if queries exist
    if search_queries:
        scrape_futures = []

        def scrape_link(link):
            """Scrape a single link."""
            text = scrape_webpage(link)
            if not text:
                logger.debug(f"Parse failed for {link}, trying Parse...")
                text = Parse(link)
            if text:
                scraped_content[link] = text
            return text

        def search_and_submit(query, delay, executor):
            """Search, then IMMEDIATELY submit scrape tasks to shared pool."""
            time.sleep(delay)
            logger.info(f"Searching with query: {query}")
            links = search(query, num_results=3)
            if links:
                logger.info(
                    f"Found {len(links)} links:\n"
                    + "\n".join(f"  - {link}" for link in links)
                )
            for link in links:
                scrape_futures.append(executor.submit(scrape_link, link))

        # SHARED POOL: scrape starts as soon as ANY link arrives
        with ThreadPoolExecutor(max_workers=8) as executor:
            search_futs = [
                executor.submit(search_and_submit, q, i * 1.5, executor)
                for i, q in enumerate(search_queries)
            ]
            for f in search_futs:
                f.result()

            # Log scraping progress
            completed = 0
            total = len(scrape_futures)
            logger.info(f"Scraping {total} pages...")
            for f in as_completed(scrape_futures):
                text = f.result()
                completed += 1
                if text:
                    all_texts.append(text)
                    logger.debug(f"Scraped {completed}/{total} pages")

        logger.info(f"Search complete. Found {len(scraped_content)} valid links.")
    else:
        logger.info("No search queries - generating question from answer only")

    # Pre-filter with TextRank to reduce chunk count
    relevant_chunks = []
    if all_texts:
        from H_Summaraizer import textrank

        logger.info(f"Applying TextRank to {len(all_texts)} texts...")

        # Extract top sentences from each text using TextRank (PARALLEL)
        def process_text(text):
            top_sentences = textrank(text)
            if top_sentences:
                return " ".join(top_sentences.keys())
            return None

        with ThreadPoolExecutor(max_workers=4) as executor:
            filtered_texts = [r for r in executor.map(process_text, all_texts) if r]

        logger.info(f"TextRank reduced to {len(filtered_texts)} filtered texts")

        # Use TextRank filtered texts directly as context (skip RAG for speed)
        relevant_chunks = filtered_texts
        logger.info(f"Using {len(relevant_chunks)} filtered texts as context")

        # # RAG on the filtered texts (commented out for speed)
        # if filtered_texts:
        #     from L_llamaindex_rag import VectorRAGBuilder
        #     logger.info(f"Starting RAG indexing for {len(filtered_texts)} filtered texts...")
        #     rag = VectorRAGBuilder()
        #     rag.create_index_parallel(filtered_texts, num_workers=4)
        #     logger.info("Indexing complete, retrieving chunks...")
        #     results = rag.retrieve(answer, top_k=5)
        #     relevant_chunks = [r["chunk"] for r in results] if results else []
        #     logger.info(f"Retrieved {len(relevant_chunks)} chunks for question generation")

    state["scraped_content"] = scraped_content
    state["relevant_chunks"] = relevant_chunks
    return state


def generate_questions_node(state: AgentState) -> AgentState:
    """Generate interview questions from retrieved chunks or user answer."""
    history = state.get("history", [])
    answer = (
        history[-1].replace("User: ", "")
        if history and history[-1].startswith("User: ")
        else (history[-1] if history else "")
    )
    relevant_chunks = state.get("relevant_chunks", [])
    question = "which job would you prefer?"  # default question
    history_section = ""
    context_section = ""

    # Include Conversation History

    if history:
        # Use token limit (2000 tokens) instead of fixed turn count
        history_formatted = truncate_to_token_limit(history, max_tokens=2000)
        if history_formatted:
            history_section = f"PREVIOUS CONVERSATION HISTORY:\n\n{history_formatted}\n\n"

    # Use chunks if available, with token limit (3000 tokens)
    if relevant_chunks:
        context_text = truncate_to_token_limit(relevant_chunks[:5], max_tokens=3000)
        if context_text:
            context_section = (
                f"CONTEXT INFORMATION (from knowledge base):\n\n{context_text}\n\n"
            )

    prompt = f"""You are an AI interviewer conducting a professional interview.
    
{history_section}
{context_section}

Based on the conversation, generate 3 relevant follow-up interview questions.
- Do NOT number the questions
- Do NOT use bullet points or asterisks
- Do NOT use markdown formatting (no ** or *)
- Just write plain questions, one per line"""

    response = llm.invoke(
        [
            {
                "role": "system",
                "content": "You are an AI interviewer. Generate plain questions without numbering or formatting.",
            },
            {"role": "user", "content": prompt},
        ]
    )

    # Parse and clean questions - remove numbering, bullets, markdown
    import re

    raw_questions = [
        q.strip()
        for q in response.content.strip().split("\n")
        if q.strip() and "?" in q
    ]
    questions = []
    for q in raw_questions:
        # Remove leading numbers, bullets, asterisks, markdown
        clean = re.sub(r"^[\d\.\)\-\*\s]+", "", q)  # Remove "1." "1)" "-" "*" etc
        clean = re.sub(r"\*\*([^*]+)\*\*:?", r"\1:", clean)  # Remove **bold**
        clean = re.sub(r"\*([^*]+)\*", r"\1", clean)  # Remove *italic*
        clean = clean.strip().strip('"').strip()
        if clean:
            questions.append(clean)

    state["question_scores"] = (
        similarity_score(question, questions) if questions else {}
    )
    # Optional: Build knowledge graph from this turn's data
    if USE_KNOWLEDGE_GRAPH and relevant_chunks:
        try:
            graph_result = build_knowledge_graph_from_state(
                state, relevant_chunks, questions
            )
            logger.info(f"Knowledge graph updated: {graph_result.get('stats', {})}")
        except Exception as e:
            logger.warning(f"Knowledge graph building failed: {e}")

    return state


def respond_node(state: AgentState) -> AgentState:
    """Select and return the best question."""

    user_id = state["user_id"]

    q = state.get("question_scores", {})
    qa = dict(state.get("conversation", []))

    if not q:
        # No questions generated - use generic fallback
        state["question"] = "What interests you most about this career path?"
        return state

    # Select question with median similarity
    n = 1

    centre_value = np.mean(list(q.values()))
    smallest = heapq.nsmallest(
        n, q.items(), key=lambda item: abs(item[1] - centre_value)
    )

    if len(smallest) >= n:
        closest_key = smallest[0][0]
    else:
        closest_key = smallest[-1][0]
    logger.info(
        f"Generated {len(q)} questions:\n"
        + "\n".join(f"  {q.get(question, 0):.2f}: {question}" for question in q.keys())
    )


    logger.info(f"Selected Question : {closest_key}")

    state["question"] = next(iter(q.keys()))

    return state


# =============================================================================
# LangGraph Workflow
# =============================================================================


def create_workflow():
    """Create and compile the LangGraph workflow."""
    workflow = StateGraph(AgentState)
    workflow.add_node("handle_input", handle_input_node)
    workflow.add_node("extract_keywords", extract_keywords_node)
    workflow.add_node("query_generation", query_generation_node)
    workflow.add_node("search_and_process", search_and_process_node)
    workflow.add_node("generate_questions", generate_questions_node)
    workflow.add_node("respond", respond_node)

    workflow.add_edge("handle_input", "extract_keywords")
    workflow.add_edge("extract_keywords", "query_generation")
    workflow.add_edge("query_generation", "search_and_process")
    workflow.add_edge("search_and_process", "generate_questions")
    workflow.add_edge("generate_questions", "respond")

    workflow.set_entry_point("handle_input")
    workflow.set_finish_point("respond")

    return workflow  # Return uncompiled - caller adds checkpointer


# Create the workflow
aspira_workflow = create_workflow()


# =============================================================================
# Terminal Conversation (LangGraph Persistence)
# =============================================================================

from langgraph.checkpoint.memory import MemorySaver


def terminal_conversation():
    """Interactive terminal conversation using LangGraph MemorySaver."""
    print("\n" + "=" * 60)
    print("ASPIRA GROQ - AI Interviewer (Terminal + MemorySaver)")
    print("=" * 60)
    print("Type 'quit' or 'exit' to end the conversation.")
    print("=" * 60 + "\n")

    # Initialize Checkpointer
    memory = MemorySaver()
    app = aspira_workflow.compile(checkpointer=memory)

    # Thread config for persistence
    thread_id = "terminal_session"
    config = {"configurable": {"thread_id": thread_id}}

    # Initial Interviewer Question
    question = ""

    # Seed history if empty
    current_state = app.get_state(config).values
    if not current_state.get("history"):
        # Use update_state to seed without triggering the full workflow
        initial_history = [f"Interviewer: {question}"]
        app.update_state(
            config,
            {"history": initial_history, "keywords": {}, "user_id": "terminal_user"},
        )

    while True:
        # Get latest state
        current_values = app.get_state(config).values
        last_history = current_values.get("history", [])

        # Determine last question from history or fallback
        # (Usually the last message in history is the AI's question if we finished a turn)
        last_msg = last_history[-1] if last_history else f"Interviewer: {question}"
        if last_msg.startswith("Interviewer: "):
            print(f"\n🎤 {last_msg}\n")
        else:
            # Should not happen in normal flow, but fallback
            print(f"\n🎤 INTERVIEWER: {question}\n")

        user_input = input("👤 YOU: ").strip()

        if user_input.lower() in ["quit", "exit", "q"]:
            print("\n👋 Thank you for the interview! Goodbye.\n")
            break

        if not user_input:
            print("Please provide an answer.")
            continue

        # Reset timer to only count processing time
        from logger_config import reset_timer

        reset_timer()

        # Append user input to history (Manual append for TypedDict state)
        updated_history = last_history + [f"User: {user_input}"]

        inputs = {
            "history": updated_history,
            "user_id": "terminal_user",
            # Other fields can be omitted, they will be preserved or regenerated
            "keywords": current_values.get("keywords", {}),
        }

        # Run Workflow
        result = app.invoke(inputs, config)

        ai_question = result.get("question", "What else?")

        # Update history with AI response for the NEXT time
        final_history = updated_history + [f"Interviewer: {ai_question}"]
        app.update_state(config, {"history": final_history})


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--terminal":
        terminal_conversation()
    else:
        # app.run(debug=False, port=5000)
        print("Use 'uvicorn api_server:app' to run the API server.")
        terminal_conversation()
