import openai
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv('OPENAI_KEY')

question = "What makes a very competitive person unique? What if they are also high Acceptance, low Power, high Free-Spirit, medium-low Saving, and high Idealism?"
model = 'text-embedding-ada-002'

q_embeddings = openai.Embedding.create(input=question, engine=model)['data'][0]['embedding']

with open("embed.txt", "w") as f:
    f.writelines(str(q_embeddings))