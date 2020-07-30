import discord
import os

from dotenv import load_dotenv
from tinydb import TinyDB, Query
from discord.ext import commands

load_dotenv()

client = commands.Bot(('!host ','!Host ','!h ','!H '))
BOT_PREFIX = client.command_prefix
TOKEN = os.environ.get('HOST_BOT_TOKEN')

client.remove_command("help")       # Remove the default help command

ranks = {
    "Companion": {
        "name": "Companion",
        "limit": 20,
        "good_message": "Fantastic! {discord-id}, you are now a `Companion`! How does it feel to be at the top? "
                        "But don't let this stop you though. The more, the merrier!",
        "bad_message": None
    },
    "Friendly": {
        "name": "Friendly",
        "limit": 15,
        "good_message": "Fantastic! {discord-id}, you are now a `Friendly`! How does it feel to be at the top? "
                        "But don't let this stop you though. The more, the merrier!",
        "bad_message": "Whoopsies! {discord-id}, looks like someone you've invited left. Sorry to say this but "
                        "we'll have to knock you down a rank. Don't worry, you can always make more friends!"

    },
    "Buddy": {
        "name": "Buddy",
        "limit": 5,
        "good_message": "Congratulations! {discord-id}, you are now a `Buddy`! Feel's good to... _buddy up_ with someone, huh?",
        "bad_message": "Oh, {discord-id}, looks like someone you invited left. Don't let this discourage you"
    },
    "Unranked": {
        "name": "Unranked",
        "limit": 0,
        "good_message": None,
        "bad_message": "Well, {discord-id}, it looks like you're back to square one. It's fine! There's always next time"
    }
}

async def get_db(filename):
    return TinyDB(filename, indent=4, separators=(',', ': '))

async def check_referral_rank(db, referrer_count, referral_rank, message, member):
    final_rank = None
    for rank in ranks:
        if referrer_count >= ranks[rank]["limit"]:
            final_rank = ranks[rank]
            break
    
    if referral_rank != final_rank["name"]:
        role_old = discord.utils.get(message.guild.roles, name=referral_rank)
        if role_old is not None:
            await member.remove_roles(role_old)
        role_new = discord.utils.get(message.guild.roles, name=final_rank["name"])
        db.update({"referral_rank": final_rank["name"]}, Query().member_id == member.id)
        await member.add_roles(role_new)
        notif_message = None
        if referrer_count >= ranks[referral_rank]["limit"]:
            notif_message = final_rank["good_message"]
        else:
            notif_message = final_rank["bad_message"]
        
        notif_message = notif_message.replace("{discord-id}", member.mention)
        
        if message is not None:
            await message.channel.send(notif_message)

@client.event
async def on_ready():
    print("Host bot is ready!")
    await client.change_presence(activity = discord.Activity(name = "referrals", type = 2))

@client.event
async def on_guild_join(guild):
    DB_CONFIG = await get_db('config.json')
    Server = Query()
    server_row = DB_CONFIG.search(Server.server_id == guild.id)
    if len(server_row) == 0:
        DB_CONFIG.insert({'server_id' : guild.id, 'server_name': guild.name, 'referral_channel_id':''})

@client.event
async def on_guild_remove(guild):
    DB_CONFIG = await get_db('config.json')
    Server = Query()
    server_row = DB_CONFIG.search(Server.server_id == guild.id)
    if len(server_row) == 1:
        DB_CONFIG.remove(Server.server_id == guild.id)

