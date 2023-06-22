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

bot.load_extension("cogs.Listeners")
bot.load_extension("cogs.AI")

@bot.command(name="reloadall", aliases=["ra"])
@commands.has_permissions(administrator=True)
async def reload_all(ctx):
    bot.reload_extension("cogs.Listeners")
    bot.reload_extension("cogs.AI")
    await ctx.channel.send("Reloaded all modules!")

@bot.command(name="reloadlisteners", aliases=["rl"])
@commands.has_permissions(administrator=True)
async def reload_listeners(ctx):
    bot.reload_extension("cogs.Listeners")
    await ctx.channel.send("Reloaded listeners module **only**.")

@bot.command(name="reloadai", aliases=["rai"])
@commands.has_permissions(administrator=True)
async def reload_ai(ctx):
    bot.reload_extension("cogs.AI")
    await ctx.channel.send("Reloaded AI module **only**.")

@bot.command(name="clear")
@commands.has_permissions(administrator=True)
async def clear(ctx, num=1):
    try:
        num = int(num)
    except Exception as e:
        await ctx.channel.send("Please enter a valid number.")
        return
    
    if (num > 100):
        await ctx.channel.send("Please enter a number between 1 and 100.")
        return

    # clear # messages + user message
    await ctx.channel.purge(limit=num+1)
    num_cleared = await ctx.channel.send(f"I have cleared **{num}** messages!")
    await asyncio.sleep(3)
    await num_cleared.delete()



# @bot.command(name="thing")
# @commands.has_permissions(administrator=True)
# async def thing(ctx):
#     bot.chat_history.update_many({}, {"$rename": {"chat_log_ai" : "chat_log_user"}})



bot.run(TOKEN)
