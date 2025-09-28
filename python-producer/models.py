"""
Data models and DTOs for the web crawler producer
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class CrawledURL:
    """Represents a crawled URL with its content and metadata"""
    url: str
    domain: str
    content: str
    links: List[str]
    content_id: Optional[str] = None
    crawled_at: Optional[datetime] = None


@dataclass
class URLMetadata:
    """Represents URL metadata for tracking"""
    url: str
    domain: str
    url_hash: str
    status: str
    discovered_at: datetime
    last_crawled: Optional[datetime] = None
    content_id: Optional[str] = None


@dataclass
class DomainInfo:
    """Represents domain-specific information"""
    domain: str
    robots_txt: Optional[str] = None
    robots_txt_updated: Optional[datetime] = None
    crawl_delay: int = 1000
    last_crawled: Optional[datetime] = None


@dataclass
class KafkaMessage:
    """Represents a Kafka message"""
    topic: str
    key: str
    value: str
    partition: Optional[int] = None
    offset: Optional[int] = None
