import nextcord
from nextcord import PermissionOverwrite
from nextcord.ext import commands

import os
import asyncio

import pymongo

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # for any of the "reload" commands, require that the member has administrator on the server
    # AND that they are in the administrator list
    @commands.command(name="reloadall", aliases=["rall", "ra"])
    @commands.has_permissions(administrator=True)
    async def reload_all(self, ctx):
        self.bot.reload_extension("cogs.Listeners")
        self.bot.reload_extension("cogs.AI_PINECONE")
        self.bot.reload_extension("cogs.Setup")
        self.bot.reload_extension("cogs.Admin")
        await ctx.channel.send("Reloaded all modules!")

    @commands.command(name="reloadlisteners", aliases=["rl"])
    @commands.has_permissions(administrator=True)
    async def reload_listeners(self, ctx):
        self.bot.reload_extension("cogs.Listeners")
        await ctx.channel.send("Reloaded listeners module **only**.")

    @commands.command(name="reloadai", aliases=["rai"])
    @commands.has_permissions(administrator=True)
    async def reload_ai(self, ctx):
        self.bot.reload_extension("cogs.AI_PINECONE")
        await ctx.channel.send("Reloaded AI module **only**.")

    @commands.command(name="reloadsetup", aliases=["rs"])
    @commands.has_permissions(administrator=True)
    async def reload_setup(self, ctx):
        self.bot.reload_extension("cogs.Setup")
        await ctx.channel.send("Reloaded setup module **only**.")
        
    @commands.command(name="reloadadmin", aliases=["rad"])
    @commands.has_permissions(administrator=True)
    async def reload_setup(self, ctx):
        self.bot.reload_extension("cogs.Admin")
        await ctx.channel.send("Reloaded admin module **only**.")

def setup(bot):
    bot.add_cog(Admin(bot))