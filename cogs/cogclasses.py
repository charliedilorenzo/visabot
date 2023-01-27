""""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.5.0
"""

from discord.ext import commands, tasks
from discord.ext.commands import Bot,Context
import datetime

from helpers import checks
import discord
import math
import os
import random
import json

# Here we name the cog and create a new class for the cog.
class GuildedCog(commands.Cog):
    def get_now(self) -> datetime.datetime:
        return datetime.datetime.now((datetime.timezone.utc))

    def str_datetime_to_datetime_obj(self,str_datetime: str) -> datetime.datetime:
        datetime_obj = datetime.datetime.strptime(str_datetime,
                                                    "%Y-%m-%d %H:%M:%S.%f%z")
        return datetime_obj
    # TODO add some base class called "GuildedCog" or something with all the config and get options
    def update_var_json(self, new_data: dict) -> bool:
        data = self.get_json_data()
        data.update(new_data)
        with open(self.tracker_file, "w") as outfile:
            json.dump(data, outfile)
        return True
    
    def get_json_data(self) -> dict:
        with open(self.tracker_file, 'r') as openfile:
            data = json.load(openfile)
        return data

    def __init__(self, bot: Bot):
        self.bot = bot
        # manually import this just cause not in config i guess
        self.test_mode = bot.config['test_mode']
        #for while on replit
        if self.test_mode == True:
            self.main_dir = f"{os.path.realpath(os.path.dirname(__file__))}"
            self.main_dir = self.main_dir.replace("\cogs","")
        #for while on replit
        else:
            self.main_dir = "/home/runner/visabot"
        self.warning_gif = self.main_dir+"/visabot_is_watching_you.gif"

        self.tracker_file = "var_tracker.json"
        if self.test_mode:
            self.tracker_file = "test_" + self.tracker_file
        self.timestamp_before_online = self.get_json_data()['LAST_TIME_OF_ACTION']

    async def get_guild(self) -> discord.Guild:
        guild = await self.bot.fetch_guild(self.bot.config['guild_id'])
        return guild

    # uses config to determine guild
    async def get_spam_channel(self, fetched_guild=None) -> discord.TextChannel:
        if fetched_guild is None:
            fetched_guild = await self.get_guild()
        return await fetched_guild.fetch_channel(self.bot.config['spam_channel'])
    
    async def report_error(self, fetched_guild=None):
        if fetched_guild is None:
            fetched_guild = await self.get_guild()
        dev_at = self.get_at(await fetched_guild.fetch_member(self.bot.config['dev_id']))
        spam_channel = await self.get_spam_channel()
        await spam_channel.send('Visabot has error - {} get on and fix it you dummy'.format(dev_at))

    # uses config to determine guild
    async def get_bot_status_channel(self, fetched_guild=None) -> discord.TextChannel:
        if fetched_guild is None:
            fetched_guild = await self.get_guild()
        return fetched_guild.fetch_channel(self.bot.config['bot_status_channel'])
    
    def correct_guild_check(self, guild: discord.Guild):
        # expects guild id: int or guild: discord.guild
        if isinstance(guild, discord.Guild):
            if guild.id != self.bot.config['guild_id']:
                return False
        elif isinstance(guild, int):
            if guild != self.bot.config['guild_id']:
                return False
        else:
            return False
        return True
    
    def get_last_around(self) -> datetime.datetime:
        last_around = self.str_datetime_to_datetime_obj(self.timestamp_before_online)
        return last_around

    async def user_to_member(self, user,fetched_guild=None):
        # method to get member from either id or from user object
        if fetched_guild is None:
            fetched_guild = await self.get_guild()
        if isinstance(user,int):
            return await fetched_guild.fetch_member(user)
        if isinstance(user, discord.User):
            return await fetched_guild.fetch_member(user.id)

    def get_nick_or_name(self, member: discord.Member) -> str:
        nickname = member.nick
        if not nickname is None:
            return nickname
        else:
            return member.name

    def get_at(self, member: discord.Member) -> str:
        at_member = "<@" + str(member.id) + ">"
        return at_member

# # And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
# async def setup(bot):
#     await bot.add_cog(Visabot(bot))


class VisaCog(GuildedCog):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        days = 7
        hours = 0
        minutes = 0
        seconds = 0
        if self.bot.config['test_mode'] == True:
            days = 0
            hours = 0
            minutes = 1
            seconds = 0
        self.visa_length = 24*60*60*days + 60*60*hours + 60*minutes +seconds
        self.role_name = "Visa"

    async def get_visa_role(self,fetched_guild=None) -> discord.Role:
        if fetched_guild is None:
            fetched_guild = await self.get_guild()
        visarole = discord.utils.get(fetched_guild.roles, name=self.role_name)
        return visarole

    async def has_visa(self,member,fetched_guild=None) -> bool:
        if fetched_guild is None:
            fetched_guild = await self.get_guild()
        visarole = await self.get_visa_role(fetched_guild)
        if visarole in member.roles:
            return True
        else:
            return False
        
    async def get_all_visarole_members(self, fetched_guild=None):
        if fetched_guild is None:
            fetched_guild = await self.get_guild()
        visarole_members = []
        async for member in fetched_guild.fetch_members(limit=None):
            if await self.has_visa(member):
                visarole_members.append(member)
        return visarole_members
    
    async def get_visa_total(self, fetched_guild=None) -> int:
        if fetched_guild is None:
            fetched_guild = await self.get_guild()
        total = len(await self.get_all_visarole_members(fetched_guild))
        return total