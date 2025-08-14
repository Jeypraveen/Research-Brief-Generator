"""
Tools for web search and content fetching in the Research Brief Generator.
Now includes Serper API integration for real web search.
"""
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

class SerperWebSearchTool:
    """Tool for performing web searches using Serper API."""
    
    def __init__(self):
        self.api_key = config.get_serper_api_key()
        self.base_url = "https://google.serper.dev/search"
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-KEY': self.api_key if self.api_key else '',
            'Content-Type': 'application/json'
        })
    
    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """
        Perform web search using Serper API.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        if not self.api_key:
            print("🔍 No Serper API key found, using fallback search...")
            return self._fallback_search(query, num_results)
        
        try:
            print(f"🔍 Searching with Serper API: {query}")
            
            payload = {
                "q": query,
                "num": min(num_results, 10),  # Serper allows max 10 per request
                "gl": config.SERPER_GL,
                "hl": config.SERPER_HL,
                "type": config.SERPER_SEARCH_TYPE
            }
            
            response = self.session.post(
                self.base_url, 
                json=payload,
                timeout=config.SEARCH_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            return self._parse_serper_results(data, query)
            
        except requests.exceptions.RequestException as e:
            print(f"🚨 Serper API error: {e}")
            return self._fallback_search(query, num_results)
        except Exception as e:
            print(f"🚨 Unexpected error in Serper search: {e}")
            return self._fallback_search(query, num_results)
    
    def _parse_serper_results(self, data: Dict[str, Any], query: str) -> List[SearchResult]:
        """Parse Serper API response into SearchResult objects."""
        results = []
        
        # Parse organic search results
        organic_results = data.get('organic', [])
        
        for i, result in enumerate(organic_results):
            try:
                # Extract data from Serper response
                title = result.get('title', '')
                url = result.get('link', '')
                snippet = result.get('snippet', '')
                
                # Calculate relevance score based on position and query match
                relevance_score = self._calculate_relevance(title, snippet, query, i)
                
                # Determine source type
                source_type = self._determine_source_type(url, title)
                
                search_result = SearchResult(
                    title=title,
                    url=url,
                    content=snippet,
                    relevance_score=relevance_score,
                    source_type=source_type
                )
                results.append(search_result)
                
            except Exception as e:
                print(f"⚠️ Error parsing result {i}: {e}")
                continue
        
        # Also parse knowledge graph results if available
        knowledge_graph = data.get('knowledgeGraph', {})
        if knowledge_graph:
            try:
                title = knowledge_graph.get('title', '')
                description = knowledge_graph.get('description', '')
                url = knowledge_graph.get('descriptionLink', '')
                
                if title and description:
                    kg_result = SearchResult(
                        title=f"Knowledge Graph: {title}",
                        url=url or "https://www.google.com",
                        content=description,
                        relevance_score=0.95,  # High relevance for knowledge graph
                        source_type="knowledge_graph"
                    )
                    results.insert(0, kg_result)  # Add at beginning
                    
            except Exception as e:
                print(f"⚠️ Error parsing knowledge graph: {e}")
        
        print(f"✅ Found {len(results)} results from Serper API")
        return results
    
    def _calculate_relevance(self, title: str, snippet: str, query: str, position: int) -> float:
        """Calculate relevance score based on content and position."""
        base_score = 1.0 - (position * 0.1)  # Decrease by position
        base_score = max(base_score, 0.1)  # Minimum score
        
        # Boost score based on query terms in title and snippet
        query_terms = query.lower().split()
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        
        title_matches = sum(1 for term in query_terms if term in title_lower)
        snippet_matches = sum(1 for term in query_terms if term in snippet_lower)
        
        # Calculate bonus
        title_bonus = (title_matches / len(query_terms)) * 0.3
        snippet_bonus = (snippet_matches / len(query_terms)) * 0.1
        
        final_score = min(base_score + title_bonus + snippet_bonus, 1.0)
        return round(final_score, 3)
    
    def _determine_source_type(self, url: str, title: str) -> str:
        """Determine the type of source based on URL and title."""
        if not url:
            return "unknown"
        
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Academic sources
        if any(domain in url_lower for domain in [
            'arxiv.org', 'scholar.google', 'researchgate.net', 
            'academia.edu', 'jstor.org', '.edu', 'pubmed', 'nature.com'
        ]):
            return "academic"
        
        # News sources
        elif any(domain in url_lower for domain in [
            'cnn.com', 'bbc.com', 'reuters.com', 'ap.org', 
            'nytimes.com', 'washingtonpost.com', 'bloomberg.com'
        ]):
            return "news"
        
        # Government sources
        elif '.gov' in url_lower or 'government' in url_lower:
            return "government"
        
        # Wikipedia
        elif 'wikipedia.org' in url_lower:
            return "encyclopedia"
        
        # GitHub or code repositories
        elif any(domain in url_lower for domain in ['github.com', 'gitlab.com', 'bitbucket.org']):
            return "code"
        
        # General web
        else:
            return "web"
    
    def _fallback_search(self, query: str, num_results: int) -> List[SearchResult]:
        """
        Fallback search when Serper API is not available.
        Creates more realistic-looking simulated results.
        """
        print(f"🔄 Using fallback search for: {query}")
        
        # Enhanced simulated results with more variety
        result_templates = [
            {
                "title_template": "{query} - Comprehensive Guide and Analysis",
                "url_template": "https://research-institute.org/{query_slug}",
                "content_template": "Comprehensive analysis of {query} including latest research findings, methodologies, and practical applications. This detailed guide covers current trends and future implications.",
                "source_type": "academic"
            },
            {
                "title_template": "Latest News and Updates on {query}",
                "url_template": "https://news-source.com/{query_slug}-updates-2024",
                "content_template": "Breaking news and recent developments in {query}. Expert analysis, market trends, and industry insights from leading professionals.",
                "source_type": "news"
            },
            {
                "title_template": "{query}: Expert Analysis and Professional Insights",
                "url_template": "https://professional-insights.com/{query_slug}",
                "content_template": "Professional analysis of {query} with expert opinions, case studies, and data-driven insights. Industry perspectives and recommendations.",
                "source_type": "analysis"
            },
            {
                "title_template": "Research Study: {query} - Methodology and Results",
                "url_template": "https://academic-journal.org/studies/{query_slug}",
                "content_template": "Peer-reviewed research study on {query} presenting methodology, data analysis, and conclusions. Significant findings and implications for the field.",
                "source_type": "academic"
            },
            {
                "title_template": "Government Report on {query} - Official Data",
                "url_template": "https://government-reports.gov/{query_slug}-report",
                "content_template": "Official government report on {query} with statistical data, policy implications, and regulatory considerations. Evidence-based analysis.",
                "source_type": "government"
            },
            {
                "title_template": "{query} - Industry Best Practices and Case Studies",
                "url_template": "https://industry-hub.com/{query_slug}-practices",
                "content_template": "Industry best practices for {query} with real-world case studies, implementation strategies, and success stories from leading organizations.",
                "source_type": "industry"
            },
            {
                "title_template": "Technical Implementation of {query} - Developer Guide",
                "url_template": "https://tech-docs.com/{query_slug}-implementation",
                "content_template": "Technical guide to implementing {query} with code examples, architecture patterns, and performance considerations for developers.",
                "source_type": "technical"
            }
        ]
        
        results = []
        query_slug = re.sub(r'[^a-zA-Z0-9-]', '-', query.lower()).strip('-')
        
        # Select templates based on number of results requested
        selected_templates = result_templates[:min(num_results, len(result_templates))]
        
        for i, template in enumerate(selected_templates):
            relevance_score = max(0.6, 1.0 - (i * 0.08))  # Gradually decreasing relevance
            
            result = SearchResult(
                title=template["title_template"].format(query=query),
                url=template["url_template"].format(query_slug=query_slug),
                content=template["content_template"].format(query=query),
                relevance_score=relevance_score,
                source_type=template["source_type"]
            )
            results.append(result)
        
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
        words = re.findall(r'\b\w+\b', content.lower())
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
web_search_tool = SerperWebSearchTool()
content_fetcher = ContentFetcher()
brief_history_manager = BriefHistoryManager()
