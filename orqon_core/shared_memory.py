
conversation_memory = {
    'shared_context': {},
    'conversation_history': []
}


def save_client_data(client_name: str, client_data: dict):
    """Save client data to shared memory"""
    conversation_memory['shared_context']['last_client_data'] = client_data
    conversation_memory['shared_context']['last_client_name'] = client_name
    print(f"💾 Saved {client_name} to shared memory")
    return client_data


def get_last_client_data():
    """Get last client data from shared memory"""
    return conversation_memory['shared_context'].get('last_client_data')


def get_last_client_name():
    """Get last client name from shared memory"""
    return conversation_memory['shared_context'].get('last_client_name')


def clear_memory():
    """Clear all shared memory"""
    conversation_memory['shared_context'].clear()
    conversation_memory['conversation_history'].clear()
    print("🧹 Cleared shared memory")
