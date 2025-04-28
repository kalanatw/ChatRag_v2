"""
This script sets up a Django view to process user queries using an intelligent assistant (based on OpenAI's GPT-4 model) to determine the appropriate action or data retrieval required. 
The assistant identifies whether the query pertains to sensors, actions, or documents and returns a JSON structure indicating the next steps.

Author: Chethiya Galkaduwa
"""

from django.http import JsonResponse
from rest_framework.decorators import api_view
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os, json
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    model_kwargs={"response_format": {"type": "json_object"}},
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

# LLM Chain
chain = prompt | llm

@api_view(['POST'])
def api_decision(request):
    user_query = request.data.get('query')
    if not user_query:
        return JsonResponse({'error': 'No query provided'}, status=400)

    response = chain.invoke({"input": user_query})
        
    return JsonResponse(response.content, safe=False) 

