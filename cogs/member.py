import discord
import util

from discord.ext import commands
from tinydb import Query

RANKS = [
    {
        "name": "Companion",
        "limit": 20,
        "good_message": "Fantastic! @user, you are now a `Companion`! How does it feel to be at the top? "
                        "But don't let this stop you though. The more, the merrier!",
        "bad_message": None
    },
    {
        "name": "Friendly",
        "limit": 15,
        "good_message": "Fantastic! @user, you are now a `Friendly`! How does it feel to be at the top? "
                        "But don't let this stop you though. The more, the merrier!",
        "bad_message": "Whoopsies! @user, looks like someone you've invited left. Sorry to say this but "
                        "we'll have to knock you down a rank. Don't worry, you can always make more friends!"
    },
    {
        "name": "Buddy",
        "limit": 5,
        "good_message": "Congratulations! @user, you are now a `Buddy`! Feel's good to... _buddy up_ with someone, huh?",
        "bad_message": "Oh, @user, looks like someone you invited left. Don't let this discourage you"
    },
    {
        "name": "Unranked",
        "limit": 0,
        "good_message": None,
        "bad_message": "Well, @user, it looks like you're back to square one. It's fine! There's always next time"
    }
]

class Member(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        referrer = member
        db_referrals = util.get_db('db_referrals.json')
        db_users = util.get_db('db_users.json')
        table_referral = db_referrals.table(str(referrer.guild.id))
        table_users = db_users.table(str(referrer.guild.id))

        referrals_data = table_referral.search(Query().referrer_id == referrer.id)
        table_users.remove(Query().member_id == referrer.id)
        if len(referrals_data) == 0:
            return
        referral_row = referrals_data[0]
        member = await member.guild.fetch_member(referral_row['member_id'])
        table_referral.remove(Query().referrer_id == referrer.id)

        referral_count = len(table_referral.search(Query().member_id == member.id))
        table_users.update({"member_name":str(member), "referral_count":referral_count}, Query().member_id == member.id)
        ranks_ascending = sorted(RANKS, key=lambda k: k['limit'])
        for idx, rank in enumerate(ranks_ascending):
            if idx + 1 == len(ranks_ascending):
                continue
            if referral_count >= rank['limit'] and referral_count < RANKS[idx+1]['limit']:
                role_names = [row['name'] for row in RANKS if row['name'] != rank['name']]
                for role_name in role_names:
                    if discord.utils.get(member.roles, name=role_name) is not None:
                        await member.remove_roles(discord.utils.get(member.roles, name=role_name))

                table_users.update({"referral_rank":rank['name']}, Query().member_id == member.id)
                role = discord.utils.get(member.guild.roles, name=rank['name'])
                if role is not None:
                    await member.add_roles(role)
                    break
        self.bot.logger.info(f"{referrer} has unreferred {member} (leave)")

    @commands.command(name="refer", description="Refer to a friend who invited you", usage="refer @user", aliases=["referral","r"])
    async def refer(self, ctx, member:discord.Member=None):
        if member is None:
            response = f"Well, {ctx.author.mention}, looks like you didn't mention a friend. Be sure to mention them!"
            embed = util.log_embed(response, "failed")
            await ctx.send(embed=embed)
            return

        db_referrals = util.get_db('db_referrals.json')
        db_users = util.get_db('db_users.json')
        db_servers = util.get_db('db_servers.json')
        servers_data = db_servers.search(Query().server_id == ctx.guild.id)

        if not servers_data:
            return

        server_row = servers_data[0]
        referral_channel_id = None if "referral_channel_id" not in server_row else server_row['referral_channel_id']

        if referral_channel_id is None:
            return

        if ctx.channel.id != referral_channel_id:
            response = f"Sorry, you can only use this command in <#{referral_channel_id}>"
            embed = util.log_embed(response, "failed")
            await ctx.send(embed=embed)
            return

        referrer = ctx.author
        table_referral = db_referrals.table(str(ctx.guild.id))
        table_users = db_users.table(str(ctx.guild.id))
        referrals_data = table_referral.search(Query().referrer_id == referrer.id)
        users_data = table_users.search(Query().member_id == member.id)

        if (member.id == referrer.id):
            response = f"Well, {referrer.mention}, you cannot refere to yourself!"
            embed = util.log_embed(response, "failed")
            await ctx.send(embed=embed)
            return

        if len(referrals_data) == 1:
            response = f"{referrer.mention}, looks like you've already reffered someone. You can always unrefer someone by using `{ctx.prefix}unrefer`"
            embed = util.log_embed(response, "failed")
            await ctx.send(embed=embed)
            return

        new_referral = dict(
            member_id=member.id,
            referrer_id=referrer.id
        )
        table_referral.insert(new_referral)


        referral_count = len(table_referral.search(Query().member_id == member.id))
        if len(users_data) == 1:
            table_users.update({"member_name":str(member), "referral_count":referral_count}, Query().member_id == member.id)
            try:
                rank_name = next(rank['name'] for rank in RANKS if 5 == rank['limit'])
            except StopIteration:
                rank_name = None
            
            if rank_name is not None:
                role_names = [row['name'] for row in RANKS if row['name'] != rank_name]
                for role_name in role_names:
                    if discord.utils.get(member.roles, name=role_name) is not None:
                        await member.remove_roles(discord.utils.get(member.roles, name=role_name))

                table_users.update({"referral_rank":rank_name}, Query().member_id == member.id)
                role = discord.utils.get(ctx.guild.roles, name=rank_name)
                if role is not None:
                    await member.add_roles(role)
        else:
            table_users.insert(dict(member_id=member.id, member_name=str(member), referral_count=1, referral_rank="Unranked"))
        self.bot.logger.info(f"Member {referrer} has referred to {member}")
        await ctx.message.add_reaction("✅")

    @commands.command(name="unrefer", description="Unrefer a friend", usage="unrefer")
    async def unrefer(self, ctx):
        db_referrals = util.get_db('db_referrals.json')
        db_users = util.get_db('db_users.json')
        table_referral = db_referrals.table(str(ctx.guild.id))
        table_users = db_users.table(str(ctx.guild.id))

        referrals_data = table_referral.search(Query().referrer_id == ctx.author.id)
        if len(referrals_data) == 0:
            return
        referral_row = referrals_data[0]
        member = await ctx.guild.fetch_member(referral_row['member_id'])
        if member is None:
            return
        table_referral.remove(Query().referrer_id == ctx.author.id)

        referral_count = len(table_referral.search(Query().member_id == member.id))
        table_users.update({"member_name":str(member), "referral_count":referral_count}, Query().member_id == member.id)
        ranks_ascending = sorted(RANKS, key=lambda k: k['limit'])
        for idx, rank in enumerate(ranks_ascending):
            if idx + 1 == len(ranks_ascending):
                continue
            if referral_count >= rank['limit'] and referral_count < RANKS[idx+1]['limit']:
                role_names = [row['name'] for row in RANKS if row['name'] != rank['name']]
                for role_name in role_names:
                    role = discord.utils.get(member.roles, name=role_name)
                    if role is not None:
                        await member.remove_roles(role)

                table_users.update({"referral_rank":rank['name']}, Query().member_id == member.id)
                role = discord.utils.get(ctx.guild.roles, name=rank['name'])
                if role is not None:
                    await member.add_roles(role)
                    break
        response = f"{ctx.author} has unreferred {member}"
        embed = util.log_embed(response, "success")
        await ctx.send(embed=embed)

    @commands.command(name="info", description="Shows referral info", usage="info")
    async def info(self, ctx):
        db_users = util.get_db('db_users.json')
        table_user = db_users.table(str(ctx.guild.id))
        users_data = table_user.search(Query().member_id == ctx.author.id)
        if len(users_data) == 0:
            response = f"Looks like {ctx.author.mention} doesn't have any refferals so far. Got any friends you can bring over?"
            embed = util.log_embed(response, "failed")
            await ctx.send(embed=embed)
            return

        user_row = users_data[0]

        embed = discord.Embed(
            title="Referral Info",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.add_field(name="Member Name", value=str(ctx.author), inline=False)
        embed.add_field(name="Referral Count", value=user_row['referral_count'], inline=False)
        embed.add_field(name="Referral Rank", value=user_row['referral_rank'], inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="leaderboard", description="Shows referral leaderboard", usage="leaderboard", aliases=["rank", "lb"])
    async def leaderboard(self, ctx, number:int=20):
        db_users = util.get_db('db_users.json')
        table_users = db_users.table(str(ctx.guild.id))

        leaderboard_list = sorted(table_users.all(), key=lambda k: k['referral_count'], reverse=True)

        response = ""
        if len(leaderboard_list) >= number:
            leaderboard_list = leaderboard_list[:number]

        for idx, val in enumerate(leaderboard_list):
            response =  response + f"#**{idx+1}** Member : **{val['member_name']}** | Referrals : **{val['referral_count']}** | Rank: **{val['referral_rank']}**\n"
        
        embed = discord.Embed(title=f"**{ctx.guild.name}'s Referral Leaderboard**",
                                description=response,
                                color=discord.Color.blue()
                                )
        embed.set_thumbnail(url="https://image.flaticon.com/icons/png/512/548/548484.png")
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Member(bot))