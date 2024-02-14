import pandas as pd
from dotenv import load_dotenv
import os
from pinecone import Pinecone
from openai import OpenAI
import time

# read numpy converted embeddings dataframe
df = pd.read_csv("../processed/embeddings.csv", index_col=0)

data = df["text"]

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

count = 0
vectors = []
for embed in data:
    count += 1
    print(f"Count: {count}")

    embedding_response = client.embeddings.create(input=embed, model='text-embedding-3-small', dimensions=1536)
    embedding_response_dict = embedding_response.model_dump()
    
    embedding = embedding_response_dict['data'][0]['embedding']
    token_usage = embedding_response_dict['usage']['total_tokens']

    vectors.append({
        'id': str(count),
        'values': embedding,
        'metadata': {
            'token_ct': token_usage,
            'text': embed
        }
    })

# upsert vectors
pai_index.upsert(vectors=vectors)