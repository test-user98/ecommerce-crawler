# EcommerceCrawler

## Overview
EcommerceCrawler is an asynchronous web crawler designed to extract product URLs from specified e-commerce domains. By leveraging Python's `asyncio` and `aiohttp`, the crawler operates efficiently, allowing for concurrent requests while adhering to a specified maximum depth for crawling.

## Technologies Used
- **Python**: Core programming language.
- **Asyncio**: Provides the framework for asynchronous programming.
- **Aiohttp**: Allows for making asynchronous HTTP requests.
- **BeautifulSoup**: Parses HTML and XML documents, useful for web scraping.
- **TLDExtract**: Extracts the top-level domain from URLs.
- **JSON**: For saving and loading crawl progress.

## Features
- **Asynchronous Processing**: Efficiently manages multiple HTTP requests concurrently.
- **Product URL Detection**: Uses regex patterns and HTML meta tags to identify product URLs.
- **Progress Management**: Saves and loads crawling state using JSON files, enabling resumption.
- **Configurable Parameters**: Users can set the maximum crawl depth, concurrent requests, batch size, and rate limits.

## Architectural Flow
1. **Initialization**: The crawler is initialized with a list of domains and configurations.
2. **URL Processing**:
   - The crawler fetches the HTML of each URL.
   - It checks if the URL is a product page using regex patterns and HTML content analysis.
3. **Queue Management**: 
   - URLs to be processed are added to an asyncio queue.
   - Worker tasks are spawned to handle URL processing concurrently.
4. **Progress Saving**: After crawling, the visited URLs and identified product URLs are saved to a JSON file.
5. **Termination**: The crawler can be gracefully shut down, saving its state for future sessions.

## Optimization Strategies
- **Concurrency**: Utilizes asynchronous programming to handle multiple requests without blocking, significantly improving crawl speed.
- **Error Handling**: Catches exceptions during fetch operations to ensure robust performance even when encountering network issues.
- **Rate Limiting**: Configurable parameters help avoid overwhelming target servers.
- **Domain Filtering**: Only processes URLs belonging to the specified root domains, reducing unnecessary requests.

## Usage
1. Clone the repository.
2. Install the required packages using:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the crawler:
   ```bash
   python main.py
   ```
