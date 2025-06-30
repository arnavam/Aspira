import requests
from bs4 import BeautifulSoup

# Function to fetch and parse text from a webpage with enhanced error handling
def Parse(url):
    try:
        # Send a GET request to fetch the page content
        response = requests.get(url)
        
        # Raise an HTTPError for bad responses (4xx and 5xx)
        response.raise_for_status()

        # Parse the page content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract all the text from the page
        page_text = soup.get_text()

        # Clean up the text (optional)
        cleaned_text = ' '.join(page_text.split())
        return cleaned_text

    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}"  # For 4xx or 5xx status codes

    except requests.exceptions.RequestException as req_err:
        return f"Request error occurred: {req_err}"  # For other request-related issues

    except requests.exceptions.ConnectionError as conn_err:
        return f"Connection error occurred: {conn_err}"  # For network-related issues

    except requests.exceptions.Timeout as timeout_err:
        return f"Timeout error occurred: {timeout_err}"  # For timeout-related issues

    except requests.exceptions.TooManyRedirects as redirects_err:
        return f"Too many redirects error occurred: {redirects_err}"  # For redirect loops

    except Exception as err:
        return f"An unexpected error occurred: {err}"  # For any other unexpected errors


if __name__=="__main__":
    url = 'https://example.com'  # Replace with the link you want to parse
    text = Parse(url)
    print(text)
