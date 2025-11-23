from typing import Dict, List, Optional
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@tool(
    name="parse_trade_log_with_llm",
    description="Parse natural language trade log into structured trade data using IBM watsonx LLM. Handles complex broker notes, client calls, and emergency trade logs.",
    permission=ToolPermission.ADMIN
)
def parse_trade_log_with_llm(trade_log: str) -> str:
    try:
        from watsonx_llm import WatsonxLLM
        from langchain_core.messages import SystemMessage, HumanMessage
        import json
        from datetime import datetime
        
        llm = WatsonxLLM()
        
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Parse this trade log:\n\n{trade_log}")
        ]
        
        response = llm.invoke(messages)
        response_text = response.content.strip()
        
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end <= json_start:
            return "❌ Could not parse trade log. No valid JSON found in LLM response."
        
        parsed_data = json.loads(response_text[json_start:json_end])
        trades = parsed_data.get('trades', [])
        
        if not trades:
            return "❌ No trades found in the log."
        
        for trade in trades:
            if not trade.get('ticket_id'):
                trade['ticket_id'] = f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            trade['timestamp'] = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        
        return json.dumps({"success": True, "trades": trades}, indent=2)
    
    except Exception as e:
        return f"❌ Error parsing trade log: {str(e)}"


@tool(
    name="save_trade_to_csv",
    description="Save parsed trade data to trade blotter CSV file. Use after parsing trade logs to persist trades to database.",
    permission=ToolPermission.ADMIN
)
def save_trade_to_csv(
    ticket_id: str,
    client_name: str,
    account_number: str,
    side: str,
    ticker: str,
    quantity: int,
    order_type: str = "Market",
    price: float = 0.0,
    solicited: bool = True,
    notes: str = "",
    follow_up_date: str = "",
    email: str = "",
    stage: str = "Pending",
    meeting_needed: bool = False
) -> str:
    try:
        import csv
        from datetime import datetime
        
        csv_path = Path(__file__).parent.parent.parent / "data" / "trade_blotter.csv"
        
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Ticket ID', 'Client', 'Account', 'Side', 'Ticker', 'Qty',
                'Type', 'Price', 'Solicited', 'Timestamp', 'Notes',
                'Follow-up', 'Email', 'Stage', 'Meeting'
            ])
            
            if csv_path.stat().st_size == 0:
                writer.writeheader()
            
            writer.writerow({
                'Ticket ID': ticket_id,
                'Client': client_name,
                'Account': account_number,
                'Side': side,
                'Ticker': ticker.upper(),
                'Qty': quantity,
                'Type': order_type,
                'Price': price,
                'Solicited': 'Yes' if solicited else 'No',
                'Timestamp': datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                'Notes': notes,
                'Follow-up': follow_up_date,
                'Email': email,
                'Stage': stage,
                'Meeting': 'Yes' if meeting_needed else 'No'
            })
        
        
        if meeting_needed:
            result += "\n⚠️  Meeting Required"
        
        return result
    
    except Exception as e:
        return f"❌ Error saving trade to CSV: {str(e)}"


@tool(
    name="parse_and_save_trade_log",
    description="End-to-end trade log processing: parse natural language log with LLM and save to CSV in one operation. Most efficient tool for trade logging.",
    permission=ToolPermission.ADMIN
)
def parse_and_save_trade_log(trade_log: str) -> str:
    try:
        import json
        from datetime import datetime
        
        parse_result = parse_trade_log_with_llm(trade_log)
        
        if parse_result.startswith("❌"):
            return parse_result
        
        parsed_data = json.loads(parse_result)
        
        if not parsed_data.get('success'):
            return "❌ Failed to parse trade log"
        
        trades = parsed_data.get('trades', [])
        
        if not trades:
            return "❌ No trades found in log"
        
        results = []
        for trade in trades:
            save_result = save_trade_to_csv(
                ticket_id=trade.get('ticket_id', f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                client_name=trade.get('client_name', ''),
                account_number=trade.get('account_number', ''),
                side=trade.get('side', ''),
                ticker=trade.get('ticker', ''),
                quantity=trade.get('quantity', 0),
                order_type=trade.get('order_type', 'Market'),
                price=trade.get('price', 0.0),
                solicited=trade.get('solicited', True),
                notes=trade.get('notes', ''),
                follow_up_date=trade.get('follow_up_date', ''),
                email=trade.get('email', ''),
                stage=trade.get('stage', 'Pending'),
                meeting_needed=trade.get('meeting_needed', False)
            )
            results.append(save_result)
        
        summary = f"✅ Successfully processed {len(trades)} trade(s)\n\n"
        summary += "\n\n".join(results)
        
        return summary
    
    except Exception as e:
        return f"❌ Error in trade log processing: {str(e)}"


@tool(
    name="get_trade_by_ticket_id",
    description="Retrieve trade details by ticket ID from trade blotter. Use for trade lookups, confirmations, or status checks.",
    permission=ToolPermission.READ_ONLY
)
def get_trade_by_ticket_id(ticket_id: str) -> str:
    try:
        import pandas as pd
        
        csv_path = Path(__file__).parent.parent.parent / "data" / "trade_blotter.csv"
        
        if not csv_path.exists():
            return f"❌ Trade blotter CSV not found"
        
        df = pd.read_csv(csv_path)
        
        matches = df[df['Ticket ID'].astype(str).str.upper() == ticket_id.upper()]
        
        if matches.empty:
            return f"❌ No trade found with ticket ID '{ticket_id}'"
        
        trade = matches.iloc[0]
        
        
        return result
    
    except Exception as e:
        return f"❌ Error retrieving trade: {str(e)}"
