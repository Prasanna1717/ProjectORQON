from typing import Optional
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@tool(
    name="get_stock_price_quote",
    description="Get real-time stock price quote including current price, high, low, volume, and change. Use for market data inquiries and price checks.",
    permission=ToolPermission.READ_ONLY
)
def get_stock_price_quote(ticker: str) -> str:
    try:
        import yfinance as yf
        
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        
        if not info:
            return f"❌ Could not fetch data for ticker '{ticker}'"
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        prev_close = info.get('previousClose', 0)
        day_high = info.get('dayHigh') or info.get('regularMarketDayHigh', 0)
        day_low = info.get('dayLow') or info.get('regularMarketDayLow', 0)
        volume = info.get('volume') or info.get('regularMarketVolume', 0)
        
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close > 0 else 0
        
        change_emoji = "🟢" if change >= 0 else "🔴"
        change_sign = "+" if change >= 0 else ""
        
        
        return result
    
    except ImportError:
        return "❌ yfinance library not installed. Run: pip install yfinance"
    except Exception as e:
        return f"❌ Error fetching stock price: {str(e)}"


@tool(
    name="get_company_information",
    description="Get detailed company information including name, sector, industry, market cap, description, and key metrics. Use for company research and due diligence.",
    permission=ToolPermission.READ_ONLY
)
def get_company_information(ticker: str) -> str:
    try:
        import yfinance as yf
        
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        
        if not info:
            return f"❌ Could not fetch company info for '{ticker}'"
        
        company_name = info.get('longName', ticker.upper())
        sector = info.get('sector', 'N/A')
        industry = info.get('industry', 'N/A')
        market_cap = info.get('marketCap', 0)
        description = info.get('longBusinessSummary', 'No description available')
        employees = info.get('fullTimeEmployees', 0)
        country = info.get('country', 'N/A')
        website = info.get('website', 'N/A')
        
        if market_cap >= 1e12:
            market_cap_str = f"${market_cap/1e12:.2f}T"
        elif market_cap >= 1e9:
            market_cap_str = f"${market_cap/1e9:.2f}B"
        elif market_cap >= 1e6:
            market_cap_str = f"${market_cap/1e6:.2f}M"
        else:
            market_cap_str = f"${market_cap:,.0f}"
        
        
        return result
    
    except ImportError:
        return "❌ yfinance library not installed. Run: pip install yfinance"
    except Exception as e:
        return f"❌ Error fetching company info: {str(e)}"


@tool(
    name="compare_multiple_stocks",
    description="Compare multiple stock tickers side-by-side with prices, changes, and market caps. Use for portfolio analysis or investment comparisons.",
    permission=ToolPermission.READ_ONLY
)
def compare_multiple_stocks(tickers: str) -> str:
    try:
        import yfinance as yf
        
        ticker_list = [t.strip().upper() for t in tickers.split(',')]
        
        if len(ticker_list) < 2:
            return "❌ Please provide at least 2 tickers separated by commas"
        
        result = f"✅ STOCK COMPARISON\n{'━' * 60}\n\n"
        
        for ticker in ticker_list:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                prev_close = info.get('previousClose', 0)
                market_cap = info.get('marketCap', 0)
                
                change = current_price - prev_close
                change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                
                if market_cap >= 1e12:
                    mcap_str = f"{market_cap/1e12:.2f}T"
                elif market_cap >= 1e9:
                    mcap_str = f"{market_cap/1e9:.2f}B"
                else:
                    mcap_str = "N/A"
                
                change_emoji = "🟢" if change >= 0 else "🔴"
                change_sign = "+" if change >= 0 else ""
                
            except Exception as e:
                result += f"{ticker}: ❌ Error - {str(e)}\n\n"
        
        result += "━" * 60
        
        return result
    
    except ImportError:
        return "❌ yfinance library not installed"
    except Exception as e:
        return f"❌ Error comparing stocks: {str(e)}"


@tool(
    name="get_stock_historical_performance",
    description="Get historical stock performance over specified period (1d, 5d, 1mo, 3mo, 6mo, 1y, 5y). Use for trend analysis and performance tracking.",
    permission=ToolPermission.READ_ONLY
)
def get_stock_historical_performance(ticker: str, period: str = "1mo") -> str:
    try:
        import yfinance as yf
        
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period=period)
        
        if hist.empty:
            return f"❌ No historical data found for '{ticker}'"
        
        start_price = hist['Close'].iloc[0]
        end_price = hist['Close'].iloc[-1]
        high = hist['High'].max()
        low = hist['Low'].min()
        avg_volume = hist['Volume'].mean()
        
        total_return = ((end_price - start_price) / start_price) * 100
        
        
        return result
    
    except ImportError:
        return "❌ yfinance library not installed"
    except Exception as e:
        return f"❌ Error fetching historical data: {str(e)}"


@tool(
    name="search_stock_ticker_by_company_name",
    description="Search for stock ticker symbol by company name. Use when user provides company name instead of ticker.",
    permission=ToolPermission.READ_ONLY
)
def search_stock_ticker_by_company_name(company_name: str) -> str:
    common_tickers = {
        'tesla': 'TSLA',
        'apple': 'AAPL',
        'microsoft': 'MSFT',
        'google': 'GOOGL',
        'alphabet': 'GOOGL',
        'amazon': 'AMZN',
        'meta': 'META',
        'facebook': 'META',
        'netflix': 'NFLX',
        'nvidia': 'NVDA',
        'amd': 'AMD',
        'intel': 'INTC',
        'rivian': 'RIVN',
        'lucid': 'LCID',
        'ford': 'F',
        'gm': 'GM',
        'general motors': 'GM',
        'toyota': 'TM',
        'walmart': 'WMT',
        'target': 'TGT',
        'costco': 'COST',
        'visa': 'V',
        'mastercard': 'MA',
        'paypal': 'PYPL',
        'disney': 'DIS',
        'coca cola': 'KO',
        'pepsi': 'PEP',
        'boeing': 'BA',
        'nike': 'NKE',
        'starbucks': 'SBUX'
    }
    
    name_lower = company_name.lower().strip()
    
    if name_lower in common_tickers:
        ticker = common_tickers[name_lower]
        return f"✅ {company_name} → {ticker}"
    else:
        return f"❌ Ticker not found for '{company_name}'. Please try the exact ticker symbol instead."