@client.event
async def on_member_remove(member):
    DB_CHECK = await get_db('check_referral.json')
    DB_REFERRAL = await get_db('referral.json')
    table_check = DB_CHECK.table(str(member.guild.id))
    table_referral = DB_REFERRAL.table(str(member.guild.id))

    Check = Query()
    Referral = Query()
    referrer_id = member.id
    referrer_name = member.name
    check_row = table_check.search(Check.referrer_id == referrer_id)

    if (len(check_row) == 1):
        member_id = check_row[0]["member_id"]
        member_name = check_row[0]["member_name"]
        referral_row = table_referral.search(Referral.member_id == member_id)
        list_referrer_id = referral_row[0]["list_referrer_id"]
        list_referrer_name = referral_row[0]["list_referrer_name"]
        list_referrer_id.remove(referrer_id)
        list_referrer_name.remove(referrer_name)
        table_check.remove(Check.referrer_id == referrer_id)
        table_referral.update({"list_referrer_id":list_referrer_id, "list_referrer_name":list_referrer_name, "referrer_count":len(list_referrer_id)}, Check.member_id == member_id)
        print(f"Referrer {referrer_name} has been removed from {member_name} referral (left server)")

@client.event
async def on_message(message):
    member = message.author
    Member = Query()
    DB_REFERRAL = await get_db('referral.json')
    table_referral = DB_REFERRAL.table(str(message.guild.id))

    try: 
        row = table_referral.search(Member.member_id == member.id)[0]
        referrer_count = row["referrer_count"]
        referral_rank = row["referral_rank"]
        await check_referral_rank(db=table_referral,referrer_count=referrer_count,referral_rank=referral_rank,message=message,member=member)
    except:
        pass

    await client.process_commands(message)

# ---------------------- help command ---------------------- #

@commands.has_permissions(administrator=True)
@client.command('help')
async def help(ctx):
    embed = discord.Embed(title="**Admin's Host Bot Command List**",
                        description=f"All Host Bot's usable commands. You just need to type {BOT_PREFIX[0]}<command> to see how it works.",
                        color=discord.Color.blue()
                        )
    embed.add_field(name="1. Check referral information", value=f"{BOT_PREFIX[0]}info")
    embed.add_field(name="2. Check your invitation links info", value=f"{BOT_PREFIX[0]}invites")
    embed.add_field(name="3. Give referral to a friend", value=f"{BOT_PREFIX[0]}referral")
    embed.add_field(name="4. Rollback (unrefer) your referral if you referred to anyone", value=f"{BOT_PREFIX[0]}unrefer")
    embed.add_field(name="5. Show Referral Leaderboard", value=f"{BOT_PREFIX[0]}leaderboard")
    embed.add_field(name="6. Update Members' Referral rank", value=f"{BOT_PREFIX[0]}update_rank")
    embed.add_field(name="7. Set a channel as referral channel", value=f"{BOT_PREFIX[0]}set_referral_channel #channel")
    await ctx.send(embed=embed)

@help.error
async def help_error(ctx,error):
    embed = discord.Embed(title="**Host Bot Command List**",
                        description=f"All Host Bot's usable commands. You just need to type {BOT_PREFIX[0]}<command> to see how it works.",
                        color=discord.Color.blue()
                        )
    embed.add_field(name="1. Check referral information", value=f"{BOT_PREFIX[0]}info")
    embed.add_field(name="2. Check your invitation links info", value=f"{BOT_PREFIX[0]}invites")
    embed.add_field(name="3. Give referral to a friend", value=f"{BOT_PREFIX[0]}referral")
    embed.add_field(name="4. Rollback (unrefer) your referral", value=f"{BOT_PREFIX[0]}unrefer")
    embed.add_field(name="5. Show Referral Leaderboard", value=f"{BOT_PREFIX[0]}leaderboard")
    await ctx.send(embed=embed)

# --------------------- End help command -------------------- #

# -------------- set and get referral channel -------------- #

@commands.has_permissions(administrator=True)
@client.command('set_referral_channel')
async def set_referral_channel(ctx, channel : discord.TextChannel):
    DB_CONFIG = await get_db('config.json')
    Server = Query()
    server_row = DB_CONFIG.search(Server.server_id == ctx.guild.id)
    if len(server_row) == 1:
        DB_CONFIG.update({'referral_channel_id':channel.id},Server.server_id == ctx.guild.id)
    else:
        DB_CONFIG.insert({'server_id' : ctx.guild.id, 'server_name': ctx.guild.name, 'referral_channel_id':channel.id})
    await ctx.message.add_reaction("✅")
    await ctx.send(f"You have successfully set {channel.mention} as referral channel")

