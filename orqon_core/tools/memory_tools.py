"""
Memory Management System
Short-term (conversation buffer) + Long-term (persistent storage)
"""
import json
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from pathlib import Path
from typing import List, Dict, Optional, Literal
from datetime import datetime
from collections import deque

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
MEMORY_DIR = DATA_DIR / "memory"
CHROMA_DIR = MEMORY_DIR / "chroma_db"
SHORT_TERM_FILE = MEMORY_DIR / "short_term_memory.json"

# Memory config
SHORT_TERM_LIMIT = 10  # Last 10 conversation turns
LONG_TERM_SEARCH_LIMIT = 5  # Top 5 relevant memories


class MemoryManager:
    """Manage short-term and long-term memory"""
    
    def __init__(self, conversation_id: str = "default"):
        """
        Initialize memory manager
        
        Args:
            conversation_id: Unique ID for conversation (for multi-user support)
        """
        self.conversation_id = conversation_id
        
        # Create directories
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize short-term memory (in-memory buffer)
        self.short_term_buffer = deque(maxlen=SHORT_TERM_LIMIT)
        self._load_short_term()
        
        # Initialize ChromaDB for long-term memory
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Use sentence transformers for embeddings
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get or create long-term memory collection
        self.long_term_collection = self.client.get_or_create_collection(
            name="long_term_memory",
            embedding_function=self.embedding_fn,
            metadata={"description": "Persistent agent memory"}
        )
    
    def _load_short_term(self):
        """Load short-term memory from disk"""
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
        """Save short-term memory to disk"""
        try:
            # Load existing data
            data = {}
            if SHORT_TERM_FILE.exists():
                with open(SHORT_TERM_FILE, 'r') as f:
                    data = json.load(f)
            
            # Update this conversation
            data[self.conversation_id] = list(self.short_term_buffer)
            
            # Save
            with open(SHORT_TERM_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving short-term memory: {e}")
    
    def add_to_short_term(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add message to short-term memory
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata (e.g., parsed trade, timestamp)
        """
        memory_entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.short_term_buffer.append(memory_entry)
        self._save_short_term()
    
    def get_short_term(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get recent conversation history
        
        Args:
            limit: Max messages to return (default: all)
        
        Returns:
            List of recent messages
        """
        if limit:
            return list(self.short_term_buffer)[-limit:]
        return list(self.short_term_buffer)
    
    def clear_short_term(self):
        """Clear short-term conversation buffer"""
        self.short_term_buffer.clear()
        self._save_short_term()
    
    def add_to_long_term(
        self,
        key: str,
        value: str,
        category: str = "general",
        importance: float = 0.5
    ):
        """
        Add important information to long-term memory
        
        Args:
            key: Unique identifier (e.g., "client_preferences_john_smith")
            value: Information to remember
            category: Memory category (e.g., "client_info", "compliance", "preferences")
            importance: Importance score 0-1 (for future prioritization)
        """
        try:
            # Create metadata
            metadata = {
                "key": key,
                "category": category,
                "importance": importance,
                "timestamp": datetime.now().isoformat(),
                "conversation_id": self.conversation_id
            }
            
            # Check if already exists
            existing = self.long_term_collection.get(ids=[key])
            
            if existing['ids']:
                # Update existing
                self.long_term_collection.update(
                    ids=[key],
                    documents=[value],
                    metadatas=[metadata]
                )
            else:
                # Add new
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
        """
        Query long-term memory using semantic search
        
        Args:
            query: Natural language query
            limit: Max results
            category: Filter by category
        
        Returns:
            List of relevant memories
        """
        try:
            # Build filter
            where_filter = None
            if category:
                where_filter = {"category": category}
            
            # Query
            results = self.long_term_collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter
            )
            
            # Format results
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
        """Get specific memory by key"""
        try:
            result = self.long_term_collection.get(ids=[key])
            
            if result['ids']:
                return {
                    "key": key,
                    "content": result['documents'][0],
                    "category": result['metadatas'][0]['category'],
                    "importance": result['metadatas'][0]['importance'],
                    "timestamp": result['metadatas'][0]['timestamp']
                }
            return None
        
        except Exception as e:
            print(f"Error getting memory: {e}")
            return None
    
    def delete_memory(self, key: str):
        """Delete a specific memory"""
        try:
            self.long_term_collection.delete(ids=[key])
        except Exception as e:
            print(f"Error deleting memory: {e}")
    
    def get_all_long_term(self, category: Optional[str] = None) -> List[Dict]:
        """Get all long-term memories, optionally filtered by category"""
        try:
            where_filter = {"category": category} if category else None
            results = self.long_term_collection.get(where=where_filter)
            
            memories = []
            if results['ids']:
                for i in range(len(results['ids'])):
                    memory = {
                        "key": results['ids'][i],
                        "content": results['documents'][i],
                        "category": results['metadatas'][i]['category'],
                        "importance": results['metadatas'][i]['importance'],
                        "timestamp": results['metadatas'][i]['timestamp']
                    }
                    memories.append(memory)
            
            return memories
        
        except Exception as e:
            print(f"Error getting memories: {e}")
            return []
    
    def get_context_for_prompt(self, query: Optional[str] = None) -> str:
        """
        Get formatted memory context for LLM prompt
        
        Args:
            query: Optional query to retrieve relevant long-term memories
        
        Returns:
            Formatted string with short-term + relevant long-term memories
        """
        context_parts = []
        
        # Add short-term conversation history
        short_term = self.get_short_term(limit=5)  # Last 5 turns
        if short_term:
            context_parts.append("=== Recent Conversation ===")
            for msg in short_term:
                role = msg['role'].capitalize()
                context_parts.append(f"{role}: {msg['content']}")
        
        # Add relevant long-term memories
        if query:
            long_term = self.query_long_term(query, limit=3)
            if long_term:
                context_parts.append("\n=== Relevant Information ===")
                for mem in long_term:
                    context_parts.append(f"[{mem['category']}] {mem['content']}")
        
        return "\n".join(context_parts)


# Tool functions for agent
def remember_short_term(role: str, content: str) -> str:
    """Add message to short-term conversation memory"""
    try:
        manager = MemoryManager()
        manager.add_to_short_term(role, content)
        return f"✅ Added to short-term memory"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def remember_long_term(key: str, value: str, category: str = "general", importance: float = 0.5) -> str:
    """
    Store important information in long-term memory
    
    Args:
        key: Unique identifier (e.g., "client_preferences_john")
        value: Information to remember
        category: Type (client_info, compliance, preferences, etc.)
        importance: 0-1 score
    """
    try:
        manager = MemoryManager()
        manager.add_to_long_term(key, value, category, importance)
        return f"✅ Stored in long-term memory: {key}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def recall_memory(query: str, memory_type: Literal["short", "long", "both"] = "both") -> str:
    """
    Recall relevant memories
    
    Args:
        query: What to search for
        memory_type: "short" (recent chat), "long" (persistent), or "both"
    """
    try:
        manager = MemoryManager()
        response = []
        
        # Short-term memory
        if memory_type in ["short", "both"]:
            short_term = manager.get_short_term(limit=5)
            if short_term:
                response.append("📝 Recent Conversation:")
                for msg in short_term[-3:]:  # Last 3 messages
                    response.append(f"  {msg['role']}: {msg['content'][:100]}...")
        
        # Long-term memory
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
    """Delete a specific long-term memory"""
    try:
        manager = MemoryManager()
        manager.delete_memory(key)
        return f"✅ Deleted memory: {key}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def clear_conversation() -> str:
    """Clear short-term conversation history"""
    try:
        manager = MemoryManager()
        manager.clear_short_term()
        return "✅ Conversation history cleared"
    except Exception as e:
        return f"❌ Error: {str(e)}"
