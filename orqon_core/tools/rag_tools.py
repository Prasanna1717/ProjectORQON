"""
RAG Tools with ChromaDB
Query historical trade data using semantic search
"""
import pandas as pd
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
EXCEL_FILE = DATA_DIR / "trade_blotter.xlsx"
CSV_FILE = DATA_DIR / "trade_blotter.csv"
CHROMA_DIR = DATA_DIR / "chroma_db"


class TradeRAG:
    """RAG system for querying historical trade data"""
    
    def __init__(self):
        """Initialize ChromaDB and embedding function"""
        # Create chroma directory
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Use sentence transformers for embeddings
        # Using all-MiniLM-L6-v2: fast and accurate for short texts
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="trade_history",
            embedding_function=self.embedding_fn,
            metadata={"description": "Trade blotter historical data"}
        )
    
    def _load_trades(self) -> pd.DataFrame:
        """Load trades from Excel or CSV"""
        if EXCEL_FILE.exists():
            return pd.read_excel(EXCEL_FILE)
        elif CSV_FILE.exists():
            return pd.read_csv(CSV_FILE)
        else:
            return pd.DataFrame()
    
    def _create_trade_text(self, row: pd.Series) -> str:
        """
        Create searchable text from trade data
        Format: "Client [name] traded [quantity] shares of [ticker] ([side]) 
                 on [date]. Order type: [order_type]. Solicited: [solicited]. 
                 Notes: [notes]"
        """
        # Handle both column name formats
        client = row.get('Client_Name', row.get('Client', 'Unknown'))
        quantity = row.get('Quantity', row.get('Qty', 0))
        ticker = row.get('Ticker', 'UNKNOWN')
        side = row.get('Side', 'Unknown')
        order_type = row.get('Order_Type', row.get('Type', 'Unknown'))
        price = row.get('Price', 0.0)
        solicited = row.get('Solicited', 'No')
        notes = row.get('Notes', '')
        email = row.get('Email', '')
        timestamp = row.get('Timestamp', '')
        
        date = pd.to_datetime(timestamp).strftime('%Y-%m-%d %H:%M') if timestamp else 'Unknown date'
        
        text_parts = [
            f"Client {client} traded {quantity} shares of {ticker} ({side})",
            f"on {date}",
            f"Order type: {order_type}",
            f"Price: ${price:.2f}" if pd.notna(price) and price > 0 else "Market price",
            f"Solicited: {solicited}",
        ]
        
        if pd.notna(notes) and notes:
            text_parts.append(f"Notes: {notes}")
        
        if pd.notna(email) and email:
            text_parts.append(f"Email: {email}")
        
        return ". ".join(text_parts)
    
    def index_trades(self, force_reindex: bool = False) -> Dict:
        """
        Index all trades into ChromaDB
        
        Args:
            force_reindex: If True, delete existing collection and reindex
        
        Returns:
            Dict with status and count
        """
        try:
            # Check if already indexed
            if not force_reindex and self.collection.count() > 0:
                return {
                    "success": True,
                    "message": f"Collection already indexed with {self.collection.count()} trades",
                    "count": self.collection.count()
                }
            
            # Reset collection if force reindex
            if force_reindex:
                self.client.delete_collection("trade_history")
                self.collection = self.client.create_collection(
                    name="trade_history",
                    embedding_function=self.embedding_fn,
                    metadata={"description": "Trade blotter historical data"}
                )
            
            # Load trades
            df = self._load_trades()
            
            if df.empty:
                return {
                    "success": False,
                    "message": "No trades found to index",
                    "count": 0
                }
            
            # Prepare data for indexing
            documents = []
            metadatas = []
            ids = []
            
            for idx, row in df.iterrows():
                # Create searchable text
                text = self._create_trade_text(row)
                documents.append(text)
                
                # Handle both column formats
                ticket_id = row.get('Ticket_ID', row.get('TicketID', f'TKT-{idx}'))
                client_name = row.get('Client_Name', row.get('Client', 'Unknown'))
                ticker = row.get('Ticker', 'UNKNOWN')
                side = row.get('Side', 'Unknown')
                quantity = row.get('Quantity', row.get('Qty', 0))
                order_type = row.get('Order_Type', row.get('Type', 'Unknown'))
                price = row.get('Price', 0.0)
                solicited_val = row.get('Solicited', 'No')
                stage = row.get('Stage', 'Pending')
                timestamp = row.get('Timestamp', '')
                
                # Convert solicited to boolean
                solicited_bool = solicited_val in ['Yes', True, 'yes', 'true', '1', 1]
                
                # Create metadata (ChromaDB can store rich metadata)
                metadata = {
                    "ticket_id": str(ticket_id),
                    "timestamp": str(timestamp),
                    "client_name": str(client_name),
                    "ticker": str(ticker),
                    "side": str(side),
                    "quantity": int(quantity) if pd.notna(quantity) else 0,
                    "order_type": str(order_type),
                    "price": float(price) if pd.notna(price) else 0.0,
                    "solicited": solicited_bool,
                    "stage": str(stage) if pd.notna(stage) else 'Pending'
                }
                metadatas.append(metadata)
                
                # Use ticket ID as unique ID
                ids.append(str(ticket_id))
            
            # Add to collection (batch operation)
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                "success": True,
                "message": f"Successfully indexed {len(documents)} trades",
                "count": len(documents)
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Error indexing trades: {str(e)}",
                "count": 0
            }
    
    def query(
        self,
        query_text: str,
        limit: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Query trade history using semantic search
        
        Args:
            query_text: Natural language query
            limit: Max number of results
            filter_dict: Optional metadata filters (e.g., {"ticker": "AAPL"})
        
        Returns:
            List of matching trades with scores
        """
        try:
            # Ensure collection is indexed
            if self.collection.count() == 0:
                self.index_trades()
            
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query_text],
                n_results=limit,
                where=filter_dict  # Metadata filtering
            )
            
            # Format results
            formatted_results = []
            
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    result = {
                        "ticket_id": results['metadatas'][0][i]['ticket_id'],
                        "client_name": results['metadatas'][0][i]['client_name'],
                        "ticker": results['metadatas'][0][i]['ticker'],
                        "side": results['metadatas'][0][i]['side'],
                        "quantity": results['metadatas'][0][i]['quantity'],
                        "price": results['metadatas'][0][i]['price'],
                        "order_type": results['metadatas'][0][i]['order_type'],
                        "solicited": results['metadatas'][0][i]['solicited'],
                        "timestamp": results['metadatas'][0][i]['timestamp'],
                        "description": results['documents'][0][i],
                        "relevance_score": 1.0 - results['distances'][0][i]  # Convert distance to score
                    }
                    formatted_results.append(result)
            
            return formatted_results
        
        except Exception as e:
            print(f"Error querying: {e}")
            return []
    
    def get_client_trades(self, client_name: str, limit: int = 10) -> List[Dict]:
        """Get all trades for a specific client"""
        return self.query(
            query_text=f"trades by {client_name}",
            limit=limit,
            filter_dict={"client_name": client_name}
        )
    
    def get_ticker_trades(self, ticker: str, limit: int = 10) -> List[Dict]:
        """Get all trades for a specific ticker"""
        return self.query(
            query_text=f"trades of {ticker}",
            limit=limit,
            filter_dict={"ticker": ticker.upper()}
        )
    
    def get_recent_solicited_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent solicited trades"""
        return self.query(
            query_text="solicited trades",
            limit=limit,
            filter_dict={"solicited": True}
        )
    
    def search_by_notes(self, keyword: str, limit: int = 10) -> List[Dict]:
        """Search trades by keywords in notes"""
        return self.query(
            query_text=keyword,
            limit=limit
        )


# Tool functions for agent
def query_trade_history(query: str, limit: int = 5) -> str:
    """
    Query historical trades using natural language
    
    Example queries:
    - "Show me all Apple trades"
    - "What trades did John Smith make?"
    - "Find recent solicited trades"
    - "Trades with compliance issues"
    """
    try:
        rag = TradeRAG()
        results = rag.query(query, limit=limit)
        
        if not results:
            return f"No trades found matching: '{query}'"
        
        # Format results
        response = f"Found {len(results)} matching trade(s):\n\n"
        
        for i, trade in enumerate(results, 1):
            response += f"{i}. {trade['description']}\n"
            response += f"   Relevance: {trade['relevance_score']:.2%}\n"
            response += f"   Ticket ID: {trade['ticket_id']}\n\n"
        
        return response
    
    except Exception as e:
        return f"❌ Error: {str(e)}"


def get_client_history(client_name: str, limit: int = 10) -> str:
    """Get trade history for a specific client"""
    try:
        rag = TradeRAG()
        results = rag.get_client_trades(client_name, limit=limit)
        
        if not results:
            return f"No trades found for client: {client_name}"
        
        response = f"📊 Trade history for {client_name} ({len(results)} trades):\n\n"
        
        for i, trade in enumerate(results, 1):
            response += f"{i}. {trade['side']} {trade['quantity']} {trade['ticker']} "
            response += f"@ ${trade['price']:.2f} ({trade['timestamp']})\n"
        
        return response
    
    except Exception as e:
        return f"❌ Error: {str(e)}"


def get_ticker_history(ticker: str, limit: int = 10) -> str:
    """Get trade history for a specific stock ticker"""
    try:
        rag = TradeRAG()
        results = rag.get_ticker_trades(ticker, limit=limit)
        
        if not results:
            return f"No trades found for ticker: {ticker}"
        
        response = f"📈 Trade history for {ticker} ({len(results)} trades):\n\n"
        
        for i, trade in enumerate(results, 1):
            response += f"{i}. {trade['client_name']}: {trade['side']} {trade['quantity']} "
            response += f"@ ${trade['price']:.2f} ({trade['timestamp']})\n"
        
        return response
    
    except Exception as e:
        return f"❌ Error: {str(e)}"


def index_all_trades(force_reindex: bool = False) -> str:
    """Index all trades into vector database"""
    try:
        rag = TradeRAG()
        result = rag.index_trades(force_reindex=force_reindex)
        
        if result['success']:
            return f"✅ {result['message']}"
        else:
            return f"❌ {result['message']}"
    
    except Exception as e:
        return f"❌ Error: {str(e)}"


def query_knowledge_base(query: str) -> str:
    """
    Query compliance guidelines, risk rules, and trading procedures
    from knowledge base documents
    """
    try:
        # Initialize ChromaDB for knowledge base
        kb_client = chromadb.PersistentClient(
            path=str(DATA_DIR / "compliance_memory"),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get or create knowledge base collection
        kb_collection = kb_client.get_or_create_collection(
            name="compliance_knowledge",
            embedding_function=embedding_fn,
            metadata={"description": "Compliance guidelines and trading rules"}
        )
        
        # Check if we need to index the knowledge base
        if kb_collection.count() == 0:
            # Read and index knowledge base documents
            docs_to_index = []
            
            # Read compliance guidelines
            compliance_file = DATA_DIR.parent / "docs" / "compliance_guidelines.txt"
            if compliance_file.exists():
                with open(compliance_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Split into sections
                    sections = content.split('\n\n')
                    for i, section in enumerate(sections):
                        if section.strip():
                            docs_to_index.append({
                                'id': f'compliance_{i}',
                                'text': section.strip(),
                                'source': 'compliance_guidelines.txt'
                            })
            
            # Read risk assessment rules
            risk_file = DATA_DIR.parent / "docs" / "risk_assessment_rules.txt"
            if risk_file.exists():
                with open(risk_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    sections = content.split('\n\n')
                    for i, section in enumerate(sections):
                        if section.strip():
                            docs_to_index.append({
                                'id': f'risk_{i}',
                                'text': section.strip(),
                                'source': 'risk_assessment_rules.txt'
                            })
            
            # Read trading procedures
            procedures_file = DATA_DIR.parent / "docs" / "trading_procedures.txt"
            if procedures_file.exists():
                with open(procedures_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    sections = content.split('\n\n')
                    for i, section in enumerate(sections):
                        if section.strip():
                            docs_to_index.append({
                                'id': f'procedure_{i}',
                                'text': section.strip(),
                                'source': 'trading_procedures.txt'
                            })
            
            # Index documents
            if docs_to_index:
                kb_collection.add(
                    ids=[doc['id'] for doc in docs_to_index],
                    documents=[doc['text'] for doc in docs_to_index],
                    metadatas=[{'source': doc['source']} for doc in docs_to_index]
                )
        
        # Query the knowledge base
        results = kb_collection.query(
            query_texts=[query],
            n_results=3
        )
        
        if not results['documents'] or not results['documents'][0]:
            return "I don't have specific information about that in my knowledge base."
        
        # Format response with relevant excerpts
        response = "💡 **I found this in my knowledge base:**\n\n"
        
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            # Trim long documents
            if len(doc) > 500:
                doc = doc[:497] + "..."
            
            response += f"{doc}\n\n"
            response += f"_Source: {metadata['source']}_\n\n"
            
            if i < len(results['documents'][0]) - 1:
                response += "---\n\n"
        
        return response
    
    except Exception as e:
        return f"❌ Error querying knowledge base: {str(e)}"
