from bs4 import BeautifulSoup
import requests
import socket
import time
included_domain=['wikipedia','geekforgeek']
def Parse(url):
    start_time=time.time()

    if any(domain.lower() in url.lower() for domain in included_domain):

# Function to extract content from the page based on site structure
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the content of the webpage with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove unwanted tags (like headers, script, style, etc.)
            for unwanted_tag in soup(['style', 'script', 'link', 'button', 'header', 'footer', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                unwanted_tag.decompose()

            # Initialize variable to store the content
            important_content = ""

            # Extract content for Wikipedia pages, typically found in the mw-parser-output class
            if "wikipedia" in url:
                content_div = soup.find('div', {'class': 'mw-parser-output'})
                if content_div:
                    paragraphs = content_div.find_all('p')
                    for p in paragraphs:
                        # Get the text of each paragraph, clean up, and join them into meaningful content
                        paragraph_text = p.get_text(separator=" ", strip=True)
                        if paragraph_text:  # Only add non-empty paragraphs
                            important_content += paragraph_text + "\n\n"

            # If no content is found, fallback to extracting text from all <p> tags
            if not important_content:
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    paragraph_text = p.get_text(separator=" ", strip=True)
                    if paragraph_text:
                        important_content += paragraph_text + "\n\n"

            # Return the content with proper formatting
            return important_content.strip()

        else:
            return f"Failed to retrieve webpage. Status code: {response.status_code}"


    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove header, footer, and other unwanted sections
            for element in soup(['header', 'footer', 'nav', 'aside']):
                element.decompose()  # This removes the element completely

            main_content = soup.get_text(separator=' ', strip=True)
            print(time.time()-start_time)
            return(main_content)
        else:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
    except socket.gaierror as e:
        print(f"Name resolution error occurred: {e}")
        return 'skipw'

