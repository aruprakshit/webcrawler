"""
Cassandra service following Single Responsibility Principle
"""
from typing import Optional, List
from datetime import datetime
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from loguru import logger

from config import Config
from models import URLMetadata


class CassandraService:
    """Service responsible for Cassandra database operations"""
    
    def __init__(self):
        self._cluster: Optional[Cluster] = None
        self._session = None
    
    def initialize(self) -> None:
        """Initialize Cassandra connection"""
        try:
            self._cluster = Cluster([Config.CASSANDRA_HOST], port=Config.CASSANDRA_PORT)
            self._session = self._cluster.connect()
            self._session.set_keyspace(Config.CASSANDRA_KEYSPACE)
            logger.info("Cassandra connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Cassandra connection: {e}")
            raise
    
    def is_url_seen(self, url_hash: str) -> bool:
        """
        Check if URL has been seen before
        
        Args:
            url_hash: URL hash to check
            
        Returns:
            True if URL has been seen, False otherwise
        """
        try:
            result = self._session.execute(
                "SELECT url_hash FROM urls WHERE url_hash = %s",
                (url_hash,)
            )
            return bool(result.one())
        except Exception as e:
            logger.error(f"Failed to check if URL seen: {e}")
            return True  # Assume seen on error to avoid duplicates
    
    def mark_url_seen(self, url_metadata: URLMetadata) -> None:
        """
        Mark URL as seen in database
        
        Args:
            url_metadata: URL metadata to store
        """
        try:
            self._session.execute(
                """
                INSERT INTO urls (url_hash, url, domain, status, discovered_at)
                VALUES (%s, %s, %s, %s, toTimestamp(now()))
                """,
                (url_metadata.url_hash, url_metadata.url, url_metadata.domain, url_metadata.status)
            )
            logger.debug(f"Marked URL as seen: {url_metadata.url}")
        except Exception as e:
            logger.error(f"Failed to mark URL as seen: {e}")
            raise
    
    def update_url_status(self, url_hash: str, status: str, content_id: Optional[str] = None) -> None:
        """
        Update URL status in database
        
        Args:
            url_hash: URL hash to update
            status: New status
            content_id: Optional content ID
        """
        try:
            if content_id:
                self._session.execute(
                    """
                    UPDATE urls 
                    SET status = %s, last_crawled = toTimestamp(now()), content_id = %s
                    WHERE url_hash = %s
                    """,
                    (status, content_id, url_hash)
                )
            else:
                self._session.execute(
                    """
                    UPDATE urls 
                    SET status = %s, last_crawled = toTimestamp(now())
                    WHERE url_hash = %s
                    """,
                    (status, url_hash)
                )
            logger.debug(f"Updated URL status: {url_hash} -> {status}")
        except Exception as e:
            logger.error(f"Failed to update URL status: {e}")
            raise
    
    def get_urls_by_domain(self, domain: str, limit: int = 100) -> List[URLMetadata]:
        """
        Get URLs by domain
        
        Args:
            domain: Domain to search for
            limit: Maximum number of URLs to return
            
        Returns:
            List of URL metadata
        """
        try:
            result = self._session.execute(
                "SELECT url_hash, url, domain, status, discovered_at, last_crawled, content_id FROM urls WHERE domain = %s LIMIT %s",
                (domain, limit)
            )
            
            urls = []
            for row in result:
                urls.append(URLMetadata(
                    url=row.url,
                    domain=row.domain,
                    url_hash=row.url_hash,
                    status=row.status,
                    discovered_at=row.discovered_at,
                    last_crawled=row.last_crawled,
                    content_id=row.content_id
                ))
            
            return urls
        except Exception as e:
            logger.error(f"Failed to get URLs by domain: {e}")
            return []
    
    def get_urls_by_status(self, status: str, limit: int = 100) -> List[URLMetadata]:
        """
        Get URLs by status
        
        Args:
            status: Status to search for
            limit: Maximum number of URLs to return
            
        Returns:
            List of URL metadata
        """
        try:
            result = self._session.execute(
                "SELECT url_hash, url, domain, status, discovered_at, last_crawled, content_id FROM urls WHERE status = %s LIMIT %s",
                (status, limit)
            )
            
            urls = []
            for row in result:
                urls.append(URLMetadata(
                    url=row.url,
                    domain=row.domain,
                    url_hash=row.url_hash,
                    status=row.status,
                    discovered_at=row.discovered_at,
                    last_crawled=row.last_crawled,
                    content_id=row.content_id
                ))
            
            return urls
        except Exception as e:
            logger.error(f"Failed to get URLs by status: {e}")
            return []
    
    def close(self) -> None:
        """Close Cassandra connection"""
        try:
            if self._cluster:
                self._cluster.shutdown()
                logger.info("Cassandra connection closed")
        except Exception as e:
            logger.error(f"Error closing Cassandra connection: {e}")
