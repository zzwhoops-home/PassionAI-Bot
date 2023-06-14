import nextcord
from nextcord.ext import commands

import json
import os

from dotenv import load_dotenv
import openai

import pandas as pd
# import matplotlib.pyplot as plt
# import plotly.express as px
# from scipy import spatial
from sklearn.decomposition import PCA
import numpy as np
from openai.embeddings_utils import distances_from_embeddings
import json

openai.api_key = os.environ['openai']

# convert to numpy arrays
df = pd.read_csv("processed/embeddings.csv", index_col=0)
df['embeddings'] = df['embeddings'].apply(eval).apply(np.array)

df.head()

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # load API key from env
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_KEY')

    @commands.command(name="chatbase", aliases=["cbm", "chb"])
    async def chat_base_model(self, ctx, *message: str):
        length = -1
        for word in message:
            length += len(word) + 1
        if (length == -1):
            await ctx.channel.send(f"{ctx.author.mention} Please enter something you want to ask me.")
            return
        if (length > 200):
            await ctx.channel.send(f"{ctx.author.mention} Hey, try to keep your requests under 200 characters.")
            return

        max_tokens = 150
        prompt = "You are a friendly chatbot.\n"

        # customize response
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"{prompt} {message}",
            temperature=0,
            max_tokens=max_tokens
        )
        
        # convert to json, extract text with no new lines
        response_json = json.loads(str((response)))
        text = response_json['choices'][0]['text'].strip()

        embed = nextcord.Embed(description=text)

        await ctx.channel.send(f"{ctx.author.mention}", embed=embed)

        usage = int(response_json['usage']['total_tokens'])
        
        # warn user if AI response may be cut off
        if (usage >= max_tokens):
            await ctx.channel.send(f"{ctx.author.mention} Hey, this response may be cut off due to API limitations!")
            return

    @commands.command(name="chat", aliases=["ch"])
    async def embeddings_model(self, ctx, *question: str):
        messages = ""

        length = -1
        max_len = 1024
        model="gpt-3.5-turbo"
        max_tokens=512
        stop_sequence=None

        for word in question:
            length += len(word) + 1
        if (length == -1):
            await ctx.channel.send(f"{ctx.author.mention} Please enter something you want to ask me.")
            return
        if (length > 300):
            await ctx.channel.send(f"{ctx.author.mention} Hey, try to keep your requests under 300 characters.")
            return
        
        response = self.ask_question_v35(df, question=question)
        if context == None:
            context = self.create_context(question, df, max_len, size="ada")
            messages.extend([{
            "role": "assistant",
            "content": context
            }, {
            "role": "user",
            "content": question
            }])
        else:
            messages.append({"role": "user", "content": question})
        temperature = 1.0

        print(f"Temperature: {temperature}\n")
        print(messages)
        try:
            response = openai.ChatCompletion.create(model=model,
                                                    messages=messages,
                                                    temperature=temperature,
                                                    max_tokens=max_tokens,
                                                    top_p=1,
                                                    frequency_penalty=0,
                                                    presence_penalty=0,
                                                    stop=stop_sequence)

            # convert to json, extract text with no new lines
            response_json = json.loads(str((response)))
            text = response_json['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(e)
            await ctx.channel.send("An error occurred. Please let Zach know.")

    def create_context(self, question, df, max_len=1024, size="ada"):
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
            cur_len += row["token_ct"] + 4

            if cur_len > max_len:
                break

            results.append(row["text"])

        # print embeddings used
        print("\n\n###\n\n".join(results))
        return "\n\n###\n\n".join(results)


"""
    def ask_question_v3(self,
                        df,
                        question="",
                        model="text-davinci-003",
                        max_len=1024,
                        size="ada",
                        max_tokens=256,
                        stop_sequence=None):
        context = self.create_context(question, df, max_len, size=size)

        temperature = 0.9
        print(f"Temperature: {temperature}\n")
        try:
            response = openai.Completion.create(
            prompt=
            f"Answer the question based on the context below, and always attempt to synthesize the context into a unique personality. Always attempt to answer the question AND PRIORITIZE using the context, however you may draw from prior knowledge as well. There are five tiers: low, medium-low, neutral, medium-high, and high, which represent how strongly a passion affects a person's personality. Any tier below 'neutral' should be treated as if the passion were the opposite.\n\nContext: {context}\n\n---\n\nQuestion: {question}\nAnswer:",
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop_sequence)
            return (response["choices"][0]["text"].strip())

            response = openai.Completion.create(
            prompt=
            f"Answer the question based on the current knowledge that you have.\n\nQuestion: {question}\nAnswer:",
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop_sequence)
            print(response["choices"][0]["text"].strip())
            # return response["choices"][0]["text"].strip()
        except Exception as e:
            print(e)
            return ""

        return ""


        messages = [{
        "role":
        "system",
        "content":
        "Answer as a chatbot, and be simple, trustworthy, and genuine in  your responses."
        }, {
        "role":
        "user",
        "content":
        "Answer the question based on the information provided, and always attempt to synthesize the information into a unique personality. Always attempt to answer the question AND PRIORITIZE using the information given, however you may draw from prior knowledge as well. There are five tiers: low, medium-low, neutral, medium-high, and high, which represent how strongly a passion affects a person's personality. Any tier below 'neutral' should be treated as if the passion were the opposite."
        }]
        context = None


    def ask_question_v35(self,
                     df,
                     question="",
                     model="gpt-3.5-turbo",
                     max_len=1024,
                     size="ada",
                     max_tokens=512,
                     stop_sequence=None):
        global context
        global messages
        if context == None:
            context = self.create_context(question, df, max_len, size=size)
            messages.extend([{
            "role": "assistant",
            "content": context
            }, {
            "role": "user",
            "content": question
            }])
        else:
            messages.append({"role": "user", "content": question})
        temperature = 1.0

        print(f"Temperature: {temperature}\n")
        print(messages)
        try:
            response = openai.ChatCompletion.create(model=model,
                                                    messages=messages,
                                                    temperature=temperature,
                                                    max_tokens=max_tokens,
                                                    top_p=1,
                                                    frequency_penalty=0,
                                                    presence_penalty=0,
                                                    stop=stop_sequence)

            # convert to json, extract text with no new lines
            response_json = json.loads(str((response)))
            text = response_json['choices'][0]['message']['content'].strip()
            return text
        except Exception as e:
            print(e)
            return ""

        return ""
"""