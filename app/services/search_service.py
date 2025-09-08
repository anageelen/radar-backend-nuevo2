import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from ..database import Result

class SearchService:
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx = os.getenv("GOOGLE_CX")
        self.bing_api_key = os.getenv("BING_API_KEY")
        self.newsapi_key = os.getenv("NEWSAPI_KEY")
        
    async def search_all_sources(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search across all configured sources"""
        
        tasks = []
        
        if self.google_api_key and self.google_cx:
            tasks.append(self.search_google(query, filters))
            
        if self.bing_api_key:
            tasks.append(self.search_bing(query, filters))
            
        if self.newsapi_key:
            tasks.append(self.search_newsapi(query, filters))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        combined_results = []
        seen_urls = set()
        
        for result_set in results:
            if isinstance(result_set, list):
                for result in result_set:
                    if result.get("url") not in seen_urls:
                        seen_urls.add(result.get("url"))
                        combined_results.append(result)
        
        return combined_results
    
    async def search_google(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search using Google Custom Search API"""
        
        if not self.google_api_key or not self.google_cx:
            return []
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.google_api_key,
            "cx": self.google_cx,
            "q": query,
            "num": 10
        }
        
        if filters:
            if filters.get("country"):
                params["cr"] = f"country{filters['country']}"
            if filters.get("language"):
                params["lr"] = f"lang_{filters['language'][:2].lower()}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_google_results(data)
        except Exception as e:
            print(f"Google search error: {e}")
        
        return []
    
    async def search_bing(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search using Bing Search API"""
        
        if not self.bing_api_key:
            return []
        
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": self.bing_api_key}
        params = {
            "q": query,
            "count": 10,
            "responseFilter": "Webpages"
        }
        
        if filters:
            if filters.get("country"):
                params["cc"] = filters["country"]
            if filters.get("language"):
                params["setLang"] = filters["language"][:2].lower()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_bing_results(data)
        except Exception as e:
            print(f"Bing search error: {e}")
        
        return []
    
    async def search_newsapi(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search using NewsAPI"""
        
        if not self.newsapi_key:
            return []
        
        url = "https://newsapi.org/v2/everything"
        params = {
            "apiKey": self.newsapi_key,
            "q": query,
            "pageSize": 10,
            "sortBy": "relevancy"
        }
        
        if filters:
            if filters.get("language"):
                params["language"] = filters["language"][:2].lower()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_newsapi_results(data)
        except Exception as e:
            print(f"NewsAPI search error: {e}")
        
        return []
    
    def _parse_google_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Google Custom Search results"""
        results = []
        
        for item in data.get("items", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": "Google",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "category": "Web",
                "status": "Activo",
                "country": "Unknown",
                "language": "Unknown",
                "score": 85
            })
        
        return results
    
    def _parse_bing_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Bing Search results"""
        results = []
        
        for item in data.get("webPages", {}).get("value", []):
            results.append({
                "title": item.get("name", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
                "source": "Bing",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "category": "Web",
                "status": "Activo",
                "country": "Unknown",
                "language": "Unknown",
                "score": 80
            })
        
        return results
    
    def _parse_newsapi_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse NewsAPI results"""
        results = []
        
        for article in data.get("articles", []):
            results.append({
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "snippet": article.get("description", ""),
                "source": article.get("source", {}).get("name", "NewsAPI"),
                "date": article.get("publishedAt", "")[:10] if article.get("publishedAt") else datetime.now().strftime("%Y-%m-%d"),
                "category": "News",
                "status": "Activo",
                "country": "Unknown",
                "language": "Unknown",
                "score": 90
            })
        
        return results
