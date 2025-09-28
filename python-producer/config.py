"""
Configuration management for the web crawler producer
"""
import os
from typing import List


class Config:
    """Configuration class following Single Responsibility Principle"""
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_CONSUMER_GROUP: str = os.getenv('KAFKA_CONSUMER_GROUP', 'url-producer-group')
    KAFKA_URLS_TOPIC: str = os.getenv('KAFKA_URLS_TOPIC', 'urls-to-crawl')
    KAFKA_CRAWLED_TOPIC: str = os.getenv('KAFKA_CRAWLED_TOPIC', 'crawled-content')
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))
    
    # Cassandra Configuration
    CASSANDRA_HOST: str = os.getenv('CASSANDRA_HOST', 'localhost')
    CASSANDRA_PORT: int = int(os.getenv('CASSANDRA_PORT', '9042'))
    CASSANDRA_KEYSPACE: str = os.getenv('CASSANDRA_KEYSPACE', 'webcrawler')
    
    # Bloom Filter Configuration
    BLOOM_FILTER_CAPACITY: int = int(os.getenv('BLOOM_FILTER_CAPACITY', '1000000000'))
    BLOOM_FILTER_ERROR_RATE: float = float(os.getenv('BLOOM_FILTER_ERROR_RATE', '0.01'))
    
    # HTTP Configuration
    HTTP_TIMEOUT: int = int(os.getenv('HTTP_TIMEOUT', '30'))
    USER_AGENT: str = os.getenv('USER_AGENT', 'WebCrawler/1.0')
    
    # Logging Configuration
    LOG_DIR: str = os.getenv('LOG_DIR', '/app/logs')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Metrics Configuration
    METRICS_PORT: int = int(os.getenv('METRICS_PORT', '8000'))
    
    # TLD Extract Configuration
    TLDEXTRACT_CACHE_DIR: str = os.getenv('TLDEXTRACT_CACHE_DIR', '/app/cache')
    
    # Seed URLs
    SEED_URLS: List[str] = [
        "https://en.wikipedia.org/wiki/History_of_India",
        "https://en.wikipedia.org/wiki/Lists_of_films",
        "https://en.wikipedia.org/wiki/Animal",
        "https://developer.mozilla.org/en-US/docs/Web/CSS/Reference",
        "https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements"
    ]
    
    @classmethod
    def get_kafka_servers(cls) -> List[str]:
        """Get Kafka servers as a list"""
        return cls.KAFKA_BOOTSTRAP_SERVERS.split(',')
    
    @classmethod
    def get_redis_url(cls) -> str:
        """Get Redis connection URL"""
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
