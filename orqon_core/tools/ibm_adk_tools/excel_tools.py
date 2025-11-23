from typing import Optional, Dict, List
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@tool(
    name="read_trade_blotter_csv",
    description="Read and filter data from trade blotter CSV file. Use to find client information, trades, account numbers, or any data from the trade records.",
    permission=ToolPermission.READ_ONLY
)
def read_trade_blotter_csv(filter_column: Optional[str] = None, filter_value: Optional[str] = None) -> str:
    try:
        import pandas as pd
        
        csv_path = Path(__file__).parent.parent.parent / "data" / "trade_blotter.csv"
        
        if not csv_path.exists():
            return f"❌ Trade blotter CSV not found at {csv_path}"
        
        df = pd.read_csv(csv_path)
        
        if filter_column and filter_value:
            if filter_column not in df.columns:
                return f"❌ Column '{filter_column}' not found. Available columns: {', '.join(df.columns)}"
            
            mask = df[filter_column].astype(str).str.lower().str.contains(filter_value.lower(), na=False)
            df = df[mask]
            
            if df.empty:
                return f"❌ No records found matching {filter_column}='{filter_value}'"
        
        if df.empty:
            return "❌ No records found in trade blotter"
        
        result = f"✅ Found {len(df)} record(s)\n\n"
        result += df.to_string(index=False)
        
        return result
    
    except Exception as e:
        return f"❌ Error reading trade blotter: {str(e)}"


@tool(
    name="get_client_profile",
    description="Get complete client profile including email, account number, recent trades, and meeting info. Use when you need full client details for communication or analysis.",
    permission=ToolPermission.READ_ONLY
)
def get_client_profile(client_name: str) -> str:
    try:
        import pandas as pd
        
        csv_path = Path(__file__).parent.parent.parent / "data" / "trade_blotter.csv"
        
        if not csv_path.exists():
            return f"❌ Trade blotter CSV not found"
        
        df = pd.read_csv(csv_path)
        
        name_lower = client_name.lower()
        matches = df[df['Client_Name'].astype(str).str.lower().str.contains(name_lower, na=False)]
        
        if matches.empty:
            return f"❌ No client found matching '{client_name}'"
        
        client = matches.iloc[0]
        
        
        for idx, trade in matches.iterrows():
            profile += f"\n• {trade.get('Ticker', 'N/A')} - {trade.get('Side', 'N/A')} {trade.get('Qty', 'N/A')} shares"
            if pd.notna(trade.get('Follow_up_Date')):
                profile += f"\n  📅 Follow-up: {trade['Follow_up_Date']}"
            if pd.notna(trade.get('Meeting_Needed')):
                profile += f"\n  🤝 Meeting: {trade['Meeting_Needed']}"
        
        profile += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        return profile
    
    except Exception as e:
        return f"❌ Error retrieving client profile: {str(e)}"


@tool(
    name="extract_field_from_trade_blotter",
    description="Extract a specific field value for a client (e.g., email, account number, ticker, quantity). Use when you need one specific piece of information.",
    permission=ToolPermission.READ_ONLY
)
def extract_field_from_trade_blotter(client_name: str, field_name: str) -> str:
    try:
        import pandas as pd
        
        csv_path = Path(__file__).parent.parent.parent / "data" / "trade_blotter.csv"
        
        if not csv_path.exists():
            return f"❌ Trade blotter CSV not found"
        
        df = pd.read_csv(csv_path)
        
        name_lower = client_name.lower()
        matches = df[df['Client_Name'].astype(str).str.lower().str.contains(name_lower, na=False)]
        
        if matches.empty:
            return f"❌ No client found matching '{client_name}'"
        
        if field_name not in df.columns:
            return f"❌ Field '{field_name}' not found. Available fields: {', '.join(df.columns)}"
        
        value = matches.iloc[0][field_name]
        
        if pd.isna(value):
            return f"❌ {field_name} is not available for {matches.iloc[0]['Client_Name']}"
        
        return f"✅ {field_name}: {value}"
    
    except Exception as e:
        return f"❌ Error extracting field: {str(e)}"


