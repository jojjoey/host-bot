import json
import os
import discord
import datetime

from tinydb import TinyDB, Query

def get_db(filename):
    return TinyDB(filename, indent=4, separators=(',', ': '))

def read_json(filename):
    with open(filename) as json_data:
        config = json.load(json_data)
        json_data.close()
    return config

def get_key(element, *keys):
    """
    Check if *keys (nested) exists in `element` (dict).
    """
    if not isinstance(element, dict):
        raise AttributeError('keys_exists() expects dict as first argument.')
    if len(keys) == 0:
        raise AttributeError('keys_exists() expects at least two arguments, one given.')

    _element = element
    for key in keys:
        try:
            _element = _element[key]
        except KeyError:
            return None
    return _element

def keys_exists(element, *keys):
    """
    Check if *keys (nested) exists in `element` (dict).
    """
    if not isinstance(element, dict):
        raise AttributeError('keys_exists() expects dict as first argument.')
    if len(keys) == 0:
        raise AttributeError('keys_exists() expects at least two arguments, one given.')

    _element = element
    for key in keys:
        try:
            _element = _element[key]
        except KeyError:
            return False
    return True

async def send_message(channel, content):
    if content is None:
        print("Error: One of the configurations is not set properly and content has come out to None.")
        return
    
    if isinstance(content, discord.Embed):
        message = await channel.send(embed=content)
    else:
        message = await channel.send(content)
    return message

async def remove_reaction(message, user, reaction):
    await message.remove_reaction(reaction, user)

def log_embed(description:str, level:str):
    dict_level = {
        "info":{"color": discord.Color.blue(), "description": f"ℹ "},
        "success":{"color": discord.Color.green(), "description": f"✅ "},
        "failed":{"color": discord.Color.red(), "description": f"❌ "},
        "warning":{"color": discord.Color.orange(), "description": f"⚠ "},
    }
    if level in dict_level:
        description = dict_level[level]['description'] + description
        color = dict_level[level]['color']
        embed = discord.Embed(description=description, color=color)
        return embed
    else:
        return