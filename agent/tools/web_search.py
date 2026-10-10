import json
import urllib.parse
import requests
from typing import Optional
from .base import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    """Web Search Tool using DuckDuckGo Instant Answer / HTML Search API with safe fallbacks."""

    name = "web_search"
    description = "Searches the web for current information, documentation, news, or general facts."
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query string."
            }
        },
        "required": ["query"]
    }

    def run(self, query: str = "", **kwargs) -> ToolResult:
        if not query or not query.strip():
            return ToolResult(success=False, output="", error="Search query cannot be empty.")
        
        query = query.strip()
        
        # 1. Try DuckDuckGo Instant Answer API
        try:
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(url, headers=headers, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                results = []
                
                if data.get("Abstract"):
                    results.append(f"**Abstract**: {data.get('Abstract')}")
                    if data.get("AbstractURL"):
                        results.append(f"**URL**: {data.get('AbstractURL')}")
                
                related_topics = data.get("RelatedTopics", [])
                for topic in related_topics[:4]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        results.append(f"- {topic.get('Text')}")
                
                if results:
                    return ToolResult(
                        success=True,
                        output=f"Search Results for '{query}':\n" + "\n".join(results)
                    )
        except Exception:
            pass

        # 2. Try DuckDuckGo Lite HTML Search scrape
        try:
            lite_url = "https://lite.duckduckgo.com/lite/"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.post(lite_url, data={"q": query}, headers=headers, timeout=5)
            
            if resp.status_code == 200 and "result-snippet" in resp.text:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                snippets = []
                for tr in soup.find_all("td", class_="result-snippet")[:5]:
                    text = tr.get_text(strip=True)
                    if text:
                        snippets.append(f"- {text}")
                
                if snippets:
                    return ToolResult(
                        success=True,
                        output=f"Web Search Results for '{query}':\n" + "\n".join(snippets)
                    )
        except Exception:
            pass

        # 3. Graceful fallback if external web is unreachable
        return ToolResult(
            success=True,
            output=f"Web Search Query: '{query}'\n"
                   f"Note: Live network search is currently operating in offline/local fallback mode.\n"
                   f"The agent can continue processing using Python interpreter or internal knowledge."
        )
