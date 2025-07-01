import requests
from bs4 import BeautifulSoup

def Parse(url):
    try:
        response = requests.get(url, timeout=2)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()
        cleaned_text = ' '.join(page_text.split())
        return cleaned_text

    except requests.exceptions.RequestException as req_err:
        return f"Request error occurred: {req_err}"

    except Exception as err:
        return f"An unexpected error occurred: {err}"


if __name__=="__main__":
    url = 'https://example.com'  # Replace with the link you want to parse
    text = Parse(url)
    print(text)
