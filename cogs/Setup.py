import nextcord
from nextcord import PermissionOverwrite
from nextcord.ext import commands

import os
import asyncio
from openai import OpenAI

import pymongo

from datetime import datetime

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx):
        """
        Command that handles the setup of the bot in a new server.
        The bot should have administrator privileges for this to work without issues.
        Args:
            ctx (nextcord.ext.commands.Context): Context
        Returns:
            _type_: _description_
        """
        # delete original command message
        await ctx.message.delete()

        # first check if the server has already setup in a channel
        already_setup = await self.check_already_setup(ctx)
        if (already_setup):
            await ctx.channel.send(f"You have already setup PassionAI in **{ctx.guild.name}**. (WIP) Please use a command to change your setup channel.")
            return

        # tell the user we are setting up in this channel
        setup_msg = await ctx.channel.send(f"{ctx.author.mention} You are now setting up **PassionAI** for **{ctx.guild.name}**. Please follow the prompts to proceed.")

        # get the user to confirm, adding two reactions
        verify_channel_msg = await ctx.channel.send(f"This is channel <#{ctx.channel.id}>. Are you sure you want to use this channel as your setup channel? The channel's permissions will be **irrevocably altered**! It is also advised to set up in a blank channel.")
        await verify_channel_msg.add_reaction("✅")
        await verify_channel_msg.add_reaction("❌")

        async def cancel():
            """
            Within setup: deletes messages used to setup the bot in the channel
            """
            await setup_msg.delete()
            await verify_channel_msg.delete()

        # ensure reaction is valid, and that the reacting user is the author of the setup message
        def check_message(user_response, user):
            return user == ctx.author and str(user_response.emoji) in ["✅", "❌"]
        try:
            user_response, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check_message)
            reaction_str = str(user_response.emoji)

            if reaction_str == "✅":
                await ctx.channel.send(f"Setting up in <#{ctx.channel.id}>...", delete_after=5.0)
                await self.setup_verified(ctx)
            elif reaction_str == "❌":
                await ctx.channel.send(f"Canceling!", delete_after=3.0)
                await cancel()
        except asyncio.TimeoutError:
            await ctx.channel.send(f"{ctx.author.mention} You didn't react in time. Please run the command again.", delete_after=10.0)
            await cancel()
        except Exception as e:
            await ctx.channel.send(f"An error occurred: {e}")
            return
        
    async def check_already_setup(self, ctx):
        """Checks if the server specified in the given context has already gone through the PassionAI setup process
        Args:
            ctx (nextcord.ext.commands.Context): Context
        Returns:
            bool: whether or not the server has already been setup with PassionAI
        """
        # get guild id from context
        guild_id = ctx.guild.id

        # queries DB to find if the guild is already there
        query = {
            "guild_id": guild_id
        }
        result = self.bot.guilds_setup.find_one(query)

        # returns if the document was found (guild was already setup)
        return result is not None

    async def setup_verified(self, ctx):
        """
        Runs after the user verifies that they want to setup the bot in this channel.
        """
        # get default role
        default_role = ctx.guild.default_role

        # remove any channel permission overwrites
        for overwrite in ctx.channel.overwrites:
            await ctx.channel.set_permissions(overwrite, overwrite=None)

        # remove member reaction and message permissions
        permissions = PermissionOverwrite(send_messages=False, add_reactions=False)

        # set permissions for channel
        await ctx.channel.set_permissions(default_role, overwrite=permissions)

        welcome_msg = await ctx.channel.send(f"Welcome to PassionAI! Please click the below reaction to create a private channel for yourself.")
        await welcome_msg.add_reaction("🍊")

        # add to DB
        await self.setup_verified_update_DB(ctx)

    async def setup_verified_update_DB(self, ctx):
        """Once the user finishes setting up in a channel, update our database with the current guild's ID
        Args:
            ctx (nextcord.ext.commands.Context): Context
        """
        # get guild id and name from context
        guild_id = ctx.guild.id
        guild_name = ctx.guild.name

        # we find one and update because we want to make sure we keep the guild's name up to date
        query = {
            "guild_id": guild_id
        }

        # set guild id and timestamp on INSERT only    
        data = {
            "$setOnInsert": {
                "timestamp": datetime.now(),
                "guild_id": guild_id
            },
            "$set": {
                "guild_name": guild_name
            }
        }

        self.bot.guilds_setup.find_one_and_update(filter=query, update=data, upsert=True)

def setup(bot):
    bot.add_cog(Setup(bot))