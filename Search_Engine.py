import time
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException

a = []
exclude_domains = ['reddit', 'coursera']
include_domains = ['wikipedia']#'interview questions'
exclude_title = ['course', 'tutorial']
instance = DDGS()

def search(search_query='Machine Learning', no=2):
    start_time = time.time()
    try:
        results = instance.text(
            keywords=search_query,
            safesearch='off',
            timelimit='7d',
            max_results=no
        )
        
        for i in include_domains:
            try:
                name = search_query + ' ' + i
                I = instance.text(
                    keywords=name,
                    safesearch='off',
                    timelimit='7d',
                    max_results=1
                )
                # Add results to the main results list (make sure it's a list of dictionaries)
                if isinstance(I, list):
                    results += I # Assuming `I` is a list of results

            except Exception as e:
                print(f"Error with domain {i}: {e}")
        
        # Loop through the results and apply filters
        for idx, item in enumerate(results, 1):
            if isinstance(item, dict) and 'href' in item:

                if any(domain in item['href'] for domain in exclude_domains):
                    continue
                if any(domain.lower() in item['title'].lower() for domain in exclude_title):
                    continue

                print(f"{idx}. {item['title']}")
                print(f"Link: {item['href']}")
                print('-' * 50)  # Separator between results
                a.append(item['href'])
    except DuckDuckGoSearchException as e:
        print(f"Error: {e}")
        if "Ratelimit" in str(e):
            print("Rate limit exceeded. Breaking the search process.")
        print("Retry...")

    print(time.time() - start_time)
    return a
if __name__ == "__main__":
    search_results = search('Machine Learning', no=2)
