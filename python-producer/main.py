#!/usr/bin/env python3
"""
Web Crawler Producer Service
Handles URL parsing, normalization, and discovery
"""

import asyncio
import logging
import os
import sys
from typing import List, Set
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass

import aiohttp
import tldextract
from bs4 import BeautifulSoup
from kafka import KafkaProducer
from pybloom_live import BloomFilter
from cassandra.cluster import Cluster
import redis
from loguru import logger
from prometheus_client import Counter, Histogram, start_http_server

# Metrics
URLS_PROCESSED = Counter('urls_processed_total', 'Total URLs processed')
URLS_DISCOVERED = Counter('urls_discovered_total', 'Total new URLs discovered')
PARSING_DURATION = Histogram('parsing_duration_seconds', 'Time spent parsing HTML')

@dataclass
class CrawledURL:
    url: str
    domain: str
    content: str
    links: List[str]

class URLProducer:
    def __init__(self):
        self.kafka_producer = None
        self.redis_client = None
        self.cassandra_session = None
        self.bloom_filter = None
        self.session = None
        
    async def initialize(self):
        """Initialize all connections and services"""
        logger.info("Initializing URL Producer...")
        
        # Kafka producer
        kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=kafka_servers.split(','),
            value_serializer=lambda v: v.encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        
        # Redis for caching
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # Cassandra for URL tracking
        cassandra_host = os.getenv('CASSANDRA_HOST', 'localhost')
        cassandra_port = int(os.getenv('CASSANDRA_PORT', '9042'))
        cluster = Cluster([cassandra_host], port=cassandra_port)
        self.cassandra_session = cluster.connect()
        
        # Initialize Cassandra keyspace and table
        await self._init_cassandra_schema()
        
        # Bloom filter for fast duplicate detection
        # 1 billion URLs with 1% false positive rate
        self.bloom_filter = BloomFilter(capacity=1000000000, error_rate=0.01)
        
        # HTTP session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'WebCrawler/1.0'}
        )
        
        logger.info("URL Producer initialized successfully")
    
    async def _init_cassandra_schema(self):
        """Initialize Cassandra keyspace and tables"""
        try:
            # Create keyspace
            self.cassandra_session.execute("""
                CREATE KEYSPACE IF NOT EXISTS webcrawler 
                WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1}
            """)
            
            # Use keyspace
            self.cassandra_session.set_keyspace('webcrawler')
            
            # Create URL tracking table
            self.cassandra_session.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    url_hash text PRIMARY KEY,
                    url text,
                    domain text,
                    status text,
                    discovered_at timestamp,
                    last_crawled timestamp
                )
            """)
            
            # Create domain tracking table
            self.cassandra_session.execute("""
                CREATE TABLE IF NOT EXISTS domains (
                    domain text PRIMARY KEY,
                    robots_txt text,
                    robots_txt_updated timestamp,
                    crawl_delay int,
                    last_crawled timestamp
                )
            """)
            
            logger.info("Cassandra schema initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Cassandra schema: {e}")
            raise
    
    def normalize_url(self, url: str, base_url: str = None) -> str:
        """Normalize URL to standard form"""
        try:
            # Convert relative URLs to absolute
            if base_url:
                url = urljoin(base_url, url)
            
            # Parse URL
            parsed = urlparse(url)
            
            # Remove fragment and normalize
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            
            return normalized
        except Exception as e:
            logger.warning(f"Failed to normalize URL {url}: {e}")
            return None
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            extracted = tldextract.extract(url)
            return f"{extracted.domain}.{extracted.suffix}"
        except Exception as e:
            logger.warning(f"Failed to extract domain from {url}: {e}")
            return None
    
    async def check_robots_txt(self, domain: str) -> bool:
        """Check if URL is allowed by robots.txt"""
        try:
            # Check cache first
            cache_key = f"robots:{domain}"
            cached_rules = self.redis_client.get(cache_key)
            
            if cached_rules:
                # Parse cached rules (simplified)
                return "Disallow: /" not in cached_rules
            
            # Fetch robots.txt
            robots_url = f"http://{domain}/robots.txt"
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    robots_content = await response.text()
                    # Cache for 24 hours
                    self.redis_client.setex(cache_key, 86400, robots_content)
                    return "Disallow: /" not in robots_content
            
            return True  # Allow if robots.txt not found
        except Exception as e:
            logger.warning(f"Failed to check robots.txt for {domain}: {e}")
            return True  # Allow on error
    
    async def parse_html_content(self, content: str, base_url: str) -> List[str]:
        """Parse HTML content and extract links"""
        try:
            soup = BeautifulSoup(content, 'lxml')
            links = []
            
            # Extract all href attributes
            for link in soup.find_all('a', href=True):
                href = link['href']
                normalized_url = self.normalize_url(href, base_url)
                if normalized_url:
                    links.append(normalized_url)
            
            return links
        except Exception as e:
            logger.error(f"Failed to parse HTML content: {e}")
            return []
    
    async def is_url_seen(self, url: str) -> bool:
        """Check if URL has been seen before using Bloom filter and Cassandra"""
        try:
            # Quick check with Bloom filter
            if url in self.bloom_filter:
                # Double-check with Cassandra
                url_hash = str(hash(url))
                result = self.cassandra_session.execute(
                    "SELECT url_hash FROM urls WHERE url_hash = %s", (url_hash,)
                )
                return bool(result.one())
            
            return False
        except Exception as e:
            logger.error(f"Failed to check if URL seen: {e}")
            return True  # Assume seen on error
    
    async def mark_url_seen(self, url: str, domain: str):
        """Mark URL as seen in both Bloom filter and Cassandra"""
        try:
            url_hash = str(hash(url))
            
            # Add to Bloom filter
            self.bloom_filter.add(url)
            
            # Store in Cassandra
            self.cassandra_session.execute(
                """
                INSERT INTO urls (url_hash, url, domain, status, discovered_at)
                VALUES (%s, %s, %s, %s, toTimestamp(now()))
                """,
                (url_hash, url, domain, 'discovered')
            )
        except Exception as e:
            logger.error(f"Failed to mark URL as seen: {e}")
    
    async def process_crawled_url(self, crawled_url: CrawledURL):
        """Process a crawled URL and extract new links"""
        try:
            with PARSING_DURATION.time():
                # Parse HTML content
                new_links = await self.parse_html_content(
                    crawled_url.content, 
                    crawled_url.url
                )
                
                # Process each new link
                for link in new_links:
                    domain = self.extract_domain(link)
                    if not domain:
                        continue
                    
                    # Check if URL already seen
                    if await self.is_url_seen(link):
                        continue
                    
                    # Check robots.txt
                    if not await self.check_robots_txt(domain):
                        logger.info(f"URL {link} blocked by robots.txt")
                        continue
                    
                    # Mark as seen
                    await self.mark_url_seen(link, domain)
                    
                    # Send to Kafka for crawling
                    self.kafka_producer.send(
                        'urls-to-crawl',
                        key=domain,
                        value=link
                    )
                    
                    URLS_DISCOVERED.inc()
                    logger.info(f"Discovered new URL: {link}")
                
                URLS_PROCESSED.inc()
                logger.info(f"Processed {len(new_links)} links from {crawled_url.url}")
                
        except Exception as e:
            logger.error(f"Failed to process crawled URL {crawled_url.url}: {e}")
    
    async def run(self):
        """Main producer loop"""
        logger.info("Starting URL Producer...")
        
        # Start metrics server
        start_http_server(8000)
        
        # Main processing loop
        while True:
            try:
                # In a real implementation, this would consume from a Kafka topic
                # containing crawled URLs. For now, we'll simulate with seed URLs
                seed_urls = [
                    "https://en.wikipedia.org/wiki/History_of_India",
                    "https://en.wikipedia.org/wiki/Lists_of_films",
                    "https://en.wikipedia.org/wiki/Animal"
                ]
                
                for url in seed_urls:
                    # Simulate processing a crawled URL
                    domain = self.extract_domain(url)
                    if domain:
                        crawled_url = CrawledURL(
                            url=url,
                            domain=domain,
                            content="<html><body><a href='https://example.com/page1'>Link</a></body></html>",
                            links=[]
                        )
                        await self.process_crawled_url(crawled_url)
                
                await asyncio.sleep(10)  # Process every 10 seconds
                
            except KeyboardInterrupt:
                logger.info("Shutting down URL Producer...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        if self.kafka_producer:
            self.kafka_producer.close()
        if self.cassandra_session:
            self.cassandra_session.shutdown()

async def main():
    """Main entry point"""
    # Configure logging
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    logger.add("producer.log", rotation="10 MB", level="DEBUG")
    
    producer = URLProducer()
    
    try:
        await producer.initialize()
        await producer.run()
    finally:
        await producer.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
