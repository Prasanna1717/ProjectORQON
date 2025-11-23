"""
IBM watsonx.ai LLM wrapper for Orqon
Replaces Groq with IBM Granite model
"""
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import os
from typing import List
from watsonx_config import (
    WATSONX_API_KEY,
    WATSONX_PROJECT_ID,
    WATSONX_URL,
    WATSONX_MODEL_ID,
    WATSONX_PARAMETERS
)


class WatsonxLLM:
    """Wrapper for IBM watsonx.ai Granite model"""
    
    def __init__(self):
        """Initialize watsonx.ai model"""
        if not WATSONX_API_KEY or not WATSONX_PROJECT_ID:
            raise ValueError(
                "Missing watsonx credentials. Set WATSONX_API_KEY and WATSONX_PROJECT_ID in .env"
            )
        
        # Initialize credentials
        from ibm_watsonx_ai import Credentials
        
        credentials = Credentials(
            url=WATSONX_URL,
            api_key=WATSONX_API_KEY
        )
        
        self.model = ModelInference(
            model_id=WATSONX_MODEL_ID,
            credentials=credentials,
            project_id=WATSONX_PROJECT_ID,
            params=WATSONX_PARAMETERS
        )
    
    def invoke(self, messages: List) -> AIMessage:
        """
        Invoke the watsonx model with messages
        
        Args:
            messages: List of LangChain message objects (SystemMessage, HumanMessage, AIMessage)
        
        Returns:
            AIMessage with the model response
        """
        # Convert LangChain messages to watsonx prompt format
        prompt = self._format_messages(messages)
        
        # Generate response
        response = self.model.generate_text(prompt=prompt)
        
        # Return as AIMessage for compatibility
        return AIMessage(content=response)
    
    def _format_messages(self, messages: List) -> str:
        """
        Format LangChain messages into a single prompt for watsonx
        
        Args:
            messages: List of LangChain message objects
        
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                prompt_parts.append(f"System: {msg.content}")
            elif isinstance(msg, HumanMessage):
                prompt_parts.append(f"Human: {msg.content}")
            elif isinstance(msg, AIMessage):
                prompt_parts.append(f"Assistant: {msg.content}")
        
        # Add final prompt for assistant response
        prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
