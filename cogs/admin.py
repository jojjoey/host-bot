import discord
import util

from discord.ext import commands
from tinydb import Query

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(administrator=True)
    @commands.command(name="setup", description="Setup the bot", usage="setup")
    async def setup(self, ctx):
        guild = ctx.guild
        db_servers = util.get_db("db_servers.json")

        referral_log_channel = await guild.create_text_channel(name="referral-log")
        db_servers.update(
            {
                "referral_channel_id": referral_log_channel.id
            },
            Query().server_id == guild.id
        )
        response = f"Referral log channel has been set! ({referral_log_channel.mention})"
        response = util.log_embed(response, "success")
        await ctx.send(embed=response)

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(name="say", description="Send message using bot", usage="say [message]", aliases=["send", "speak"])
    async def say(self, ctx, *, msg:str=None):
        await ctx.message.delete()
        if msg is None:
            return
        await ctx.send(msg)

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(name="embed", description="Send message using bot (embed)", usage="embed [message]")
    async def embed(self, ctx, *, msg:str=None):
        await ctx.message.delete()
        if msg is None:
            return
        embed = discord.Embed(description=msg, color=discord.Color.blue())
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Admin(bot))