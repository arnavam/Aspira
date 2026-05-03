"""
Aspira Groq - Combined AI Interviewer with Groq LLM and LangGraph

This module merges aspira.py and search-agent.py functionalities:

- Uses Pydantic AI with Groq LLM (llama-3.1-8b-instant) for intelligent responses
- Uses LangGraph for state machine workflow
- Preserves sentence-transformers for similarity scoring
- Hybrid query generation: keywords + message -> Groq -> search queries
"""

from langgraph.graph import END
from dotenv import load_dotenv
from typing import List, TypedDict
import asyncio
import os
import heapq
import numpy as np
from langgraph.checkpoint.memory import MemorySaver
from logger_config import get_logger
from langgraph.graph import StateGraph
from H_Summaraizer import textrank
from K_llamaindex_graph import build_knowledge_graph_from_state
from M_embeddings import similarity_score
from G_Parser import Parse, scrape_webpage
from F_Search_Engine import search
from D_keyword_generator import keyword_extraction
from C_ans_checker import scoring
from prompts import (
    QUERY_AGENT_SYSTEM_PROMPT,
    QUESTION_AGENT_SYSTEM_PROMPT,
    QUERY_GENERATION_PROMPT,
    INTERVIEW_QUESTION_PROMPT,
    DEFAULT_CRITERIA,
)
from agent_factory import create_agent, extract_agent_data
from langfuse import Langfuse, observe

langfuse = Langfuse()

load_dotenv()
# Suppress tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Logging setup
logger = get_logger(__name__)

USE_KNOWLEDGE_GRAPH = os.environ.get(
    "USE_KNOWLEDGE_GRAPH", "false").lower() == "true"
logger.debug(f"Knowledge graph enabled: {USE_KNOWLEDGE_GRAPH}")

# Token counting helper
try:
    import tiktoken
    _tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4/Llama tokenizer
except ImportError:
    _tokenizer = None
    logger.warning(
        "tiktoken not installed, falling back to char-based estimation")


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


def get_last_user_message(history: list) -> str:
    """Extract the most recent user message, stripping the 'User: ' prefix."""
    if not history:
        return ""
    last = history[-1]
    if last.startswith("User: "):
        return last[6:]           # len("User: ") == 6
    return last                   # fallback if prefix missing


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
    no_keywords: int
    no_links: int
    no_chunks: int
    answer_stats: dict  # Statistical baseline metrics
    is_interview_complete: bool  # End interview flag
    interview_metadata: dict  # Company, role, requirements

# =============================================================================
# LangGraph Workflow
# =============================================================================


def should_continue(state: AgentState):
    if state.get("is_interview_complete"):
        return END
    return "search_and_process"


def create_workflow():
    """Create and compile the LangGraph workflow."""
    workflow = StateGraph(AgentState)
    workflow.add_node("handle_input", handle_input_node)
    workflow.add_node("extract_keywords", extract_keywords_node)  # as a bonus
    workflow.add_node("query_generation", query_generation_node)
    workflow.add_node("search_and_process", search_and_process_node)
    workflow.add_node("generate_questions", generate_questions_node)
    workflow.add_node("respond", respond_node)

    workflow.add_edge("handle_input", "extract_keywords")
    workflow.add_edge("extract_keywords", "query_generation")
    workflow.add_conditional_edges("query_generation", should_continue)
    workflow.add_edge("search_and_process", "generate_questions")
    workflow.add_edge("generate_questions", "respond")

    workflow.set_entry_point("handle_input")
    workflow.set_finish_point("respond")

    return workflow  # Return uncompiled - caller adds checkpointer


# =============================================================================
# LangGraph Nodes
# =============================================================================


async def handle_input_node(state: AgentState) -> AgentState:
    """Process user input (simple pass-through now)."""
    history = state.get("history", [])
    if history:
        logger.info(f"Handling input: {history[-1][:50]}...")
    return state


