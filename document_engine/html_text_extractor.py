"""
HTML Text Extractor

This module provides functionality to extract text from HTML files,
cleaning and formatting the content for further processing.
"""

import os
import logging
from typing import Optional
from pathlib import Path
from urllib.parse import urlparse

# HTML processing
from bs4 import BeautifulSoup
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HTMLTextExtractor:
    """
    A class to extract text from HTML files and web pages.
    """
    
    def __init__(self):
        """Initialize the HTML text extractor."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_text_from_html_file(self, html_path: str) -> str:
        """
        Extract text from a local HTML file.
        
        Args:
            html_path: Path to the HTML file
            
        Returns:
            Extracted text as a string
            
        Raises:
            FileNotFoundError: If the HTML file doesn't exist
            Exception: If there's an error processing the HTML
        """
        if not os.path.exists(html_path):
            raise FileNotFoundError(f"HTML file not found: {html_path}")
        
        logger.info(f"Processing HTML file: {html_path}")
        
        try:
            with open(html_path, 'r', encoding='utf-8', errors='ignore') as file:
                html_content = file.read()
            
            return self._extract_text_from_html_content(html_content, html_path)
            
        except Exception as e:
            logger.error(f"Error processing HTML file {html_path}: {e}")
            raise
    
    def extract_text_from_url(self, url: str) -> str:
        """
        Extract text from a web URL.
        
        Args:
            url: URL to extract text from
            
        Returns:
            Extracted text as a string
            
        Raises:
            Exception: If there's an error fetching or processing the URL
        """
        logger.info(f"Processing URL: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            html_content = response.text
            return self._extract_text_from_html_content(html_content, url)
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            raise
    
    def _extract_text_from_html_content(self, html_content: str, source: str) -> str:
        """
        Extract text from HTML content.
        
        Args:
            html_content: Raw HTML content
            source: Source identifier (file path or URL)
            
        Returns:
            Extracted text as a string
        """
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract text from main content areas
            main_content = []
            
            # Try to find main content areas first
            main_selectors = [
                'main', 'article', '.content', '#content', 
                '.main-content', '#main-content', '.post-content',
                '.entry-content', '.page-content'
            ]
            
            main_element = None
            for selector in main_selectors:
                main_element = soup.select_one(selector)
                if main_element:
                    break
            
            if main_element:
                main_content.append(main_element.get_text(separator=' ', strip=True))
            else:
                # Fallback to body if no main content found
                body = soup.find('body')
                if body:
                    main_content.append(body.get_text(separator=' ', strip=True))
                else:
                    # Last resort: get all text
                    main_content.append(soup.get_text(separator=' ', strip=True))
            
            # Join and clean the text
            text = ' '.join(main_content)
            
            # Clean up the text
            text = self._clean_text(text)
            
            logger.info(f"Successfully extracted {len(text)} characters from {source}")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from HTML content: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and format extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        import re
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def get_document_metadata(self, source: str) -> dict:
        """
        Extract metadata from HTML source.
        
        Args:
            source: File path or URL
            
        Returns:
            Dictionary with metadata
        """
        metadata = {
            'source': source,
            'source_type': 'file' if os.path.exists(source) else 'url',
            'filename': os.path.basename(source) if os.path.exists(source) else None
        }
        
        if not os.path.exists(source):  # It's a URL
            try:
                parsed_url = urlparse(source)
                metadata['domain'] = parsed_url.netloc
                metadata['path'] = parsed_url.path
            except:
                pass
        
        return metadata


def extract_html_text(html_path: str) -> str:
    """
    Convenience function to extract text from an HTML file.
    
    Args:
        html_path: Path to the HTML file
        
    Returns:
        Extracted text as a string
    """
    extractor = HTMLTextExtractor()
    return extractor.extract_text_from_html_file(html_path)


# Example usage
if __name__ == "__main__":
    # Example usage
    html_file = "/path/to/your/document.html"
    
    # Extract text from HTML file
    # text = extract_html_text(html_file)
    # print(text)
    pass
