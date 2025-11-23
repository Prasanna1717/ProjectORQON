import pandas as pd
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json

DATA_DIR = Path(__file__).parent.parent / "data"
EXCEL_FILE = DATA_DIR / "trade_blotter.xlsx"
CSV_FILE = DATA_DIR / "trade_blotter.csv"
CHROMA_DIR = DATA_DIR / "chroma_db"


class TradeRAG:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name="trade_history",
            embedding_function=self.embedding_fn,
            metadata={"description": "Trade blotter historical data"}
        )
    
    def _load_trades(self) -> pd.DataFrame:
        Create searchable text from trade data
        Format: "Client [name] traded [quantity] shares of [ticker] ([side]) 
                 on [date]. Order type: [order_type]. Solicited: [solicited]. 
                 Notes: [notes]"
        Index all trades into ChromaDB
        
        Args:
            force_reindex: If True, delete existing collection and reindex
        
        Returns:
            Dict with status and count
        Query trade history using semantic search
        
        Args:
            query_text: Natural language query
            limit: Max number of results
            filter_dict: Optional metadata filters (e.g., {"ticker": "AAPL"})
        
        Returns:
            List of matching trades with scores
        return self.query(
            query_text=f"trades by {client_name}",
            limit=limit,
            filter_dict={"client_name": client_name}
        )
    
    def get_ticker_trades(self, ticker: str, limit: int = 10) -> List[Dict]:
        return self.query(
            query_text="solicited trades",
            limit=limit,
            filter_dict={"solicited": True}
        )
    
    def search_by_notes(self, keyword: str, limit: int = 10) -> List[Dict]:
    Query historical trades using natural language
    
    Example queries:
    - "Show me all Apple trades"
    - "What trades did John Smith make?"
    - "Find recent solicited trades"
    - "Trades with compliance issues"
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
    try:
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
        
        kb_collection = kb_client.get_or_create_collection(
            name="compliance_knowledge",
            embedding_function=embedding_fn,
            metadata={"description": "Compliance guidelines and trading rules"}
        )
        
        if kb_collection.count() == 0:
            docs_to_index = []
            
            compliance_file = DATA_DIR.parent / "docs" / "compliance_guidelines.txt"
            if compliance_file.exists():
                with open(compliance_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    sections = content.split('\n\n')
                    for i, section in enumerate(sections):
                        if section.strip():
                            docs_to_index.append({
                                'id': f'compliance_{i}',
                                'text': section.strip(),
                                'source': 'compliance_guidelines.txt'
                            })
            
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
            
            if docs_to_index:
                kb_collection.add(
                    ids=[doc['id'] for doc in docs_to_index],
                    documents=[doc['text'] for doc in docs_to_index],
                    metadatas=[{'source': doc['source']} for doc in docs_to_index]
                )
        
        results = kb_collection.query(
            query_texts=[query],
            n_results=3
        )
        
        if not results['documents'] or not results['documents'][0]:
            return "I don't have specific information about that in my knowledge base."
        
        response = "💡 **I found this in my knowledge base:**\n\n"
        
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            if len(doc) > 500:
                doc = doc[:497] + "..."
            
            response += f"{doc}\n\n"
            response += f"_Source: {metadata['source']}_\n\n"
            
            if i < len(results['documents'][0]) - 1:
                response += "---\n\n"
        
        return response
    
    except Exception as e:
        return f"❌ Error querying knowledge base: {str(e)}"
