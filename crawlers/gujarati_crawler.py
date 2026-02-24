import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

class GujaratiCrawler:
    def __init__(self, base_url, max_pages=5):
        self.base_url = base_url
        self.max_pages = max_pages
        self.visited_urls = set()
        self.urls_to_visit = [base_url]
        
        # Regex pattern for Gujarati Unicode characters (U+0A80 to U+0AFF)
        # Includes letters, vowel signs, and Gujarati digits
        self.gujarati_pattern = re.compile(r'[\u0A80-\u0AFF]+')

    def is_valid_url(self, url):
        """Ensure the URL belongs to the same domain and hasn't been visited."""
        parsed_base = urlparse(self.base_url)
        parsed_url = urlparse(url)
        return (parsed_base.netloc == parsed_url.netloc and 
                url not in self.visited_urls)

    def extract_gujarati_text(self, text):
        """Extract only Gujarati words from a given text block."""
        matches = self.gujarati_pattern.findall(text)
        return " ".join(matches)

    def crawl(self):
        """Start the crawling process."""
        pages_crawled = 0
        all_extracted_text = []

        while self.urls_to_visit and pages_crawled < self.max_pages:
            current_url = self.urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            print(f"Crawling: {current_url}")
            try:
                response = requests.get(current_url, timeout=10)
                response.raise_for_status()  # Check for HTTP errors
            except requests.RequestException as e:
                print(f"Failed to fetch {current_url}: {e}")
                continue

            self.visited_urls.add(current_url)
            pages_crawled += 1

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements to avoid extracting code syntax
            for script_or_style in soup(["script", "style"]):
                script_or_style.extract()

            # Get raw text and extract Gujarati
            raw_text = soup.get_text(separator=' ')
            gujarati_text = self.extract_gujarati_text(raw_text)
            
            if gujarati_text.strip():
                all_extracted_text.append(f"--- Text from {current_url} ---\n{gujarati_text}\n")

            # Find all links on the page to continue crawling
            for a_tag in soup.find_all('a', href=True):
                next_url = urljoin(current_url, a_tag['href'])
                # Clean up URL fragments (e.g., #section)
                next_url = next_url.split('#')[0] 
                
                if self.is_valid_url(next_url) and next_url not in self.urls_to_visit:
                    self.urls_to_visit.append(next_url)

        return "\n".join(all_extracted_text)
