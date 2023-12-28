import pandas as pd
from dotenv import load_dotenv
import os
import pinecone

# read numpy converted embeddings dataframe
df = pd.read_csv("../processed/embeddings.csv", index_col=0)

# for vals in df:
#     print(vals)

# api key for pinecone, load dotenv first
load_dotenv()
pc_api_key = os.getenv('PINECONE_KEY')

# load pinecone instance
pinecone.init(api_key=pc_api_key, environment="gcp-starter")
# get correct 'collection'
pai_index = pinecone.Index("passion-ai-db")

# formatter for dataframe
data = []
for column, vals in df.iterrows():
    convert = vals['embeddings'][1:-1].split(", ")
    new = [float(num) for num in convert]

    data.append((str(vals['index']), new, {'token_ct': vals['token_ct'], 'text': vals['text']}))

print(data)

# upsert to pinecone db
pai_index.upsert(data)

# pai_index.upsert([("A", [0.5 for i in range(1536)], {"data": "data"})])

# # def df_to_pinecone_dict(col):
# # columns
# column_filter = ["index", "embeddings", "token_ct"]

# # filter with only columns, orient record style [{}, {}, {}]
# result_dict = df[column_filter].to_dict(orient="records")

