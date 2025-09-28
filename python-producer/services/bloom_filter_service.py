"""
Bloom filter service following Single Responsibility Principle
"""
from typing import Set
from pybloom_live import BloomFilter
from loguru import logger

from config import Config


class BloomFilterService:
    """Service responsible for Bloom filter operations"""
    
    def __init__(self):
        self._bloom_filter: Optional[BloomFilter] = None
    
    def initialize(self) -> None:
        """Initialize Bloom filter"""
        try:
            self._bloom_filter = BloomFilter(
                capacity=Config.BLOOM_FILTER_CAPACITY,
                error_rate=Config.BLOOM_FILTER_ERROR_RATE
            )
            logger.info("Bloom filter initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Bloom filter: {e}")
            raise
    
    def add(self, item: str) -> None:
        """
        Add item to Bloom filter
        
        Args:
            item: Item to add
        """
        try:
            if self._bloom_filter:
                self._bloom_filter.add(item)
                logger.debug(f"Added item to Bloom filter: {item}")
        except Exception as e:
            logger.error(f"Failed to add item to Bloom filter: {e}")
    
    def contains(self, item: str) -> bool:
        """
        Check if item is in Bloom filter
        
        Args:
            item: Item to check
            
        Returns:
            True if item might be in filter, False if definitely not
        """
        try:
            if self._bloom_filter:
                return item in self._bloom_filter
            return False
        except Exception as e:
            logger.error(f"Failed to check item in Bloom filter: {e}")
            return True  # Assume present on error to avoid duplicates
    
    def add_multiple(self, items: Set[str]) -> None:
        """
        Add multiple items to Bloom filter
        
        Args:
            items: Set of items to add
        """
        try:
            if self._bloom_filter:
                for item in items:
                    self._bloom_filter.add(item)
                logger.debug(f"Added {len(items)} items to Bloom filter")
        except Exception as e:
            logger.error(f"Failed to add multiple items to Bloom filter: {e}")
    
    def get_capacity(self) -> int:
        """
        Get Bloom filter capacity
        
        Returns:
            Bloom filter capacity
        """
        return Config.BLOOM_FILTER_CAPACITY
    
    def get_error_rate(self) -> float:
        """
        Get Bloom filter error rate
        
        Returns:
            Bloom filter error rate
        """
        return Config.BLOOM_FILTER_ERROR_RATE
    
    def get_approximate_size(self) -> int:
        """
        Get approximate number of items in Bloom filter
        
        Returns:
            Approximate number of items
        """
        try:
            if self._bloom_filter:
                return len(self._bloom_filter)
            return 0
        except Exception as e:
            logger.error(f"Failed to get Bloom filter size: {e}")
            return 0
