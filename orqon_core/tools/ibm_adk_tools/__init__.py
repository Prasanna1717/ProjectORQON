
from .gmail_tools import (
    send_email_to_client,
    send_email_with_trade_blotter,
    create_calendar_reminder,
    schedule_google_meet,
    get_client_email_address
)

from .excel_tools import (
    read_trade_blotter_csv,
    get_client_profile,
    extract_field_from_trade_blotter,
    open_csv_file,
    open_excel_file,
    search_trades_by_ticker,
    get_trade_statistics
)

from .trade_tools import (
    parse_trade_log_with_llm,
    save_trade_to_csv,
    parse_and_save_trade_log,
    get_trade_by_ticket_id
)

from .compliance_tools import (
    search_compliance_knowledge_base,
    get_client_risk_profile,
    search_trade_history_by_client,
    search_trade_history_by_ticker,
    index_client_knowledge_graph,
    hybrid_search_across_all_collections,
    check_compliance_violation
)

from .finance_tools import (
    get_stock_price_quote,
    get_company_information,
    compare_multiple_stocks,
    get_stock_historical_performance,
    search_stock_ticker_by_company_name
)

__all__ = [
    "send_email_to_client",
    "send_email_with_trade_blotter",
    "create_calendar_reminder",
    "schedule_google_meet",
    "get_client_email_address",
    
    "read_trade_blotter_csv",
    "get_client_profile",
    "extract_field_from_trade_blotter",
    "open_csv_file",
    "open_excel_file",
    "search_trades_by_ticker",
    "get_trade_statistics",
    
    "parse_trade_log_with_llm",
    "save_trade_to_csv",
    "parse_and_save_trade_log",
    "get_trade_by_ticket_id",
    
    "search_compliance_knowledge_base",
    "get_client_risk_profile",
    "search_trade_history_by_client",
    "search_trade_history_by_ticker",
    "index_client_knowledge_graph",
    "hybrid_search_across_all_collections",
    "check_compliance_violation",
    
    "get_stock_price_quote",
    "get_company_information",
    "compare_multiple_stocks",
    "get_stock_historical_performance",
    "search_stock_ticker_by_company_name"
]

GMAIL_TOOLS = [
    "send_email_to_client",
    "send_email_with_trade_blotter",
    "create_calendar_reminder",
    "schedule_google_meet",
    "get_client_email_address"
]

EXCEL_TOOLS = [
    "read_trade_blotter_csv",
    "get_client_profile",
    "extract_field_from_trade_blotter",
    "open_csv_file",
    "open_excel_file",
    "search_trades_by_ticker",
    "get_trade_statistics"
]

TRADE_TOOLS = [
    "parse_trade_log_with_llm",
    "save_trade_to_csv",
    "parse_and_save_trade_log",
    "get_trade_by_ticket_id"
]

COMPLIANCE_TOOLS = [
    "search_compliance_knowledge_base",
    "get_client_risk_profile",
    "search_trade_history_by_client",
    "search_trade_history_by_ticker",
    "index_client_knowledge_graph",
    "hybrid_search_across_all_collections",
    "check_compliance_violation"
]

FINANCE_TOOLS = [
    "get_stock_price_quote",
    "get_company_information",
    "compare_multiple_stocks",
    "get_stock_historical_performance",
    "search_stock_ticker_by_company_name"
]
