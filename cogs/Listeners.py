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
            if bot_mention in msg and self.bot.prefix not in msg:
                context = await self.bot.get_context(message)
                mentions = message.mentions

                # delete mentions to feed into AI model (may cause issues if discord updates mention format)
                for mention in mentions:
                    msg = msg.replace(f"<@{mention.id}>", "")

                await context.invoke(self.bot.get_command('chat'), msg)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # get member
        user = payload.member

        # get guild and message id
        guild_id = payload.guild_id
        guild = self.bot.get_guild(guild_id)
        message_id = payload.message_id
        
        # get emoji and event type
        emoji = str(payload.emoji)
        event_type = payload.event_type

        # don't react to the bot adding reactions, and only respond if the user ADDS a reaction, AND only reactions to the setup message, not just any message
        if (self.bot.user.id != user.id and event_type == "REACTION_ADD" and message_id in self.bot.welcome_msg_list):
            # check for the orange emoji
            if (emoji == "🍊"):
                setup = self.bot.get_cog("Setup")
                await setup.create_private_channel(guild, user)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        return
        channel = self.bot.get_channel(1074091364419108874)
        message = f"Welcome {member.mention}! Enjoy testing PassionAI!\n\n**To get started:**\nUse the command pq!chat (question) to start chatting with the bot in any of the ai channels below.\ne.g. pq!chat What is the difference between a high Idealism, high Acceptance person and a high Idealism, high Confidence person?"
        await channel.send(message)

def setup(bot):
    bot.add_cog(Listeners(bot))