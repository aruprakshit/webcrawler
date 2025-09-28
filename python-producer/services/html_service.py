"""
HTML parsing service following Single Responsibility Principle
"""
from typing import List
from bs4 import BeautifulSoup
from loguru import logger


class HTMLService:
    """Service responsible for HTML parsing operations"""
    
    def __init__(self):
        self._parser = 'lxml'
    
    def extract_links(self, html_content: str, base_url: str) -> List[str]:
        """
        Extract all links from HTML content
        
        Args:
            html_content: HTML content to parse
            base_url: Base URL for relative link resolution
            
        Returns:
            List of extracted and normalized links
        """
        try:
            soup = BeautifulSoup(html_content, self._parser)
            links = []
            
            # Extract all href attributes
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href:  # Skip empty hrefs
                    links.append(href)
            
            return links
        except Exception as e:
            logger.error(f"Failed to extract links from HTML: {e}")
            return []
    
    def extract_title(self, html_content: str) -> str:
        """
        Extract page title from HTML content
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            Page title or empty string if not found
        """
        try:
            soup = BeautifulSoup(html_content, self._parser)
            title_tag = soup.find('title')
            return title_tag.get_text().strip() if title_tag else ""
        except Exception as e:
            logger.warning(f"Failed to extract title: {e}")
            return ""
    
    def extract_meta_description(self, html_content: str) -> str:
        """
        Extract meta description from HTML content
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            Meta description or empty string if not found
        """
        try:
            soup = BeautifulSoup(html_content, self._parser)
            meta_tag = soup.find('meta', attrs={'name': 'description'})
            return meta_tag.get('content', '').strip() if meta_tag else ""
        except Exception as e:
            logger.warning(f"Failed to extract meta description: {e}")
            return ""
    
    def is_html_content(self, content: str) -> bool:
        """
        Check if content appears to be HTML
        
        Args:
            content: Content to check
            
        Returns:
            True if content appears to be HTML, False otherwise
        """
        try:
            # Simple check for HTML tags
            return '<html' in content.lower() or '<!doctype' in content.lower()
        except Exception:
            return False