async def extract_keywords_node(state: AgentState) -> AgentState:
    """Enhance keywords with similarity scoring. Pure function - no DB calls."""
    current_kw = state.get("keywords", {})
    if not isinstance(current_kw, dict):
        current_kw = {}

    question = "which job would you prefer?"
    # Get answer from history
    answer = get_last_user_message(state.get("history", []))

    # Ensure answer is a plain string to avoid passing non-text to KeyBERT
    if not isinstance(answer, str):
        logger.warning(f'''extract_keywords_node: answer is {
                       type(answer)}, coercing to str''')
        answer = str(answer)

    # Extract keywords using aspira's keyword extraction (CPU bound)
    new_keywords = await asyncio.to_thread(keyword_extraction, answer)

    # Adding scoring to get noun_phrases (CPU bound)
    try:
        subj, pol, noun_phrases = await asyncio.to_thread(scoring, answer)
        from C_ans_checker import scoring2
        explainablity, technicality, depth = await asyncio.to_thread(scoring2, answer)
        state["answer_stats"] = {
            "subjectivity": float(subj),
            "polarity": float(pol),
            "readability": float(explainablity),
            "technicality": float(technicality),
            "depth": float(depth)
        }
    except Exception as e:
        logger.warning(f"Scoring extraction failed: {e}")
        noun_phrases = []
        state["answer_stats"] = {}

    # Add noun phrases to new_keywords
    for phrase in noun_phrases:
        phrase_lower = phrase.lower()
        if phrase_lower not in new_keywords and len(phrase_lower) > 2:
            new_keywords[phrase_lower] = [0.1, 0.0]
    # ------------------------------------------

    # Reduce relevancy of old keywords
    if current_kw:
        current_kw = {
            key: [float(a), float(b)]
            for key, (a, b) in current_kw.items()
            if isinstance((a, b), (list, tuple)) and len((a, b)) == 2
        }

    # Merge new keywords into current_kw
    if new_keywords:
        keys = list(new_keywords.keys())
        # Normalize scores to list
        scores = [v[0] if isinstance(
            v, list) else v for v in new_keywords.values()]

        sims = await asyncio.to_thread(similarity_score, question, keys)

        for key, score in zip(keys, scores):
            sm = float(sims.get(key, 0))
            if key in current_kw:
                current_kw[key][0] += float(score)
                current_kw[key][1] += sm
            else:
                current_kw[key] = [float(score), sm]

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


@observe(as_type="generation")
async def query_generation_node(state: AgentState) -> AgentState:
    """Decide if search is needed and generate queries using Groq."""
    import json

    history = state.get("history", [])
    answer = get_last_user_message(history)
    keywords = state.get("keywords", {})
    metadata = state.get("interview_metadata", {})

    # Format conversation history with token limit (1500 tokens max)
    history_str = truncate_to_token_limit(history, max_tokens=1500)
    context = "\nCONVERSATION HISTORY\n" + \
        history_str + "\n\n" if history_str else ""

    company = metadata.get("company", "Not specified")
    role = metadata.get("role", "Not specified")
    requirements = metadata.get("requirements")

    metadata_section = f"COMPANY: {company}\nROLE: {role}"

    if requirements:
        criteria_section = f"EVALUATION CRITERIA:\n{requirements}"
    else:
        criteria_section = f"EVALUATION CRITERIA:\n{DEFAULT_CRITERIA}"

    try:
        langfuse_prompt = langfuse.get_prompt("QUERY_GENERATION_PROMPT")
        prompt = langfuse_prompt.compile(
            context=context, answer=answer, metadata_section=metadata_section, criteria_section=criteria_section)
    except Exception:
        logger.warning(
            "Prompt 'QUERY_GENERATION_PROMPT' is missing in Langfuse. Falling back to local default.")
        prompt = QUERY_GENERATION_PROMPT
        prompt = prompt.replace("{{context}}", context)
        prompt = prompt.replace("{{answer}}", answer)
        prompt = prompt.replace("{{metadata_section}}", metadata_section)
        prompt = prompt.replace("{{criteria_section}}", criteria_section)

    query_agent = create_agent(QUERY_AGENT_SYSTEM_PROMPT)
    result = await query_agent.run(prompt)
    content = extract_agent_data(result).strip()
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
            search_queries = data.get("queries", [])
            logger.info(f"Generated search queries: {search_queries}")

    except json.JSONDecodeError:
        # Fallback: try to extract queries from malformed response
        logger.warning(f"Failed to parse JSON, attempting fallback: {content}")
        search_queries = [
            l.strip().strip("\"'")
            for l in content.split("\n")
            if l.strip() and 5 < len(l.strip()) < 100
        ]

    state["is_interview_complete"] = data.get(
        "is_interview_complete", False) if isinstance(data, dict) else False
    if state["is_interview_complete"]:
        logger.info("AI determined interview is complete based on criteria.")

    state["search_queries"] = search_queries
    return state