@set_referral_channel.error
async def set_referral_channel_error(ctx,error):
    DB_CONFIG = await get_db('config.json')
    Server = Query()
    server_row = DB_CONFIG.search(Server.server_id == ctx.guild.id)
    if isinstance(error, commands.MissingRequiredArgument):
        if len(server_row) == 1:
            DB_CONFIG.update({'referral_channel_id':ctx.channel.id},Server.server_id == ctx.guild.id)
        else:
            DB_CONFIG.insert({'server_id' : ctx.guild.id, 'server_name': ctx.guild.name, 'referral_channel_id':ctx.channel.id})
        await ctx.message.add_reaction("✅")
        await ctx.send(f"You have successfully set {ctx.channel.mention} as referral channel")


@client.command('referralchannel')
async def referralchannel(ctx):
    DB_CONFIG = await get_db('config.json')
    Server = Query()
    server_row = DB_CONFIG.search(Server.server_id == ctx.guild.id)
    if len(server_row) == 1 and server_row[0]["referral_channel_id"] != "":
        channel = client.get_channel(server_row[0]["referral_channel_id"])
        await ctx.send(f"Your server's referral channel is {channel.mention}")
    else:
        await ctx.send(f"There is no referral channel in this server. Please type `{BOT_PREFIX[0]}set_referral_channel #channel` to set up a referral channel")

# -------- End set and get referral channel command -------- #

# --------------- Admin's update rank command -------------- #

@commands.has_permissions(administrator=True)
@client.command('update_rank')
async def update_rank(ctx):
    DB_REFERRAL = await get_db('referral.json')
    table_referral = DB_REFERRAL.table(str(ctx.guild.id))

    for row in table_referral.all():
        referral_rank = row["referral_rank"]
        member_id = row["member_id"]
        member = ctx.guild.get_member(member_id)
        if referral_rank in ["Buddy", "Friendly", "Companion"]:
            role = discord.utils.get(ctx.message.guild.roles, name=referral_rank)
            await member.add_roles(role)
    await ctx.send("You have successfully updated all members' referral rank and role!")
    await ctx.message.add_reaction("✅")

# ------------- End admin's update rank command ------------ #

# --- referral and unrefer command to refers to @member ---- #

@commands.has_role('Member')
@client.command(name='referral',aliases=['refer','r'])
async def referral(ctx, member : discord.User):
    DB_REFERRAL = await get_db('referral.json')
    DB_CHECK = await get_db('check_referral.json')
    DB_CONFIG = await get_db('config.json')

    table_referral = DB_REFERRAL.table(str(ctx.guild.id))
    table_check = DB_CHECK.table(str(ctx.guild.id))

    referrer = ctx.author
    Member = Query()

    referral_row = table_referral.search(Member.member_id == member.id)
    check_row = table_check.search(Query().referrer_id == referrer.id)
    config_row = DB_CONFIG.search(Query().server_id == ctx.guild.id)

    referral_channel_id = config_row[0]["referral_channel_id"]
    channel = client.get_channel(referral_channel_id)

    if (ctx.channel.id == referral_channel_id):
        if (member.id != referrer.id):
            if (len(referral_row) == 1) and (len(check_row) == 0):
                print(f"Member {member} already exist in referral.json. {referrer} has referred to {member}")
                list_referrer_id = referral_row[0]["list_referrer_id"]
                list_referrer_name = referral_row[0]["list_referrer_name"]
                if (referrer.id not in list_referrer_id):
                    list_referrer_id.append(referrer.id)
                    list_referrer_name.append(referrer.name)
                    table_referral.update({"list_referrer_id":list_referrer_id}, Member.member_id == member.id)
                    table_referral.update({"list_referrer_name":list_referrer_name}, Member.member_id == member.id)
                    table_referral.update({'referrer_count':len(set(list_referrer_id))}, Member.member_id == member.id)
                    table_check.insert(dict(referrer_id=referrer.id, referrer_name=referrer.name, member_id=member.id, member_name=member.name))
                    await ctx.message.add_reaction("✅")
            elif (len(referral_row) == 0) and (len(check_row) == 0):
                print(f"Member {member} does not exist yet in referral.json. {referrer} has referred to {member}")
                referral_rank = "Unranked"
                referrer_count = 1
                table_referral.insert(dict(member_id=member.id,member_name=member.name,referral_rank=referral_rank,list_referrer_id=[referrer.id],
                                            list_referrer_name=[referrer.name],referrer_count=referrer_count))
                table_check.insert(dict(referrer_id=referrer.id, referrer_name=referrer.name, member_id=member.id, member_name=member.name))
                await ctx.message.add_reaction("✅")
            elif (len(check_row) == 1):
                await ctx.send(f"{referrer.mention}, looks like you've already reffered someone already. You can always unrefer someone by using {BOT_PREFIX[0]}unrefer")
                await ctx.message.add_reaction("❌")
        else:
            await ctx.send(f"Well, {referrer.mention}, looks like you didn't mention a friend. Be sure to include their username!")
            await ctx.message.add_reaction("❌")
    else:
        await ctx.send(f"Sorry, You can only use this command in {channel.mention}")
        await ctx.message.add_reaction("❌")
        

