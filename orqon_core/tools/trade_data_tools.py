"""
Trade Data Management Tools
Excel and CSV export with visualization capabilities
"""
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Optional: matplotlib for visualization
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import io
    import base64
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data"
EXCEL_FILE = DATA_DIR / "trade_blotter.xlsx"
CSV_FILE = DATA_DIR / "trade_blotter.csv"


class TradeDataManager:
    """Manage trade data in Excel and CSV formats"""
    
    def __init__(self):
        self.excel_file = EXCEL_FILE
        self.csv_file = CSV_FILE
        DATA_DIR.mkdir(exist_ok=True)
    
    def save_trade(self, trade_data: Dict) -> str:
        """
        Save a trade to Excel and CSV
        
        Args:
            trade_data: Dictionary with trade information
        
        Returns:
            Success message with ticket ID
        """
        try:
            # Create DataFrame for new trade
            new_trade = pd.DataFrame([{
                'Ticket_ID': trade_data.get('ticket_id', self._generate_ticket_id()),
                'Timestamp': datetime.now().isoformat(),
                'Client_Name': trade_data.get('client_name', ''),
                'Account_Number': trade_data.get('account_number', ''),
                'Ticker': trade_data.get('ticker', '').upper(),
                'Side': trade_data.get('side', 'Buy'),
                'Quantity': trade_data.get('quantity', 0),
                'Order_Type': trade_data.get('order_type', 'Market'),
                'Price': trade_data.get('price', 0.0),
                'Solicited': trade_data.get('solicited', False),
                'Notes': trade_data.get('notes', ''),
                'Email': trade_data.get('email', ''),
                'Stage': trade_data.get('stage', 'Pending'),
                'Follow_Up_Date': trade_data.get('follow_up_date', ''),
                'Meeting_Needed': trade_data.get('meeting_needed', False)
            }])
            
            # Load existing data or create new
            if self.excel_file.exists():
                existing_df = pd.read_excel(self.excel_file)
                df = pd.concat([existing_df, new_trade], ignore_index=True)
            else:
                df = new_trade
            
            # Save to Excel
            df.to_excel(self.excel_file, index=False)
            
            # Save to CSV
            df.to_csv(self.csv_file, index=False)
            
            return f"Trade saved successfully. Ticket ID: {new_trade['Ticket_ID'].iloc[0]}"
        
        except Exception as e:
            return f"Error saving trade: {str(e)}"
    
    def get_all_trades(self) -> pd.DataFrame:
        """Load all trades from Excel"""
        if self.excel_file.exists():
            return pd.read_excel(self.excel_file)
        return pd.DataFrame()
    
    def get_trade_summary(self) -> Dict:
        """Get summary statistics of trades"""
        df = self.get_all_trades()
        
        if df.empty:
            return {"message": "No trades found"}
        
        # Handle both column naming conventions
        qty_col = 'Qty' if 'Qty' in df.columns else 'Quantity'
        client_col = 'Client' if 'Client' in df.columns else 'Client_Name'
        
        # Convert Solicited column to boolean if it's string
        if 'Solicited' in df.columns and df['Solicited'].dtype == object:
            df['Solicited_Bool'] = df['Solicited'].str.lower() == 'solicited'
        else:
            df['Solicited_Bool'] = df['Solicited'] == True
        
        return {
            "total_trades": len(df),
            "buy_orders": len(df[df['Side'] == 'Buy']),
            "sell_orders": len(df[df['Side'] == 'Sell']),
            "solicited": int(df['Solicited_Bool'].sum()),
            "unsolicited": int((~df['Solicited_Bool']).sum()),
            "total_volume": int(df[qty_col].sum()),
            "unique_tickers": df['Ticker'].nunique(),
            "unique_clients": df[client_col].nunique(),
            "most_traded": df['Ticker'].value_counts().index[0] if len(df) > 0 else "N/A"
        }
    
    def generate_trade_chart(self, chart_type: str = "buy_sell") -> str:
        """
        Generate trade analytics chart
        
        Args:
            chart_type: Type of chart ('buy_sell', 'solicited', 'top_tickers', 'all')
        
        Returns:
            Base64 encoded PNG image
        """
        df = self.get_all_trades()
        
        if df.empty:
            return "No data available for chart generation"
        
        try:
            if chart_type == "all":
                fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
                fig.suptitle('Trade Analytics Dashboard', fontsize=16, fontweight='bold')
            else:
                fig, ax1 = plt.subplots(figsize=(10, 6))
            
            # Buy vs Sell Distribution
            if chart_type in ["buy_sell", "all"]:
                ax = ax1 if chart_type == "all" else ax1
                buy_sell_counts = df['Side'].value_counts()
                colors = ['#4ade80', '#f87171']  # Green for Buy, Red for Sell
                wedges, texts, autotexts = ax.pie(
                    buy_sell_counts.values,
                    labels=buy_sell_counts.index,
                    autopct='%1.1f%%',
                    colors=colors,
                    startangle=90
                )
                ax.set_title('Buy vs Sell Distribution', fontweight='bold')
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
            
            # Solicited vs Unsolicited
            if chart_type in ["solicited", "all"]:
                ax = ax2 if chart_type == "all" else ax1
                solicited_counts = df['Solicited'].value_counts()
                labels = ['Solicited' if x else 'Unsolicited' for x in solicited_counts.index]
                colors = ['#3b82f6', '#f59e0b']  # Blue, Orange
                ax.bar(labels, solicited_counts.values, color=colors, edgecolor='black')
                ax.set_title('Solicited vs Unsolicited', fontweight='bold')
                ax.set_ylabel('Count')
                ax.grid(axis='y', alpha=0.3)
            
            # Top 10 Tickers
            if chart_type in ["top_tickers", "all"]:
                ax = ax3 if chart_type == "all" else ax1
                top_tickers = df['Ticker'].value_counts().head(10)
                ax.barh(top_tickers.index, top_tickers.values, color='#a855f7', edgecolor='black')
                ax.set_title('Top 10 Tickers', fontweight='bold')
                ax.set_xlabel('Trade Count')
                ax.grid(axis='x', alpha=0.3)
            
            # Summary Statistics
            if chart_type == "all":
                ax4.axis('off')
                summary = self.get_trade_summary()
                summary_text = f"""
SUMMARY STATISTICS

Total Trades: {summary['total_trades']}
Buy Orders: {summary['buy_orders']}
Sell Orders: {summary['sell_orders']}
Solicited: {summary['solicited']}
Unsolicited: {summary['unsolicited']}

Most Traded: {summary['most_traded']}
                """.strip()
                ax4.text(0.1, 0.5, summary_text, fontsize=12, verticalalignment='center',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
        
        except Exception as e:
            return f"Error generating chart: {str(e)}"
    
    def get_trades_table_html(self, limit: int = 10) -> str:
        """Get HTML table of recent trades"""
        df = self.get_all_trades()
        
        if df.empty:
            return "<p>No trades found</p>"
        
        # Get last N trades
        recent_df = df.tail(limit)
        
        # Convert to HTML with styling
        html = recent_df.to_html(
            index=False,
            classes='trade-table',
            border=0,
            justify='center'
        )
        
        return html
    
    def search_trades(self, query: str) -> pd.DataFrame:
        """Search trades by client name, ticker, or notes"""
        df = self.get_all_trades()
        
        if df.empty:
            return df
        
        query_lower = query.lower()
        mask = (
            df['Client_Name'].str.lower().str.contains(query_lower, na=False) |
            df['Ticker'].str.lower().str.contains(query_lower, na=False) |
            df['Notes'].str.lower().str.contains(query_lower, na=False)
        )
        
        return df[mask]
    
    def _generate_ticket_id(self) -> str:
        """Generate unique ticket ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"TKT-{timestamp}"


# Tool functions for agent
def save_trade_to_excel(trade_data: Dict) -> str:
    """Save trade data to Excel and CSV"""
    manager = TradeDataManager()
    return manager.save_trade(trade_data)


def get_trade_summary() -> str:
    """Get summary of all trades"""
    manager = TradeDataManager()
    summary = manager.get_trade_summary()
    
    if "message" in summary:
        return summary["message"]
    
    return f"""
Trade Summary:
- Total Trades: {summary['total_trades']}
- Buy Orders: {summary['buy_orders']}
- Sell Orders: {summary['sell_orders']}
- Solicited: {summary['solicited']}
- Unsolicited: {summary['unsolicited']}
- Total Volume: {summary['total_volume']:,} shares
- Unique Tickers: {summary['unique_tickers']}
- Unique Clients: {summary['unique_clients']}
- Most Traded: {summary['most_traded']}
"""


def generate_trade_chart(chart_type: str = "all") -> str:
    """Generate trade analytics chart (returns base64 image)"""
    manager = TradeDataManager()
    return manager.generate_trade_chart(chart_type)


def show_recent_trades(limit: int = 10) -> str:
    """Show recent trades in table format"""
    manager = TradeDataManager()
    return manager.get_trades_table_html(limit)


def search_trade_records(query: str) -> str:
    """Search for trades by client, ticker, or notes"""
    manager = TradeDataManager()
    results = manager.search_trades(query)
    
    if results.empty:
        return f"No trades found matching '{query}'"
    
    return f"Found {len(results)} trades:\n\n{results.to_string(index=False)}"
