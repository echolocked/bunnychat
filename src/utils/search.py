"""
Web search and scraping utilities.
"""

import sys
import subprocess
from typing import List, Dict
import json
import logging
from ..config.settings import search_settings

# Set up logging
logger = logging.getLogger(__name__)

def search_web(query: str) -> List[Dict[str, str]]:
    """Search the web using the search engine tool.
    
    Args:
        query: Search query
        
    Returns:
        List of search results with URL, title, and snippet
    """
    try:
        # Run the search engine tool
        result = subprocess.run(
            ["venv/bin/python3", "tools/search_engine.py", query],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the results
        results = []
        lines = result.stdout.strip().split('\n')
        current_result = {}
        
        for line in lines:
            if line.startswith('URL: '):
                if current_result:
                    results.append(current_result.copy())
                current_result = {'url': line[5:]}
            elif line.startswith('Title: '):
                current_result['title'] = line[7:]
            elif line.startswith('Snippet: '):
                current_result['snippet'] = line[9:]
        
        if current_result:
            results.append(current_result)
            
        return results[:search_settings.max_results]
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Search engine error: {e.stderr}")
        return []

def scrape_urls(urls: List[str]) -> List[Dict[str, str]]:
    """Scrape content from URLs using the web scraper tool.
    
    Args:
        urls: List of URLs to scrape
        
    Returns:
        List of dictionaries containing URL and content
    """
    try:
        # Run the web scraper tool
        cmd = ["venv/bin/python3", "tools/web_scraper.py", f"--max-concurrent={search_settings.max_concurrent}"]
        cmd.extend(urls)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the results
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.error("Failed to parse web scraper output")
            return []
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Web scraper error: {e.stderr}")
        return []

def search_and_scrape(query: str) -> str:
    """Search the web and scrape relevant content.
    
    Args:
        query: Search query
        
    Returns:
        Formatted string with search results and content
    """
    # Search for results
    search_results = search_web(query)
    if not search_results:
        return "No search results found."
    
    # Scrape content from URLs
    urls = [result['url'] for result in search_results]
    scraped_content = scrape_urls(urls)
    
    # Format results
    output = []
    output.append(f"Search results for: {query}\n")
    
    for i, result in enumerate(search_results, 1):
        output.append(f"{i}. {result['title']}")
        output.append(f"   URL: {result['url']}")
        output.append(f"   Summary: {result['snippet']}")
        
        # Add scraped content if available
        matching_content = next((item['content'] for item in scraped_content if item['url'] == result['url']), None)
        if matching_content:
            content_preview = matching_content[:500] + "..." if len(matching_content) > 500 else matching_content
            output.append(f"   Content preview: {content_preview}\n")
        
        output.append("")
    
    return "\n".join(output) 