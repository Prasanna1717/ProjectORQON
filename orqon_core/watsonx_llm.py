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
        if not WATSONX_API_KEY or not WATSONX_PROJECT_ID:
            raise ValueError(
                "Missing watsonx credentials. Set WATSONX_API_KEY and WATSONX_PROJECT_ID in .env"
            )
        
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
        prompt = self._format_messages(messages)
        
        response = self.model.generate_text(prompt=prompt)
        
        return AIMessage(content=response)
    
    def _format_messages(self, messages: List) -> str:
        prompt_parts = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                prompt_parts.append(f"System: {msg.content}")
            elif isinstance(msg, HumanMessage):
                prompt_parts.append(f"Human: {msg.content}")
            elif isinstance(msg, AIMessage):
                prompt_parts.append(f"Assistant: {msg.content}")
        
        prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
