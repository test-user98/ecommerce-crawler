import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import json
from asyncio import Queue
import tldextract

class Config:
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Connection': 'keep-alive',
    }
    TIMEOUT = 30


class URLUtils:
    @staticmethod
    def get_root_domain(url):
        ext = tldextract.extract(url)
        return f"{ext.domain}.{ext.suffix}"


class AsyncEcommerceCrawler:
    def __init__(self, domains, max_depth=1, max_concurrent=10, batch_size=100, rate_limit=5):
        self.domains = domains
        self.max_depth = max_depth
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.visited_urls = set()
        self.product_urls = {domain: set() for domain in domains}
        self.queue = Queue()

    async def is_product_url(self, url, html):
        product_patterns = [
            r'/product/', r'/item/', r'/p/', r'pid=', r'productid=',
            r'/dp/', r'/gp/product/', r'product/', r'categoryId='
        ]
        if any(re.search(pattern, url, re.IGNORECASE) for pattern in product_patterns):
            return True
        
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            if soup.find('meta', {'name': 'og:type', 'content': 'product'}) or \
               soup.find('meta', {'property': 'product'}):
                return True
            
            product_keywords = ['add to cart', 'buy now', 'price', 'in stock', 'SKU', 'quantity']
            page_text = soup.get_text().lower()
            if any(keyword in page_text for keyword in product_keywords):
                return True
            
        return False

    async def fetch(self, session, url):
        try:
            async with session.get(url, headers=Config.HEADERS, timeout=Config.TIMEOUT) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Error fetching {url}: Status code: {response.status}")
        except Exception as e:
            print(f"Fetch error: {e}")
        return None

    async def process_url(self, session, url, depth, root_domain):
        if depth > self.max_depth or url in self.visited_urls:
            return

        self.visited_urls.add(url)
        html = await self.fetch(session, url)
        if not html:
            return

        if await self.is_product_url(url, html):
            self.product_urls[root_domain].add(url)

        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=True)

        for link in links:
            next_url = urljoin(url, link['href'])
            next_root_domain = URLUtils.get_root_domain(next_url)
            if next_root_domain == root_domain and next_url not in self.visited_urls:
                await self.queue.put((next_url, depth + 1, root_domain))

    async def worker(self, session):
        while True:
            try:
                url, depth, root_domain = await asyncio.wait_for(self.queue.get(), timeout=10)
                await self.process_url(session, url, depth, root_domain)
                self.queue.task_done()
            except asyncio.TimeoutError:
                break
            except Exception as e:
                print(f"Error in worker {e}")

    async def crawl_domain(self, domain):
        base_url = f"https://{domain}"
        root_domain = URLUtils.get_root_domain(base_url)
        await self.queue.put((base_url, 0, root_domain))

    async def save_progress(self):
        with open('crawler_progress.json', 'w') as f:
            json.dump({
                'visited_urls': list(self.visited_urls),
                'product_urls': {domain: list(urls) for domain, urls in self.product_urls.items()}
            }, f)

    async def load_progress(self):
        try:
            with open('crawler_progress.json', 'r') as f:
                data = json.load(f)
                self.visited_urls = set(data.get('visited_urls', []))
                self.product_urls = {domain: set(urls) for domain, urls in data.get('product_urls', {}).items()}
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    async def run(self):
        await self.load_progress()
        print(f"Starting crawl for {len(self.domains)} domains")
        
        async with aiohttp.ClientSession() as session:
            for domain in self.domains:
                await self.crawl_domain(domain)

            workers = [asyncio.create_task(self.worker(session)) for _ in range(self.max_concurrent)]

            await self.queue.join()  # Wait until the queue is fully processed

            for w in workers:
                w.cancel()

        await self.save_progress()
        total_product_urls = sum(len(urls) for urls in self.product_urls.values())
        print(f"Crawl completed. Found {total_product_urls} product URLs across all domains")
        return self.product_urls

# Usage
async def main():
    domains = ["flipkart.com", "amazon.in", "myntra.com"]
    crawler = AsyncEcommerceCrawler(domains)
    product_urls = await crawler.run()
    for domain, urls in product_urls.items():
        print(f"{domain}: {len(urls)} product URLs")

if __name__ == "__main__":
    asyncio.run(main())
