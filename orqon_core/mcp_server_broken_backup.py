import asyncio
import json
import sys
import re
from typing import Dict, Any, Optional, AsyncGenerator, List, Literal
from dataclasses import dataclass, asdict
from enum import Enum
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("orqon_mcp_server")

try:
    from ibm_watsonx_orchestrate.agent_builder.agents import (
        AssistantAgent,
        AgentKind,
    )
    from ibm_watsonx_orchestrate.agent_builder.agents.types import (
        AssistantAgentConfig,
    )
    HAS_AGENT_BUILDER = True
    logger.info("✓ IBM watsonx Orchestrate agent_builder loaded (v1.15.0)")
except ImportError as e:
    HAS_AGENT_BUILDER = False
    AssistantAgent = None
    AgentKind = None
    AssistantAgentConfig = None
    logger.warning(f"⚠️  IBM agent_builder not available: {e}")
    logger.info("   Install: pip install ibm-watsonx-orchestrate")



class MCPToolSchema(BaseModel):
    content: List[Dict[str, Any]] = Field(..., description="Response content")
    isError: bool = Field(default=False, description="Whether the response is an error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": [
                    {
                        "type": "text",
                        "text": "Email sent successfully"
                    }
                ],
                "isError": False
            }
        }


class MCPListToolsResponse(BaseModel):
    name: str = Field(..., description="Tool name to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class MCPServerInfo(BaseModel):
    tool = MCPToolSchema(
        name=name,
        description=description,
        inputSchema=input_schema
    )
    MCP_TOOL_REGISTRY.append(tool)
    logger.info(f"✓ Registered MCP tool: {name}")



from shared_memory import conversation_memory

def get_client_email_from_csv(client_name: str) -> Optional[str]:
    COORDINATOR = "coordinator"        # Routes to appropriate agent
    GMAIL = "gmail"                   # Email operations
    EXCEL = "excel"                   # CSV/Excel data operations
    FINANCE = "finance"               # Stock prices, trade data
    COMPLIANCE = "compliance"         # RAG knowledge base
    TRADE_PARSER = "trade_parser"     # Parse trade logs and tickets
    CALENDAR = "calendar"             # Google Calendar
    MATH = "math"                     # Calculations
    DATETIME = "datetime"             # Date/time queries


@dataclass
class AgentHandoff:
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.capabilities = []
        self.adk_agent = None
        
        if HAS_AGENT_BUILDER:
            self._init_adk_agent()
    
    def _init_adk_agent(self):
        raise NotImplementedError
    
    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class GmailAgent(BaseAgent):
    
    def __init__(self):
        super().__init__(AgentType.GMAIL)
        self.capabilities = [
            "send_email",
            "draft_email",
            "read_emails",
            "search_emails",
            "create_reminder",
            "schedule_meeting"
        ]
        
        try:
            from tools.google_workspace_tools import GoogleWorkspaceTools
            self.gmail_tools = GoogleWorkspaceTools()
            self.available = True
            print("✓ Gmail Agent initialized with Calendar support")
        except Exception as e:
            print(f"⚠️  Gmail Agent unavailable: {e}")
            self.available = False
    
    async def can_handle(self, query: str, context: Dict[str, Any]) -> bool:
        from watsonx_llm import WatsonxLLM
        from langchain_core.messages import SystemMessage, HumanMessage
        import re
        from datetime import datetime, timedelta
        
        llm = WatsonxLLM()
        
        query_lower = query.lower()
        
        is_cancel = any(keyword in query_lower for keyword in ['cancel', 'delete', 'remove'])
        
        if is_cancel:
            logger.info(f"🗑️ Cancel meeting request detected: {query}")
            
            try:
                cancel_all = any(keyword in query_lower for keyword in ['all', 'everything', 'every'])
                
                if cancel_all:
                    logger.info(f"🗑️ Cancelling ALL upcoming meetings...")
                    result = self.gmail_tools.cancel_all_meetings()
                    
                    if result.get('success'):
                        cancelled_count = result.get('cancelled_count', 0)
                        cancelled_titles = result.get('cancelled_titles', [])
                        
                        if cancelled_count == 0:
                            response_text = "ℹ️ No upcoming meetings found to cancel."
                        else:
                            response_text = f"✅ **Cancelled {cancelled_count} Meeting(s)**\n\n"
                            for i, title in enumerate(cancelled_titles, 1):
                                response_text += f"{i}. {title}\n"
                        
                        logger.info(f"✅ Cancelled {cancelled_count} meetings")
                        return {
                            "success": True,
                            "agent": "gmail",
                            "action": "meetings_cancelled",
                            "response": response_text
                        }
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        logger.error(f"❌ Failed to cancel meetings: {error_msg}")
                        return {
                            "success": False,
                            "agent": "gmail",
                            "error": f"Failed to cancel meetings: {error_msg}"
                        }
                else:
                    return {
                        "success": False,
                        "agent": "gmail",
                        "error": "Please specify 'cancel all meetings' to cancel. Specific meeting cancellation coming soon."
                    }
            
            except Exception as e:
                logger.error(f"❌ Exception cancelling meetings: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "agent": "gmail",
                    "error": f"Error cancelling meetings: {str(e)}"
                }
        
        is_meeting = any(keyword in query_lower for keyword in ['meeting', 'meet with', 'schedule with', 'google meet', 'gmeet']) and not is_cancel
        is_reminder = any(keyword in query_lower for keyword in ['reminder', 'remind me', 'calendar', 'set me a']) and not is_cancel
        
        if is_meeting or is_reminder:
            logger.info(f"📅 Calendar/Reminder request detected: {query}")
            
            reminder_context = ""
            reminder_date = None
            client_info = ""
            
            logger.info(f"📅 Checking shared memory for client data...")
            logger.info(f"📅 Available keys: {list(conversation_memory['shared_context'].keys())}")
            
            client_name_match = re.search(r'(?:with|regarding|for)\s+([a-z]+(?:\s+[a-z]+)?)', query_lower)
            if client_name_match and 'last_client_data' not in conversation_memory['shared_context']:
                potential_client = client_name_match.group(1).title()
                logger.info(f"📅 Query mentions '{potential_client}' but no memory - looking up in CSV...")
                
                import csv
                from pathlib import Path
                csv_path = Path(__file__).parent / "data" / "trade_blotter.csv"
                
                if csv_path.exists():
                    try:
                        with open(csv_path, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                csv_client = row.get('Client', '').lower()
                                if potential_client.lower() in csv_client or csv_client in potential_client.lower():
                                    from shared_memory import save_client_data
                                    client_data = {
                                        'client_name': row.get('Client', potential_client),
                                        'email': row.get('Email', ''),
                                        'account': row.get('Acct#', ''),
                                        'ticker': row.get('Ticker', ''),
                                        'quantity': row.get('Qty', ''),
                                        'follow_up': row.get('FollowUpDate', ''),
                                        'FollowUpDate': row.get('FollowUpDate', ''),
                                        'meeting_needed': row.get('MeetingNeeded', ''),
                                        'stage': row.get('Stage', ''),
                                        'notes': row.get('Notes', '')
                                    }
                                    save_client_data(row.get('Client', potential_client), client_data)
                                    logger.info(f"📅 Auto-loaded {row.get('Client')} from CSV!")
                                    break
                    except Exception as e:
                        logger.warning(f"📅 Failed to auto-lookup client: {e}")
            
            if 'last_client_data' in conversation_memory['shared_context']:
                client_data = conversation_memory['shared_context']['last_client_data']
                client_name = client_data.get('client_name', client_data.get('Client', 'Unknown'))
                follow_up = client_data.get('follow_up', client_data.get('FollowUpDate', ''))
                
                logger.info(f"📅 Found client data for: {client_name}")
                logger.info(f"📅 Follow-up date raw: {follow_up}")
                
                if follow_up and follow_up.strip():
                    try:
                        reminder_date = datetime.strptime(follow_up.split()[0], '%Y-%m-%d')
                        reminder_date = reminder_date.replace(hour=9, minute=0, second=0, microsecond=0)
                        reminder_context = f"Follow up with {client_name}"
                        client_info = f"{client_name}'s follow-up"
                        logger.info(f"📅 ✅ Parsed follow-up date from memory: {reminder_date}")
                    except Exception as e:
                        logger.warning(f"📅 Failed to parse follow-up date '{follow_up}': {e}")
                else:
                    logger.warning(f"📅 Client {client_name} has no follow-up date set")
            else:
                logger.warning(f"📅 No last_client_data in shared memory")
            
            if not reminder_date:
                logger.info(f"📅 No date from memory, parsing query for explicit date...")
                
                if 'tomorrow' in query_lower:
                    reminder_date = datetime.now() + timedelta(days=1)
                    reminder_date = reminder_date.replace(hour=9, minute=0, second=0, microsecond=0)
                    logger.info(f"📅 Found 'tomorrow' → {reminder_date}")
                elif 'next week' in query_lower:
                    reminder_date = datetime.now() + timedelta(days=7)
                    reminder_date = reminder_date.replace(hour=9, minute=0, second=0, microsecond=0)
                    logger.info(f"📅 Found 'next week' → {reminder_date}")
                else:
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', query)
                    if date_match:
                        try:
                            reminder_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                            reminder_date = reminder_date.replace(hour=9, minute=0, second=0, microsecond=0)
                            logger.info(f"📅 Extracted date from query: {reminder_date}")
                        except Exception as e:
                            logger.warning(f"📅 Failed to parse date '{date_match.group(1)}': {e}")
            
            if not reminder_date:
                logger.info(f"📅 No explicit date found, using LLM to extract or default to tomorrow...")
                
                
                try:
                    llm_response = llm.invoke(llm_prompt).strip()
                    logger.info(f"📅 LLM response: {llm_response}")
                    
                    if llm_response == "TOMORROW_MORNING" or "tomorrow" in llm_response.lower():
                        reminder_date = datetime.now() + timedelta(days=1)
                        reminder_date = reminder_date.replace(hour=9, minute=0, second=0, microsecond=0)
                        logger.info(f"📅 LLM suggested tomorrow → {reminder_date}")
                    else:
                        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', llm_response)
                        if date_match:
                            reminder_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                            reminder_date = reminder_date.replace(hour=9, minute=0, second=0, microsecond=0)
                            logger.info(f"📅 LLM extracted date: {reminder_date}")
                except Exception as e:
                    logger.warning(f"📅 LLM extraction failed: {e}, defaulting to tomorrow")
                    reminder_date = datetime.now() + timedelta(days=1)
                    reminder_date = reminder_date.replace(hour=9, minute=0, second=0, microsecond=0)
            
            if reminder_date:
                try:
                    client_email = None
                    client_name_for_title = "Client"
                    
                    if 'last_client_data' in conversation_memory['shared_context']:
                        client_data = conversation_memory['shared_context']['last_client_data']
                        client_email = client_data.get('email')
                        client_name_for_title = client_data.get('client_name', client_data.get('Client', 'Client'))
                    
                    if is_meeting:
                        if not client_email:
                            return {
                                "success": False,
                                "agent": "gmail",
                                "error": f"Cannot schedule meeting - no email found for {client_name_for_title}. Please check the client data."
                            }
                        
                        title = f"Portfolio Review Meeting - {client_name_for_title}"
                        notes = f"Scheduled via Orqon assistant.\nOriginal query: {query}\n\nAgenda: Portfolio review and follow-up discussion"
                        duration_minutes = 60
                        
                        logger.info(f"📅 Creating Google Meet meeting: {title}")
                        logger.info(f"📅 Date: {reminder_date}")
                        logger.info(f"📅 Attendee: {client_email}")
                        
                        result = self.gmail_tools.schedule_meeting(
                            title=title,
                            start_time=reminder_date,
                            duration_minutes=duration_minutes,
                            attendee_emails=[client_email],
                            description=notes
                        )
                        
                        logger.info(f"📅 Meeting result: {json.dumps(result, indent=2)}")
                        
                        if result.get('success'):
                            meet_link = result.get('meet_link', 'N/A')
                            response_text = (
                                f"✅ **Google Meet Meeting Scheduled**\n\n"
                                f"📅 Title: {title}\n"
                                f"👤 Attendee: {client_name_for_title} ({client_email})\n"
                                f"🕐 Date: {reminder_date.strftime('%B %d, %Y at %I:%M %p')}\n"
                                f"⏱️ Duration: {duration_minutes} minutes\n\n"
                                f"🔗 [View in Calendar]({result.get('event_link', 'N/A')})\n"
                                f"📹 [Join Google Meet]({meet_link})"
                            )
                            logger.info(f"✅ Meeting scheduled successfully: {title}")
                            
                            should_send_email = any(phrase in query_lower for phrase in ['mail him', 'mail her', 'email him', 'email her', 'send email', 'notify'])
                            
                            if should_send_email and client_email:
                                logger.info(f"📧 User also requested email notification - sending meeting invite email...")
                                
                                email_subject = f"Meeting Invitation: Portfolio Review - {reminder_date.strftime('%B %d, %Y')}"
                                email_body = f"Dear {client_name_for_title},<br><br>I hope this email finds you well.<br><br>I've scheduled a portfolio review meeting for us to discuss your investment strategy and review your recent transactions.<br><br>📅 <strong>Meeting Details:</strong><br><br>• <strong>Date:</strong> {reminder_date.strftime('%B %d, %Y at %I:%M %p')}<br>• <strong>Duration:</strong> {duration_minutes} minutes<br>• <strong>Topic:</strong> Portfolio Review & Follow-up Discussion<br><br>📹 <strong>Join the meeting:</strong><br><a href=\"{meet_link}\">{meet_link}</a><br><br>📆 <strong>Add to your calendar:</strong><br><a href=\"{result.get('event_link', '')}\">{result.get('event_link', 'Calendar Link')}</a><br><br>Looking forward to our conversation. Please let me know if you need to reschedule.<br><br>Best regards,<br>Prasanna Vijay<br>Financial Advisor<br>The Orqon Team<br><br>📧 Email: prasannathefreelancer@gmail.com<br>📞 Available for consultation"
                                
                                try:
                                    email_result = self.gmail_tools.send_email(
                                        to_email=client_email,
                                        subject=email_subject,
                                        body=email_body
                                    )
                                    
                                    if email_result.get('success'):
                                        logger.info(f"✅ Meeting invite email sent to {client_email}")
                                        response_text += f"\n\n📧 **Meeting invite email sent to {client_name_for_title}**"
                                    else:
                                        logger.error(f"❌ Failed to send meeting invite email: {email_result.get('error')}")
                                        response_text += f"\n\n⚠️ Meeting created but email notification failed"
                                except Exception as e:
                                    logger.error(f"❌ Exception sending meeting email: {e}")
                                    response_text += f"\n\n⚠️ Meeting created but email notification failed"
                            
                            return {
                                "success": True,
                                "agent": "gmail",
                                "action": "meeting_scheduled",
                                "response": response_text
                            }
                    except Exception as e:
                        logger.error(f"❌ Exception creating calendar event: {str(e)}", exc_info=True)
                        return {
                            "success": False,
                            "agent": "gmail",
                            "error": f"Error creating calendar event: {str(e)}"
                        }
                else:
                    logger.warning(f"⚠️ Could not determine reminder date from query: {query}")
                    return {
                        "success": False,
                        "agent": "gmail",
                        "error": "Could not determine reminder date"
                    }

        extracted_email = None
        client_name = None
        
        if 'client_data' in context and context['client_data'].get('email'):
            extracted_email = context['client_data']['email']
            client_name = context['client_data'].get('client_name', context['client_data'].get('Client'))
            context['client_email_from_csv'] = extracted_email
            context['client_name'] = client_name
        
        return await self._send_email_logic(query, context)

    async def _send_email_logic(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        from watsonx_llm import WatsonxLLM
        from langchain_core.messages import SystemMessage, HumanMessage
        import json

        llm = WatsonxLLM()
        
        system_prompt = "Extract email parameters from user query and return JSON with to_email, subject, and body fields."
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Query: {query}\nContext: {json.dumps(context)}")
        ]
        
        try:
            response = await llm.ainvoke(messages)
            email_params = json.loads(response.content)
            
            result = self.gmail_tools.send_email(
                to_email=email_params['to_email'],
                subject=email_params['subject'],
                body=email_params.get('body', ''),
                cc_emails=email_params.get('cc_emails'),
                attachment_paths=context.get('attachments')
            )
            
            return {
                "success": True,
                "agent": "gmail",
                "action": "email_sent",
                "response": f"Email sent to {email_params['to_email']}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to send email: {str(e)}"
            }


class TradeParserAgent(BaseAgent):
    
    def __init__(self):
        super().__init__(AgentType.TRADE_PARSER)
        self.capabilities = [
            "parse_trade_log",
            "extract_trade_data",
            "log_trade_ticket",
            "multiple_trade_parsing"
        ]
        self.available = True
        print("✓ Trade Parser Agent initialized")
    
    async def can_handle(self, query: str, context: Dict[str, Any]) -> bool:
        from watsonx_llm import WatsonxLLM
        from langchain_core.messages import SystemMessage, HumanMessage
        import csv
        from pathlib import Path
        from datetime import datetime
        
        llm = WatsonxLLM()
        
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Parse this trade log:\n\n{query}")
        ]
        
        try:
            response = llm.invoke(messages)
            response_text = response.content.strip()
            
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                return {
                    "success": False,
                    "error": "Could not parse trade log. Please provide trade details."
                }
            
            parsed_data = json.loads(response_text[json_start:json_end])
            trades = parsed_data.get('trades', [])
            
            if not trades:
                return {
                    "success": False,
                    "error": "No trades found in the log."
                }
            
            csv_path = Path(__file__).parent / "data" / "trade_blotter.csv"
            trades_logged = []
            
            for trade in trades:
                trade['timestamp'] = datetime.now().strftime("%Y-%m-%d %I:%M %p")
                
                if not trade.get('ticket_id'):
                    trade['ticket_id'] = f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                try:
                    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=[
                            'Ticket ID', 'Client', 'Account', 'Side', 'Ticker', 'Qty',
                            'Type', 'Price', 'Solicited', 'Timestamp', 'Notes',
                            'Follow-up', 'Email', 'Stage', 'Meeting'
                        ])
                        
                        writer.writerow({
                            'Ticket ID': trade.get('ticket_id', ''),
                            'Client': trade.get('client_name', ''),
                            'Account': trade.get('account_number', ''),
                            'Side': trade.get('side', ''),
                            'Ticker': trade.get('ticker', '').upper(),
                            'Qty': trade.get('quantity', 0),
                            'Type': trade.get('order_type', 'Market'),
                            'Price': trade.get('price', 0),
                            'Solicited': 'Yes' if trade.get('solicited') else 'No',
                            'Timestamp': trade['timestamp'],
                            'Notes': trade.get('notes', ''),
                            'Follow-up': trade.get('follow_up_date', ''),
                            'Email': trade.get('email', ''),
                            'Stage': trade.get('stage', 'Pending'),
                            'Meeting': 'Yes' if trade.get('meeting_needed') else 'No'
                        })
                    
                    trades_logged.append(trade)
                except Exception as e:
                    print(f"Error writing to CSV: {e}")
            
            response_lines = ["✅ Trade(s) logged successfully:\n"]
            for trade in trades_logged:
                response_lines.append(f"📋 Ticket: {trade['ticket_id']}")
                response_lines.append(f"   Client: {trade['client_name']} ({trade['account_number']})")
                response_lines.append(f"   Trade: {trade['side']} {trade['quantity']} {trade['ticker']} @ {trade['order_type']}")
                response_lines.append(f"   Stage: {trade['stage']}")
                if trade.get('meeting_needed'):
                    response_lines.append(f"   ⚠️  Meeting Required")
                response_lines.append("")
            
            return {
                "success": True,
                "agent": "trade_parser",
                "trades_logged": len(trades_logged),
                "trades": trades_logged,
                "response": "\n".join(response_lines)
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse trade data: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Trade parsing error: {str(e)}"
            }


