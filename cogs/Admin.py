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
    async def reload_all(self, ctx: nextcord.ext.commands.Context):
        """
        Reloads all cogs currently loaded in this instance of the bot
        Args:
            ctx (nextcord.ext.commands.Context): Context
        """
        if (not await self.check_user_admin(ctx)):
            return

        self.bot.reload_extension("cogs.Listeners")
        self.bot.reload_extension("cogs.AI_PINECONE")
        self.bot.reload_extension("cogs.Setup")
        self.bot.reload_extension("cogs.Admin")
        await ctx.channel.send("Reloaded all modules!")

    @commands.command(name="reloadlisteners", aliases=["rl"])
    @commands.has_permissions(administrator=True)
    async def reload_listeners(self, ctx):
        """
        Reloads the Listeners cog
        Args:
            ctx (nextcord.ext.commands.Context): Context
        """
        if (not await self.check_user_admin(ctx)):
            return
        
        self.bot.reload_extension("cogs.Listeners")
        await ctx.channel.send("Reloaded listeners module **only**.")

    @commands.command(name="reloadai", aliases=["rai"])
    @commands.has_permissions(administrator=True)
    async def reload_ai(self, ctx):
        """
        Reloads the AI_PINECONE cog
        Args:
            ctx (nextcord.ext.commands.Context): Context
        """
        if (not await self.check_user_admin(ctx)):
            return
        
        self.bot.reload_extension("cogs.AI_PINECONE")
        await ctx.channel.send("Reloaded AI module **only**.")

    @commands.command(name="reloadsetup", aliases=["rs"])
    @commands.has_permissions(administrator=True)
    async def reload_setup(self, ctx):
        """
        Reloads the Setup cog
        Args:
            ctx (nextcord.ext.commands.Context): Context
        """
        if (not await self.check_user_admin(ctx)):
            return
        
        self.bot.reload_extension("cogs.Setup")
        await ctx.channel.send("Reloaded setup module **only**.")
        
    @commands.command(name="reloadadmin", aliases=["rad"])
    @commands.has_permissions(administrator=True)
    async def reload_setup(self, ctx):
        """
        Reloads the Admin cog
        Args:
            ctx (nextcord.ext.commands.Context): Context
        """
        if (not await self.check_user_admin(ctx)):
            return
        
        self.bot.reload_extension("cogs.Admin")
        await ctx.channel.send("Reloaded admin module **only**.")

    @commands.command(name="admin")
    @commands.has_permissions(administrator=True)
    async def admin(self, ctx: nextcord.ext.commands.Context, choice: str = "", user: nextcord.Member = None):
        """
        Command used to add or remove members from the list of bot managers in DB
        Args:
            ctx (nextcord.ext.commands.Context): Context
            choice (str, optional): Either to add or remove. Defaults to "", which will be an invalid response.
            user (nextcord.Member, optional): The Member to add. Will automatically default to ctx.author
        """
        if (not await self.check_user_admin(ctx)):
            return

        if user is None:
            user = ctx.author

        async def admin_add():
            """
            Helper function to add a member to the list of bot managers
            """
            # get user id and username
            user_id = user.id
            username = user.name

            # insert to DB, update username if required
            query = {
                "user_id": user_id
            }
            data = {
                "$setOnInsert":{
                    "user_id": user_id
                },
                "$set": {
                    "username": username
                }
            }
            self.bot.admin_list.find_one_and_update(filter=query, update=data, upsert=True)

            await ctx.channel.send(f"Added {user.mention} to the list of bot managers.")

        async def admin_remove():
            """
            Helper function to remove a bot manager
            """
            # get user id
            user_id = user.id
            
            # remove from DB
            query = {
                "user_id": user_id
            }
            self.bot.admin_list.delete_one(query)

            await ctx.channel.send(f"Removed {user.mention} from being a bot manager.")

        if (choice == "add"):
            await admin_add()
        elif (choice == "remove"):
            await admin_remove()
        else:
            await ctx.channel.send("Please choose either 'add' or 'remove'")

    async def check_user_admin(self, ctx: nextcord.ext.commands.Context):
        """Checks if the current user is authorized to manage the bot
        Args:
            ctx (nextcord.ext.commands.Context): Context - who ran the command?

        Returns:
            bool: whether the user is a bot manager or not
        """
        user_id = ctx.author.id

        query = {
            "user_id": user_id
        }

        response = self.bot.admin_list.find_one(query)
        if response is None:
            await ctx.channel.send(f"{ctx.author.mention}, you may not run this command, as you are not authorized as a bot manager.")
            return False
        return True

def setup(bot):
    bot.add_cog(Admin(bot))