@referral.error
async def referral_error(ctx, error):
    member = ctx.author
    await ctx.message.add_reaction("❌")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Well, {member.mention}, looks like you didn't mention a friend. Be sure to include their username!")
    elif isinstance(error, commands.MissingRole):
        await ctx.send(f"```{error}```")

@commands.has_role('Member')
@client.command('unrefer')
async def unrefer(ctx):
    DB_CHECK = await get_db('check_referral.json')
    DB_REFERRAL = await get_db('referral.json')
    DB_CONFIG = await get_db('config.json')

    Check = Query()
    Referral = Query()
    Config = Query()

    table_referral = DB_REFERRAL.table(str(ctx.guild.id))
    table_check = DB_CHECK.table(str(ctx.guild.id))

    referrer = ctx.author
    referrer_id = referrer.id
    referrer_name = referrer.name
    check_row = table_check.search(Check.referrer_id == referrer_id)
    config_row = DB_CONFIG.search(Config.server_id == ctx.guild.id)
    referral_channel_id = config_row[0]["referral_channel_id"]
    channel = client.get_channel(referral_channel_id)

    if (ctx.channel.id == referral_channel_id):
        if (len(check_row) == 1):
            member_id = check_row[0]["member_id"]
            referral_row = table_referral.search(Referral.member_id == member_id)
            list_referrer_id = referral_row[0]["list_referrer_id"]
            list_referrer_name = referral_row[0]["list_referrer_name"]
            list_referrer_id.remove(referrer_id)
            list_referrer_name.remove(referrer_name)
            table_check.remove(Check.referrer_id == referrer_id)
            table_referral.update({"list_referrer_id":list_referrer_id, "list_referrer_name":list_referrer_name, "referrer_count":len(list_referrer_id)}, Check.member_id == member_id)
            await ctx.send(f"{referrer.mention} has unreferred <@{member_id}>")
            await ctx.message.add_reaction("✅")
        else:
            await ctx.send(f"{referrer.mention}, You cannot unrefer when you haven't referred to a friend yet.")
            await ctx.message.add_reaction("❌")
    else:
        await ctx.send(f"Sorry, You can only use this command in {channel.mention}")
        await ctx.message.add_reaction("❌")

# ------------ End referral and unrefer command ------------ #

# ------------------- leaderboard command ------------------ #

