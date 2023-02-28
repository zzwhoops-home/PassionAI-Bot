import nextcord
from nextcord.ext import commands

import json
import os

from dotenv import load_dotenv
import openai

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # load API key from env
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_KEY')

    @commands.command(name="chat", aliases=["cbm", "ch"])
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

    @commands.command(name="chattm", aliases=["ctm"])
    async def chat_trained_model(self, ctx, *message: str):
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

