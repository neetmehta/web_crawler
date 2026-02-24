import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
import concurrent.futures

class LanguageCrawler:
    def __init__(self, base_url, max_pages, lang_code, regex_pattern, headers=None, max_workers=10):
        self.base_url = base_url
        self.max_pages = max_pages
        self.lang_code = lang_code
        self.headers = headers or {'User-Agent': 'Mozilla/5.0 (NLP Dataset Crawler)'}
        self.max_workers = max_workers # Number of parallel threads
        
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
        return re.sub(r'[ \t]+', ' ', extracted_text).strip()

    def _process_url(self, url):
        """Worker function to fetch and parse a single URL."""
        dataset = []
        new_links = []
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status() 
        except requests.RequestException as e:
            print(f"  -> Failed to fetch {url}: {e}")
            return dataset, new_links

        soup = BeautifulSoup(response.content, 'html.parser')

        # Strip out noise completely
        for noise_element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            noise_element.extract()

        raw_text = soup.get_text(separator='\n', strip=True)
        paragraphs = re.split(r'\n+', raw_text)
        
        # Extract Text
        for para in paragraphs:
            filtered_text = self.extract_language_text(para)
            if filtered_text and len(filtered_text.split()) > 20:
                record = {
                    "url": url,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "language": self.lang_code,
                    "text": filtered_text
                }
                dataset.append(record)

        # Extract Links
        for a_tag in soup.find_all('a', href=True):
            next_url = urljoin(url, a_tag['href']).split('#')[0] 
            new_links.append(next_url)

        return dataset, new_links

    def crawl(self):
        """Start multi-threaded crawling."""
        pages_crawled = 0
        final_dataset = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = set()

            # Loop until we hit max pages, or we run out of URLs and active threads
            while (self.urls_to_visit or futures) and pages_crawled < self.max_pages:
                
                # Submit new URLs to the thread pool up to the max_workers limit
                while self.urls_to_visit and len(futures) < self.max_workers and (pages_crawled + len(futures)) < self.max_pages:
                    current_url = self.urls_to_visit.pop(0)
                    
                    if current_url not in self.visited_urls:
                        self.visited_urls.add(current_url) # Mark visited immediately to prevent duplicates
                        print(f"  -> Submitting: {current_url}")
                        # Submit task to executor
                        futures.add(executor.submit(self._process_url, current_url))

                # If no futures are running, break out
                if not futures:
                    break

                # Wait for at least ONE thread to finish its job
                done, futures = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)

                # Process the completed threads
                for future in done:
                    pages_crawled += 1
                    try:
                        records, links = future.result()
                        final_dataset.extend(records)
                        
                        # Add newly found valid links to our queue
                        for link in links:
                            if self.is_valid_url(link) and link not in self.urls_to_visit:
                                self.urls_to_visit.append(link)
                                
                    except Exception as e:
                        print(f"  -> Error processing thread result: {e}")

        return final_dataset