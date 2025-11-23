import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import json
import re

try:
    from astrapy import DataAPIClient
    from astrapy.constants import VectorMetric
    from astrapy.ids import UUID
    ASTRA_AVAILABLE = True
except ImportError:
    ASTRA_AVAILABLE = False
    print("⚠️  astrapy not installed. Run: pip install astrapy")

try:
    from ibm_watsonx_ai.foundation_models import Embeddings
    from ibm_watsonx_ai.metanames import EmbedTextParamsMetaNames as EmbedParams
    WATSONX_EMBEDDINGS_AVAILABLE = True
except ImportError:
    WATSONX_EMBEDDINGS_AVAILABLE = False
    print("⚠️  IBM watsonx embeddings not available")

try:
    from watsonx_llm import WatsonxLLM
    WATSONX_LLM_AVAILABLE = True
except ImportError:
    WATSONX_LLM_AVAILABLE = False

DATA_DIR = Path(__file__).parent.parent / "data"
CSV_FILE = DATA_DIR / "trade_blotter.csv"

ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN", "")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT", "")
ASTRA_DB_NAMESPACE = os.getenv("ASTRA_DB_NAMESPACE", "default_keyspace")

KNOWLEDGE_BASE_CONFIG = {
    "mode": "dynamic",
    "query_source": "Agent",  # "Agent" (dynamic) or "SessionHistory" (classic)
    
    "generation": {
        "enabled": False,  # False for dynamic mode - agent decides how to use info
        "prompt_instruction": "Provide accurate, professional financial advice based on retrieved documents. Focus on compliance and risk management.",
        "max_docs_passed_to_llm": 10,  # IBM recommendation: 1-20 docs
        "generated_response_length": "Moderate",  # Concise/Moderate/Verbose
        "idk_message": "I don't have enough information in my knowledge base to answer that. Could you rephrase or provide more context?"
    },
    
    "confidence_thresholds": {
        "retrieval_confidence_threshold": "Low",  # Filters search results
        "response_confidence_threshold": "Low"    # Filters LLM responses
    },
    
    "query_rewrite": {
        "enabled": True
    },
    
    "citations": {
        "citations_shown": -1  # -1 = all sources, 0 = none, N = max N sources
    },
    
    "supports_full_document": True,
    
    "search": {
        "mode": "hybrid",  # "vector", "lexical", or "hybrid"
        "limit": 5,        # Max results per query
        "min_similarity": 0.7  # Minimum cosine similarity (0-1)
    },
    
    "chunking": {
        "strategy": "sentence",  # "sentence", "paragraph", "fixed"
        "chunk_size": 512,       # tokens per chunk
        "chunk_overlap": 50      # overlap between chunks for context
    },
    
    "field_mapping": {
        "title": "title",
        "body": "text",
        "url": "source_url"
    }
}


class ClientKnowledgeGraph:
    
    def __init__(self, astra_db):
        try:
            self.collection = self.db.create_collection(
                self.collection_name,
                dimension=None,
                metric=None
            )
            print(f"✓ Created knowledge graph collection: {self.collection_name}")
        except Exception as e:
            self.collection = self.db.get_collection(self.collection_name)
            print(f"✓ Using existing knowledge graph: {self.collection_name}")
    
    def index_client_from_csv(self) -> Dict:
        if not CSV_FILE.exists():
            return {"success": False, "message": "CSV file not found"}
        
        df = pd.read_csv(CSV_FILE)
        
        client_data = {}
        
        for _, row in df.iterrows():
            client_name = row.get('Client', 'Unknown')
            
            if client_name not in client_data:
                client_data[client_name] = {
                    "client_name": client_name,
                    "accounts": set(),
                    "emails": set(),
                    "tickers_traded": {},  # ticker -> count
                    "total_trades": 0,
                    "buy_count": 0,
                    "sell_count": 0,
                    "solicited_count": 0,
                    "unsolicited_count": 0,
                    "stages": {},
                    "meetings_needed": 0,
                    "trade_tickets": [],
                    "notes": []
                }
            
            client = client_data[client_name]
            
            if pd.notna(row.get('Account')) or pd.notna(row.get('Acct#')):
                account = row.get('Account', row.get('Acct#'))
                client['accounts'].add(str(account))
            
            if pd.notna(row.get('Email')):
                client['emails'].add(str(row.get('Email')))
            
            client['total_trades'] += 1
            
            side = row.get('Side', '').lower()
            if 'buy' in side:
                client['buy_count'] += 1
            elif 'sell' in side:
                client['sell_count'] += 1
            
            solicited = str(row.get('Solicited', '')).lower()
            if solicited in ['yes', 'true', 'solicited']:
                client['solicited_count'] += 1
            else:
                client['unsolicited_count'] += 1
            
            ticker = row.get('Ticker', 'UNKNOWN')
            client['tickers_traded'][ticker] = client['tickers_traded'].get(ticker, 0) + 1
            
            stage = row.get('Stage', 'Unknown')
            client['stages'][stage] = client['stages'].get(stage, 0) + 1
            
            meeting = str(row.get('Meeting', row.get('MeetingNeeded', ''))).lower()
            if meeting in ['yes', 'true']:
                client['meetings_needed'] += 1
            
            ticket_id = row.get('Ticket ID', row.get('TicketID', 'UNKNOWN'))
            client['trade_tickets'].append(ticket_id)
            
            notes = row.get('Notes', '')
            if pd.notna(notes) and notes:
                client['notes'].append(str(notes))
        
        inserted_count = 0
        for client_name, data in client_data.items():
            data['accounts'] = list(data['accounts'])
            data['emails'] = list(data['emails'])
            
            risk_score = 0
            if data['unsolicited_count'] > data['solicited_count']:
                risk_score += 30
            if data['meetings_needed'] > 2:
                risk_score += 20
            if data['stages'].get('Compliance Review', 0) > 0:
                risk_score += 50
            
            data['risk_score'] = min(risk_score, 100)
            
            try:
                self.collection.insert_one({
                    "_id": client_name.lower().replace(" ", "_"),
                    "type": "client_profile",
                    "data": data,
                    "indexed_at": datetime.now().isoformat()
                })
                inserted_count += 1
            except Exception as e:
                print(f"⚠️  Failed to insert {client_name}: {e}")
        
        return {
            "success": True,
            "clients_indexed": inserted_count,
            "message": f"Indexed {inserted_count} client profiles"
        }
    
    def get_client_profile(self, client_name: str) -> Optional[Dict]:
        try:
            results = self.collection.find(
                {"data.risk_score": {"$gte": min_risk_score}},
                projection={"data": True},
                limit=20
            )
            return [r["data"] for r in results]
        except Exception as e:
            print(f"⚠️  Failed to search clients: {e}")
            return []


class AstraDBVectorStore:
    
    def __init__(self):
        if WATSONX_EMBEDDINGS_AVAILABLE:
            try:
                from watsonx_config import get_credentials
                credentials = get_credentials()
                
                self.embeddings = Embeddings(
                    model_id="ibm/slate-125m-english-rtrvr",
                    params={
                        EmbedParams.TRUNCATE_INPUT_TOKENS: KNOWLEDGE_BASE_CONFIG["chunking"]["chunk_size"],
                        EmbedParams.RETURN_OPTIONS: {"input_text": False}
                    },
                    credentials=credentials,
                    project_id=os.getenv("WATSONX_PROJECT_ID")
                )
                print("✓ IBM watsonx slate-125m-english-rtrvr initialized (768-dim)")
                self.embedding_dimension = 768
            except Exception as e:
                print(f"⚠️  Failed to initialize watsonx embeddings: {e}")
                self.embeddings = None
                self.embedding_dimension = 384
        else:
            self.embeddings = None
            self.embedding_dimension = 384
        
        if WATSONX_LLM_AVAILABLE and KNOWLEDGE_BASE_CONFIG["query_rewrite"]["enabled"]:
            try:
                self.llm = WatsonxLLM()
                print("✓ IBM watsonx LLM initialized for query rewriting")
            except Exception as e:
                print(f"⚠️  LLM not available for query rewriting: {e}")
                self.llm = None
        else:
            self.llm = None
    
    def _init_collections(self):
        Chunk text using IBM recommended sentence-based strategy
        Preserves context with overlap between chunks
        Rewrite query using conversation context (IBM dynamic mode)
        Enables multi-turn conversations with context awareness
Rewrite the user's query to be more specific and searchable, incorporating conversation context.
Keep it concise (1-2 sentences max).
Focus on key entities: client names, tickers, trade types, compliance terms.

Examples:
User: "What about Sheila?"
Context: Previous query about TSLA trades
Rewritten: "What are Sheila Carter's TSLA trades and account information?"

User: "Check compliance"
Context: Previous query about unsolicited trades
Rewritten: "What are the compliance rules for unsolicited trades?"
        Calculate confidence level based on cosine similarity score
        Returns: (confidence_level, passes_threshold)
        
        IBM confidence levels:
        - Off: 0.0 (no filtering)
        - Lowest: 0.5
        - Low: 0.6 (recommended)
        - High: 0.75
        - Highest: 0.85
        if self.embeddings:
            try:
                max_tokens = KNOWLEDGE_BASE_CONFIG["chunking"]["chunk_size"]
                words = text.split()
                if len(words) > max_tokens:
                    text = ' '.join(words[:max_tokens])
                
                result = self.embeddings.embed_query(text)
                return result
            except Exception as e:
                print(f"⚠️  Embedding generation failed: {e}")
                return None
        else:
            try:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer('all-MiniLM-L6-v2')
                return model.encode(text).tolist()
            except Exception as e:
                print(f"⚠️  Fallback embedding failed: {e}")
                return None
    
    def index_trade_data(self) -> Dict:
        IBM-optimized hybrid search with confidence thresholds and citations
        
        Features:
        - Query rewriting for multi-turn conversations (IBM dynamic mode)
        - Confidence-based filtering (retrieval threshold)
        - Citation support with structured metadata
        - Hybrid vector + lexical search
        
        Args:
            query: Search query
            search_type: "trades", "emails", "compliance", or "all"
            limit: Max results (defaults to config)
            conversation_history: Previous queries for context
            include_citations: Return source citations
        
        Returns:
            {
                "query": original query,
                "rewritten_query": query after rewriting,
                "results": List of results with confidence scores,
                "citations": List of sources (if enabled),
                "metadata": Search metadata
            }
        try:
            text = f"Email from {email_data.get('from')} to {email_data.get('to')}. "
            text += f"Subject: {email_data.get('subject', 'No subject')}. "
            text += f"Body: {email_data.get('body', '')}"
            
            embedding = self._generate_embedding(text)
            if not embedding:
                return False
            
            self.email_collection.insert_one({
                "_id": str(UUID()),
                "$vector": embedding,
                "text": text,
                "metadata": {
                    "from": email_data.get("from", ""),
                    "to": email_data.get("to", ""),
                    "subject": email_data.get("subject", ""),
                    "timestamp": datetime.now().isoformat(),
                    "type": "email"
                }
            })
            return True
        except Exception as e:
            print(f"⚠️  Failed to add email: {e}")
            return False


_astra_store = None

def get_astra_store() -> Optional[AstraDBVectorStore]:
    IBM-optimized Astra DB query with knowledge base features
    
    Features:
    - Query rewriting for multi-turn conversations
    - Confidence-based filtering
    - Citation support
    - Structured output for LLM consumption
    
    Args:
        query: Search query
        search_type: "trades", "emails", "compliance", or "all"
        limit: Max results (uses config default if None)
        conversation_history: Previous queries for context
        return_citations: Include source citations
        format_output: "structured" (dict) or "text" (formatted string)
    
    Returns:
        Structured dict or formatted text based on format_output
    store = get_astra_store()
    if not store:
        return {"success": False, "message": "Astra DB not available"}
    
    return store.knowledge_graph.index_client_from_csv()


def get_client_profile(client_name: str) -> Optional[Dict]:
IBM watsonx Orchestrate Knowledge Base Optimizations Applied:

✅ Dynamic Mode Support:
   - query_source: "Agent" for agent-driven queries
   - generation.enabled: False (agent decides how to use info)
   - Flexible task completion and reasoning

✅ Confidence Thresholds (5 levels):
   - Off (0.0), Lowest (0.5), Low (0.6), High (0.75), Highest (0.85)
   - Retrieval threshold: Filters search results by similarity
   - Response threshold: Filters LLM-generated responses
   - Default: Low (0.6) for balanced retrieval

✅ Query Rewriting:
   - Multi-turn conversation support
   - Context-aware query enhancement
   - Uses last 3 queries for context
   - LLM-powered query rewriting with financial domain knowledge

✅ Document Chunking:
   - Sentence-based strategy (IBM recommendation)
   - Chunk size: 512 tokens
   - Overlap: 50 tokens for context preservation
   - Maintains semantic coherence

✅ Citation Support:
   - Structured metadata: title, body, url
   - Source tracking for all results
   - Confidence levels per citation
   - Configurable display: -1 (all), 0 (none), N (max N)

✅ Generation Options:
   - max_docs_passed_to_llm: 10 (controls context size)
   - generated_response_length: Moderate (Concise/Moderate/Verbose)
   - idk_message: Custom fallback when no results found
   - prompt_instruction: Domain-specific instructions for LLM

✅ Hybrid Search:
   - Vector search with IBM slate-125m-english-rtrvr (768-dim)
   - Lexical search capability
   - Hybrid mode combining vector + lexical
   - COSINE similarity metric

✅ Field Mapping:
   - title: Document/email/trade title
   - body: Full text content
   - url: Source reference (trade://, email://, compliance://)
   - metadata: Additional context (client, ticker, timestamps)

✅ Full Document Support:
   - Supports summarization tasks
   - Supports proofreading tasks
   - Chunking for large documents
   - Context preservation with overlap

Configuration Source:
- IBM watsonx Orchestrate Documentation
- https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=agents-adding-knowledge
- https://developer.watson-orchestrate.ibm.com/knowledge_base/build_kb

Knowledge Base Spec:
- spec_version: v1
- kind: knowledge_base
- conversational_search_tool with index_config
- Astra DB as vector store backend
- IBM watsonx embeddings and LLM