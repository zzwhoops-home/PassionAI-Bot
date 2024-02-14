from dotenv import load_dotenv
import os
from pinecone import Pinecone
from openai import OpenAI

# api key for pinecone, load dotenv first
load_dotenv()
pc_api_key = os.getenv('PINECONE_KEY_SERVERLESS')
openai_api_key = os.getenv('OPENAI_KEY')

# create openai client
client = OpenAI(api_key=openai_api_key)
# load pinecone instance
pinecone_client = Pinecone(api_key=pc_api_key)

# get correct 'collection' - SERVERLESS now
pai_index = pinecone_client.Index("passion-ai-db-serverless")

# testing embeddings if necessary
q_embeddings = client.embeddings.create(input="I have high curiosity, family, status, acceptance, power passions, Is Cheng Kung University Taiwan Engineering School suitable college for me?", model='text-embedding-3-small', dimensions=1536)
q_embeddings_dict = q_embeddings.model_dump()
embeddings = q_embeddings_dict['data'][0]['embedding']
# print(embeddings)

res = pai_index.query(vector=embeddings, top_k=4, include_metadata=True)
for i in res['matches']:
    print(i['score'])