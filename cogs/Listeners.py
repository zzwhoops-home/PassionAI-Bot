import nextcord
from nextcord.ext import commands

class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if (self.bot.user.id != message.author.id):
            msg = message.content