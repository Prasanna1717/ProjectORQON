import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import io
    import base64
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

DATA_DIR = Path(__file__).parent.parent / "data"
EXCEL_FILE = DATA_DIR / "trade_blotter.xlsx"
CSV_FILE = DATA_DIR / "trade_blotter.csv"


class TradeDataManager:
        Save a trade to Excel and CSV
        
        Args:
            trade_data: Dictionary with trade information
        
        Returns:
            Success message with ticket ID
        if self.excel_file.exists():
            return pd.read_excel(self.excel_file)
        return pd.DataFrame()
    
    def get_trade_summary(self) -> Dict:
        Generate trade analytics chart
        
        Args:
            chart_type: Type of chart ('buy_sell', 'solicited', 'top_tickers', 'all')
        
        Returns:
            Base64 encoded PNG image
SUMMARY STATISTICS

Total Trades: {summary['total_trades']}
Buy Orders: {summary['buy_orders']}
Sell Orders: {summary['sell_orders']}
Solicited: {summary['solicited']}
Unsolicited: {summary['unsolicited']}

Most Traded: {summary['most_traded']}
        df = self.get_all_trades()
        
        if df.empty:
            return "<p>No trades found</p>"
        
        recent_df = df.tail(limit)
        
        html = recent_df.to_html(
            index=False,
            classes='trade-table',
            border=0,
            justify='center'
        )
        
        return html
    
    def search_trades(self, query: str) -> pd.DataFrame:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"TKT-{timestamp}"


def save_trade_to_excel(trade_data: Dict) -> str:
    manager = TradeDataManager()
    summary = manager.get_trade_summary()
    
    if "message" in summary:
        return summary["message"]
    


def generate_trade_chart(chart_type: str = "all") -> str:
    manager = TradeDataManager()
    return manager.get_trades_table_html(limit)


def search_trade_records(query: str) -> str: