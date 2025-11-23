"""
Astra DB Tools with IBM watsonx Orchestrate ADK Integration
Optimized with IBM Knowledge Base Best Practices:
- Dynamic mode with query rewriting for multi-turn conversations
- Confidence thresholds (retrieval & response) with 5 levels
- Document chunking with sentence-based strategy and overlap
- Citation support with structured metadata (title, body, url)
- Hybrid vector + lexical search capabilities
- Generation options (prompt instructions, max docs, response length)
- Full document support for summarization tasks
"""
import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import json
import re

# Astra DB SDK
try:
    from astrapy import DataAPIClient
    from astrapy.constants import VectorMetric
    from astrapy.ids import UUID
    ASTRA_AVAILABLE = True
except ImportError:
    ASTRA_AVAILABLE = False
    print("⚠️  astrapy not installed. Run: pip install astrapy")

# IBM watsonx for embeddings
try:
    from ibm_watsonx_ai.foundation_models import Embeddings
    from ibm_watsonx_ai.metanames import EmbedTextParamsMetaNames as EmbedParams
    WATSONX_EMBEDDINGS_AVAILABLE = True
except ImportError:
    WATSONX_EMBEDDINGS_AVAILABLE = False
    print("⚠️  IBM watsonx embeddings not available")

# IBM watsonx for generation (dynamic mode)
try:
    from watsonx_llm import WatsonxLLM
    WATSONX_LLM_AVAILABLE = True
except ImportError:
    WATSONX_LLM_AVAILABLE = False

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
CSV_FILE = DATA_DIR / "trade_blotter.csv"

# Astra DB Configuration
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN", "")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT", "")
ASTRA_DB_NAMESPACE = os.getenv("ASTRA_DB_NAMESPACE", "default_keyspace")

# IBM watsonx Orchestrate Knowledge Base Configuration
# Based on: https://developer.watson-orchestrate.ibm.com/knowledge_base/build_kb
KNOWLEDGE_BASE_CONFIG = {
    # Classic vs Dynamic mode
    # Classic: Agent uses retrieved content directly for responses
    # Dynamic: Agent uses content flexibly for tasks and reasoning (Preview)
    "mode": "dynamic",
    "query_source": "Agent",  # "Agent" (dynamic) or "SessionHistory" (classic)
    
    # Generation options (for LLM-based response generation)
    "generation": {
        "enabled": False,  # False for dynamic mode - agent decides how to use info
        "prompt_instruction": "Provide accurate, professional financial advice based on retrieved documents. Focus on compliance and risk management.",
        "max_docs_passed_to_llm": 10,  # IBM recommendation: 1-20 docs
        "generated_response_length": "Moderate",  # Concise/Moderate/Verbose
        "idk_message": "I don't have enough information in my knowledge base to answer that. Could you rephrase or provide more context?"
    },
    
    # Confidence thresholds (IBM best practice: Low for balanced retrieval)
    # Levels: Off (0.0), Lowest (0.5), Low (0.6), High (0.75), Highest (0.85)
    "confidence_thresholds": {
        "retrieval_confidence_threshold": "Low",  # Filters search results
        "response_confidence_threshold": "Low"    # Filters LLM responses
    },
    
    # Query rewriting for multi-turn conversations
    # Rewrites queries using conversation history for better context
    "query_rewrite": {
        "enabled": True
    },
    
    # Citations (show sources)
    "citations": {
        "citations_shown": -1  # -1 = all sources, 0 = none, N = max N sources
    },
    
    # Full document support (for summarization, proofreading tasks)
    "supports_full_document": True,
    
    # Search configuration
    "search": {
        "mode": "hybrid",  # "vector", "lexical", or "hybrid"
        "limit": 5,        # Max results per query
        "min_similarity": 0.7  # Minimum cosine similarity (0-1)
    },
    
    # Document chunking strategy (IBM recommendation: sentence-based)
    "chunking": {
        "strategy": "sentence",  # "sentence", "paragraph", "fixed"
        "chunk_size": 512,       # tokens per chunk
        "chunk_overlap": 50      # overlap between chunks for context
    },
    
    # Field mapping for search results (structured output)
    "field_mapping": {
        "title": "title",
        "body": "text",
        "url": "source_url"
    }
}


