"""
Finnhub API Tools for Agentic AI
Real-time stock market data integration
"""
import os
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta

FINNHUB_API_KEY = "d4h0cd1r01qgvvc5ft20d4h0cd1r01qgvvc5ft2g"
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


class FinnhubTools:
    """Finnhub API integration for market data"""
    
    def __init__(self, api_key: str = FINNHUB_API_KEY):
        self.api_key = api_key
        self.base_url = FINNHUB_BASE_URL
    
    def get_quote(self, symbol: str) -> Dict:
        """
        Get real-time quote for a symbol
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL', 'TSLA')
        
        Returns:
            Dict with current price, change, percent change, etc.
        """
        try:
            response = requests.get(
                f"{self.base_url}/quote",
                params={"symbol": symbol.upper(), "token": self.api_key},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "symbol": symbol.upper(),
                "current_price": data.get("c", 0),
                "change": data.get("d", 0),
                "percent_change": data.get("dp", 0),
                "high": data.get("h", 0),
                "low": data.get("l", 0),
                "open": data.get("o", 0),
                "previous_close": data.get("pc", 0),
                "timestamp": datetime.fromtimestamp(data.get("t", 0)).isoformat()
            }
        except Exception as e:
            return {"error": str(e), "symbol": symbol}
    
    def get_company_profile(self, symbol: str) -> Dict:
        """Get company profile information"""
        try:
            response = requests.get(
                f"{self.base_url}/stock/profile2",
                params={"symbol": symbol.upper(), "token": self.api_key},
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "symbol": symbol}
    
    def get_market_news(self, category: str = "general", limit: int = 10) -> List[Dict]:
        """Get market news"""
        try:
            response = requests.get(
                f"{self.base_url}/news",
                params={"category": category, "token": self.api_key},
                timeout=5
            )
            response.raise_for_status()
            news = response.json()
            return news[:limit]
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_company_news(self, symbol: str, days: int = 7) -> List[Dict]:
        """Get company-specific news"""
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            response = requests.get(
                f"{self.base_url}/company-news",
                params={
                    "symbol": symbol.upper(),
                    "from": from_date.strftime("%Y-%m-%d"),
                    "to": to_date.strftime("%Y-%m-%d"),
                    "token": self.api_key
                },
                timeout=5
            )
            response.raise_for_status()
            return response.json()[:10]
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_multiple_quotes(self, symbols: List[str]) -> List[Dict]:
        """Get quotes for multiple symbols"""
        return [self.get_quote(symbol) for symbol in symbols]
    
    def search_symbol(self, query: str) -> List[Dict]:
        """Search for stock symbols"""
        try:
            response = requests.get(
                f"{self.base_url}/search",
                params={"q": query, "token": self.api_key},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            return data.get("result", [])[:10]
        except Exception as e:
            return [{"error": str(e)}]


# Tool functions for LangChain integration
def get_stock_price(symbol: str) -> str:
    """Get current stock price and info"""
    tools = FinnhubTools()
    data = tools.get_quote(symbol)
    
    if "error" in data:
        return f"Error fetching data for {symbol}: {data['error']}"
    
    return f"""
Stock: {data['symbol']}
Current Price: ${data['current_price']:.2f}
Change: ${data['change']:.2f} ({data['percent_change']:.2f}%)
Day High: ${data['high']:.2f}
Day Low: ${data['low']:.2f}
Open: ${data['open']:.2f}
Previous Close: ${data['previous_close']:.2f}
Last Updated: {data['timestamp']}
"""


def get_company_info(symbol: str) -> str:
    """Get company profile information"""
    tools = FinnhubTools()
    data = tools.get_company_profile(symbol)
    
    if "error" in data:
        return f"Error fetching company info for {symbol}: {data['error']}"
    
    return f"""
Company: {data.get('name', 'N/A')}
Ticker: {data.get('ticker', symbol)}
Industry: {data.get('finnhubIndustry', 'N/A')}
Market Cap: ${data.get('marketCapitalization', 0):,.0f}M
Exchange: {data.get('exchange', 'N/A')}
Country: {data.get('country', 'N/A')}
Website: {data.get('weburl', 'N/A')}
"""


def search_stocks(query: str) -> str:
    """Search for stock symbols by company name"""
    tools = FinnhubTools()
    results = tools.search_symbol(query)
    
    if not results or (len(results) == 1 and "error" in results[0]):
        return f"No results found for '{query}'"
    
    output = f"Search results for '{query}':\n\n"
    for result in results[:5]:
        output += f"- {result.get('description', 'N/A')} ({result.get('symbol', 'N/A')})\n"
        output += f"  Type: {result.get('type', 'N/A')}\n\n"
    
    return output