class ExcelAgent(BaseAgent):
        if not self.available:
            return False
        
        query_lower = query.lower()
        
        if len(query.split()) > 15:
            trade_log_indicators = ['emergency log', 'ticket reference', 'demanded', 'executed', 'unsolicited', 'solicited']
            if any(indicator in query_lower for indicator in trade_log_indicators):
                return False
        
        open_keywords = ['open', 'show me the', 'display', 'view']
        file_keywords = ['csv', 'excel', 'spreadsheet', 'file', 'blotter']
        if any(ok in query_lower for ok in open_keywords):
            if any(fk in query_lower for fk in file_keywords):
                return True
        
        email_query_patterns = ['what', 'whats', 'what\'s', 'show', 'get', 'find', 'tell me', 'give me']
        if any(pattern in query_lower for pattern in email_query_patterns):
            if 'email' in query_lower or 'mail' in query_lower:
                return True
        
        data_keywords = [
            'show', 'data', 'table', 'csv', 'excel', 
            'client', 'trade', 'blotter', 'account',
            'ticker', 'follow up', 'meeting'
        ]
        
        return any(keyword in query_lower for keyword in data_keywords)
    
    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    
    def __init__(self):
        super().__init__(AgentType.FINANCE)
        self.capabilities = [
            "stock_price",
            "company_info",
            "trade_summary"
        ]
        
        try:
            from tools.finnhub_tools import get_stock_price
            from tools.trade_data_tools import get_trade_summary
            self.get_stock_price = get_stock_price
            self.get_trade_summary = get_trade_summary
            self.available = True
            print("✓ Finance Agent initialized")
        except Exception as e:
            print(f"⚠️  Finance Agent unavailable: {e}")
            self.available = False
    
    async def can_handle(self, query: str, context: Dict[str, Any]) -> bool:
        from agent_orchestrator import create_orqon_agent
        
        agent = create_orqon_agent()
        result = agent.run(query)
        
        return {
            "success": True,
            "agent": "finance",
            "response": result
        }


