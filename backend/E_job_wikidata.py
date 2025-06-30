from D_keyword_generator import is_job
from I_chatbot import similarity_score

import wikipedia
import wikipediaapi
from urllib.request import urlopen
from bs4 import BeautifulSoup
import time
import heapq

def get_wiki_links_fast(keyword):
    start_time=time.perf_counter()

    wiki = wikipediaapi.Wikipedia(
        user_agent="MyApp/1.0 (adeadhumqn@gmail.com)",
        language='en'
    )
    page = wiki.page(keyword)
    
    if not page.exists():
        return []
    print(time.perf_counter()-start_time)
    return{
        link: f"https://en.wikipedia.org/wiki/{link.replace(' ', '_')}"
        for link in page.links.keys()
    }


def get_wiki_links(keyword):
    try:    
        start_time=time.perf_counter()
        # Get Wikipedia page URL
        page = wikipedia.page(keyword)
        url = page.url
        
        # Parse the page
        html = urlopen(url)
        soup = BeautifulSoup(html, 'html.parser')

        print(time.perf_counter()-start_time)

        # Find all links in the main content
        links = {}
        for link in soup.find('div', {'id': 'bodyContent'}).find_all('a', href=True):
            href = link['href']
            if href.startswith('/wiki/') and ':' not in href:
                link_title = href[6:].replace('_', ' ')
                link_url = f"https://en.wikipedia.org{href}"
                links[link_title]= link_url
        print(time.perf_counter()-start_time)

        return links
    
    except wikipedia.exceptions.PageError:
        print(f"Wikipedia page for '{keyword}' not found.")
        return []
    except wikipedia.exceptions.DisambiguationError as e:
        print(f"Disambiguation page for '{keyword}'. Options: {e.options}")
        return []






def job_links(keyword,no=3):
    start_time=time.perf_counter()
    links = get_wiki_links(keyword)
    titles={}
    for title in  links.keys():
        if   not is_job(title):
            titles[title]=similarity_score(keyword,title)

    # sorted_links = dict(sorted(kw.items(), key=lambda item: item[1], reverse=True))
    # for title , score in sorted_links.items():
    #     print(f"{score:.2f}:{title}= {links[title]}")

    top_tuples= heapq.nlargest(no, titles.items(), key=lambda x: x[1])
    top_links = [links[key] for key, value in top_tuples]
    # top_title ,top_score=zip(*top_tuples)
    print(top_links)
    print(time.perf_counter()-start_time)
    return top_links


if __name__ =="__main__":
    # job_links("accountant")
    # Usage
    links1 = get_wiki_links("accountant job ")
    # links2=get_wiki_links_fast("Accountant")
    # print(links2.keys()-links1.keys())
    # print(f"Found {len(links)} links via API")
    print(links1)

