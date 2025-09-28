#!/usr/bin/env python3
"""
Refactored Web Crawler Producer Service
Following SOLID principles and service class patterns
"""

import asyncio
import json
import sys
from typing import Optional

from loguru import logger

from config import Config
from models import CrawledURL
from services.url_service import URLService
from services.html_service import HTMLService
from services.kafka_service import KafkaService
from services.cassandra_service import CassandraService
from services.redis_service import RedisService
from services.bloom_filter_service import BloomFilterService
from services.url_processor_service import URLProcessorService
from services.metrics_service import MetricsService


class URLProducerApplication:
    """
    Main application class following Dependency Inversion Principle
    """
    
    def __init__(self):
        # Initialize services
        self._url_service = URLService()
        self._html_service = HTMLService()
        self._kafka_service = KafkaService()
        self._cassandra_service = CassandraService()
        self._redis_service = RedisService()
        self._bloom_filter_service = BloomFilterService()
        self._metrics_service = MetricsService()
        
        # Initialize URL processor with dependencies
        self._url_processor = URLProcessorService(
            self._url_service,
            self._html_service,
            self._cassandra_service,
            self._bloom_filter_service,
            self._kafka_service
        )
    
    async def initialize(self) -> None:
        """Initialize all services"""
        logger.info("Initializing URL Producer Application...")
        
        try:
            # Initialize all services
            self._kafka_service.initialize_producer()
            self._kafka_service.initialize_consumer(
                Config.KAFKA_CRAWLED_TOPIC,
                Config.KAFKA_CONSUMER_GROUP
            )
            self._cassandra_service.initialize()
            self._redis_service.initialize()
            self._bloom_filter_service.initialize()
            self._metrics_service.start_metrics_server()
            
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    async def run(self) -> None:
        """Main application loop"""
        logger.info("Starting URL Producer Application...")
        
        # Inject seed URLs at startup
        await self._url_processor.inject_seed_urls()
        
        # Main processing loop
        while True:
            try:
                # Consume from crawled-content topic
                for message in self._kafka_service.consume_messages():
                    try:
                        # Parse the crawled content message
                        crawled_data = json.loads(message.value)
                        
                        # Create CrawledURL object
                        crawled_url = CrawledURL(
                            url=crawled_data['url'],
                            domain=crawled_data['domain'],
                            content=crawled_data['content'],
                            links=[]
                        )
                        
                        # Process the crawled URL to extract new links
                        await self._url_processor.process_crawled_url(crawled_url)
                        
                    except Exception as e:
                        logger.error(f"Failed to process crawled content message: {e}")
                        continue
                
            except KeyboardInterrupt:
                logger.info("Shutting down URL Producer Application...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)
    
    async def cleanup(self) -> None:
        """Cleanup all services"""
        logger.info("Cleaning up services...")
        
        try:
            self._kafka_service.close()
            self._cassandra_service.close()
            self._redis_service.close()
            
            logger.info("All services cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def setup_logging() -> None:
    """Setup logging configuration"""
    log_dir = Config.LOG_DIR
    logger.remove()
    logger.add(sys.stdout, level=Config.LOG_LEVEL)
    logger.add(f"{log_dir}/producer.log", rotation="10 MB", level="DEBUG")


async def main():
    """Main entry point"""
    # Setup logging
    setup_logging()
    
    # Create and run application
    app = URLProducerApplication()
    
    try:
        await app.initialize()
        await app.run()
    finally:
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