class ComplianceAgent(BaseAgent):
        if not self.available:
            return False
        
        compliance_keywords = [
            'compliance', 'regulation', 'rule', 'policy',
            'churning', 'solicited', 'unsolicited', 'risk',
            'guideline', 'procedure', 'what is', 'define',
            'profile', 'history', 'search', 'find trades',
            'client background', 'past trades'
        ]
        query_lower = query.lower()
        
        return any(keyword in query_lower for keyword in compliance_keywords)
    
    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    
    def __init__(self):
        super().__init__(AgentType.COORDINATOR)
        
        self.agents = {
            AgentType.GMAIL: GmailAgent(),
            AgentType.EXCEL: ExcelAgent(),
            AgentType.FINANCE: FinanceAgent(),
            AgentType.COMPLIANCE: ComplianceAgent(),
            AgentType.TRADE_PARSER: TradeParserAgent(),
        }
        
        if HAS_AGENT_BUILDER:
            self._init_orchestrator_agent()
        
        print("✓ Coordinator Agent initialized with all sub-agents")
    
    def _init_orchestrator_agent(self):
        
        if AgentType.TRADE_PARSER in self.agents:
            if await self.agents[AgentType.TRADE_PARSER].can_handle(query, context):
                print(f"🎯 Routing to trade_parser agent (priority)")
                return self.agents[AgentType.TRADE_PARSER]
        
        if AgentType.GMAIL in self.agents:
            if await self.agents[AgentType.GMAIL].can_handle(query, context):
                print(f"🎯 Routing to gmail agent")
                return self.agents[AgentType.GMAIL]
        
        for agent_type, agent in self.agents.items():
            if agent_type in [AgentType.TRADE_PARSER, AgentType.GMAIL]:
                continue
            if await agent.can_handle(query, context):
                print(f"🎯 Routing to {agent_type.value} agent")
                return agent
        
        print(f"🎯 Routing to excel agent (default)")
        return self.agents[AgentType.EXCEL]
    
    async def process_with_handoff(
        self, 
        query: str, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
    IBM MCP toolkit server information endpoint
    Returns server capabilities and protocol version
    
    Required for IBM watsonx Orchestrate toolkit import
    IBM MCP toolkit list tools endpoint
    Returns all available tools with their schemas
    
    Called during toolkit import with 30-second timeout
    IBM MCP toolkit call tool endpoint
    Executes a specific tool with provided arguments
    
    Returns:
        MCPToolResponse with content or error
    IBM MCP toolkit SSE (Server-Sent Events) transport endpoint
    Enables remote MCP toolkit import via SSE protocol
    
    IBM requirement:
    - 30-second handshake timeout
    - Standard SSE headers
    - JSON-RPC 2.0 messages
    
    async def generate():
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            query = request_data.get("message", "")
            context = request_data.get("context", {})
            
            async for chunk in coordinator.process_with_handoff(query, context):
                await websocket.send_json(chunk)
            
            await websocket.send_json({
                "type": "complete",
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        print("Client disconnected")


@app.post("/chat")
async def chat_standard(request: ChatRequest):
    return {
        "name": "Orqon Multi-Agent MCP Server",
        "version": "3.0.0",
        "description": "IBM watsonx Orchestrate ADK with specialized agents",
        "endpoints": {
            "chat": "/chat",
            "streaming": "/chat/stream",
            "websocket": "/ws/chat",
            "health": "/health",
            "agents": "/agents"
        }
    }


@app.get("/health")
async def health():
    return {
        "coordinator": {
            "type": "coordinator",
            "description": "Routes queries to specialized agents"
        },
        "agents": {
            agent_type.value: {
                "type": agent_type.value,
                "capabilities": agent.capabilities,
                "available": agent.available if hasattr(agent, 'available') else True
            }
            for agent_type, agent in coordinator.agents.items()
        }
    }


@app.get("/api/calendar/upcoming")
async def get_upcoming_calendar_events():
    Admin endpoint: Build client knowledge graph from CSV data
    Indexes client profiles, relationships, and trade history into Astra DB
    Admin endpoint: Get client profile from knowledge graph
    Admin endpoint: Test Astra DB hybrid search
    Download trade blotter CSV file
    Download trade blotter Excel file
    Get CSV data as JSON for analytics charts
    Open CSV file in system default application (GET endpoint for frontend)
    Open Excel file in system default application (GET endpoint for frontend)
    Open CSV or Excel file in system default application
    Used when LLM wants to show the file to user
    Parse uploaded document and extract trade information
    Supports: PDF, DOCX, DOC, TXT (max 10MB per IBM limits)
    Transcribe audio using IBM Watson Speech-to-Text
    Supports: WAV, MP3, FLAC, OGG (max 100MB)
    Audit transcript by appending to Word document
    Get recent audit log versions from Word document
    Get RAG-generated executive summary from Word document content
    Generate Client Portfolio Report with RAG analysis
    Open the generated portfolio report
    Email supervisor with Word doc and Excel attachments
<h2>Compliance Analysis Report</h2>
<p><strong>Date & Time:</strong> {email_time}</p>
<p>Please find attached the compliance audit documents and trade blotter for your review.</p>
<p><strong>Attachments:</strong></p>
<ul>
<li>Compliance Audit Document (Word)</li>
<li>Client Portfolio Report (Word)</li>
<li>Trade Blotter (Excel/CSV)</li>
</ul>
<p>Best regards,<br>ORQON Compliance System</p>
    Save trades to CSV from frontend confirmation button
    Used when user clicks "Confirm & Save Trade(s) to CSV"