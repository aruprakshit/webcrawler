"""
URL processing service following Single Responsibility Principle
"""
import hashlib
from typing import Optional
from urllib.parse import urljoin, urlparse

import tldextract
from loguru import logger

from config import Config


class URLService:
    """Service responsible for URL processing operations"""
    
    def __init__(self):
        self._extractor = None
    
    def _get_extractor(self):
        """Lazy initialization of tldextract"""
        if self._extractor is None:
            import os
            os.makedirs(Config.TLDEXTRACT_CACHE_DIR, exist_ok=True)
            self._extractor = tldextract.TLDExtract(cache_dir=Config.TLDEXTRACT_CACHE_DIR)
        return self._extractor
    
    def normalize_url(self, url: str, base_url: Optional[str] = None) -> Optional[str]:
        """
        Normalize URL to standard form
        
        Args:
            url: URL to normalize
            base_url: Base URL for relative URL resolution
            
        Returns:
            Normalized URL or None if invalid
        """
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
    
    def extract_domain(self, url: str) -> Optional[str]:
        """
        Extract domain from URL
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name or None if extraction fails
        """
        try:
            extractor = self._get_extractor()
            extracted = extractor(url)
            return f"{extracted.domain}.{extracted.suffix}"
        except Exception as e:
            logger.warning(f"Failed to extract domain from {url}: {e}")
            return None
    
    def generate_url_hash(self, url: str) -> str:
        """
        Generate hash for URL
        
        Args:
            url: URL to hash
            
        Returns:
            URL hash as string
        """
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
