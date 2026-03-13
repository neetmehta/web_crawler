import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
import concurrent.futures
import trafilatura

class LanguageCrawler:
    def __init__(self, base_urls, max_pages, lang_code, regex_pattern, headers=None, max_workers=10):
        # Accept either a single URL or a list of start URLs
        if isinstance(base_urls, (list, tuple)):
            self.base_urls = list(base_urls)
        else:
            self.base_urls = [base_urls]

        self.max_pages = max_pages
        self.lang_code = lang_code
        self.headers = headers or {'User-Agent': 'Mozilla/5.0 (NLP Dataset Crawler)'}
        self.max_workers = max_workers  # Number of parallel threads

        # Global visited set to prevent duplicates across start URLs
        self.visited_urls = set()
        self.lang_pattern = re.compile(regex_pattern)

    def is_valid_url(self, url, base_netloc):
        parsed_url = urlparse(url)
        return (parsed_url.netloc == base_netloc and url not in self.visited_urls)

    def extract_language_text(self, text):
        """Extract words matching the pattern, keep punctuation, clean spaces."""
        matches = self.lang_pattern.findall(text)
        extracted_text = " ".join(matches)
        return re.sub(r'[ \t]+', ' ', extracted_text).strip()

    def _process_url(self, url):
        """Worker function using Trafilatura for smart extraction."""
        dataset = []
        new_links = []
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status() 
        except requests.RequestException as e:
            return dataset, new_links

        # 1. Extract links using BeautifulSoup (Trafilatura is for text, BS4 is better for links)
        soup = BeautifulSoup(response.content, 'html.parser')
        for a_tag in soup.find_all('a', href=True):
            next_url = urljoin(url, a_tag['href']).split('#')[0] 
            new_links.append(next_url)

        # 2. SMART TEXT EXTRACTION
        # Trafilatura automatically ignores menus, footers, and cookie banners!
        downloaded = response.content
        extracted_text = trafilatura.extract(
            downloaded, 
            include_comments=False, # Ignore user comments
            include_tables=False,   # Ignore tabular data
            include_links=False     # Strip out link texts
        )

        # If trafilatura couldn't find a main article, skip the page
        if not extracted_text:
            return dataset, new_links

        # 3. Process the cleanly extracted article paragraphs
        paragraphs = re.split(r'\n+', extracted_text)
        
        for para in paragraphs:
            filtered_text = self.extract_language_text(para)
            
            # Keep the 20-word minimum as a final safety net
            if filtered_text and len(filtered_text.split()) > 20:
                record = {
                    "url": url,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "language": self.lang_code,
                    "text": filtered_text
                }
                dataset.append(record)

        return dataset, new_links
    
    def crawl(self):
        """Start multi-threaded crawling.

        This implementation crawls up to `self.max_pages` pages per start URL
        in `self.base_urls`. A global `visited_urls` set prevents duplicates
        across multiple start URLs.
        """
        final_dataset = []

        # Process each start URL independently (limit applies per-start)
        for start_url in self.base_urls:
            pages_crawled = 0
            urls_to_visit = [start_url]
            parsed_base = urlparse(start_url)
            base_netloc = parsed_base.netloc

            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = set()

                while (urls_to_visit or futures) and pages_crawled < self.max_pages:

                    # Submit new URLs to the thread pool up to the max_workers limit
                    while urls_to_visit and len(futures) < self.max_workers and (pages_crawled + len(futures)) < self.max_pages:
                        current_url = urls_to_visit.pop(0)

                        if current_url not in self.visited_urls:
                            self.visited_urls.add(current_url)  # Mark visited immediately to prevent duplicates
                            print(f"  -> Submitting: {current_url}")
                            futures.add(executor.submit(self._process_url, current_url))

                    # If no futures are running, break out
                    if not futures:
                        break

                    # Wait for at least one thread to finish its job
                    done, futures = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)

                    # Process the completed threads
                    for future in done:
                        pages_crawled += 1
                        try:
                            records, links = future.result()
                            final_dataset.extend(records)

                            # Add newly found valid links to our queue
                            for link in links:
                                if self.is_valid_url(link, base_netloc) and link not in urls_to_visit:
                                    urls_to_visit.append(link)

                        except Exception as e:
                            print(f"  -> Error processing thread result: {e}")

            print(f"  -> Finished start URL {start_url}: crawled {pages_crawled} pages")

        return final_dataset