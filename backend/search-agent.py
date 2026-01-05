import os
from typing import TypedDict

import requests
import trafilatura
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph

import sys_msgs


load_dotenv()
# Set API key in environment first:
llm = ChatGroq(
    temperature=0,
    model_name="llama-3.3-70b-versatile",
    groq_api_key=os.environ.get("GROQ_API_KEY"),
)

class AgentState(TypedDict):
    conversation: list
    context: str
    user_input: str



def should_search(state):
    sys_msg = sys_msgs.search_or_not_msg
    last_message = state["conversation"][-1]
    user_content = (
        last_message["content"] if isinstance(last_message, dict) else last_message
    )
    response = llm.invoke(
        [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_content},
        ]
    )
    content = response.content
    print(f"SEARCH OR NOT RESULTS: {content}")
    if "true" in content.lower():
        return "true"
    return "false"


def stream_assistant_response(state):
    messages = [
        {"role": msg["role"], "content": msg["content"]} for msg in state["conversation"]
    ]
    complete_response = ""
    print("ASSISTANT: ")
    for chunk in llm.stream(messages):
        content = chunk if isinstance(chunk, str) else getattr(chunk, "content", "")
        if content:
            print(content, end="", flush=True)
            complete_response += content
    state["conversation"].append({"role": "assistant", "content": complete_response})
    print("\n\n")
    return state


def query_generator(state):
    sys_msg = sys_msgs.query_msg
    last_message = state["conversation"][-1]
    query_msg = f"CREATE A SEARCH QUERY FOR THIS PROMPT: \n{
        last_message['content'] if isinstance(last_message, dict) else last_message
    }"
    response = llm.invoke(
        [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": query_msg},
        ]
    )
    return response.content


def contains_data_needed(state, search_content, query):
    sys_msg = sys_msgs.contains_data_msg
    needed_prompt = f"PAGE_TEXT: {search_content} \nUSER_PROMPT: {
        state['conversation'][-1]
    } \nSEARCH_QUERY: {query}"

    response = llm.invoke(
        [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": needed_prompt},
        ]
    )

    content = response.content
    if "true" in content.lower():
        return True
    else:
        return False


def duckduckgo_search(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    url = f"https://html.duckduckgo.com/html/?q={query}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    results = []
    soup = BeautifulSoup(response.text, "html.parser")
    for i, result in enumerate(soup.find_all("div", class_="result"), start=1):
        if i > 10:
            break
        title_tag = result.find("a", class_="result_a")
        if not title_tag:
            continue

        Link = title_tag["href"]
        snippet_tag = result.find("a", class_=" result_snippet")
        snippet = (
            snippet_tag.text.strip() if snippet_tag else "No description available"
        )
        results.append({"id": i, "link": Link, "search_description": snippet})

    return results


def best_search_result(state, s_results, query):
    sys_msg = sys_msgs.best_search_msg
    best_msg = f"""SEARCH_RESULTS: {s_results} \nUSER_PROMPT: {
        state['conversation'][-1]
    } \nSEARCH_QUERY: {query}"""
    response = llm.invoke(
        [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": best_msg},
        ]
    )

    return int(response.content)


def perform_search(state: AgentState):
    print("GENERATING SEARCH QUERY. ")
    search_query = query_generator(state)
    if search_query[0] == '"':
        search_query = search_query[1:-1]
    search_results = duckduckgo_search(search_query)
    context_found = False
    while not context_found and len(search_results) > 0:
        best_result = best_search_result(state, s_results=search_results, query=search_query)
        try:
            page_link = search_results[best_result]["link"]
        except:
            print("Failed to select based on search result, try again")
            continue
        page_text = scrape_webpage(page_link)
        search_results.pop(best_result)

        if page_text and contains_data_needed(
            state, search_content=page_text, query=search_query
        ):
            state["context"] = page_text
            context_found = True
    return state


def scrape_webpage(url):
    downloaded = trafilatura.fetch_url(url=url)
    return trafilatura.extract(
        downloaded, include_formatting=True, include_links=True
    )



def handle_user_input(state: AgentState):
    state["conversation"].append({"role": "user", "content": state["user_input"]})
    return state


def search_result_router(state: AgentState):
    if state.get("context"):
        return "search_success"
    return "search_failed"


def respond(state: AgentState):
    if state.get("context"):
        prompt = f"SEARCH RESULT: {state['context']} \n\nUSER PROMPT: {state['user_input']}"
        state["conversation"].append({"role": "user", "content": prompt})
    return stream_assistant_response(state)


def main():
    workflow = StateGraph(AgentState)

    workflow.add_node("handle_input", handle_user_input)
    workflow.add_node("perform_search", perform_search)
    workflow.add_node("respond", respond)

    workflow.add_conditional_edges(
        "handle_input",
        should_search,
        {"true": "perform_search", "false": "respond"},
    )
    workflow.add_edge("perform_search", "respond")

    workflow.set_entry_point("handle_input")
    workflow.set_finish_point("respond")

    app = workflow.compile()

    conversation = [sys_msgs.assistant_msg]
    while True:
        user_input = input("USER: \n")
        state = {
            "conversation": conversation,
            "context": "",
            "user_input": user_input,
        }
        result = app.invoke(state)
        conversation = result["conversation"]


if __name__ == "__main__":
    main()
