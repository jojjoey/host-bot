import discord
import logging
import util

from discord.ext import commands, tasks
from tinydb import Query

class HostBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s|%(name)s::%(levelname)s: %(message)s'))
        self.logger = logging.getLogger('HostBot')
        self.logger.addHandler(handler)
        self.logger.setLevel('INFO')
        self.remove_command('help')

    async def on_ready(self):
        self.logger.info(f"Host Bot is Ready! (Prefix: {self.command_prefix})")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, 
                                                            name=f"referrals"))

    async def on_guild_join(self, guild):
        DB_SERVERS = util.get_db('db_servers.json')
        Server = Query()
        server_row = DB_SERVERS.search(Server.server_id == guild.id)
        if len(server_row) == 0:
            DB_SERVERS.insert({'server_id': guild.id, 'server_name': guild.name})

    async def on_guild_remove(self, guild):
        DB_SERVERS = util.get_db('db_servers.json')
        Server = Query()
        server_row = DB_SERVERS.search(Server.server_id == guild.id)
        if len(server_row) == 1:
            DB_SERVERS.remove(Server.server_id == guild.id)

    async def on_message(self, message):
        if message.author.bot:
            return

        if message.guild:
            DB_SERVERS = util.get_db('db_servers.json')
            Server = Query()
            server_row = DB_SERVERS.search(Server.server_id == message.guild.id)
            if len(server_row) == 0:
                DB_SERVERS.insert({'server_id' : message.guild.id, 'server_name': message.guild.name})

        await self.process_commands(message)