import nextcord
from nextcord.ext import commands

from cogs.Listeners import Listeners
from cogs.AI import AI

import pymongo
import asyncio

import os
import requests
import math

# load env variables
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
USER = os.getenv('USER')
PWD = os.getenv('PWD')

intents = nextcord.Intents.all()
prefix = "pq!"

class PQBot(commands.Bot):
    def __init__(self, case_insensitive, command_prefix, intents):
        super().__init__(case_insensitive=case_insensitive, command_prefix=command_prefix, intents=intents)
     
# config bot
bot = PQBot(True, command_prefix=prefix, intents=intents)

# create connection to database
client = pymongo.MongoClient(f"mongodb+srv://{USER}:{PWD}@passionaibot.4dwr2me.mongodb.net/?retryWrites=true&w=majority")
# change main to actual database name later
db = client['PassionAIDB']

bot.chat_history = db['chat_history']
bot.counter = db['counter']

def setup(bot):
    bot.add_cog(Listeners(bot))
    bot.add_cog(AI(bot))

setup(bot)
bot.run(TOKEN)