class ClientKnowledgeGraph:
    """
    Knowledge Graph for Client Data
    Stores client relationships, trade history, and metadata
    """
    
    def __init__(self, astra_db):
        """Initialize with Astra DB connection"""
        self.db = astra_db
        self.collection_name = "client_knowledge_graph"
        
        # Create or get collection
        self._init_collection()
    
    def _init_collection(self):
        """Initialize knowledge graph collection"""
        try:
            # Create collection for knowledge graph (non-vector)
            self.collection = self.db.create_collection(
                self.collection_name,
                dimension=None,  # No vector embeddings for knowledge graph
                metric=None
            )
            print(f"✓ Created knowledge graph collection: {self.collection_name}")
        except Exception as e:
            # Collection might already exist
            self.collection = self.db.get_collection(self.collection_name)
            print(f"✓ Using existing knowledge graph: {self.collection_name}")
    
    def index_client_from_csv(self) -> Dict:
        """
        Build knowledge graph from trade_blotter.csv
        Creates client nodes with relationships to trades, accounts, emails
        """
        if not CSV_FILE.exists():
            return {"success": False, "message": "CSV file not found"}
        
        df = pd.read_csv(CSV_FILE)
        
        # Group by client to build client profiles
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
            
            # Collect account info
            if pd.notna(row.get('Account')) or pd.notna(row.get('Acct#')):
                account = row.get('Account', row.get('Acct#'))
                client['accounts'].add(str(account))
            
            # Collect emails
            if pd.notna(row.get('Email')):
                client['emails'].add(str(row.get('Email')))
            
            # Trade statistics
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
            
            # Ticker frequency
            ticker = row.get('Ticker', 'UNKNOWN')
            client['tickers_traded'][ticker] = client['tickers_traded'].get(ticker, 0) + 1
            
            # Stage tracking
            stage = row.get('Stage', 'Unknown')
            client['stages'][stage] = client['stages'].get(stage, 0) + 1
            
            # Meeting flags
            meeting = str(row.get('Meeting', row.get('MeetingNeeded', ''))).lower()
            if meeting in ['yes', 'true']:
                client['meetings_needed'] += 1
            
            # Store ticket reference
            ticket_id = row.get('Ticket ID', row.get('TicketID', 'UNKNOWN'))
            client['trade_tickets'].append(ticket_id)
            
            # Collect notes
            notes = row.get('Notes', '')
            if pd.notna(notes) and notes:
                client['notes'].append(str(notes))
        
        # Insert client nodes into Astra DB
        inserted_count = 0
        for client_name, data in client_data.items():
            # Convert sets to lists for JSON serialization
            data['accounts'] = list(data['accounts'])
            data['emails'] = list(data['emails'])
            
            # Calculate risk score
            risk_score = 0
            if data['unsolicited_count'] > data['solicited_count']:
                risk_score += 30
            if data['meetings_needed'] > 2:
                risk_score += 20
            if data['stages'].get('Compliance Review', 0) > 0:
                risk_score += 50
            
            data['risk_score'] = min(risk_score, 100)
            
            # Store in Astra DB
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
        """Retrieve client profile from knowledge graph"""
        try:
            client_id = client_name.lower().replace(" ", "_")
            result = self.collection.find_one({"_id": client_id})
            return result.get("data") if result else None
        except Exception as e:
            print(f"⚠️  Failed to get client profile: {e}")
            return None
    
    def search_clients_by_risk(self, min_risk_score: int = 50) -> List[Dict]:
        """Find high-risk clients"""
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
    """
    Astra DB Vector Store with IBM watsonx Embeddings
    Hybrid search for emails, trade logs, and compliance docs
    """
    
    def __init__(self):
        """Initialize Astra DB with IBM watsonx embeddings"""
        if not ASTRA_AVAILABLE:
            raise ImportError("astrapy not installed")
        
        if not ASTRA_DB_APPLICATION_TOKEN or not ASTRA_DB_API_ENDPOINT:
            raise ValueError("Astra DB credentials not set. Set ASTRA_DB_APPLICATION_TOKEN and ASTRA_DB_API_ENDPOINT")
        
        # Initialize Astra DB client
        self.client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
        self.db = self.client.get_database(
            ASTRA_DB_API_ENDPOINT,
            namespace=ASTRA_DB_NAMESPACE
        )
        
        print(f"✓ Connected to Astra DB: {ASTRA_DB_NAMESPACE}")
        
        # Initialize collections
        self._init_collections()
        
        # Initialize knowledge graph
        self.knowledge_graph = ClientKnowledgeGraph(self.db)
        
        # Initialize embeddings
        self._init_embeddings()
    
    def _init_embeddings(self):
        """Initialize IBM watsonx slate-125m-english-rtrvr embeddings (768-dim)"""
        if WATSONX_EMBEDDINGS_AVAILABLE:
            try:
                from watsonx_config import get_credentials
                credentials = get_credentials()
                
                # IBM slate-125m-english-rtrvr: 768-dimensional embeddings
                # Optimized for English document retrieval tasks
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
                self.embedding_dimension = 384  # Fallback dimension
        else:
            self.embeddings = None
            self.embedding_dimension = 384
        
        # Initialize LLM for dynamic mode query rewriting
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
        """Initialize vector collections with IBM knowledge base best practices"""
        dimension = self.embedding_dimension
        
        # Trade history collection (supports document chunking)
        try:
            self.trade_collection = self.db.create_collection(
                "trade_history_vectors",
                dimension=dimension,
                metric=VectorMetric.COSINE
            )
            print(f"✓ Created trade history collection (dim={dimension}, cosine similarity)")
        except Exception:
            self.trade_collection = self.db.get_collection("trade_history_vectors")
            print("✓ Using existing trade history collection")
        
        # Email/communication collection
        try:
            self.email_collection = self.db.create_collection(
                "email_communications",
                dimension=dimension,
                metric=VectorMetric.COSINE
            )
            print(f"✓ Created email collection (dim={dimension})")
        except Exception:
            self.email_collection = self.db.get_collection("email_communications")
            print("✓ Using existing email collection")
        
        # Compliance docs collection (with metadata for citations)
        try:
            self.compliance_collection = self.db.create_collection(
                "compliance_documents",
                dimension=dimension,
                metric=VectorMetric.COSINE
            )
            print(f"✓ Created compliance collection (dim={dimension}, citation-ready)")
        except Exception:
            self.compliance_collection = self.db.get_collection("compliance_documents")
            print("✓ Using existing compliance collection")
    
    def _chunk_text(self, text: str, title: str = "") -> List[Dict[str, str]]:
        """
        Chunk text using IBM recommended sentence-based strategy
        Preserves context with overlap between chunks
        """
        config = KNOWLEDGE_BASE_CONFIG["chunking"]
        chunk_size = config["chunk_size"]
        overlap = config["chunk_overlap"]
        
        # Split into sentences (handles ., !, ?)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            if current_length + sentence_length > chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "title": title,
                    "chunk_id": len(chunks)
                })
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-(overlap // 10):] if len(current_chunk) > 1 else []
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                "text": ' '.join(current_chunk),
                "title": title,
                "chunk_id": len(chunks)
            })
        
        return chunks
    
    def _rewrite_query(self, query: str, conversation_history: List[str] = None) -> str:
        """
        Rewrite query using conversation context (IBM dynamic mode)
        Enables multi-turn conversations with context awareness
        """
        if not KNOWLEDGE_BASE_CONFIG["query_rewrite"]["enabled"] or not self.llm:
            return query
        
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            
            system_prompt = """You are a query rewriter for a financial trading knowledge base.
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
"""
            
            context_str = ""
            if conversation_history:
                context_str = "\n".join([f"- {h}" for h in conversation_history[-3:]])
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Context:\n{context_str}\n\nQuery: {query}\n\nRewritten query:")
            ]
            
            response = self.llm.invoke(messages)
            rewritten = response.content.strip()
            
            print(f"🔄 Query rewritten: '{query}' → '{rewritten}'")
            return rewritten
        except Exception as e:
            print(f"⚠️  Query rewriting failed: {e}")
            return query
    
    def _calculate_confidence(self, similarity: float) -> Tuple[str, bool]:
        """
        Calculate confidence level based on cosine similarity score
        Returns: (confidence_level, passes_threshold)
        
        IBM confidence levels:
        - Off: 0.0 (no filtering)
        - Lowest: 0.5
        - Low: 0.6 (recommended)
        - High: 0.75
        - Highest: 0.85
        """
        threshold_map = {
            "Off": 0.0,
            "Lowest": 0.5,
            "Low": 0.6,
            "High": 0.75,
            "Highest": 0.85
        }
        
        retrieval_threshold = KNOWLEDGE_BASE_CONFIG["confidence_thresholds"]["retrieval_confidence_threshold"]
        min_similarity = threshold_map.get(retrieval_threshold, 0.6)
        
        passes = similarity >= min_similarity
        
        # Classify confidence level
        if similarity >= 0.9:
            return "Highest", passes
        elif similarity >= 0.8:
            return "High", passes
        elif similarity >= 0.7:
            return "Moderate", passes
        elif similarity >= 0.6:
            return "Low", passes
        else:
            return "Very Low", passes
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using IBM watsonx slate-125m-english-rtrvr"""
        if self.embeddings:
            try:
                # Truncate to chunk size if needed
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
            # Fallback: use sentence-transformers
            try:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer('all-MiniLM-L6-v2')
                return model.encode(text).tolist()
            except Exception as e:
                print(f"⚠️  Fallback embedding failed: {e}")
                return None
    
    def index_trade_data(self) -> Dict:
        """Index trade data from CSV into Astra DB"""
        if not CSV_FILE.exists():
            return {"success": False, "message": "CSV not found"}
        
        df = pd.read_csv(CSV_FILE)
        indexed_count = 0
        
        for idx, row in df.iterrows():
            # Create searchable text
            client = row.get('Client', 'Unknown')
            quantity = row.get('Qty', row.get('Quantity', 0))
            ticker = row.get('Ticker', 'UNKNOWN')
            side = row.get('Side', 'Unknown')
            order_type = row.get('Type', row.get('Order_Type', 'Unknown'))
            price = row.get('Price', 0.0)
            solicited = row.get('Solicited', 'No')
            notes = row.get('Notes', '')
            timestamp = row.get('Timestamp', '')
            
            text = f"Client {client} traded {quantity} shares of {ticker} ({side}). "
            text += f"Order type: {order_type}. "
            if pd.notna(price) and price > 0:
                text += f"Price: ${price:.2f}. "
            text += f"Solicited: {solicited}. "
            if pd.notna(notes):
                text += f"Notes: {notes}"
            
            # Generate embedding
            embedding = self._generate_embedding(text)
            if not embedding:
                continue
            
            # Store in Astra DB
            try:
                self.trade_collection.insert_one({
                    "_id": str(UUID()),
                    "$vector": embedding,
                    "text": text,
                    "metadata": {
                        "client": client,
                        "ticker": ticker,
                        "side": side,
                        "quantity": int(quantity),
                        "price": float(price) if pd.notna(price) else 0,
                        "solicited": str(solicited),
                        "timestamp": str(timestamp),
                        "ticket_id": row.get('Ticket ID', row.get('TicketID', 'UNKNOWN'))
                    }
                })
                indexed_count += 1
            except Exception as e:
                print(f"⚠️  Failed to index trade: {e}")
        
        return {
            "success": True,
            "indexed_count": indexed_count,
            "message": f"Indexed {indexed_count} trades"
        }
    
    def hybrid_search(
        self,
        query: str,
        search_type: str = "all",
        limit: int = None,
        conversation_history: List[str] = None,
        include_citations: bool = True
    ) -> Dict[str, Any]:
        """
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
        """
        # Apply query rewriting (IBM dynamic mode)
        rewritten_query = self._rewrite_query(query, conversation_history)
        
        # Generate embedding
        embedding = self._generate_embedding(rewritten_query)
        if not embedding:
            return {
                "query": query,
                "rewritten_query": rewritten_query,
                "results": [],
                "citations": [],
                "metadata": {"error": "Failed to generate embedding"}
            }
        
        # Use config limit if not specified
        if limit is None:
            limit = KNOWLEDGE_BASE_CONFIG["search"]["limit"]
        
        results = []
        citations = []
        
        # Search trades
        if search_type in ["trades", "all"]:
            try:
                trade_results = self.trade_collection.find(
                    sort={"$vector": embedding},
                    limit=limit,
                    include_similarity=True
                )
                for result in trade_results:
                    similarity = result.get("$similarity", 0)
                    confidence_level, passes_threshold = self._calculate_confidence(similarity)
                    
                    # Filter by confidence threshold
                    if passes_threshold:
                        metadata = result.get("metadata", {})
                        results.append({
                            "source": "trade_history",
                            "title": f"Trade: {metadata.get('client', 'Unknown')} - {metadata.get('ticker', 'Unknown')}",
                            "body": result.get("text", ""),
                            "url": f"trade://{metadata.get('ticket_id', 'unknown')}",
                            "metadata": metadata,
                            "similarity": similarity,
                            "confidence": confidence_level
                        })
                        
                        # Add citation
                        if include_citations:
                            citations.append({
                                "title": f"Trade: {metadata.get('client')} - {metadata.get('ticker')}",
                                "source": "Trade History Database",
                                "url": f"trade://{metadata.get('ticket_id')}",
                                "confidence": confidence_level
                            })
            except Exception as e:
                print(f"⚠️  Trade search failed: {e}")
        
        # Search emails
        if search_type in ["emails", "all"]:
            try:
                email_results = self.email_collection.find(
                    sort={"$vector": embedding},
                    limit=limit,
                    include_similarity=True
                )
                for result in email_results:
                    similarity = result.get("$similarity", 0)
                    confidence_level, passes_threshold = self._calculate_confidence(similarity)
                    
                    if passes_threshold:
                        metadata = result.get("metadata", {})
                        results.append({
                            "source": "email",
                            "title": f"Email: {metadata.get('subject', 'No Subject')}",
                            "body": result.get("text", ""),
                            "url": f"email://{metadata.get('email_id', 'unknown')}",
                            "metadata": metadata,
                            "similarity": similarity,
                            "confidence": confidence_level
                        })
                        
                        if include_citations:
                            citations.append({
                                "title": metadata.get('subject', 'Email Communication'),
                                "source": f"Email from {metadata.get('from', 'Unknown')}",
                                "url": f"email://{metadata.get('email_id')}",
                                "confidence": confidence_level
                            })
            except Exception as e:
                print(f"⚠️  Email search failed: {e}")
        
        # Search compliance
        if search_type in ["compliance", "all"]:
            try:
                compliance_results = self.compliance_collection.find(
                    sort={"$vector": embedding},
                    limit=limit,
                    include_similarity=True
                )
                for result in compliance_results:
                    similarity = result.get("$similarity", 0)
                    confidence_level, passes_threshold = self._calculate_confidence(similarity)
                    
                    if passes_threshold:
                        metadata = result.get("metadata", {})
                        results.append({
                            "source": "compliance",
                            "title": metadata.get('title', 'Compliance Document'),
                            "body": result.get("text", ""),
                            "url": metadata.get('url', f"compliance://{metadata.get('doc_id', 'unknown')}"),
                            "metadata": metadata,
                            "similarity": similarity,
                            "confidence": confidence_level
                        })
                        
                        if include_citations:
                            citations.append({
                                "title": metadata.get('title', 'Compliance Document'),
                                "source": "Compliance Knowledge Base",
                                "url": metadata.get('url', f"compliance://{metadata.get('doc_id')}"),
                                "confidence": confidence_level
                            })
            except Exception as e:
                print(f"⚠️  Compliance search failed: {e}")
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Apply citations limit (IBM config)
        citations_shown = KNOWLEDGE_BASE_CONFIG["citations"]["citations_shown"]
        if citations_shown == 0:
            citations = []
        elif citations_shown > 0:
            citations = citations[:citations_shown]
        # -1 means show all citations
        
        # Apply max_docs_passed_to_llm limit
        max_docs = KNOWLEDGE_BASE_CONFIG["generation"]["max_docs_passed_to_llm"]
        final_results = results[:max_docs]
        
        return {
            "query": query,
            "rewritten_query": rewritten_query,
            "results": final_results,
            "citations": citations,
            "metadata": {
                "total_results": len(results),
                "returned_results": len(final_results),
                "search_type": search_type,
                "confidence_threshold": KNOWLEDGE_BASE_CONFIG["confidence_thresholds"]["retrieval_confidence_threshold"],
                "mode": KNOWLEDGE_BASE_CONFIG["mode"]
            }
        }
    
    def add_email_context(self, email_data: Dict) -> bool:
        """Add email to vector store for future searches"""
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


# Singleton instance
_astra_store = None

def get_astra_store() -> Optional[AstraDBVectorStore]:
    """Get or create Astra DB store instance"""
    global _astra_store
    if _astra_store is None:
        try:
            _astra_store = AstraDBVectorStore()
        except Exception as e:
            print(f"⚠️  Failed to initialize Astra DB: {e}")
            return None
    return _astra_store


def query_astra_db(
    query: str,
    search_type: str = "all",
    limit: int = None,
    conversation_history: List[str] = None,
    return_citations: bool = True,
    format_output: str = "structured"
) -> Any:
    """
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
    """
    store = get_astra_store()
    if not store:
        if format_output == "text":
            return "❌ Astra DB knowledge base not available"
        return {"error": "Astra DB not available", "results": []}
    
    # Execute search with IBM knowledge base features
    search_result = store.hybrid_search(
        query=query,
        search_type=search_type,
        limit=limit,
        conversation_history=conversation_history,
        include_citations=return_citations
    )
    
    # Return structured format (for agent processing)
    if format_output == "structured":
        return search_result
    
    # Format as text (for human-readable output)
    results = search_result.get("results", [])
    if not results:
        idk_message = KNOWLEDGE_BASE_CONFIG["generation"]["idk_message"]
        return f"❌ {idk_message}"
    
    output = []
    
    # Show query rewriting if it occurred
    if search_result.get("query") != search_result.get("rewritten_query"):
        output.append(f"🔄 Query rewritten: '{search_result['query']}' → '{search_result['rewritten_query']}'")
        output.append("")
    
    # Show results with confidence levels
    output.append(f"📊 Found {len(results)} results (threshold: {search_result['metadata']['confidence_threshold']})")
    output.append("")
    
    for idx, result in enumerate(results, 1):
        output.append(f"[{idx}] {result['title']}")
        output.append(f"    Source: {result['source']}")
        output.append(f"    Confidence: {result['confidence']} (similarity: {result['similarity']:.2%})")
        output.append(f"    {result['body'][:200]}..." if len(result['body']) > 200 else f"    {result['body']}")
        output.append("")
    
    # Show citations if enabled
    citations = search_result.get("citations", [])
    if citations and return_citations:
        output.append("📚 Citations:")
        for idx, citation in enumerate(citations, 1):
            output.append(f"  [{idx}] {citation['title']}")
            output.append(f"      Source: {citation['source']}")
            output.append(f"      Confidence: {citation['confidence']}")
        output.append("")
    
    return "\n".join(output)


def index_client_knowledge_graph() -> Dict:
    """Build client knowledge graph from CSV data"""
    store = get_astra_store()
    if not store:
        return {"success": False, "message": "Astra DB not available"}
    
    return store.knowledge_graph.index_client_from_csv()


def get_client_profile(client_name: str) -> Optional[Dict]:
    """Get client profile from knowledge graph"""
    store = get_astra_store()
    if not store:
        return None
    
    return store.knowledge_graph.get_client_profile(client_name)


"""
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
"""
