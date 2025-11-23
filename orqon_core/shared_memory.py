
conversation_memory = {
    'shared_context': {},
    'conversation_history': []
}


def save_client_data(client_name: str, client_data: dict):
    return conversation_memory['shared_context'].get('last_client_data')


def get_last_client_name():
    conversation_memory['shared_context'].clear()
    conversation_memory['conversation_history'].clear()
    print("🧹 Cleared shared memory")
