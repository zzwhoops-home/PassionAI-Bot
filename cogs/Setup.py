import nextcord
from nextcord.ext import commands

import os
from openai import OpenAI

import pymongo

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Setup(bot))