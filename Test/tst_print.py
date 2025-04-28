import openai, os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in .env file")

openai.api_key = OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

text = 'Is the butterfly valve still exempt in 2023?'

response = client.embeddings.create( model="text-embedding-3-small", input=text)

print(response.data[0].embedding)

