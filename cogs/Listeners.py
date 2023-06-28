import nextcord
from nextcord.ext import commands

class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if (self.bot.user.id != message.author.id):
            msg = message.content
            bot_mention = f"{self.bot.user.mention}"
            # if the bot is pinged, activate a chat instance
            if bot_mention in msg:
                context = await self.bot.get_context(message)
                mentions = message.mentions

                # delete mentions to feed into AI model (may cause issues if discord updates mention format)
                for mention in mentions:
                    msg = msg.replace(f"<@{mention.id}>", "")

                await context.invoke(self.bot.get_command('chat'), msg)


    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(1074091364419108874)
        message = f"Welcome {member.mention}! Enjoy testing PassionAI!\n\n**To get started:**\nUse the command pq!chat (question) to start chatting with the bot in any of the ai channels below.\ne.g. pq!chat What is the difference between a high Idealism, high Acceptance person and a high Idealism, high Confidence person?"
        await channel.send(message)

def setup(bot):
    bot.add_cog(Listeners(bot))