import discord
import util

from discord.ext import commands
from tinydb import Query

ROLES = ["Unranked", "Buddy", "Friendly", "Companion"]

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

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(name="updaterank", description="Update all referral ranks", usage="updaterank")
    async def updaterank(self, ctx, *, msg:str=None):
        db_referrals = util.get_db('db_referrals.json')
        db_users = util.get_db('db_users.json')
        table_referral = db_referrals.table(str(ctx.guild.id))
        table_users = db_users.table(str(ctx.guild.id))

        for row in table_users.all():
            member_id = row['member_id']
            try:
                member = await ctx.guild.fetch_member(member_id)
            except discord.errors.NotFound:
                table_users.remove(Query().member_id == member_id)
                table_referral.remove((Query().member_id == member_id) & (Query().referrer_id == member_id))
                self.bot.logger.info(f"Removed data for member ID: {member_id}")
                continue
            role_name = row['referral_rank']
            table_users.update({"member_name":str(member)}, Query().member_id == member_id)
            other_roles = [role for role in ROLES if role != role_name]
            for other_role_name in other_roles:
                other_role = discord.utils.get(member.roles, name=other_role_name)
                if other_role is not None:
                    await member.remove_roles(other_role)

            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if role is not None:
                await ctx.author.add_roles(role)

        response = f"Successfully updated {len(table_referral)} referrals row and {len(table_users)} users row"
        self.bot.logger.info(f"{ctx.author} has {response}")
        embed = util.log_embed(response, "success")
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Admin(bot))