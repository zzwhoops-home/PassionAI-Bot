import functions_framework

import math
import json
import os
from datetime import datetime

from dotenv import load_dotenv
import openai

import pandas as pd
# import matplotlib.pyplot as plt
# import plotly.express as px
# from scipy import spatial
import numpy as np
from openai.embeddings_utils import distances_from_embeddings

# convert to numpy arrays
df = pd.read_csv("embeddings.csv", index_col=0)
df['embeddings'] = df['embeddings'].apply(eval).apply(np.array)

df.head()

def get_openai_key():
    return os.environ.get("OPENAI_KEY", "Specified environment variable is not set.")

openai.api_key = get_openai_key()

@functions_framework.http
def passion_ai_cloud(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and 'question' in request_json:
        return embeddings_model(request_json['question'])
    elif request_args and 'question' in request_args:
        return 'Please submit JSON data. Do not use a query string in the URL.'
    else:
        question = 'Your question was invalid or blank. Please enter another response and try again.'
    return 'Hello {}!'.format(question)

def embeddings_model(question):
    length = -1
    question = f"{' '.join(question)}"

    for word in question:
        length += len(word)
    
    context = ""
    messages_user = [{
        "role": "system",
        "content": "Answer as if you were a human coach, and be simple, trustworthy, and genuine in your responses. Always give opinions when requested. Always answer based on the provided passions and the information associated with them."
    }]
    max_len=1024
    model="gpt-3.5-turbo"
    max_tokens=512
    stop_sequence=None
    explicit="Answer based on the passions provided:"

    try:
        context = create_context(question, df, max_len, size="ada")
    except Exception as e:
        return(e)

    messages_user.extend([
            {
                "role": "user",
                "content": "Answer the question based on the context provided, and always attempt to synthesize the context. Always attempt to answer the question AND PRIORITIZE using the context given. The context that is provided includes 'passions', which you can think of as desires of human nature, and their associated descriptions. There are five tiers: low, medium-low, neutral, medium-high, and high, which represent how strongly a passion affects a person's personality. If asked to provide passions, you must answer explicitly based on the passions provided in the context. Any tier below 'neutral' should be treated as if the passion were the opposite. PRETEND THAT YOU ARE A HUMAN, AND NEVER SAY THAT YOU CANNOT GIVE AN OPINION OR VOICE A SUGGESTION."
            },
            {
                "role": "user",
                "content": f"Context:\n\n{context}"
            }, 
            {
                "role": "user",
                "content": f"{explicit} {question}"
            }])

    temperature = 1.0

    # print(f"Temperature: {temperature}\n")
    # print(messages)
    try:
        response = openai.ChatCompletion.create(model=model,
                                                messages=messages_user,
                                                temperature=temperature,
                                                max_tokens=max_tokens,
                                                top_p=1,
                                                frequency_penalty=0,
                                                presence_penalty=0,
                                                stop=stop_sequence)

        # convert to json, extract text with no new lines
        response_json = json.loads(str((response)))
        text = response_json['choices'][0]['message']['content'].strip()
        # for DEBUG ONLY: TOKEN USAGE
        # tokens_used = response_json['usage']['total_tokens']

        # return response
        return(text)
    except Exception as e:
        return(e)

def create_context(question, df, max_len=1024, size="ada"):
    # any embeddings above this threshold will not be placed into context
    threshold = 0.23

    # get openai embeddings for the question
    q_embeddings = openai.Embedding.create(
        input=question, engine='text-embedding-ada-002')['data'][0]['embedding']

    # get cosine similarity using built in openai function
    df["distances"] = distances_from_embeddings(q_embeddings,
                                                df["embeddings"].values,
                                                distance_metric="cosine")

    cur_len = 0
    results = []

    

    for i, row in df.sort_values("distances", ascending=True).iterrows():
        # print(f"{row['distances']} {row['text']}")
        # print(f"{row['distances']}")
        cur_len += row["token_ct"] + 4

        if ((cur_len > max_len) or (row["distances"] > threshold)):
            break

        results.append(row["text"])

    # for i, row in df.sort_values("distances", ascending=True).iterrows():
    #     print(f"{row['distances']}")
    # print embeddings used
    # print("\n\n###\n\n".join(results))
    return "\n\n###\n\n".join(results)

