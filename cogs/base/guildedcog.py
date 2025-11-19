""" "
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.5.0
"""

import shutil
import traceback
from datetime import datetime
from typing import Optional, Union

import discord
from discord import ClientUser, Guild, TextChannel, User
from discord.ext import commands
from discord.ext.commands import CommandError, Context

from bots.basebot import BaseBot
from utils import BASE_PATH, LOG_PATH, MEDIA_PATH


class GuildedCog(commands.Cog):
    def __init__(self, bot: BaseBot):
        self.bot = bot
        self.logger = self.bot.logger
        # manually import this just cause not in config i guess
        self.test_mode = bot.config.test_mode
        self.warning_gif = MEDIA_PATH / "warning_gifs" / "visabot_is_watching_you.gif"
        # this is currently defined in the visa bot but we may waant to move some stuff to another place
        self.guild: Optional[Guild] = None
        self.spam_channel: Optional[TextChannel] = None

    def is_correct_guild_check(self, guild: Guild) -> bool:
        if isinstance(guild, Guild):
            guild = guild.id
        return guild == self.bot.config.server

    async def wrong_guild_message(self, channel: TextChannel, context):
        message = "Visabot is not currently monitoring this server"
        embed = discord.Embed(description=f"{message}", color=0x9C84EF)
        embed.set_footer(text=f"Just trying to get some sleep in...")
        if context is None:
            await channel.send(embed=embed)
        else:
            await context.reply(embed=embed)

    async def user_to_member(self, user: User):
        if isinstance(user, int):
            return await self.guild.fetch_member(user)
        if isinstance(user, discord.User):
            return await self.guild.fetch_member(user.id)

    def get_nick_or_name(self, member: discord.Member) -> str:
        nickname = member.nick
        return nickname if nickname is not None else member.name

    def get_at(self, member: Union[discord.Member, ClientUser]) -> str:
        at_member = "<@" + str(member.id) + ">"
        return at_member

    async def namediscriminator_to_member(self, name: str):
        split = name.split("#")
        name = split[0]
        discriminator = split[1]
        member = self.guild.get_member_named(name, discriminator)
        return member

    async def cog_command_error(self, ctx: Context, error: CommandError):
        if self.bot.config.dev_id:
            dev_at = self.get_at(await self.guild.fetch_member(self.bot.config.dev_id))
        else:
            dev_at = "Dev!"

        # Send messages in spam telling about error and where for mroe details
        spam_channel = self.spam_channel
        error_message = f"Visabot has error - {dev_at} get on and fix it you dummy."
        error_message += f"\nError Type: {type(error).__name__}"
        error_message += f"\nError Args: {error.args}"
        await spam_channel.send(error_message)
        await spam_channel.send(f"Logging errors to {str(LOG_PATH / 'discord.log')}")
        await spam_channel.send(f"I explode now bye")
        explode_gif = MEDIA_PATH / "exit_gifs" / "nge_explode.gif"
        with open(explode_gif, "rb") as f:
            picture = discord.File(f)
            await spam_channel.send(file=picture)
        exception_str = traceback.format_exception(error)
        exception_str = "".join(exception_str)
        exception_str = exception_str.replace("\\n", "\n")
        self.logger.info(exception_str)

        # Copy just in case idiot and you copy over it after running it
        log_path = LOG_PATH / "discord.log"
        formatted_now = datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)")
        shutil.copy(log_path, LOG_PATH / f"discord_error_{formatted_now}.log")

        exit()

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = await self.bot.fetch_guild(self.bot.config.server)
        most_specific_subclass = type(self).mro()[0]
        self.logger.info(f"Starting Cog: {most_specific_subclass.__name__}")
        self.spam_channel = await self.guild.fetch_channel(self.bot.config.spam_channel)
        return
