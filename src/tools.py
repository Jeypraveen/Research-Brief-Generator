import asyncio
import aiohttp
import requests
from typing import List, Dict, Any, Optional
import json
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
from .config import config
from .schemas import SearchResult

class WebSearchTool:
    """Tool for performing web searches using multiple search engines."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """
        Perform web search for the given query.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        # For this implementation, we'll use a simple search simulation
        # In a real implementation, you would integrate with APIs like:
        # - Google Custom Search API
        # - Bing Search API  
        # - DuckDuckGo API
        # - Tavily Search API (recommended for agents)
        
        try:
            return self._simulate_search(query, num_results)
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def _simulate_search(self, query: str, num_results: int) -> List[SearchResult]:
        """
        Simulate search results for demonstration purposes.
        Replace this with real search API integration.
        """
        # Create realistic-looking search results
        simulated_results = [
            {
                "title": f"Research on {query} - Academic Article",
                "url": f"https://academic.example.com/research-{query.replace(' ', '-')}",
                "content": f"Comprehensive research on {query} showing key insights and methodologies. This academic paper presents detailed analysis of {query} with evidence-based conclusions.",
                "source_type": "academic"
            },
            {
                "title": f"{query} - Latest News and Updates",
                "url": f"https://news.example.com/{query.replace(' ', '-')}-updates",
                "content": f"Recent developments in {query} including latest trends, expert opinions, and market analysis. Breaking news about {query}.",
                "source_type": "news"
            },
            {
                "title": f"Complete Guide to {query}",
                "url": f"https://guide.example.com/complete-guide-{query.replace(' ', '-')}",
                "content": f"Comprehensive guide covering all aspects of {query}. Step-by-step analysis and practical applications of {query}.",
                "source_type": "guide"
            },
            {
                "title": f"{query} - Expert Analysis and Insights",
                "url": f"https://expert.example.com/{query.replace(' ', '-')}-analysis",
                "content": f"Expert analysis of {query} with professional insights and recommendations. Industry perspectives on {query}.",
                "source_type": "analysis"
            },
            {
                "title": f"Case Studies on {query}",
                "url": f"https://casestudy.example.com/{query.replace(' ', '-')}-cases",
                "content": f"Real-world case studies demonstrating applications of {query}. Practical examples and lessons learned from {query} implementations.",
                "source_type": "case_study"
            }
        ]
        
        results = []
        for i, result in enumerate(simulated_results[:num_results]):
            # Add some variation to relevance scores
            relevance_score = max(0.6, 1.0 - (i * 0.1))
            
            search_result = SearchResult(
                title=result["title"],
                url=result["url"],
                content=result["content"],
                relevance_score=relevance_score,
                source_type=result["source_type"]
            )
            results.append(search_result)
        
        return results

class ContentFetcher:
    """Tool for fetching and parsing web content."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_content(self, url: str) -> Dict[str, Any]:
        """
        Fetch and parse content from a URL.
        
        Args:
            url: URL to fetch content from
            
        Returns:
            Dictionary containing parsed content
        """
        try:
            response = self.session.get(url, timeout=config.SEARCH_TIMEOUT)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract main content
            content = self._extract_main_content(soup)
            
            # Extract metadata
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            
            return {
                "url": url,
                "title": title,
                "content": content,
                "description": description,
                "word_count": len(content.split()),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "url": url,
                "title": "",
                "content": "",
                "description": "",
                "word_count": 0,
                "status": "error",
                "error": str(e)
            }
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main text content from HTML."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit content length to avoid token limits
        max_length = 2000  # Adjust based on your needs
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description from meta tags."""
        description_tag = soup.find('meta', attrs={'name': 'description'})
        if description_tag:
            return description_tag.get('content', '').strip()
        
        # Try og:description
        og_description_tag = soup.find('meta', attrs={'property': 'og:description'})
        if og_description_tag:
            return og_description_tag.get('content', '').strip()
        
        return ""

class BriefHistoryManager:
    """Tool for managing brief history for context in follow-up queries."""
    
    def __init__(self, history_file: str = None):
        self.history_file = history_file or config.BRIEF_HISTORY_FILE
        self._ensure_history_file()
    
    def _ensure_history_file(self):
        """Ensure history file exists."""
        try:
            with open(self.history_file, 'r') as f:
                pass
        except FileNotFoundError:
            with open(self.history_file, 'w') as f:
                json.dump({}, f)
    
    def save_brief(self, user_id: str, brief: Dict[str, Any]):
        """Save a brief to history."""
        try:
            # Load existing history
            with open(self.history_file, 'r') as f:
                history = json.load(f)
            
            # Initialize user history if not exists
            if user_id not in history:
                history[user_id] = []
            
            # Add timestamp
            brief_with_timestamp = brief.copy()
            brief_with_timestamp['timestamp'] = time.time()
            
            # Add to history
            history[user_id].append(brief_with_timestamp)
            
            # Keep only last 10 briefs per user
            history[user_id] = history[user_id][-10:]
            
            # Save back to file
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Error saving brief history: {e}")
    
    def get_user_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get brief history for a user."""
        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
            
            return history.get(user_id, [])
            
        except Exception as e:
            print(f"Error loading brief history: {e}")
            return []
    
    def get_relevant_context(self, user_id: str, current_topic: str) -> Dict[str, Any]:
        """Get relevant context from previous briefs."""
        history = self.get_user_history(user_id)
        
        if not history:
            return {
                "previous_topics": [],
                "common_themes": [],
                "relevant_context": "",
                "should_reference_previous": False
            }
        
        # Extract topics
        previous_topics = [brief.get("topic", "") for brief in history]
        
        # Find common themes (simplified)
        all_content = " ".join([
            brief.get("executive_summary", "") + " " + 
            " ".join(brief.get("key_findings", []))
            for brief in history
        ])
        
        # Extract common themes (simplified keyword extraction)
        common_themes = self._extract_common_themes(all_content, current_topic)
        
        # Generate relevant context
        relevant_context = self._generate_relevant_context(history, current_topic)
        
        return {
            "previous_topics": previous_topics,
            "common_themes": common_themes,
            "relevant_context": relevant_context,
            "should_reference_previous": len(common_themes) > 0
        }
    
    def _extract_common_themes(self, content: str, current_topic: str) -> List[str]:
        """Extract common themes from content."""
        # Simplified theme extraction
        words = re.findall(r'\\b\\w+\\b', content.lower())
        topic_words = set(current_topic.lower().split())
        
        # Find frequently occurring words that might relate to current topic
        word_freq = {}
        for word in words:
            if len(word) > 4 and word not in ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'man', 'put', 'say', 'she', 'too', 'use']:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top themes
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        themes = [word for word, freq in sorted_words[:5] if freq > 1]
        
        return themes
    
    def _generate_relevant_context(self, history: List[Dict[str, Any]], current_topic: str) -> str:
        """Generate relevant context summary."""
        if not history:
            return ""
        
        recent_brief = history[-1]
        context_parts = []
        
        if recent_brief.get("topic"):
            context_parts.append(f"Previous research topic: {recent_brief['topic']}")
        
        if recent_brief.get("key_findings"):
            key_findings = recent_brief["key_findings"][:2]  # First 2 findings
            context_parts.append(f"Previous key findings: {'; '.join(key_findings)}")
        
        return " | ".join(context_parts) if context_parts else ""

# Initialize global tool instances
web_search_tool = WebSearchTool()
content_fetcher = ContentFetcher()
brief_history_manager = BriefHistoryManager()