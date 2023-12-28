import openai
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv('OPENAI_KEY')

question = "What makes someone who is high Acceptance, medium Vengeance, and low Confidence unique?"
model = 'text-embedding-ada-002'

q_embeddings = openai.Embedding.create(input=question, engine=model)['data'][0]['embedding']

print(q_embeddings)