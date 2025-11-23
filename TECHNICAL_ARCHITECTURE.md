# ORQON Trade Intelligence Platform - Technical Architecture Documentation

**Version:** 3.0.0  
**Date:** November 23, 2025  
**Author:** Prasanna Vijay  
**Platform:** IBM watsonx Orchestrate Multi-Agent System

---

## Table of Contents
1. [System Overview](#1-system-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Multi-Agent System](#4-multi-agent-system)
5. [IBM watsonx Orchestrate ADK Integration](#5-ibm-watsonx-orchestrate-adk-integration)
6. [Vector Search & RAG Architecture](#6-vector-search--rag-architecture)
7. [Astra DB Integration](#7-astra-db-integration)
8. [Voice Agent System](#8-voice-agent-system)
9. [Agent Handoff Workflow](#9-agent-handoff-workflow)
10. [API Endpoints & MCP Protocol](#10-api-endpoints--mcp-protocol)
11. [Frontend Architecture](#11-frontend-architecture)
12. [Data Flow Diagrams](#12-data-flow-diagrams)
13. [Dependencies](#13-dependencies)
14. [Deployment Architecture](#14-deployment-architecture)

---

## 1. System Overview

### 1.1 Project Name
**ORQON** - AI-Powered Trade Intelligence & Compliance Platform

### 1.2 Purpose
Enterprise-grade multi-agent system for:
- 📊 Real-time trade monitoring and analysis
- 🤖 Intelligent query routing across specialized agents
- 📧 Automated email/calendar/meeting management
- 💹 Live stock market data integration
- 📋 SEC compliance analysis with RAG
- 🎤 Voice-based trade parsing
- 🔍 Semantic search across trade history

### 1.3 Core Technologies
- **AI Framework**: IBM watsonx.ai (Granite 3-8B Instruct)
- **Orchestration**: IBM watsonx Orchestrate ADK v1.15.0
- **Backend**: FastAPI (Python 3.13.6)
- **Frontend**: React 18.3.1 + Vite 6.4.1
- **UI Framework**: IBM Carbon Design System
- **Vector DB**: ChromaDB + Astra DB (DataStax)
- **Protocol**: Model Context Protocol (MCP) 2024-11-05

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ORQON PLATFORM ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND LAYER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │   Dashboard  │  │  Compliance  │  │   Analytics  │  │   History   │ │
│  │   (Trading)  │  │   Analysis   │  │   (Charts)   │  │   (Trades)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
│                                                                           │
│  React 18.3.1 + IBM Carbon Design + Vite 6.4.1 + TailwindCSS           │
│  Features: Real-time chat, Voice input, Data tables, Charts             │
│                                                                           │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │ HTTP/WebSocket/SSE
                               │ Port 3001 → 8003
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND LAYER                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │              MCP PROTOCOL SERVER (Port 8003)                       │ │
│  │  • JSON-RPC 2.0                • SSE Transport                     │ │
│  │  • Tool Discovery              • 30s Handshake Timeout             │ │
│  │  • Authentication (JWT)        • Streaming Responses               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │          IBM WATSONX ORCHESTRATE COORDINATOR AGENT                 │ │
│  │  • Query routing with priority                                     │ │
│  │  • Multi-agent handoffs                                            │ │
│  │  • Conversation memory management                                  │ │
│  │  • Granite-3-8B-Instruct LLM                                       │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└──────────────────┬────────────────────────────────────────┬──────────────┘
                   │                                        │
                   ▼                                        ▼
┌─────────────────────────────────────────┐  ┌─────────────────────────────┐
│      SPECIALIZED AGENTS LAYER           │  │   EXTERNAL INTEGRATIONS     │
├─────────────────────────────────────────┤  ├─────────────────────────────┤
│                                         │  │                             │
│  ┌───────────────────────────────────┐ │  │  ┌────────────────────────┐ │
│  │  1. Gmail Agent                   │ │  │  │  Google Workspace      │ │
│  │     • Email send/draft/search     │◄┼──┼──┤  • Gmail API           │ │
│  │     • Calendar management         │ │  │  │  • Calendar API        │ │
│  │     • Google Meet creation        │ │  │  │  • Meet API            │ │
│  │     • Excel data handoff          │ │  │  └────────────────────────┘ │
│  └───────────────────────────────────┘ │  │                             │
│                                         │  │  ┌────────────────────────┐ │
│  ┌───────────────────────────────────┐ │  │  │  Finnhub API           │ │
│  │  2. Finance Agent                 │ │  │  │  • Real-time stocks    │ │
│  │     • Stock price (Finnhub)       │◄┼──┼──┤  • 15+ tickers         │ │
│  │     • Stock comparison            │ │  │  │  • Market data         │ │
│  │     • Financial Q&A               │ │  │  └────────────────────────┘ │
│  └───────────────────────────────────┘ │  │                             │
│                                         │  │  ┌────────────────────────┐ │
│  ┌───────────────────────────────────┐ │  │  │  IBM Watson Speech     │ │
│  │  3. Excel Agent                   │ │  │  │  • Speech-to-text      │ │
│  │     • CSV/Excel operations        │◄┼──┼──┤  • Audio transcription │ │
│  │     • ChromaDB vector search      │ │  │  └────────────────────────┘ │
│  │     • Semantic trade retrieval    │ │  │                             │
│  │     • Client filtering            │ │  │  ┌────────────────────────┐ │
│  │     • Memory tracking             │ │  │  │  Astra DB (DataStax)   │ │
│  └───────────────────────────────────┘ │  │  │  • Vector embeddings   │ │
│                                         │  │  │  • Compliance docs     │ │
│  ┌───────────────────────────────────┐ │  │  │  • Knowledge base      │ │
│  │  4. Compliance Agent              │◄┼──┼──┤  • Session memory      │ │
│  │     • Astra DB RAG search         │ │  │  └────────────────────────┘ │
│  │     • SEC compliance Q&A          │ │  │                             │
│  │     • Document retrieval          │ │  └─────────────────────────────┘
│  │     • Session memory (50 msgs)    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  5. Trade Parser Agent            │ │
│  │     • Natural language parsing    │ │
│  │     • Trade log extraction        │ │
│  │     • Ticket generation           │ │
│  │     • Voice transcription         │ │
│  └───────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA STORAGE LAYER                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │   ChromaDB   │  │   Astra DB   │  │     CSV      │  │  In-Memory  │ │
│  │   (Vectors)  │  │  (Knowledge) │  │ (Trade Data) │  │   (Cache)   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
│                                                                           │
│  • 35 trade records indexed                                             │
│  • Semantic search with embeddings (all-MiniLM-L6-v2)                  │
│  • Session memory for multi-turn conversations                          │
│  • Short-term + Long-term memory per client                             │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

### 3.1 Backend Technologies

#### Core Framework
```yaml
Runtime: Python 3.13.6
Framework: FastAPI 0.109.0+
Server: Uvicorn 0.27.0+
Protocol: MCP (Model Context Protocol) 2024-11-05
Port: 8003
```

#### AI & ML Stack
```yaml
IBM watsonx:
  - ibm-watsonx-orchestrate: 1.15.0
  - ibm-watsonx-ai: 1.0.0+
  - Model: granite-3-8b-instruct
  
Vector Databases:
  - ChromaDB: 0.4.22+
  - Astra DB: DataStax Vector Search
  
Embeddings:
  - sentence-transformers: 2.3.1+
  - Model: all-MiniLM-L6-v2
  
LangChain:
  - langchain: 0.1.0+
  - langchain-groq: 0.0.1+
  - langgraph: 0.0.30+
```

#### Google Cloud APIs
```yaml
Authentication:
  - google-auth: 2.28.0+
  - google-auth-oauthlib: 1.2.0+
  
APIs:
  - google-api-python-client: 2.117.0+
  - Gmail API (send, draft, search)
  - Google Calendar API (events, reminders)
  - Google Meet API (conference creation)
```

#### Voice & Speech
```yaml
IBM Watson Speech:
  - ibm-watson: 8.0.0+
  
Speech Recognition:
  - SpeechRecognition: 3.10.0+
  - sounddevice: 0.5.0+
  - soundfile: 0.13.0+
  - pydub: 0.25.1+
```

#### Data Processing
```yaml
DataFrames:
  - pandas: 2.2.0+
  - openpyxl: 3.1.2+
  - numpy: 2.0.0+
  
Document Parsing:
  - PyPDF2: 3.0.0+
  - python-docx: 1.1.0+
  - pytesseract: 0.3.10+
  - Pillow: 10.0.0+
```

### 3.2 Frontend Technologies

#### Core Framework
```json
{
  "runtime": "Node.js 18+",
  "framework": "React 18.3.1",
  "bundler": "Vite 6.4.1",
  "language": "JavaScript (ES6+)",
  "port": "3001"
}
```

#### UI Framework & Design
```json
{
  "design_system": "@carbon/react 1.68.1",
  "icons": "@carbon/icons-react 11.52.1",
  "charts": "@carbon/charts-react 1.21.1",
  "styling": "TailwindCSS 3.4+",
  "fonts": "IBM Plex Sans, IBM Plex Mono"
}
```

#### Key Libraries
```json
{
  "state_management": "@tanstack/react-query 5.62.11",
  "http_client": "axios 1.7.9",
  "routing": "react-router-dom 7.1.3",
  "charts": "recharts 2.15.0, chart.js 4.4.8",
  "voice": "react-audio-voice-recorder 2.2.0",
  "notifications": "sonner 1.7.3",
  "animation": "framer-motion 11.15.0"
}
```

---

## 4. Multi-Agent System Architecture

### 4.1 Agent Overview

The ORQON platform employs a **multi-agent architecture** with 5 specialized agents, each designed for specific business capabilities. All agents inherit from a base `BaseAgent` class and use the **IBM watsonx Orchestrate ADK** for intelligent task routing and coordination.

**Agent Registry:**

| Agent | Type | Capabilities | Primary API/Tool |
|-------|------|--------------|-----------------|
| **Coordinator Agent** | Master Orchestrator | Query routing, multi-agent handoff, conversation memory | IBM watsonx.ai (Granite-3-8B) |
| **Gmail Agent** | Email & Calendar | Email sending/drafting, Google Calendar reminders, Google Meet meetings, client lookup handoff | Google Workspace APIs |
| **Excel Agent** | Data & RAG | CSV operations, ChromaDB vector search, semantic trade retrieval, client filtering | ChromaDB + sentence-transformers |
| **Finance Agent** | Market Data | Real-time stock prices, stock comparison, financial Q&A | Finnhub API |
| **Compliance Agent** | Regulatory | SEC compliance Q&A, document retrieval, Astra DB RAG | Astra DB + Granite-3-8B |

### 4.2 Agent Communication & Handoff

**Handoff Pattern:**
```
User Query → Coordinator Agent → can_handle() checks → Selected Agent → process() → Response
                    ↓
            (Optional handoff)
                    ↓
            Secondary Agent → process() → Combined Response
```

**Example: Gmail Agent + Excel Agent Handoff**
```
Query: "Gmail sheila with meeting request"
  ↓
Coordinator → Gmail Agent detects name "sheila"
  ↓
Gmail Agent → Needs email → Handoff to Excel Agent
  ↓
Excel Agent → CSV lookup → Returns client_data {"email": "sheila.carter@example.com"}
  ↓
Gmail Agent → Uses email → Composes & sends email
  ↓
Response: "✅ Email sent to sheila.carter@example.com"
```

### 4.3 Coordinator Agent - Master Orchestrator

**Class:** `CoordinatorAgent`  
**Location:** `mcp_server.py` (lines ~200-290)

**Core Responsibilities:**
- **Query Analysis**: Analyze incoming user queries using Granite-3-8B-Instruct LLM
- **Agent Routing**: Determine which specialized agent can best handle the query
- **Priority Logic**: Route based on keyword priority (Calendar > Email > Finance > Excel > Compliance)
- **Conversation Memory**: Maintain shared memory across all agents using `conversation_memory` global dict
- **Multi-Turn Context**: Store last client data, agent results, and conversation history

**Key Methods:**
```python
async def can_handle(query: str, context: Dict) -> bool:
    # Always returns True - acts as fallback orchestrator
    return True

async def route_to_agent(query: str, context: Dict) -> BaseAgent:
    # Iterate through agents by priority
    for agent in [gmail_agent, finance_agent, excel_agent, compliance_agent]:
        if await agent.can_handle(query, context):
            return agent
    return self  # Fallback to coordinator

async def process(query: str, context: Dict) -> Dict:
    # Route query to appropriate agent
    selected_agent = await self.route_to_agent(query, context)
    result = await selected_agent.process(query, context)
    
    # Store result in shared memory
    conversation_memory['shared_context']['last_agent_result'] = result
    
    return result
```

**IBM ADK Integration:**
- Uses `WatsonxLLM()` class wrapping IBM watsonx.ai SDK
- Model: `ibm/granite-3-8b-instruct` with 4096 max tokens
- Temperature: 0.7 for balanced creativity
- Decoding: `greedy` for deterministic routing decisions

### 4.4 Gmail Agent - Email & Calendar Operations

**Class:** `GmailAgent`  
**Location:** `mcp_server.py` (lines ~291-850)

**Capabilities:**
1. **Email Operations:**
   - Send email with attachments
   - Draft email (save without sending)
   - Search emails by query
   - Read email content

2. **Calendar Operations:**
   - Create Google Calendar reminders
   - Schedule Google Meet meetings with attendees
   - Cancel meetings (individual or all upcoming)
   - Auto-extract dates from queries (tomorrow, next week, YYYY-MM-DD)

3. **Client Lookup Handoff:**
   - Detects client names in queries (`gmail sheila`, `mail ron`)
   - Hands off to Excel Agent for email lookup from CSV
   - Uses retrieved `client_data` to compose emails

**Priority Routing Logic:**
```python
async def can_handle(query: str, context: Dict) -> bool:
    query_lower = query.lower()
    
    # PRIORITY 1: Calendar/reminder keywords
    if any(keyword in query_lower for keyword in ['reminder', 'schedule', 'meeting', 'calendar']):
        return True
    
    # PRIORITY 2: Email action patterns
    patterns = ['mail her', 'email him', 'gmail [name]', 'send email']
    if any(pattern in query_lower for pattern in patterns):
        return True
    
    # EXCLUDE: Email queries (what/show email) → Excel Agent handles
    if 'what is' in query_lower and 'email' in query_lower:
        return False
    
    return False
```

**Email Composition with LLM:**
- Uses Granite-3-8B to generate professional email content
- Enforces Gmail alias format: `prasannathefreelancer+{clientname}@gmail.com`
- Includes trade data from `client_data` context (ticker, quantity, side, follow-up date)
- Converts `\n` to `<br>` for HTML rendering in Gmail

**Example Email Output:**
```
To: prasannathefreelancer+sheilacarter@gmail.com
Subject: Follow-up Meeting: Your TSLA Transaction

Dear Sheila,

I hope this email finds you well. I am writing to follow up on your recent transaction.

📊 TRANSACTION DETAILS:

• Stock: TSLA (Tesla, Inc.)
• Action: SELL
• Quantity: 500 shares
• Follow-up Date: November 24, 2025

Looking forward to our conversation.

Best regards,
Prasanna Vijay
Financial Advisor
The Orqon Team

📧 Email: prasannathefreelancer@gmail.com
📞 Available for consultation
```

**Google Meet Meeting Creation:**
```python
result = gmail_tools.schedule_meeting(
    title=f"Portfolio Review Meeting - {client_name}",
    start_time=reminder_date,
    duration_minutes=60,
    attendee_emails=[client_email],
    description="Scheduled via Orqon assistant"
)

# Returns: meet_link, event_link, calendar entry
```

### 4.5 Excel Agent - Data & Vector Search

**Class:** `ExcelAgent`  
**Location:** `mcp_server.py` (lines ~1400-1650)

**Capabilities:**
1. **CSV Operations:**
   - Load trade data from `data/trade_blotter.csv` (35 records)
   - Filter by client name (exact, partial, or semantic match)
   - Filter by ticker symbol, date range, trade side (BUY/SELL)
   - Export filtered results to new CSV files

2. **Vector Search (RAG):**
   - **ChromaDB collection**: `trade_memory` with 35 trade documents
   - **Embedding model**: `all-MiniLM-L6-v2` (sentence-transformers)
   - **Semantic search**: Find similar trades by natural language query
   - **Hybrid search**: Exact match → Partial match → Semantic match

3. **Client Memory Management:**
   - **Short-term memory**: Last 5 queries per client (in-memory dict)
   - **Long-term memory**: Full conversation history per client (persistent storage)
   - **Shared memory**: Store `last_client_data` in `conversation_memory` global for handoff

**Client Filtering Logic (Lines 1540-1580):**
```python
# 1. Exact match
exact_matches = [r for r in rows if r['Client'].lower() == search_name.lower()]
if exact_matches:
    return exact_matches[0]  # Single match

# 2. Partial match (split name parts)
search_parts = search_name.lower().split()
partial_matches = [r for r in rows if any(part in r['Client'].lower() for part in search_parts)]
if len(partial_matches) == 1:
    return partial_matches[0]  # Single match

# 3. Semantic search (ChromaDB)
semantic_results = vector_store.query(
    query_texts=[f"trades for {search_name}"],
    n_results=1  # Limit to best match
)
return semantic_results[0]
```

**Example: Client Lookup**
```
Query: "show data for megan hall"
  ↓
Filter: ["megan", "hall"]
  ↓
Partial match: 1 row found (Megan Hall)
  ↓
Response: "Here is 1 trade record (matched: Megan Hall)"
```

**Vector Search Example:**
```python
# Index trade into ChromaDB
vector_store.add(
    documents=[
        f"Client: {row['Client']}, Ticker: {row['Ticker']}, Side: {row['Side']}, Qty: {row['Qty']}"
    ],
    metadatas=[row],
    ids=[row['TicketID']]
)

# Semantic search
results = vector_store.query(
    query_texts=["trades for sheila carter involving tesla"],
    n_results=3
)
# Returns: Top 3 most relevant trades with metadata
```

### 4.6 Finance Agent - Market Data

**Class:** `FinanceAgent`  
**Location:** `mcp_server.py` (lines ~1100-1250)

**Capabilities:**
1. **Real-Time Stock Prices:**
   - Finnhub API integration (`/quote` endpoint)
   - Current price, day high/low, open price, previous close
   - Percentage change calculation
   - Support for 15+ major tickers (AAPL, TSLA, MSFT, GOOGL, NVDA, etc.)

2. **Stock Comparison:**
   - Compare 2+ stocks side-by-side
   - Price delta analysis
   - Performance metrics

3. **Financial Q&A:**
   - LLM-powered responses using Granite-3-8B
   - Context-aware answers about stocks, markets, trends

**Example Stock Query:**
```python
# Query: "show me the price of AAPL"
result = finance_agent.process("price of AAPL", {})

# Response:
{
  "success": True,
  "agent": "finance",
  "ticker": "AAPL",
  "current_price": 189.50,
  "change": 2.35,
  "change_percent": 1.26,
  "high": 190.20,
  "low": 187.10,
  "response": "📈 **AAPL Stock Price**\nCurrent: $189.50 (+1.26%)"
}
```

**Stock Comparison Example:**
```
Query: "compare TSLA and NVDA"
  ↓
Finance Agent → Finnhub API (2 calls)
  ↓
Response:
  TSLA: $242.80 (+3.2%)
  NVDA: $495.30 (-1.1%)
  Delta: TSLA outperforming by 4.3%
```

### 4.7 Compliance Agent - SEC Regulatory Q&A

**Class:** `ComplianceAgent`  
**Location:** `mcp_server.py` (lines ~1250-1400)

**Capabilities:**
1. **Astra DB RAG Search:**
   - Query DataStax Astra DB vector store for SEC compliance documents
   - Hybrid search: Vector similarity + metadata filtering
   - Fallback to ChromaDB if Astra DB unavailable

2. **Compliance Q&A:**
   - Answer regulatory questions using RAG context
   - Generate compliance reports
   - Document retrieval by regulation number (e.g., "Reg D", "Rule 506")

3. **Session Memory:**
   - Maintains last 50 messages per session
   - Context-aware follow-up questions

**Astra DB Integration:**
```python
from tools.astra_db_tools import get_astra_store

astra = get_astra_store()
results = astra.similarity_search(
    query="What are the requirements for accredited investors?",
    k=5  # Top 5 most relevant documents
)

# Returns: List of Document objects with page_content and metadata
```

**Compliance Query Example:**
```
Query: "What is Regulation D?"
  ↓
Compliance Agent → Astra DB RAG search
  ↓
Retrieved: 3 relevant SEC documents
  ↓
LLM (Granite-3-8B) → Synthesize answer with citations
  ↓
Response:
  "Regulation D provides exemptions from registration requirements 
   for certain securities offerings. Key provisions include:
   
   • Rule 504: Offerings up to $10M
   • Rule 506(b): Unlimited accredited investors
   • Rule 506(c): General solicitation allowed with verification
   
   📄 Source: SEC Regulation D, 17 CFR §230.501-508"
```

### 4.8 Trade Parser Agent - Ticket Logging

**Class:** `TradeParserAgent`  
**Location:** `mcp_server.py` (lines ~850-1100)

**Capabilities:**
1. **Parse Natural Language Trade Logs:**
   - Extract structured data from free-text trade descriptions
   - Support for multiple trades in single query
   - Client name, ticker, quantity, side (BUY/SELL), order type

2. **Trade Ticket Creation:**
   - Generate unique ticket IDs (`TKT-2025-XXX`)
   - Log to CSV with all required fields
   - Compliance flags (solicited/unsolicited)

3. **Emergency Trade Logging:**
   - Quick entry for phone-based trades
   - Auto-populate timestamp and advisor info

**Example Trade Parse:**
```
Query: "Emergency log: Client Michael Rodriguez called, bought 500 shares of AAPL at market"
  ↓
Trade Parser Agent → LLM extracts:
  {
    "client": "Michael Rodriguez",
    "ticker": "AAPL",
    "quantity": 500,
    "side": "BUY",
    "order_type": "MARKET",
    "solicited": false
  }
  ↓
Generate ticket: TKT-2025-036
  ↓
Log to CSV → Vector store index
  ↓
Response: "✅ Trade ticket TKT-2025-036 created for Michael Rodriguez"
```

### 4.9 Agent Priority & Routing

**Routing Priority (Highest to Lowest):**
1. **Gmail Agent** - Calendar/meeting/email keywords
2. **Finance Agent** - Stock/price/ticker keywords
3. **Excel Agent** - Data/client/show keywords
4. **Compliance Agent** - Regulation/compliance/SEC keywords
5. **Trade Parser Agent** - Trade log/ticket keywords
6. **Coordinator Agent** - Fallback for general queries

**Routing Decision Tree:**
```
User Query
    ↓
Coordinator Agent
    ↓
Check Gmail Agent.can_handle() → If YES → Gmail Agent
    ↓ NO
Check Finance Agent.can_handle() → If YES → Finance Agent
    ↓ NO
Check Excel Agent.can_handle() → If YES → Excel Agent
    ↓ NO
Check Compliance Agent.can_handle() → If YES → Compliance Agent
    ↓ NO
Check Trade Parser.can_handle() → If YES → Trade Parser Agent
    ↓ NO
Coordinator Agent (fallback LLM response)
```

**Shared Memory Structure:**
```python
conversation_memory = {
    "shared_context": {
        "last_client_data": {...},       # Last queried client from Excel
        "last_agent_result": {...},      # Last agent response
        "last_client_name": "Sheila Carter",
        "session_id": "session_123"
    },
    "agent_memory": {
        "gmail": [...],                  # Gmail conversation history
        "excel": [...],                  # Excel query history
        "finance": [...],                # Finance query history
        "compliance": [...]              # Compliance query history (last 50)
    }
}
```

### 4.10 IBM watsonx Orchestrate ADK Integration

**SDK Version:** `watsonx-orchestrate==1.15.0`

**Key Components:**

1. **WatsonxLLM Class** (Custom LangChain Integration):
```python
from langchain_ibm import WatsonxLLM as IBMWatsonxLLM

class WatsonxLLM(IBMWatsonxLLM):
    def __init__(self):
        super().__init__(
            model_id="ibm/granite-3-8b-instruct",
            url="https://us-south.ml.cloud.ibm.com",
            apikey=os.getenv('WATSONX_API_KEY'),
            project_id=os.getenv('WATSONX_PROJECT_ID'),
            params={
                "decoding_method": "greedy",
                "max_new_tokens": 4096,
                "temperature": 0.7,
                "top_p": 0.95
            }
        )
```

2. **Agent Orchestration:**
   - Each agent uses `WatsonxLLM()` for intelligent query processing
   - Coordinator routes based on LLM analysis of query intent
   - Context-aware responses using conversation memory

3. **Multi-Agent Toolkit:**
   - `GoogleWorkspaceTools` - Gmail/Calendar/Meet APIs
   - `FinnhubTools` - Stock market data
   - `AstraDBTools` - Vector search for compliance docs
   - `ChromaDBTools` - Local vector store for trades

---