@tool(
    name="open_csv_file",
    description="Open trade blotter CSV file in system default application. Use when client requests to view or open the spreadsheet.",
    permission=ToolPermission.ADMIN
)
def open_csv_file() -> str:
    try:
        import subprocess
        import platform
        
        csv_path = Path(__file__).parent.parent.parent / "data" / "trade_blotter.csv"
        
        if not csv_path.exists():
            return f"❌ CSV file not found at {csv_path}"
        
        if platform.system() == "Windows":
            subprocess.Popen(["start", "", str(csv_path)], shell=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", str(csv_path)])
        else:
            subprocess.Popen(["xdg-open", str(csv_path)])
        
        return f"✅ Opened CSV file: {csv_path.name}\n\nThe trade blotter is now displayed in your default application."
    
    except Exception as e:
        return f"❌ Error opening CSV file: {str(e)}"


@tool(
    name="open_excel_file",
    description="Open trade blotter Excel file in system default application (Excel, Numbers, etc.). Use when client requests to view the spreadsheet.",
    permission=ToolPermission.ADMIN
)
def open_excel_file() -> str:
    try:
        import subprocess
        import platform
        
        excel_path = Path(__file__).parent.parent.parent / "data" / "trade_blotter.xlsx"
        
        if not excel_path.exists():
            return f"❌ Excel file not found at {excel_path}"
        
        if platform.system() == "Windows":
            subprocess.Popen(["start", "", str(excel_path)], shell=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", str(excel_path)])
        else:
            subprocess.Popen(["xdg-open", str(excel_path)])
        
        return f"✅ Opened Excel file: {excel_path.name}\n\nThe trade blotter is now displayed in your default application."
    
    except Exception as e:
        return f"❌ Error opening Excel file: {str(e)}"


@tool(
    name="search_trades_by_ticker",
    description="Search all trades for a specific stock ticker symbol. Use to analyze trading patterns or find all transactions for a particular stock.",
    permission=ToolPermission.READ_ONLY
)
def search_trades_by_ticker(ticker: str) -> str:
    try:
        import pandas as pd
        
        csv_path = Path(__file__).parent.parent.parent / "data" / "trade_blotter.csv"
        
        if not csv_path.exists():
            return f"❌ Trade blotter CSV not found"
        
        df = pd.read_csv(csv_path)
        
        matches = df[df['Ticker'].astype(str).str.upper() == ticker.upper()]
        
        if matches.empty:
            return f"❌ No trades found for ticker '{ticker}'"
        
        result = f"✅ Found {len(matches)} trade(s) for {ticker.upper()}\n\n"
        result += matches.to_string(index=False)
        
        return result
    
    except Exception as e:
        return f"❌ Error searching trades: {str(e)}"


@tool(
    name="get_trade_statistics",
    description="Get summary statistics from trade blotter (total trades, buy/sell ratio, top clients, etc.). Use for portfolio analysis or reporting.",
    permission=ToolPermission.READ_ONLY
)
def get_trade_statistics() -> str:
    try:
        import pandas as pd
        
        csv_path = Path(__file__).parent.parent.parent / "data" / "trade_blotter.csv"
        
        if not csv_path.exists():
            return f"❌ Trade blotter CSV not found"
        
        df = pd.read_csv(csv_path)
        
        if df.empty:
            return "❌ No trades found in blotter"
        
        total_trades = len(df)
        buy_count = len(df[df['Side'].str.upper() == 'BUY'])
        sell_count = len(df[df['Side'].str.upper() == 'SELL'])
        
        top_clients = df['Client_Name'].value_counts().head(5)
        
        top_tickers = df['Ticker'].value_counts().head(5)
        
        for client, count in top_clients.items():
            stats += f"• {client}: {count} trade(s)\n"
        
        stats += f"\n📈 TOP TICKERS:\n"
        for ticker, count in top_tickers.items():
            stats += f"• {ticker}: {count} trade(s)\n"
        
        stats += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        return stats
    
    except Exception as e:
        return f"❌ Error calculating statistics: {str(e)}"
