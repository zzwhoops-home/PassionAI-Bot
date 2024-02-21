import nextcord
from nextcord.ext import commands

import pymongo
from pinecone import Pinecone

import asyncio
import os
import requests
import math

from dotenv import load_dotenv

# load env variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MONGO_USER = os.getenv('USER')
MONGO_PWD = os.getenv('PWD')
PC_API_KEY = os.getenv('PINECONE_KEY_SERVERLESS')

intents = nextcord.Intents.all()
prefix = "pq!"

class PQBot(commands.Bot):
    def __init__(self, case_insensitive, command_prefix, intents):
        super().__init__(case_insensitive=case_insensitive, command_prefix=command_prefix, intents=intents)
     
# config bot
bot = PQBot(True, command_prefix=prefix, intents=intents)
# for accessing prefix in other code
bot.prefix = prefix

# create connection to mongodb database
client = pymongo.MongoClient(f"mongodb+srv://{MONGO_USER}:{MONGO_PWD}@passionaibot.4dwr2me.mongodb.net/?retryWrites=true&w=majority")
db = client['PassionAIDB']

bot.chat_history = db['chat_history']
bot.counter = db['counter']
bot.guilds_setup = db['guilds_setup']
bot.user_list = db['user_list']
bot.admin_list = db['admin_list']

bot.welcome_msg_list = []

# create connection to pinecone database
# load pinecone instance
pinecone_client = Pinecone(api_key=PC_API_KEY)
# get correct 'collection'
bot.pai_index = pinecone_client.Index("passion-ai-db-serverless")

# set embedding score threshold
bot.context_threshold = 0.33

# load cogs
bot.load_extension("cogs.Listeners")
bot.load_extension("cogs.AI_PINECONE")
bot.load_extension("cogs.Setup")
bot.load_extension("cogs.Admin")

@bot.event
async def on_ready():
    """
    Prints a message to tell the user about the servers the bot connects to on startup
    """
    print(f"Logged in: {bot.user.name}")
    print(f"-=-=-=-=-=-=-=-=-")
    print(f"Connected to the following servers:")
    for guild in bot.guilds:
        print(f"Bot joined server {guild.name} with id {guild.id}.")

    await get_welcome_msgs()

async def get_welcome_msgs():
    """
    Called by on_ready - gets welcome messages on bot startup to start listening for reaction clicks
    """
    # projection to only get setup message channel/message ids
    projection = {
        "setup_msg_id": 1
    }

    # get pymongo object
    guild_info = bot.guilds_setup.find(projection=projection)

    # only try if guild_info is not None
    if guild_info:
        try:
            # get IDs of messages only
            for info in guild_info:
                message_id = info['setup_msg_id']
                bot.welcome_msg_list.append(message_id)
        # not sure what exceptions could happen but catch them here
        except Exception as e:
            print(f"An exception occurred when fetching welcome message: {e}")

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

@bot.command(name="forcecreate")
@commands.has_permissions(administrator=True)
async def force_create(ctx):
    await ctx.channel.send(f"Forcing creation of channel for {ctx.member}")

# @bot.command(name="thing")
# @commands.has_permissions(administrator=True)
# async def thing(ctx):
#     bot.chat_history.update_many({}, {"$rename": {"chat_log_ai" : "chat_log_user"}})

bot.run(TOKEN)
