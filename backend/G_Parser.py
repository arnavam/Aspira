import requests
from bs4 import BeautifulSoup
import trafilatura
from trafilatura.settings import use_config
from logger_config import get_logger
import time

logger = get_logger(__name__)

# Configure trafilatura with 5 second timeout
trafilatura_config = use_config()
trafilatura_config.set("DEFAULT", "DOWNLOAD_TIMEOUT", "5")


def scrape_webpage(url: str) -> str:
    """Scrape webpage content using trafilatura with timeout."""
    start = time.time()
    try:
        downloaded = trafilatura.fetch_url(url=url, config=trafilatura_config)
        elapsed = time.time() - start
        if elapsed > 3:
            logger.info(f"Slow scrape ({elapsed:.1f}s): {url[:50]}...")
        text = trafilatura.extract(
            downloaded, include_formatting=True, include_links=True)
        return text
    except Exception as err:
        logger.debug(f"Scrape failed: {url}")
        return None


def Parse(url):
    try:
        response = requests.get(url, timeout=2)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()
        cleaned_text = ' '.join(page_text.split())

        return cleaned_text

    except requests.exceptions.RequestException as req_err:
        logger.debug(f"Parse failed: {url}")
        return None

    except Exception as err:
        logger.debug(f"Parse failed: {url}")
        return None


if __name__ == "__main__":
    url = 'https://example.com'
    text = Parse(url)
    print(text)
