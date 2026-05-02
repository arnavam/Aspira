import httpx
from bs4 import BeautifulSoup
import trafilatura
from trafilatura.settings import use_config
from logger_config import get_logger
import time
import asyncio

logger = get_logger(__name__)

# Configure trafilatura with 5 second timeout
trafilatura_config = use_config()
trafilatura_config.set("DEFAULT", "DOWNLOAD_TIMEOUT", "5")


async def scrape_webpage(url: str) -> str:
    """Scrape webpage content using trafilatura with timeout."""
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            downloaded = response.text
        
        elapsed = time.time() - start
        if elapsed > 3:
            logger.info(f"Slow scrape ({elapsed:.1f}s): {url[:50]}...")
            
        def extract_content(html):
            return trafilatura.extract(
                html, include_formatting=True, include_links=True)
                
        text = await asyncio.to_thread(extract_content, downloaded)
        return text
    except Exception as err:
        logger.debug(f"Scrape failed: {url} - {err}")
        return None


async def Parse(url):
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url)
            response.raise_for_status()

        def extract_text(html):
            soup = BeautifulSoup(html, 'html.parser')
            page_text = soup.get_text()
            return ' '.join(page_text.split())

        cleaned_text = await asyncio.to_thread(extract_text, response.text)
        return cleaned_text

    except httpx.RequestError as req_err:
        logger.debug(f"Parse failed: {url} - {req_err}")
        return None
    except Exception as err:
        logger.debug(f"Parse failed: {url} - {err}")
        return None


if __name__ == "__main__":
    async def main():
        url = 'https://example.com'
        text = await Parse(url)
        print(text)
        
    asyncio.run(main())
