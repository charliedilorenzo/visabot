"""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.5.0
"""

import asyncio

import aiosqlite
import discord

from bots.basebot import BaseBot
from utils import DATABASE_PATH, SCHEMA_PATH

intents = discord.Intents.all()
# theoretically redundant but just in case
intents.typing = False
intents.dm_typing = False
intents.guild_typing = False
intents.message_content = True
# intents.members = False
intents.members = True
intents.presences = True
intents.guilds = True

bot = BaseBot(
    intents=intents,
    help_command=None,
)


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        with open(SCHEMA_PATH) as file:
            await db.executescript(file.read())
        await db.commit()


asyncio.run(init_db())
asyncio.run(bot.load_cogs())

bot.run(bot.config.token)
