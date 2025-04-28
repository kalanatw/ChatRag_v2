from dotenv import load_dotenv
load_dotenv()
import json
import requests

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(
    model="gpt-3.5-turbo-1106",
    temperature=0.7,
    model_kwargs={"response_format": {"type": "json_object"}}
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """
        You are an intelligent assistant designed to process user queries and determine the appropriate action or data retrieval required. Your task is to parse the user's query and identify whether it pertains to sensors, documents, or specific actions. Based on this, you will return a JSON structure indicating the next steps.

        1. **Sensor API**: If the user query mentions any sensor names, return the query and the sensor name(s) in a JSON structure.
        2. **Action API**: If the user query mentions any specific action, return the action in a JSON structure. Recognized actions include:
            - "open waypoint": open_waypoint
            - "open markup": open_markup
            - "open sensors": open_sensors
            - "open sun study": open_sun_study
            - "exit": exit
        3. **Document API**: If the query does not mention a sensor or a specific action, return the original user query.

        Below is the format for your response based on the identified criteria:

        - **Sensor Query JSON Structure:**
              "type": "sensor_query",
              "query": "{{query}}",
              "sensors": ["<sensor_name_1>", "<sensor_name_2>", ...]

        - **Action Query JSON Structure:**
              "type": "action_query",
              "action": "<identified_action>"


        - **Original Query JSON Structure:**
              "type": "document_query",
              "query": "{{query}}"


        Process the user query accordingly and return the appropriate JSON structure.
        """),
        ("human", "{input}")
    ]
)

def call_endpoint(response_content):
    response_data = json.loads(response_content)
    
    if response_data['type'] == 'document_query':
        print('sending request to document endpoint')
        endpoint = "http://localhost:8000/core/api/document-response/"
        payload = {'query': response_data['query']}
        response = requests.post(endpoint, json=payload)
        return response.json()
    elif response_data['type'] == 'sensor_query':
        print('sending request to sensor endpoint')
        endpoint = "http://localhost:8000/core/api/sensor-response/"
        payload = {
            'query': response_data['query'],
            'sensors': response_data['sensors']
        }
        response = requests.post(endpoint, json=payload)
        return response.json()
    elif response_data['type'] == 'action_query':
        print('sending request to action endpoint')
    else:
        return {"error": "Unknown query type"}


# LLM Chain
chain = prompt | llm

user_query = "Is the butterfly valve still exempt in 2023?"
response = chain.invoke({"input": user_query})
result = call_endpoint(response.content)
print(result)