async def search_and_process_node(state: AgentState) -> AgentState:
    """Parallel search+scrape with async queue data pool, then LlamaIndex parallel ingestion."""
    search_queries = state.get("search_queries", [])
    n = state.get("no_keywords", 0)
    m = state.get("no_links", 0)

    if search_queries and n > 0:
        search_queries = search_queries[:n]

    answer = get_last_user_message(state.get("history", []))
    scraped_content = {}
    all_texts = []

    # Perform search + scrape if queries exist
    if search_queries:
        url_queue = asyncio.Queue()

        async def producer(query, delay):
            await asyncio.sleep(delay)
            logger.info(f"Searching with query: {query}")
            links = await search(query, num_results=m if m > 0 else 3)
            if links:
                logger.info(
                    f"Found {len(links)} links:\n"
                    + "\n".join(f"  - {link}" for link in links)
                )
                for link in links:
                    await url_queue.put(link)

        async def consumer():
            while True:
                link = await url_queue.get()
                try:
                    text = await scrape_webpage(link)
                    if not text:
                        logger.debug(f"Parse failed for {
                                     link}, trying Parse...")
                        text = await Parse(link)
                    if text:
                        scraped_content[link] = text
                        all_texts.append(text)
                finally:
                    url_queue.task_done()

        # Start producers
        producers = [asyncio.create_task(
            producer(q, i * 1.5)) for i, q in enumerate(search_queries)]

        # Start consumers (data pool workers)
        consumers = [asyncio.create_task(consumer()) for _ in range(8)]

        # Wait for all producers to finish adding URLs
        await asyncio.gather(*producers)

        # Wait for all consumers to process the queue
        await url_queue.join()

        # Cancel consumers
        for c in consumers:
            c.cancel()

        logger.info(f"Search complete. Found {
                    len(scraped_content)} valid links.")
    else:
        logger.info("No search queries - generating question from answer only")

    # Pre-filter with TextRank to reduce chunk count
    relevant_chunks = []
    if all_texts:
        logger.info(f"Applying TextRank to {len(all_texts)} texts...")

        # Extract top sentences from each text using TextRank (PARALLEL via to_thread)
        async def process_text(text):
            top_sentences = await asyncio.to_thread(textrank, text)
            if top_sentences:
                return " ".join(top_sentences.keys())
            return None

        filtered_texts = await asyncio.gather(*(process_text(t) for t in all_texts))
        filtered_texts = [r for r in filtered_texts if r]

        logger.info(f"TextRank reduced to {
                    len(filtered_texts)} filtered texts")

        # Use TextRank filtered texts directly as context (skip RAG for speed)
        relevant_chunks = filtered_texts
        logger.info(f"Using {len(relevant_chunks)} filtered texts as context")

    state["scraped_content"] = scraped_content
    state["relevant_chunks"] = relevant_chunks
    return state


