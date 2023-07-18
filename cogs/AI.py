import nextcord
from nextcord.ext import commands

import math
import json
import os
import asyncio
from datetime import datetime

from dotenv import load_dotenv
import openai

import pandas as pd
# import matplotlib.pyplot as plt
# import plotly.express as px
# from scipy import spatial
import numpy as np
from openai.embeddings_utils import distances_from_embeddings

import pymongo

openai.api_key = os.getenv('OPENAI_KEY')

# read numpy converted embeddings dataframe
df = pd.read_csv("processed/embeddings.csv", index_col=0)
# Convert the "embeddings" column to NumPy arrays
df['embeddings'] = df['embeddings'].apply(eval).apply(np.array)

# dictionary to ensure users are not already in a chat session
chat_sessions = {}

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

    # class MyView(nextcord.ui.View):
    #     @nextcord.ui.select(
    #         placeholder = "Please provide your feedback!",
    #         min_values = 1,
    #         max_values = 1,
    #         options = [
    #             nextcord.SelectOption(
    #                 label="Vanilla",
    #                 description="Pick this if you like vanilla!"
    #             ),
    #             nextcord.SelectOption(
    #                 label="Chocolate",
    #                 description="Pick this if you like chocolate!"
    #             ),
    #             nextcord.SelectOption(
    #                 label="Strawberry",
    #                 description="Pick this if you like strawberry!"
    #             )
    #         ]
    #     )
    #     async def select_callback(self, select, interaction): # the function called when the user is done selecting options
    #         await interaction.response.send_message(f"{select.values[0]} yeah buddy")

    async def embeddings_model(self, ctx, question, store_db=False):
        if (ctx.channel.category.id != 1074104279473852546):
            await ctx.channel.send("Please send your messages under any of the AI channels only.")
            return

        if (ctx.author.id in chat_sessions):
            if (chat_sessions[ctx.author.id]):
                await ctx.channel.send(f"{ctx.author.mention}, you are already in an active chat instance. Please type **'end'** or **'q'** to end your current chat instance.")
                return

        length = -1
        question = f"{' '.join(question)}"

        for word in question:
            length += len(word)
        if (length == -1):
            await ctx.channel.send(f"{ctx.author.mention}, please ping me with the first question you want to ask.\nI.e. '@PQBot what makes a high vengeance, acceptance, power person unique?'")
            return
        if (length > 1500):
            await ctx.channel.send(f"{ctx.author.mention}, hey, try to keep your requests under 1500 characters.")
            return

        chat_sessions[ctx.author.id] = True
        
        context = ""
        messages_ai = [{
            "role": "system",
            "content": "Answer as if you were a human coach, and be simple, trustworthy, and genuine in your responses. Always give opinions when requested. Always answer based on the provided passions and the information associated with them."
        }]
        max_len=1500
        model="gpt-3.5-turbo"
        max_tokens=512
        stop_sequence=None
        # try several different 'explicit' messages, like 'Answer based on the passions provided:', 'Based on my passions, ', etc...
        explicit="Based on these passions, "

        await ctx.channel.send(f"{ctx.author.mention}, you are now starting a chat instance. Please note that embeddings will only be generated for the question __**you included with the command.**__\nBe sure to list all of the passions you want to include after the mention. If you mention the bot again, more embeddings will be generated (WIP)\n**To end the chat instance**, send **'end'** or the letter **'q'**.")
        
        try:
            context = self.create_context(question, df, max_len, size="ada")
        except Exception as e:
            print(e)
            await ctx.channel.send(f"Error: {e.message}. Please try again, this error may happen after a long period with no API activity.")

        messages_ai.extend([
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
        
        # make a copy of messages to store in DB
        messages_user = messages_ai[:]

        while True:
            async def end_chat():
                msg_max_len = 4000
                # Get the current date and time
                current_datetime = datetime.now()

                await ctx.channel.send(f"{ctx.author.mention}, ending chat instance...")
                chat_sessions[ctx.author.id] = False

                cur_text = ""
                # format for storing in database
                to_database_ai = []
                to_database_user = []
                if (store_db):
                    to_database_ai = [{
                        "role": "system",
                        "content": messages_ai[0]['content']
                    },
                    {
                        "role": "user",
                        "content": messages_ai[1]['content']
                    }]
                    # duplicate array
                    to_database_user = to_database_ai[:]

                for m in range(len(messages_ai) - 3):
                    # get after system message and embeddings message
                    block = messages_ai[m + 3]
                    role = block['role']
                    content = block['content']
                    if (store_db):
                        to_database_ai.append({
                            "role": role,
                            "content": content
                        })

                for m in range(len(messages_user) - 3):
                    # get after system message and embeddings message
                    block = messages_user[m + 3]
                    role = block['role']
                    content = block['content']
                    cur_text += f"{role.capitalize()}: {content}\n"
                    if (store_db):
                        to_database_user.append({
                            "role": role,
                            "content": content
                        })

                story = []
                # ensure each embed doesn't exceed character limit
                for i in range(math.ceil(len(cur_text) / msg_max_len)):
                    story.append(cur_text[0:msg_max_len])
                    cur_text = cur_text[msg_max_len:]

                for i in range(len(story)):
                    embed = nextcord.Embed(title=f"Your finished chat log (Part **{i + 1}** of **{len(story)}**):", description=f"{story[i]}")
                    await ctx.channel.send(f"{ctx.author.mention}", embed=embed)

                if (store_db):
                    # get current id
                    id = (await self.counter())['count']
                    data = {
                        'id': id,
                        'datetime': current_datetime,
                        'user_id': ctx.author.id,
                        'username': ctx.author.name,
                        'discriminator': ctx.author.discriminator,
                        'chat_log_ai': to_database_ai,
                        'chat_log_user': to_database_user
                    }
                    self.bot.chat_history.insert_one(data)
                return
            
            placeholder = await ctx.channel.send("https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExMjU4ZW9tcHhpeWQ0dGZpYnprNTc4ODgzdm40ZzFwa256MWFyZGhsdCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/uBt1p1imV3MExnFoQs/giphy.gif")
            temperature = 1.0

            # print(f"Temperature: {temperature}\n")
            # print(messages)

            try:
                response = None
                async with ctx.channel.typing():
                    response = openai.ChatCompletion.create(model=model,
                                                            messages=messages_ai,
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
                    tokens_used = response_json['usage']['total_tokens']
                    await ctx.channel.send(f"**TOKEN USAGE**: {tokens_used}/4096")
                    # add to conversation history
                    summarized_text = await self.summarize(text)
                    messages_ai.append({"role": "assistant", "content": summarized_text})
                    messages_user.append({"role": "assistant", "content": text})
                    # cheap fix for doubling character limit (splits into two messages if exceeding limit)
                    if (len(text) > 1950):
                        text_one = text[0:1950]
                        text_two = text[1950:]
                        await placeholder.edit(content=f"{ctx.author.mention}, {text_one}")
                        await ctx.channel.send(f"{ctx.author.mention}, {text_two}")
                    else:
                        await placeholder.edit(content=f"{ctx.author.mention}, {text}")
            except Exception as e:
                print(e)
                await ctx.channel.send(f"{ctx.author.mention} An error occurred. Please let Zach know.\nEnding chat...")
                await end_chat()
                return
            
            def check(m):
                return m.channel == ctx.channel and m.author.id != self.bot.user.id and not m.content.startswith("pq!") and m.author.id == ctx.author.id
            try:
                message = await self.bot.wait_for('message', timeout=600.0, check=check)
                # make answering based on passions explicitly stated
                text = (message.content).strip()
                text_explicit_passions = f"{explicit} {text}"

                # end chat if user sends "q" or "end"
                if (text.lower() == "q" or text.lower() == "end"):
                    await end_chat()
                    return
                # add to conversation history
                messages_ai.append({"role": "user", "content": text_explicit_passions})
                messages_user.append({"role": "user", "content": text})
            except asyncio.TimeoutError:
                await ctx.channel.send(f"{ctx.author.mention}, You took over 10 minutes to write a response.")
                await end_chat()
                return

    @commands.command(name="chat", aliases=["ch"])
    async def chat_embeddings(self, ctx, *question: str):
        await self.embeddings_model(ctx=ctx, question=question, store_db=True)
        return

    @commands.command(name="chatnodb", aliases=["chndb"])
    @commands.has_permissions(administrator=True)
    async def chat_embeddings_no_db(self, ctx, *question: str):
        await self.embeddings_model(ctx=ctx, question=question, store_db=False)
        return

    async def summarize(self, text):
        model="gpt-3.5-turbo"
        max_tokens=512
        stop_sequence=None
        prompt="Please summarize this in at most, two sentences: "

        messages = [{
            "role": "system",
            "content": "Always attempt to summarize. If unable, do not respond with anything."
        }, 
        {
            "role": "user",
            "content": f"{prompt}{text}"
        }]
        
        response = openai.ChatCompletion.create(model=model,
                                                messages=messages,
                                                temperature=0.0,
                                                max_tokens=max_tokens,
                                                top_p=1,
                                                frequency_penalty=0,
                                                presence_penalty=0,
                                                stop=stop_sequence)

        # convert to json, extract text with no new lines
        response_json = json.loads(str((response)))
        response_text = response_json['choices'][0]['message']['content'].strip()
        print(response_text)
        return response_text

    async def counter(self):
        filter = {}
        data = {
            "$inc": {
                "count": 1
            }
        }
        data = self.bot.counter.find_one_and_update(filter=filter, update=data, return_document=pymongo.ReturnDocument.BEFORE)
        return data

    def create_context(self, question, df, max_len=1500, size="ada"):
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

def setup(bot):
    bot.add_cog(AI(bot))