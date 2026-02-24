import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime

class LanguageCrawler:
    def __init__(self, base_url, max_pages, lang_code, regex_pattern, headers=None):
        self.base_url = base_url
        self.max_pages = max_pages
        self.lang_code = lang_code
        self.headers = headers or {'User-Agent': 'Mozilla/5.0 (NLP Dataset Crawler)'}
        self.visited_urls = set()
        self.urls_to_visit = [base_url]
        self.lang_pattern = re.compile(regex_pattern)

    def is_valid_url(self, url):
        parsed_base = urlparse(self.base_url)
        parsed_url = urlparse(url)
        return (parsed_base.netloc == parsed_url.netloc and url not in self.visited_urls)

    def extract_language_text(self, text):
        """Extract words matching the pattern, keep punctuation, clean spaces."""
        matches = self.lang_pattern.findall(text)
        extracted_text = " ".join(matches)
        # Clean up any double spaces
        return re.sub(r'[ \t]+', ' ', extracted_text).strip()

    def crawl(self):
        """Start crawling and return paragraph-level structured data."""
        pages_crawled = 0
        dataset = []

        while self.urls_to_visit and pages_crawled < self.max_pages:
            current_url = self.urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            print(f"  -> Crawling: {current_url}")
            try:
                response = requests.get(current_url, headers=self.headers, timeout=10)
                response.raise_for_status() 
            except requests.RequestException as e:
                print(f"  -> Failed to fetch: {e}")
                continue

            self.visited_urls.add(current_url)
            pages_crawled += 1

            soup = BeautifulSoup(response.content, 'html.parser')

            # Strip out noise completely
            for noise_element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                noise_element.extract()

            # 1. Use newline as the separator for HTML block elements (<p>, <div>, etc.)
            raw_text = soup.get_text(separator='\n', strip=True)
            
            # 2. Split the raw text by one or more newlines to get distinct paragraphs
            paragraphs = re.split(r'\n+', raw_text)
            
            # 3. Process each paragraph as a completely separate context
            for para in paragraphs:
                filtered_text = self.extract_language_text(para)
                
                # Check if text exists AND has more than 3 words (filters out stray menu words)
                if filtered_text and len(filtered_text.split()) > 20:
                    record = {
                        "url": current_url,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "language": self.lang_code,
                        "text": filtered_text
                    }
                    dataset.append(record)

            # Link extraction remains the same
            for a_tag in soup.find_all('a', href=True):
                next_url = urljoin(current_url, a_tag['href']).split('#')[0] 
                if self.is_valid_url(next_url) and next_url not in self.urls_to_visit:
                    self.urls_to_visit.append(next_url)

        return dataset