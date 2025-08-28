""" "
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.5.0
"""

import datetime
from typing import Optional, Union

import discord
from discord import ClientUser, Guild, User
from discord.ext import commands
from discord.ext.commands import Context

from base import MEDIA_PATH
from base.config import ConfigedBot
from helpers import checks


class GuildedCog(commands.Cog):

    def get_now(self) -> datetime.datetime:
        return datetime.datetime.now((datetime.timezone.utc))

    def str_datetime_to_datetime_obj(self, str_datetime: str) -> datetime.datetime:
        datetime_obj = datetime.datetime.strptime(
            str_datetime, "%Y-%m-%d %H:%M:%S.%f%z"
        )
        return datetime_obj

    def __init__(self, bot: ConfigedBot):
        self.bot = bot
        # manually import this just cause not in config i guess
        self.test_mode = bot.config.test_mode
        self.warning_gif = MEDIA_PATH / "warning_gifs" / "visabot_is_watching_you.gif"
        # this is currently defined in the visa bot but we may waant to move some stuff to another place
        self.guild: Optional[Guild] = None

    # uses config to determine guild
    async def get_spam_channel(self, fetched_guild=None) -> discord.TextChannel:
        if fetched_guild is None:
            fetched_guild = self.guild
        return await fetched_guild.fetch_channel(self.bot.config.spam_channel)

    async def report_error(self, fetched_guild=None):
        if fetched_guild is None:
            fetched_guild = self.guild
        if self.bot.config.dev_id:
            dev_at = self.get_at(
                await fetched_guild.fetch_member(self.bot.config.dev_id)
            )
            spam_channel = await self.get_spam_channel()
            await spam_channel.send(
                f"Visabot has error - {dev_at} get on and fix it you dummy."
            )

    # uses config to determine guild
    async def get_bot_status_channel(self, fetched_guild=None) -> discord.TextChannel:
        if fetched_guild is None:
            fetched_guild = self.guild
        return await fetched_guild.fetch_channel(self.bot.config.bot_status_channel)

    def is_correct_guild_check(self, guild: discord.Guild) -> bool:
        # expects guild id: int or guild: discord.guild
        if isinstance(guild, discord.Guild):
            guild = guild.id
        return guild == self.bot.config.server

    async def wrong_guild_message(self, channel: discord.TextChannel, context):
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

    @commands.hybrid_command(
        name="designate_spam_channel",
        description="Give a text channel to designate it as the bot spam channel.",
    )
    @checks.is_owner()
    async def designate_spam_channel(
        self, context: Context, channel: discord.TextChannel
    ) -> None:
        """
        The bot will say anything you want, but using embeds.

        :param context: The hybrid command context.
        :param message: The message that should be repeated by the bot.
        """
        # TODO this should be stored with database
        raise NotImplementedError("This is currently no longer implemented")
        self.bot.config.spam_channel = channel.id
        message = f"The bot's spam channel has been updated to: '{channel.name}'"
        embed = discord.Embed(description=message, color=0x9C84EF)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="designate_status_channel",
        description="Give a text channel to designate it as the bot spam channel.",
    )
    @checks.is_owner()
    async def designate_status_channel(
        self, context: Context, channel: discord.TextChannel
    ) -> None:
        """
        The bot will say anything you want, but using embeds.

        :param context: The hybrid command context.
        :param message: The message that should be repeated by the bot.
        """
        # TODO this should be stored with database
        raise NotImplementedError("This is currently no longer implemented")
        self.bot.config.bot_status_channel = channel.id

        message = f"The bot's status channel has been updated to: '{channel.name}'"
        embed = discord.Embed(description=message, color=0x9C84EF)
        await context.send(embed=embed)
        await context.send(embed=embed)
