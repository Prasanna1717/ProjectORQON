import os
from dotenv import load_dotenv

load_dotenv()

WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

WATSONX_MODEL_ID = "ibm/granite-3-8b-instruct"
WATSONX_PARAMETERS = {
    "decoding_method": "greedy",
    "max_new_tokens": 500,  # Increased from 150 to accommodate full JSON with all 15 fields
    "min_new_tokens": 1,
    "temperature": 0.0,
    "top_k": 50,
    "top_p": 1,
    "repetition_penalty": 1.05,  # Slightly increased to prevent loops
    "stop_sequences": ["\n\nH:", "\n\nHuman:", "\n\nA:", "\n\nAssistant:"]  # Stop at fake dialogues
}

AGENT_NAME = "Orqon Compliance Assistant"
AGENT_DESCRIPTION = "AI-powered stockbroker compliance and trade logging system"
AGENT_VERSION = "1.0.0"
