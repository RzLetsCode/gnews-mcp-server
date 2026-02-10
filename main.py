#!/usr/bin/env python3
"""
GNews MCP Server
A Model Context Protocol (MCP) server that provides access to the GNews API.
"""

import os
import json
import requests
from typing import Any, Optional

# Initialize MCP server
class GNewsMCPServer:
    def __init__(self):
        self.api_key = os.getenv('GNEWS_API_KEY')
        if not self.api_key:
            raise ValueError('GNEWS_API_KEY environment variable is required')
        self.base_url = 'https://gnewsapi.net/api/search'
        
    def search_news(self, q: str, lang: Optional[str] = 'en', 
                   country: Optional[str] = None, max_articles: int = 10) -> dict:
        """
        Search for news articles using keywords.
        
        Args:
            q: Search query string
            lang: Language code (e.g., 'en', 'es')
            country: Country code (e.g., 'us', 'in')
            max_articles: Number of articles to return (1-100)
            
        Returns:
            Dictionary with search results
        """
        try:
            params = {
                'q': q,
                'lang': lang,
                'max': max_articles,
                'token': self.api_key
            }
            if country:
                params['country'] = country
                
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'success': True,
                'query': q,
                'totalArticles': len(data.get('articles', [])),
                'articles': data.get('articles', []),
                'parameters_used': params
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': q,
                'parameters_used': params
            }
    
    def get_top_headlines(self, category: str = 'general', 
                         lang: Optional[str] = 'en',
                         country: Optional[str] = None,
                         max_articles: int = 10) -> dict:
        """
        Get top headlines by category.
        
        Args:
            category: News category
            lang: Language code
            country: Country code
            max_articles: Number of articles to return
            
        Returns:
            Dictionary with headlines
        """
        q = f'category:{category}' if category != 'general' else ''
        return self.search_news(q, lang, country, max_articles)


def main():
    """Main entry point for the MCP server."""
    try:
        server = GNewsMCPServer()
        print('GNews MCP Server initialized successfully', flush=True)
        
        # Read from stdin and process MCP requests
        while True:
            line = input()
            if line:
                try:
                    request = json.loads(line)
                    # Process MCP request and return response
                    response = process_mcp_request(server, request)
                    print(json.dumps(response), flush=True)
                except json.JSONDecodeError:
                    print(json.dumps({'error': 'Invalid JSON'}), flush=True)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Error: {e}', file=__import__('sys').stderr)


def process_mcp_request(server: GNewsMCPServer, request: dict) -> dict:
    """Process MCP protocol requests."""
    method = request.get('method')
    params = request.get('params', {})
    
    if method == 'search_news':
        return server.search_news(**params)
    elif method == 'get_top_headlines':
        return server.get_top_headlines(**params)
    else:
        return {'error': f'Unknown method: {method}'}


if __name__ == '__main__':
    main()
