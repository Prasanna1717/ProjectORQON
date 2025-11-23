"""Test IBM watsonx Orchestrate agent_builder API"""
from ibm_watsonx_orchestrate.agent_builder.agents import (
    AssistantAgent,
    AgentKind,
)
from ibm_watsonx_orchestrate.agent_builder.agents.types import (
    AssistantAgentConfig,
)

print("Testing IBM watsonx Orchestrate Agent API...")

# Try creating an AssistantAgent
try:
    agent_spec = {
        "name": "gmail_agent",
        "description": "Handles email operations via Gmail API",
        "kind": AgentKind.ASSISTANT,
        "title": "Gmail Agent",
        "nickname": "gmail_agent",
        "config": AssistantAgentConfig(
            description="Specialized agent for email sending and management",
        ),
    }
    
    agent = AssistantAgent(**agent_spec)
    print("✓ Successfully created AssistantAgent!")
    print(f"Agent type: {type(agent)}")
    
    # Check available methods
    print("\nAssistantAgent methods:")
    methods = [x for x in dir(agent) if not x.startswith('_')]
    print(methods)
    
except Exception as e:
    print(f"✗ Error creating agent: {e}")
    import traceback
    traceback.print_exc()
