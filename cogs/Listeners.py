import nextcord
from nextcord.ext import commands

class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if (self.bot.user.id != message.author.id):
            msg = message.content

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(1074091364419108874)
        message = f"Welcome {member.mention}! Enjoy testing PassionAI!\n\n**To get started:**\nUse the command pq!chat (question) to start chatting with the bot in any of the ai channels below.\ne.g. pq!chat What is the difference between a high Idealism, high Acceptance person and a high Idealism, high Confidence person?"
        await channel.send(message)