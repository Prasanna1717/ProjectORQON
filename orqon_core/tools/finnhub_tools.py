import os
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta

FINNHUB_API_KEY = "d4h0cd1r01qgvvc5ft20d4h0cd1r01qgvvc5ft2g"
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


class FinnhubTools:
        Get real-time quote for a symbol
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL', 'TSLA')
        
        Returns:
            Dict with current price, change, percent change, etc.
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


def get_stock_price(symbol: str) -> str:
Stock: {data['symbol']}
Current Price: ${data['current_price']:.2f}
Change: ${data['change']:.2f} ({data['percent_change']:.2f}%)
Day High: ${data['high']:.2f}
Day Low: ${data['low']:.2f}
Open: ${data['open']:.2f}
Previous Close: ${data['previous_close']:.2f}
Last Updated: {data['timestamp']}
    tools = FinnhubTools()
    data = tools.get_company_profile(symbol)
    
    if "error" in data:
        return f"Error fetching company info for {symbol}: {data['error']}"
    


def search_stocks(query: str) -> str: