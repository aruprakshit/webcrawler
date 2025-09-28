"""
URL processor service following Single Responsibility Principle
"""
import json
from typing import List, Optional
from loguru import logger
from prometheus_client import Counter, Histogram

from models import CrawledURL, URLMetadata
from services.url_service import URLService
from services.html_service import HTMLService
from services.cassandra_service import CassandraService
from services.bloom_filter_service import BloomFilterService
from services.kafka_service import KafkaService
from config import Config

# Metrics
URLS_PROCESSED = Counter('urls_processed_total', 'Total URLs processed')
URLS_DISCOVERED = Counter('urls_discovered_total', 'Total new URLs discovered')
PARSING_DURATION = Histogram('parsing_duration_seconds', 'Time spent parsing HTML')


class URLProcessorService:
    """Service responsible for processing crawled URLs and discovering new ones"""
    
    def __init__(
        self,
        url_service: URLService,
        html_service: HTMLService,
        cassandra_service: CassandraService,
        bloom_filter_service: BloomFilterService,
        kafka_service: KafkaService
    ):
        self._url_service = url_service
        self._html_service = html_service
        self._cassandra_service = cassandra_service
        self._bloom_filter_service = bloom_filter_service
        self._kafka_service = kafka_service
    
    async def process_crawled_url(self, crawled_url: CrawledURL) -> None:
        """
        Process a crawled URL and extract new links
        
        Args:
            crawled_url: CrawledURL object to process
        """
        try:
            with PARSING_DURATION.time():
                # Parse HTML content to extract links
                raw_links = self._html_service.extract_links(
                    crawled_url.content, 
                    crawled_url.url
                )
                
                # Normalize and filter links
                new_links = await self._process_links(raw_links, crawled_url.url)
                
                # Process each new link
                for link in new_links:
                    await self._process_new_url(link)
                
                URLS_PROCESSED.inc()
                logger.info(f"Processed {len(new_links)} links from {crawled_url.url}")
                
        except Exception as e:
            logger.error(f"Failed to process crawled URL {crawled_url.url}: {e}")
    
    async def _process_links(self, raw_links: List[str], base_url: str) -> List[str]:
        """
        Process and normalize links
        
        Args:
            raw_links: Raw links from HTML
            base_url: Base URL for normalization
            
        Returns:
            List of normalized and valid links
        """
        new_links = []
        
        for link in raw_links:
            # Normalize URL
            normalized_url = self._url_service.normalize_url(link, base_url)
            if not normalized_url:
                continue
            
            # Validate URL
            if not self._url_service.is_valid_url(normalized_url):
                continue
            
            new_links.append(normalized_url)
        
        return new_links
    
    async def _process_new_url(self, url: str) -> None:
        """
        Process a new URL (check if seen, mark as seen, send to Kafka)
        
        Args:
            url: URL to process
        """
        try:
            # Extract domain
            domain = self._url_service.extract_domain(url)
            if not domain:
                return
            
            # Generate URL hash
            url_hash = self._url_service.generate_url_hash(url)
            
            # Check if URL already seen using Bloom filter first
            if self._bloom_filter_service.contains(url):
                # Double-check with Cassandra
                if self._cassandra_service.is_url_seen(url_hash):
                    return
            
            # Mark URL as seen
            url_metadata = URLMetadata(
                url=url,
                domain=domain,
                url_hash=url_hash,
                status='discovered',
                discovered_at=None  # Will be set by Cassandra
            )
            
            await self._mark_url_seen(url_metadata)
            
            # Send to Kafka for crawling
            self._kafka_service.send_message(
                Config.KAFKA_URLS_TOPIC,
                domain,
                url
            )
            
            URLS_DISCOVERED.inc()
            logger.info(f"Discovered new URL: {url}")
            
        except Exception as e:
            logger.error(f"Failed to process new URL {url}: {e}")
    
    async def _mark_url_seen(self, url_metadata: URLMetadata) -> None:
        """
        Mark URL as seen in both Bloom filter and Cassandra
        
        Args:
            url_metadata: URL metadata to store
        """
        try:
            # Add to Bloom filter
            self._bloom_filter_service.add(url_metadata.url)
            
            # Store in Cassandra
            self._cassandra_service.mark_url_seen(url_metadata)
            
        except Exception as e:
            logger.error(f"Failed to mark URL as seen: {e}")
    
    async def inject_seed_urls(self) -> None:
        """Inject initial seed URLs into the system"""
        logger.info(f"Injecting {len(Config.SEED_URLS)} seed URLs into the system...")
        
        for url in Config.SEED_URLS:
            try:
                domain = self._url_service.extract_domain(url)
                if not domain:
                    continue
                
                # Send seed URL to Kafka
                self._kafka_service.send_message(
                    Config.KAFKA_URLS_TOPIC,
                    domain,
                    url
                )
                
                # Mark as seen to avoid duplicates
                url_hash = self._url_service.generate_url_hash(url)
                url_metadata = URLMetadata(
                    url=url,
                    domain=domain,
                    url_hash=url_hash,
                    status='discovered',
                    discovered_at=None
                )
                
                await self._mark_url_seen(url_metadata)
                logger.info(f"Injected seed URL: {url}")
                
            except Exception as e:
                logger.error(f"Failed to inject seed URL {url}: {e}")
        
        logger.info("Seed URL injection completed")