@client.command(name='leaderboard',aliases=['lb','rank','leaderboards'])
async def leaderboard(ctx, number=20):
    DB_REFERRAL = await get_db('referral.json')
    table_referral = DB_REFERRAL.table(str(ctx.guild.id))

    list_all_referrals = [{'Member':m['member_name'], 'Referrals': m['referrer_count'], 'Rank': m['referral_rank']} for m in table_referral.all()]
    list_leaderboard = sorted(list_all_referrals, key=lambda k: k['Referrals'], reverse=True)

    response = ""
    if len(list_leaderboard) <= number:
        for i in range(0,len(list_leaderboard)):
            response =  response + f"#**{i+1}** Member : **{list_leaderboard[i]['Member']}**, Referrals : **{list_leaderboard[i]['Referrals']}**, Rank : **{list_leaderboard[i]['Rank']}** \n"
    else:
        for i in range(0,number):
            response =  response + f"#**{i+1}** Member : **{list_leaderboard[i]['Member']}**, Referrals : **{list_leaderboard[i]['Referrals']}**, Rank : **{list_leaderboard[i]['Rank']}** \n"

    embed = discord.Embed(title=f"**{ctx.guild.name}'s Referral Leaderboard**",
                            description=response,
                            color=discord.Color.blue()
                            )
    embed.set_thumbnail(url="https://image.flaticon.com/icons/png/512/548/548484.png")
    await ctx.send(embed=embed)

# ----------------- End leaderboard command ---------------- #

# -------- invites command to show invitation links -------- #

@client.command('invites')
async def invites(ctx):
    guild = client.get_guild(ctx.guild.id)
    invites = await guild.invites()
    embed = discord.Embed(title="My Invitation Links",
                            description="Information about my Invitation Links",
                            color=discord.Color.blue()
                            )
    for i in invites:
        if i.inviter.id == ctx.author.id:
            embed.add_field(name="Link", value=i, inline=True)
            embed.add_field(name="Creator", value=i.inviter, inline=True)
            embed.add_field(name="Uses", value=i.uses, inline=True)
            embed.add_field(name="Expire time (days)", value=int(i.max_age/86400), inline=False)
    
    await ctx.send(embed=embed)

# ------------------ End invites command ------------------- #

# ----------- Info command to show referral info ------------ #

@client.command('info')
async def info(ctx):
    DB_REFERRAL = await get_db('referral.json')
    table_referral = DB_REFERRAL.table(str(ctx.guild.id))
    member = ctx.author
    try:
        referrer_row = table_referral.search(Query().member_id == ctx.author.id)[0]
        embed = discord.Embed(title="Referral Information",
                            color=discord.Color.blue()
                            )
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.add_field(name="Member Name", value=referrer_row["member_name"], inline=False)
        embed.add_field(name="Referral Rank", value=referrer_row["referral_rank"], inline=True)
        embed.add_field(name="Referrals Count", value=referrer_row["referrer_count"], inline=True)
        await ctx.send(embed=embed)
    except:
        await ctx.send(f"Look's like {member.mention} doesn't have any refferals so far. Got any friends you can bring over?")

# --------------------- End Info command --------------------- #

# ----------------------- guide command ---------------------- #

@client.command('guide')
async def guide(ctx):
    DB_CONFIG = await get_db('config.json')

    Config = Query()

    config_row = DB_CONFIG.search(Config.server_id == ctx.guild.id)
    referral_channel_id = config_row[0]["referral_channel_id"]
    channel = client.get_channel(referral_channel_id)
    response = '''
Hello, I am **Host Bot**. Your **_go-to_ referral partner**.

I am here to help you to count how many people referred to you. In order to refer to someone you need to use `{0}referral @Member` on {1}.
Here is how it works:
```
1. You have to be in referral channel to use {0}referral @Member command
2. Once you typed that, the member you mentioned gains 1 number of referrals count
3. You can only use {0}referral @Member command once. So, use it wisely to refer to your friend who invited you.
4. If you want to check your referral info, type {0}info
5. You can unrefer by using {0}unrefer
```
I am looking forward to work with you. Please type `{0}help` to see all commands. If you want to know more about a command, type `{0}help <command_name>`.

Thank you!
    '''.format(BOT_PREFIX[0],channel.mention)
    await ctx.send(response)

# -------------------- End guide command --------------------- #

client.run(TOKEN)