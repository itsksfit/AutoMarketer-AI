import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging
import re

logger = logging.getLogger("automarketer")

def extract_domain(url: str) -> str:
    """Extracts a user-friendly domain name from a URL to use as a fallback title."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        # Capitalize and strip TLD for a nice fallback name
        name = domain.split('.')[0]
        return name.capitalize() if name else "Target Website"
    except Exception:
        return "Target Website"

def scrape_website(url: str) -> dict:
    """
    Scrapes a website URL, extracts the page title and clean text body.
    Includes robust fallbacks for network issues or blocked requests.
    
    Returns:
        dict: {
            "title": str,
            "content": str,
            "success": bool,
            "error_message": Optional[str]
        }
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }
    
    fallback_title = extract_domain(url)
    
    try:
        logger.info(f"Attempting to scrape URL: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check if HTTP request was successful
        response.raise_for_status()
        
        # Parse content
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Get page title
        title_tag = soup.find("title")
        page_title = title_tag.get_text().strip() if title_tag else ""
        if not page_title:
            # Fallback to h1 or domain
            h1_tag = soup.find("h1")
            page_title = h1_tag.get_text().strip() if h1_tag else fallback_title
            
        # Clean the HTML tree - remove interactive/structural elements that don't add semantic value
        for element in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe", "svg"]):
            element.decompose()
            
        # Get text and clean it
        text = soup.get_text(separator="\n")
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = "\n".join(chunk for chunk in chunks if chunk)
        
        # Limit extracted content to prevent Gemini token bloat while keeping all key information
        max_length = 6000
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length] + "\n... [Truncated]"
            
        if not clean_text.strip():
            raise ValueError("No readable text content found on the page.")
            
        logger.info(f"Successfully scraped website. Title: '{page_title}'")
        return {
            "title": page_title,
            "content": clean_text,
            "success": True,
            "error_message": None
        }
        
    except requests.exceptions.Timeout as e:
        logger.warning(f"Scraping timeout for {url}: {str(e)}")
        return {
            "title": fallback_title,
            "content": f"A website representing {fallback_title}. Scraping timed out, but campaign generation can proceed using website name metadata.",
            "success": False,
            "error_message": "Request timed out."
        }
    except Exception as e:
        logger.warning(f"Scraping failed for {url}: {str(e)}")
        return {
            "title": fallback_title,
            "content": f"A website representing {fallback_title}. Scraping encountered an error ({str(type(e).__name__)}), but campaign generation can proceed using website metadata.",
            "success": False,
            "error_message": str(e)
        }
