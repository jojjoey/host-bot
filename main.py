import discord
import os
import util

from dotenv import load_dotenv
from discord.ext import commands
from bot import HostBot

load_dotenv()

client = HostBot(
    intents=discord.Intents(guilds=True, members=True, presences=True, messages=True, reactions=True),
    command_prefix="!h ", 
    case_insensitive=True
)

TOKEN = os.environ.get('HOST_BOT_TOKEN')

@client.command()
@commands.has_permissions(administrator=True)
async def load(ctx, extension):
    client.load_extension(f"cogs.{extension}")
    embed = util.log_embed(f"{extension} module has been loaded!", "success")
    await ctx.send(embed=embed)

@client.command()
@commands.has_permissions(administrator=True)
async def unload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")
    embed = util.log_embed(f"{extension} module has been unloaded!", "success")
    await ctx.send(embed=embed)

@client.command()
@commands.has_permissions(administrator=True)
async def reload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")
    client.load_extension(f"cogs.{extension}")
    embed = util.log_embed(f"{extension} module has been reloaded!", "success")
    await ctx.send(embed=embed)

for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            client.load_extension(f"cogs.{filename[:-3]}")

client.run(TOKEN)