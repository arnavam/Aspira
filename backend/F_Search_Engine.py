import time
import os
import httpx
import asyncio
from ddgs import DDGS
from ddgs.exceptions import DDGSException
from logger_config import get_logger

logger = get_logger(__name__)

exclude_domains = ['reddit', 'coursera']
include_domains = []
exclude_title = ['course', 'tutorial']

async def ddg_search(search_query='Machine Learning', no=2, items=None):
    if items is None:
        items = []
    
    a = []
    local_include_domains = list(include_domains) + items

    start_time = time.time()
    try:
        def perform_search():
            instance = DDGS()
            # main search
            results = instance.text(
                search_query,
                safesearch='off',
                timelimit='w',
                max_results=no
            )
            if not isinstance(results, list):
                results = list(results)
            
            # domain searches
            for domain in local_include_domains:
                try:
                    name = f"{search_query} {domain}"
                    domain_results = instance.text(
                        name,
                        safesearch='off',
                        timelimit='w',
                        max_results=1
                    )
                    if domain_results:
                        results += list(domain_results)
                except Exception as e:
                    logger.warning(f"Error with domain {domain}: {e}")
                    
            return results

        results = await asyncio.to_thread(perform_search)

        # Loop through the results and apply filters
        for idx, item in enumerate(results, 1):
            if isinstance(item, dict) and 'href' in item:
                if any(domain in item['href'] for domain in exclude_domains):
                    continue
                if any(domain.lower() in item['title'].lower() for domain in exclude_title):
                    continue

                logger.info(f"{idx}. {item['title']}")
                logger.info(f"Link: {item['href']}")
                logger.info('-' * 50)  # Separator between results
                a.append(item['href'])

    except Exception as e:
        logger.warning(f"Error: {e}")
        if "Ratelimit" in str(e):
            logger.warning("Rate limit exceeded. Breaking the search process.")
        logger.warning("Retry...")

    logger.warning(time.time() - start_time)
    if not a:
        logger.error("No valid links found after applying filters.")
        print("No valid links found. Please try a different search query.")

    return a


# =============================================================================
# Alternative Search APIs
# =============================================================================

async def brave_search(query: str, num_results: int = 5) -> list:
    """Search using Brave Search API. Requires BRAVE_API_KEY in .env"""
    api_key = os.environ.get("BRAVE_API_KEY")
    if not api_key:
        logger.warning("BRAVE_API_KEY not found, skipping Brave search")
        return []

    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key
    }
    params = {
        "q": query,
        "count": num_results
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for result in data.get("web", {}).get("results", []):
                results.append(result.get("url", ""))

            logger.info(f"Brave search returned {len(results)} results")
            return results
    except Exception as e:
        logger.warning(f"Brave search error: {e}")
        return []


async def tavily_search(query: str, num_results: int = 5) -> list:
    """Search using Tavily API. Requires TAVILY_API_KEY in .env"""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        logger.warning("TAVILY_API_KEY not found, skipping Tavily search")
        return []

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": num_results,
                    "include_answer": False
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            results = [r.get("url", "") for r in data.get("results", [])]
            logger.info(f"Tavily search returned {len(results)} results")
            return results
    except Exception as e:
        logger.warning(f"Tavily search error: {e}")
        return []


async def search(query: str, num_results: int = 3) -> list:
    """
    Unified search function with automatic fallback.
    Tries: DuckDuckGo → Brave → Tavily
    """
    # Try DuckDuckGo first
    # links = await ddg_search(query, no=num_results)
    links = None
    if not links:
        logger.info("DuckDuckGo failed, trying Brave Search...")
        await asyncio.sleep(1)
        links = await brave_search(query, num_results=num_results)

    if not links:
        logger.info("Brave Search failed, trying Tavily...")
        await asyncio.sleep(1)
        links = await tavily_search(query, num_results=num_results)

    return links

if __name__ == "__main__":
    import asyncio
    search_results = asyncio.run(search('Machine Learning', num_results=10))
