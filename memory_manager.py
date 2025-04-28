# from langchain.memory import ConversationBufferMemory 

# memory_store = {}

# # Function to get or create memory for a specific  chat_instance_id
# def get_memory(chat_instance_id):
#     if  chat_instance_id not in memory_store:
#         memory_store[chat_instance_id] = ConversationBufferMemory(memory_key="chat_history", input_key="query")
#     return memory_store[chat_instance_id]

# # Function to save chat history
# def save_chat_history(chat_instance_id, query, response):
#     memory = get_memory(chat_instance_id)
#     # Save the response as a string
#     memory.save_context({"query": query}, {"response": response})


# # Function to load chat history
# def load_chat_history( chat_instance_id):
#     memory = get_memory( chat_instance_id)
#     return memory.load_memory_variables({})["chat_history"]

# # Function to limit the chat history to a maximum number of items
# def limit_memory( chat_instance_id, max_items=3):
#     memory = get_memory( chat_instance_id)
#     history = memory.load_memory_variables({})["chat_history"]
#     if len(history) > max_items:
#         memory.chat_memory.messages = memory.chat_memory.messages[-max_items:]

# # Example usage of the limit function
# def save_and_limit_chat_history( chat_instance_id, query, response, max_items=2):
#     save_chat_history( chat_instance_id, query, response)
#     limit_memory( chat_instance_id, max_items)

from langchain.memory import ConversationBufferMemory 

memory_store = {}

# Function to get or create memory for a specific  chat_instance_id
def get_memory(chat_instance_id):
    if  chat_instance_id not in memory_store:
        memory_store[chat_instance_id] = ConversationBufferMemory(memory_key="chat_history", input_key="query")
    return memory_store[chat_instance_id]

# Function to save chat history
def save_chat_history(chat_instance_id, query, response):
    memory = get_memory(chat_instance_id)
    # Save the response as a string
    memory.save_context({"query": query}, {"response": response})


# Function to load chat history
def load_chat_history( chat_instance_id):
    memory = get_memory( chat_instance_id)
    return memory.load_memory_variables({})["chat_history"]

# Function to limit the chat history to a maximum number of items
def limit_memory( chat_instance_id, max_items=3):
    memory = get_memory( chat_instance_id)
    history = memory.load_memory_variables({})["chat_history"]
    if len(history) > max_items:
        memory.chat_memory.messages = memory.chat_memory.messages[-max_items:]

# Example usage of the limit function
def save_and_limit_chat_history( chat_instance_id, query, response, max_items=2):
    save_chat_history( chat_instance_id, query, response)
    limit_memory( chat_instance_id, max_items)