@observe(as_type="generation")
async def generate_questions_node(state: AgentState) -> AgentState:
    """Generate interview questions from retrieved chunks or user answer."""
    history = state.get("history", [])
    i = state.get("no_chunks", 0)
    answer = get_last_user_message(history)

    relevant_chunks = state.get("relevant_chunks", [])
    question = "which job would you prefer?"  # default question
    history_section = ""
    context_section = ""
    metadata = state.get("interview_metadata", {})

    company = metadata.get("company", "Not specified")
    role = metadata.get("role", "Not specified")
    requirements = metadata.get("requirements")

    metadata_section = f"COMPANY: {company}\nROLE: {role}"

    if requirements:
        criteria_section = f"EVALUATION CRITERIA:\n{requirements}"
    else:
        criteria_section = f"EVALUATION CRITERIA:\n{DEFAULT_CRITERIA}"

    # Include Conversation History
    if history:
        # Use token limit (2000 tokens) instead of fixed turn count
        history_formatted = truncate_to_token_limit(history, max_tokens=2000)
        if history_formatted:
            history_section = f"PREVIOUS CONVERSATION HISTORY:\n\n{
                history_formatted}\n\n"

    # Use chunks if available, with token limit (3000 tokens)
    if relevant_chunks:
        context_text = truncate_to_token_limit(
            relevant_chunks[:i] if i > 0 else relevant_chunks, max_tokens=3000)
        if context_text:
            context_section = (
                f"CONTEXT INFORMATION (from knowledge base):\n\n{
                    context_text}\n\n"
            )

    try:
        langfuse_prompt = langfuse.get_prompt("INTERVIEW_QUESTION_PROMPT")
        prompt = langfuse_prompt.compile(
            history_section=history_section,
            context_section=context_section,
            metadata_section=metadata_section,
            criteria_section=criteria_section
        )
    except Exception:
        logger.warning(
            "Prompt 'INTERVIEW_QUESTION_PROMPT' is missing in Langfuse. Falling back to local default.")
        prompt = INTERVIEW_QUESTION_PROMPT
        prompt = prompt.replace("{{history_section}}", history_section)
        prompt = prompt.replace("{{context_section}}", context_section)
        prompt = prompt.replace("{{metadata_section}}", metadata_section)
        prompt = prompt.replace("{{criteria_section}}", criteria_section)

    question_agent = create_agent(QUESTION_AGENT_SYSTEM_PROMPT)
    result = await question_agent.run(prompt)
    response_content = extract_agent_data(result)

    # Parse and clean questions - remove numbering, bullets, markdown
    import re

    raw_questions = [
        q.strip()
        for q in response_content.strip().split("\n")
        if q.strip() and "?" in q
    ]
    questions = []
    for q in raw_questions:
        # Remove leading numbers, bullets, asterisks, markdown
        clean = re.sub(r"^[\d\.\)\-\*\s]+", "", q)
        clean = re.sub(r"\*\*([^*]+)\*\*:?", r"\1:", clean)  # Remove **bold**
        clean = re.sub(r"\*([^*]+)\*", r"\1", clean)  # Remove *italic*
        clean = clean.strip().strip('"').strip()
        if clean:
            questions.append(clean)

    state["question_scores"] = (
        await asyncio.to_thread(similarity_score, question, questions) if questions else {}
    )

    # Optional: Build knowledge graph from this turn's data
    if USE_KNOWLEDGE_GRAPH and relevant_chunks:
        try:
            graph_result = await asyncio.to_thread(build_knowledge_graph_from_state, state, relevant_chunks, questions)
            logger.info(f"Knowledge graph updated: {
                        graph_result.get('stats', {})}")
        except Exception as e:
            logger.warning(f"Knowledge graph building failed: {e}")

    return state


async def respond_node(state: AgentState) -> AgentState:
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
# Terminal Conversation (LangGraph Persistence)
# =============================================================================


async def terminal_conversation():
    """Interactive terminal conversation using LangGraph MemorySaver."""
    print("\n" + "=" * 60)
    print("ASPIRA GROQ - AI Interviewer (Terminal + MemorySaver)")
    print("=" * 60)
    print("Type 'quit' or 'exit' to end the conversation.")
    print("=" * 60 + "\n")

    aspira_workflow = create_workflow()
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
        last_msg = last_history[-1] if last_history else f"Interviewer: {
            question}"
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

        # Append user input to history
        updated_history = last_history + [f"User: {user_input}"]

        inputs = {
            "history": updated_history,
            "user_id": "terminal_user",
            "keywords": current_values.get("keywords", {}),
        }

        # Run Workflow
        result = await app.ainvoke(inputs, config)

        ai_question = result.get("question", "What else?")

        # Update history with AI response for the NEXT time
        final_history = updated_history + [f"Interviewer: {ai_question}"]
        app.update_state(config, {"history": final_history})


if __name__ == "__main__":
    asyncio.run(terminal_conversation())
