import json
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from pathlib import Path
from typing import List, Dict, Optional, Literal
from datetime import datetime
from collections import deque

DATA_DIR = Path(__file__).parent.parent / "data"
MEMORY_DIR = DATA_DIR / "memory"
CHROMA_DIR = MEMORY_DIR / "chroma_db"
SHORT_TERM_FILE = MEMORY_DIR / "short_term_memory.json"

SHORT_TERM_LIMIT = 10
LONG_TERM_SEARCH_LIMIT = 5


class MemoryManager:
        Initialize memory manager
        
        Args:
            conversation_id: Unique ID for conversation (for multi-user support)
        if SHORT_TERM_FILE.exists():
            try:
                with open(SHORT_TERM_FILE, 'r') as f:
                    data = json.load(f)
                    if self.conversation_id in data:
                        memories = data[self.conversation_id]
                        self.short_term_buffer = deque(memories, maxlen=SHORT_TERM_LIMIT)
            except Exception as e:
                print(f"Error loading short-term memory: {e}")
    
    def _save_short_term(self):
        Add message to short-term memory
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata (e.g., parsed trade, timestamp)
        Get recent conversation history
        
        Args:
            limit: Max messages to return (default: all)
        
        Returns:
            List of recent messages
        self.short_term_buffer.clear()
        self._save_short_term()
    
    def add_to_long_term(
        self,
        key: str,
        value: str,
        category: str = "general",
        importance: float = 0.5
    ):
        try:
            metadata = {
                "key": key,
                "category": category,
                "importance": importance,
                "timestamp": datetime.now().isoformat(),
                "conversation_id": self.conversation_id
            }
            
            existing = self.long_term_collection.get(ids=[key])
            
            if existing['ids']:
                self.long_term_collection.update(
                    ids=[key],
                    documents=[value],
                    metadatas=[metadata]
                )
            else:
                self.long_term_collection.add(
                    ids=[key],
                    documents=[value],
                    metadatas=[metadata]
                )
        
        except Exception as e:
            print(f"Error adding to long-term memory: {e}")
    
    def query_long_term(
        self,
        query: str,
        limit: int = LONG_TERM_SEARCH_LIMIT,
        category: Optional[str] = None
    ) -> List[Dict]:
        try:
            where_filter = None
            if category:
                where_filter = {"category": category}
            
            results = self.long_term_collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter
            )
            
            memories = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    memory = {
                        "key": results['metadatas'][0][i]['key'],
                        "content": results['documents'][0][i],
                        "category": results['metadatas'][0][i]['category'],
                        "importance": results['metadatas'][0][i]['importance'],
                        "timestamp": results['metadatas'][0][i]['timestamp'],
                        "relevance_score": 1.0 - results['distances'][0][i]
                    }
                    memories.append(memory)
            
            return memories
        
        except Exception as e:
            print(f"Error querying long-term memory: {e}")
            return []
    
    def get_by_key(self, key: str) -> Optional[Dict]:
        try:
            self.long_term_collection.delete(ids=[key])
        except Exception as e:
            print(f"Error deleting memory: {e}")
    
    def get_all_long_term(self, category: Optional[str] = None) -> List[Dict]:
        Get formatted memory context for LLM prompt
        
        Args:
            query: Optional query to retrieve relevant long-term memories
        
        Returns:
            Formatted string with short-term + relevant long-term memories
    try:
        manager = MemoryManager()
        manager.add_to_short_term(role, content)
        return f"✅ Added to short-term memory"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def remember_long_term(key: str, value: str, category: str = "general", importance: float = 0.5) -> str:
    try:
        manager = MemoryManager()
        manager.add_to_long_term(key, value, category, importance)
        return f"✅ Stored in long-term memory: {key}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def recall_memory(query: str, memory_type: Literal["short", "long", "both"] = "both") -> str:
    try:
        manager = MemoryManager()
        response = []
        
        if memory_type in ["short", "both"]:
            short_term = manager.get_short_term(limit=5)
            if short_term:
                response.append("📝 Recent Conversation:")
                for msg in short_term[-3:]:
                    response.append(f"  {msg['role']}: {msg['content'][:100]}...")
        
        if memory_type in ["long", "both"]:
            long_term = manager.query_long_term(query, limit=3)
            if long_term:
                response.append("\n🧠 Relevant Long-term Memories:")
                for mem in long_term:
                    response.append(f"  [{mem['category']}] {mem['content']}")
                    response.append(f"    (Relevance: {mem['relevance_score']:.2%})")
        
        return "\n".join(response) if response else "No relevant memories found"
    
    except Exception as e:
        return f"❌ Error: {str(e)}"


def forget_memory(key: str) -> str:
    try:
        manager = MemoryManager()
        manager.clear_short_term()
        return "✅ Conversation history cleared"
    except Exception as e:
        return f"❌ Error: {str(e)}"
