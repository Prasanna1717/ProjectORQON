from typing import Optional, Dict, List
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@tool(
    name="search_compliance_knowledge_base",
    description="Search compliance knowledge base for regulations, rules, and policies using Astra DB hybrid search. Use for compliance questions, rule lookups, or policy clarifications.",
    permission=ToolPermission.READ_ONLY
)
def search_compliance_knowledge_base(query: str, max_results: int = 5) -> str:
    try:
        from tools.astra_db_tools import query_astra_db, get_astra_store
        
        astra_store = get_astra_store()
        
        if astra_store:
            result = query_astra_db(query, collection_name="compliance", max_results=max_results)
            
            if result.startswith("✅"):
                return result
            else:
                return _search_legacy_knowledge_base(query, max_results)
        else:
            return _search_legacy_knowledge_base(query, max_results)
    
    except Exception as e:
        return f"❌ Error searching knowledge base: {str(e)}"


def _search_legacy_knowledge_base(query: str, max_results: int = 5) -> str:
    Get client risk profile and investment history.
    
    Args:
        client_name: Client's full name or partial name (e.g., "Sheila Carter")
    
    Returns:
        Client risk profile with trade history, compliance status, risk score
    
    Example:
        get_client_risk_profile("Sheila Carter")
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 Name: {profile.get('name', 'N/A')}
📧 Email: {profile.get('email', 'N/A')}
🔢 Account: {profile.get('account', 'N/A')}

⚠️  RISK ASSESSMENT:
• Risk Score: {profile.get('risk_score', 0)}/100
• Risk Tolerance: {profile.get('risk_tolerance', 'N/A')}
• Total Trades: {profile.get('total_trades', 0)}

📊 TRADE HISTORY:
    Search trade history for specific client.
    
    Args:
        client_name: Client's full name or partial name
        max_results: Maximum number of trades to return (default: 10)
    
    Returns:
        Client's trade history or error message
    
    Example:
        search_trade_history_by_client("Sheila Carter", max_results=5)
    try:
        import pandas as pd
        
        csv_path = Path(__file__).parent.parent.parent / "data" / "trade_blotter.csv"
        
        if not csv_path.exists():
            return f"❌ Trade blotter CSV not found"
        
        df = pd.read_csv(csv_path)
        
        name_lower = client_name.lower()
        matches = df[df['Client_Name'].astype(str).str.lower().str.contains(name_lower, na=False)]
        
        if matches.empty:
            return f"❌ No trades found for client '{client_name}'"
        
        matches = matches.head(max_results)
        
        result = f"✅ Found {len(matches)} trade(s) for {client_name}\n\n"
        result += matches.to_string(index=False)
        
        return result
    
    except Exception as e:
        return f"❌ Error in CSV fallback search: {str(e)}"


@tool(
    name="search_trade_history_by_ticker",
    description="Search all historical trades for a specific stock ticker using Astra DB. Use for stock-specific trade analysis or position tracking.",
    permission=ToolPermission.READ_ONLY
)
def search_trade_history_by_ticker(ticker: str, max_results: int = 10) -> str:
    try:
        from tools.astra_db_tools import query_astra_db, get_astra_store
        
        astra_store = get_astra_store()
        
        if not astra_store:
            return _search_csv_by_ticker(ticker, max_results)
        
        query = f"All trades for ticker {ticker}"
        result = query_astra_db(query, collection_name="trades", max_results=max_results)
        
        return result
    
    except Exception as e:
        return f"❌ Error searching ticker history: {str(e)}"


def _search_csv_by_ticker(ticker: str, max_results: int = 10) -> str:
    Build Astra DB knowledge graph from CSV.
    
    Returns:
        Success message with indexing statistics
    
    Example:
        index_client_knowledge_graph()
    Search across all Astra DB collections.
    
    Args:
        query: Search query
        max_results: Results per collection (default: 5)
    
    Returns:
        Combined results from trades, emails, and compliance collections
    
    Example:
        hybrid_search_across_all_collections("Sheila Carter TSLA trades and emails")
    Check trade for compliance violations.
    
    Args:
        trade_description: Description of the trade (e.g., "Client wants to sell 500 TSLA unsolicited")
        client_risk_tolerance: Client's risk tolerance level (Low/Moderate/High)
    
    Returns:
        Compliance assessment with potential violations flagged
    
    Example:
        check_compliance_violation(
            "Client demanded to sell entire TSLA position immediately",
            client_risk_tolerance="Conservative"
        )
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Trade Description:
{trade_description}

{f'⚠️  Client Risk Tolerance: {client_risk_tolerance}' if client_risk_tolerance else ''}

📋 RELEVANT RULES:
{result}
