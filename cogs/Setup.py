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

        async def delete_setup_msgs():
            """
            Within setup: deletes messages used to setup the bot in the channel
            """
            await setup_msg.delete()
            await verify_channel_msg.delete()

        # ensure reaction is valid, and that the reacting user is the author of the setup message, and that the reaction is on the correct message
        def check_message(user_response, user):
            return user == ctx.author and str(user_response.emoji) in ["✅", "❌"] and user_response.message.id == verify_channel_msg.id
        try:
            user_response, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check_message)
            reaction_str = str(user_response.emoji)

            # continue to run function that sets up the server
            if reaction_str == "✅":
                await ctx.channel.send(f"Setting up in <#{ctx.channel.id}>...", delete_after=5.0)
                await delete_setup_msgs()
                await self.setup_verified(ctx)

            elif reaction_str == "❌":
                await ctx.channel.send(f"Canceling!", delete_after=3.0)
                # delete setup messages
                await delete_setup_msgs()
                return
        except asyncio.TimeoutError:
            await ctx.channel.send(f"{ctx.author.mention} You didn't react in time. Please run the command again.", delete_after=10.0)
            # delete setup messages
            await delete_setup_msgs()
            return
        # except Exception as e:
        #     await ctx.channel.send(f"An error occurred: {e}")
        #     return
        
    @commands.command(name="channels")
    @commands.has_permissions(administrator=True)
    async def channel_manager(self, ctx: nextcord.ext.commands.Context, choice: str = "", user: nextcord.Member = None):
        """Command for managing channels:
        - channels add: adds an AI channel for a user if they don't already have one in the server
        - channels remove: removes an AI channel for a user if they don't already have one
        - channels reset: removes, then adds an AI channel
        Args:
            ctx (nextcord.ext.commands.Context): Context
            choice (str, optional): Choice between 'add', 'remove' and 'reset'. Defaults to "".
            user (nextcord.Member, optional): Member you would like to add/remove/reset the AI channel for. Defaults to ctx.author.
        """
        # ensure that the person running the command has permission to manage the bot
        admin_cog = self.bot.get_cog("Admin")
        check_user_admin = await admin_cog.check_user_admin(ctx)
        if (not check_user_admin):
            await ctx.channel.send(f"You must be a bot manager to use this command!")

        # set user to the person running the command if they do not specify a person
        if (user is None):
            user = ctx.author

        async def add_channel():
            already_setup = await self.check_already_setup(ctx)
            if (already_setup):
                await ctx.channel.send(f"User {user.mention} already has a channel setup in this server.")
                return

            await self.create_private_channel(ctx.guild, user)
        
        async def remove_channel():
            already_setup = await self.check_already_setup(ctx)
            if (not already_setup):
                await ctx.channel.send(f"User {user.mention} has not set up a channel in this server yet.")
                return
            
            # confirm that the user actually wants to delete the channel
            confirm_message = await ctx.channel.send(f"Are you sure you want to delete {user.mention}'s channel?")
            await confirm_message.add_reaction("✅")
            await confirm_message.add_reaction("❌")

            # ensure reaction is valid, and that the reacting user is the author of the setup message, and that the reaction is on the correct message
            def check_message(user_response, user):
                return user == ctx.author and str(user_response.emoji) in ["✅", "❌"] and user_response.message.id == confirm_message.id
            try:
                user_response, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check_message)
                reaction_str = str(user_response.emoji)

                if reaction_str == "✅":
                    await self.remove_private_channel(user)
                elif reaction_str == "❌":
                    await ctx.channel.send("Action canceled.", delete_after=5)
            except asyncio.TimeoutError:
                await ctx.channel.send(f"{ctx.author.mention} You didn't react in time. Please run the command again.", delete_after=10.0)
                return
        
        async def reset_channel():
            await remove_channel()
            await add_channel()

        # ensure all capitalizations work
        choice = choice.strip().lower()

        if (choice == "add"):
            await add_channel()
        elif (choice == "remove"):
            await remove_channel()
        elif (choice == "reset"):
            await reset_channel()
        else:
            await ctx.channel.send(f"You must choose between 'add', 'remove', and 'reset'. '{choice}' is not a valid choice.")

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

    async def setup_verified(self, ctx: nextcord.ext.commands.Context):
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

        # create category for AI
        ai_category = await ctx.guild.create_category("AI Channels")
        
        # welcome user and add reaction
        welcome_msg = await ctx.channel.send(f"# Welcome to PassionAI!\nPlease click the below reaction to create a private channel for yourself.")
        await welcome_msg.add_reaction("🍊")

        # add to DB after the welcome_msg is sent to get its id
        await self.setup_verified_update_DB(ctx, welcome_msg=welcome_msg, ai_category_id=ai_category.id)

        # add message ID to id array of current instance
        self.bot.welcome_msg_list.append(welcome_msg.id)

        # the code below is not needed anymore: everything is now handled in an on_raw_reaction_add listener!

        # # ensure reaction is valid, and that the reacting user is the author of the setup message
        # # REMEMBER TO CHECK CORRECT MESSAGE ID - needs to come from DB
        # def check_message(user_response, user):
        #     return str(user_response.emoji) == "🍊" and user_response.message.id == welcome_msg.id and user.id != self.bot.user.id
        
        # user_response, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check_message)
        # reaction_str = str(user_response.emoji)

        # # unnecessary right now, may be useful later
        # if reaction_str == "🍊":
        #     await self.create_private_channel(user_response.message.guild, user)

    async def setup_verified_update_DB(self, ctx: nextcord.ext.commands.Context, welcome_msg: nextcord.Message, ai_category_id: int):
        
        # awwoo 
        """Once the user finishes setting up in a channel, update our database with the current guild's ID
        Args:
            ctx (nextcord.ext.commands.Context): Context
            ai_category_id (int): The category ID for AI channels
        """

        # get guild id and name from context
        guild_id = ctx.guild.id
        guild_name = ctx.guild.name
        welcome_msg_id = welcome_msg.id
        welcome_msg_channel = welcome_msg.channel.id

        # we find one and update because we want to make sure we keep the guild's name up to date
        query = {
            "guild_id": guild_id
        }

        # set guild id, timestamp, category id, setup messasge id on INSERT only    
        data = {
            "$setOnInsert": {
                "timestamp": datetime.now(),
                "guild_id": guild_id
            },
            "$set": {
                "guild_name": guild_name,
                "ai_category_id": ai_category_id,
                "setup_msg_id": welcome_msg_id,
                "setup_msg_channel_id": welcome_msg_channel
            }
        }

        self.bot.guilds_setup.find_one_and_update(filter=query, update=data, upsert=True)

    async def create_private_channel(self, guild: nextcord.Guild, user: nextcord.Member):
        """
        Creates a private channel for a user to interact privately with PassionAI
            guild (nextcord.Guild): The guild to create the channel in
            user (nextcord.Member): The user who reacted with the setup message
        """
        
        # ping the user in their AI channel if the user has already created a channel in the given guild
        user_check_res = await self.check_user_channel(guild, user)
        if (user_check_res):
            channel_id = user_check_res['channel_id']
            channel = self.bot.get_channel(channel_id)

            await channel.send(f"{user.mention} You clicked the orange again! You may only have one channel per server that PassionAI is in.")
            return

        # get guild default role (everyone)
        default_role = guild.default_role

        # get guild id
        guild_id = guild.id

        # set channel name
        channel_name = f"{user.name}-AI"

        # set channel permissions
        permissions = {
            default_role: PermissionOverwrite(view_channel=False),
            user: PermissionOverwrite(view_channel=True)
        }

        # get category ID of guild
        query = {
            "guild_id": guild_id
        }
        ai_category_id = self.bot.guilds_setup.find_one(query)['ai_category_id']
        category = nextcord.utils.get(guild.categories, id=ai_category_id)

        # create private user channel in category
        channel = await guild.create_text_channel(
            name = channel_name,
            overwrites = permissions,
            category = category
        )

        # get channel id and user id
        user_id = user.id
        channel_id = channel.id

        # insert channel data into DB
        data = {
            "timestamp": datetime.now(),
            "user_id": user_id,
            "guild_id": guild_id,
            "channel_id": channel_id
        }
        self.bot.user_list.insert_one(data)

        await channel.send(f"{user.mention} This is your private channel. Do note that server administrators, including the PQLife team, will be able to see your questions and PassionAI's responses.")

    async def remove_private_channel(self, guild: nextcord.Guild, user: nextcord.Member):
        """
        Removes a pre-existing private channel for a user to interact privately with PassionAI
        Note that this command will not do anything if the user has not already created a channel
            guild (nextcord.Guild): The guild to remove the channel in
            user (nextcord.Member): The user that should have their channel removed
        """
        # get user and guild ID
        guild_id = guild.id
        user_id = user.id

        # delete from channels already setup in DB
        query = {
            "guild_id": guild_id,
            "user_id": user_id
        }
        self.bot.admin_list.delete_one(query)

    async def check_user_channel(self, guild: nextcord.Guild, user: nextcord.User):
        """Checks if the given user has already setup a channel in the provided guild
        Args:
            guild (nextcord.Guild): _description_
            user (nextcord.User): _description_

        Returns:
            dict: Response from querying the collection of current users and their AI channels
        """
        # get guild and user id
        guild_id = guild.id
        user_id = user.id
        
        # query DB
        query = {
            "guild_id": guild_id,
            "user_id": user_id
        }
        response = self.bot.user_list.find_one(filter=query)
        return response

def setup(bot):
    bot.add_cog(Setup(bot))