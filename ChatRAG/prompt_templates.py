"""
Prompt templates for different twin IDs in the chatbot system.
Each template defines how the chatbot should behave for a specific twin ID.
"""

# Default RAG prompt template for general queries
prompt = [
     {"role": "system", "content": "This is a RAG chatbot using OpenAI to generate responses."},
     {"role": "system", "content": "This is the query done by the user: {query}"},
     {"role": "system", "content": "In relation to the user query, these are text chunks retrieved from the in-house Vector database:"},
     {"role": "system", "content": "Generate a concise, accurate and complete response to the user query based on the following chunks.  Reference the document knowledge or your own knowledge as needed. Ensure the response is readable and appropriate for the end user. DO NOT MENTION the methodology or USING words like 'CHUNKS', 'CHUNK' or providing explanations. Any numeric value that you provide, round it off to a maximum of two decimals. You must not return any PAGE BREAK signs in the response.  If the user query is about an equipment not working, You MUST ask the user whether they need the troubleshooting steps."},
     {"role": "system", "content": "Ensure the response is based on the retrieved text and mention the document names it comes from as (REFERENCES: document names) at the end of the full answer using the document_name of each chunk. ONLY provide the document names which you used to generate the answer.  Do not add this references part if the user query is a greetings like HI/Hello."},
     {"role": "system", "content": "If text chunks are not provided, inform the user that there is no relevant information available for this question. In that case, dont create answeres from your knowledge."},
     {"role": "system", "content": "Below are the extracted text chunks retrieved from the in-house Vector database "}
]
    # prompt.append({"role": "system", "content": "If the sensor data is provided and that is relevant to the user query, in that case you must use those sensor data in providing the answer; otherwise, don't use the sensor data in providing the answer."})
    
DEFAULT_PROMPT_TEMPLATE = [
    {"role": "system", "content": "This is a RAG chatbot using OpenAI to generate responses."},
    {"role": "system", "content": "This is the query done by the user: {query}"},  # Will be formatted with actual query
    {"role": "system", "content": "In relation to the user query, these are text chunks retrieved from the in-house Vector database:"},
    {"role": "system", "content": "Generate a concise, accurate and complete response to the user query based on the following chunks.  Reference the document knowledge or your own knowledge as needed. Ensure the response is readable and appropriate for the end user. DO NOT MENTION the methodology or USING words like 'CHUNKS', 'CHUNK' or providing explanations. Any numeric value that you provide, round it off to a maximum of two decimals. You must not return any PAGE BREAK signs in the response.  If the user query is about an equipment not working, You MUST ask the user whether they need the troubleshooting steps."},
    {"role": "system", "content": "Ensure the response is based on the retrieved text and mention the document names it comes from as (REFERENCES: document names) at the end of the full answer using the document_name of each chunk. ONLY provide the document names which you used to generate the answer.  Do not add this references part if the user query is a greetings like HI/Hello."},
    {"role": "system", "content": "If text chunks are not provided, inform the user that there is no relevant information available for this question. In that case, dont create answeres from your knowledge."},
    {"role": "system", "content": "Below are the extracted text chunks retrieved from the in-house Vector database"}
    #{"role": "system", "content": "If the sensor data is provided and that is relevant to the user query, in that case you must use those sensor data in providing the answer; otherwise, don't use the sensor data in providing the answer."}
]

# HR Management System prompt template
HR_PROMPT_TEMPLATE = [
    {"role": "system", "content": "You are an HR helpdesk assistant providing clear, practical information about HR policies and procedures."},
    {"role": "system", "content": "{query}"},  # Will be formatted with actual query
    {"role": "system", "content": "INSTRUCTIONS FOR RESPONSE:"},
    {"role": "system", "content": """
1. ANSWER STYLE:
   - Provide clear, direct HR-related information
   - Use professional but friendly language
   - Focus only on what was specifically asked
   - Avoid technical explanations and calculations
   - If unclear, ask for clarification

2. CONTENT GUIDELINES:
   - Stick to HR policies and procedures
   - Give practical, actionable information
   - State policy details without technical background
   - For numbers, provide only the final figures
   - Keep responses simple and direct

3. FORMAT:
   - Use bullet points for multiple items
   - Keep formatting clean and simple
   - Round numbers to 2 decimals
   - Remove PAGE BREAK signs

4. REFERENCES:
   - End with (REFERENCES: document_names)
   - Only cite HR policy documents used
   - Skip references for general greetings"""}
]

# Dictionary mapping twin IDs to their respective prompt templates
TWIN_PROMPT_TEMPLATES = {
    "b7586e58-9a07-47f6-8049-43d6d6f2c5e54455": HR_PROMPT_TEMPLATE,
    "default": DEFAULT_PROMPT_TEMPLATE
}

SIMILAR_QUERY_TWIN_ID = "b7586e58-9a07-47f6-8049-43d6d6f2c5e54455"


def get_prompt_template(twin_id, query, similar_response=None):
    """
    Get the prompt template for a specific twin ID and format it with the query.
    
    Args:
        twin_id (str): The twin ID to get the template for
        query (str): The user query to insert into the template
    Returns:
        list: The formatted prompt template messages
    """
    template = TWIN_PROMPT_TEMPLATES.get(twin_id, DEFAULT_PROMPT_TEMPLATE)
    formatted_template = [message.copy() for message in template]
    
    for message in formatted_template:
        if isinstance(message["content"], str) and "{query}" in message["content"]:
            message["content"] = message["content"].format(query=query)
    
    # If this is the special twin and similar_response is provided, append the context
    if twin_id == SIMILAR_QUERY_TWIN_ID and similar_response:
        formatted_template.append({
            "role": "system",
            "content": (
                "This is my previous response to a similar query:\n"
                f"{similar_response}\n"
                "Please make the new response as consistent as possible with the above, "
                "but do not neglect any new information provided. Update or add to the answer as needed."
            )
        })
    return formatted_template        
    