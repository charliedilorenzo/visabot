""""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.5.0
"""

from discord.ext import commands
from discord.ext.commands import Bot, Context
import datetime

from helpers import checks
import discord
import os
import json
from typing import TypedDict
from pathlib import Path
from base import MEDIA_PATH


def fetch_guild(func):
  async def _wrapper(*args, **kwargs):
    if fetched_guild := kwargs.get("fetched_guild"):
      if fetched_guild is None:
        self: VisaCog = args[0]
        kwargs["fetched_guild"] = await self.get_guild()
    result = await func(*args, **kwargs)
    return result

  return _wrapper


class Config(TypedDict):
  test_mode: True
  token: str
  server_id: str
  spam_channel: str

class ConfigedBot(Bot):
  config: Config

class GuildedCog(commands.Cog):

  def get_now(self) -> datetime.datetime:
    return datetime.datetime.now((datetime.timezone.utc))

  def str_datetime_to_datetime_obj(self,
                                   str_datetime: str) -> datetime.datetime:
    datetime_obj = datetime.datetime.strptime(str_datetime,
                                              "%Y-%m-%d %H:%M:%S.%f%z")
    return datetime_obj

  def __init__(self, bot: ConfigedBot):
    self.bot = bot
    # manually import this just cause not in config i guess
    self.test_mode = bot.config['test_mode']
    self.warning_gif = MEDIA_PATH / "warning_gifs" / "visabot_is_watching_you.gif"
    self.server_id = self.bot.get_guild(self.bot.config['server_id'])

  async def get_guild(self) -> discord.Guild:
    guild = await self.bot.fetch_guild(self.bot.config['server_id'])
    return guild

  # uses config to determine guild
  async def get_spam_channel(self, fetched_guild=None) -> discord.TextChannel:
    if fetched_guild is None:
      fetched_guild = await self.get_guild()
    return await fetched_guild.fetch_channel(self.bot.config["spam_channel"])

  async def report_error(self, fetched_guild=None):
    if fetched_guild is None:
      fetched_guild = await self.get_guild()
    dev_at = self.get_at(await fetched_guild.fetch_member(self.bot.config['dev_id']))
    spam_channel = await self.get_spam_channel()
    await spam_channel.send(
      'Visabot has error - {} get on and fix it you dummy'.format(dev_at))

  # uses config to determine guild
  async def get_bot_status_channel(self,
                                   fetched_guild=None) -> discord.TextChannel:
    if fetched_guild is None:
      fetched_guild = await self.get_guild()
    return await fetched_guild.fetch_channel(
      self.bot.config['bot_status_channel'])

  def correct_guild_check(self, guild: discord.Guild):
    # expects guild id: int or guild: discord.guild
    if isinstance(guild, discord.Guild):
      guild = guild.id
    return guild == self.bot.config['server_id']

  async def wrong_guild_message(self, channel: discord.TextChannel,
                                context):
    message = "Visabot is not currently monitoring this server"
    embed = discord.Embed(description=f"{message}", color=0x9C84EF)
    embed.set_footer(text=f"Just trying to get some sleep in...")
    if context is None:
      await channel.send(embed=embed)
    else:
      await context.reply(embed=embed)

  def get_last_around(self) -> datetime.datetime:
    # raise NotImplementedError("Not getting last around rn")
    print("SKIPPING LAST AROUND")

  async def user_to_member(self, user, fetched_guild=None):
    # method to get member from either id or from user object
    if fetched_guild is None:
      fetched_guild = await self.get_guild()
    if isinstance(user, int):
      return await fetched_guild.fetch_member(user)
    if isinstance(user, discord.User):
      return await fetched_guild.fetch_member(user.id)

  def get_nick_or_name(self, member: discord.Member) -> str:
    nickname = member.nick
    return nickname if nickname is not None else member.name

  def get_at(self, member: discord.Member) -> str:
    at_member = "<@" + str(member.id) + ">"
    return at_member

  async def namediscriminator_to_member(self,
                                        name: str,
                                        fetched_guild=None
                                        ) :
    if fetched_guild is None:
      fetched_guild = await self.get_guild()
    split = name.split("#")
    name = split[0]
    discriminator = split[1]
    member = fetched_guild.get_member_named(name, discriminator)
    return member

  @commands.hybrid_command(
    name="designate_spam_channel",
    description="Give a text channel to designate it as the bot spam channel.",
  )
  @checks.is_owner()
  async def designate_spam_channel(self, context: Context,
                                   channel: discord.TextChannel) -> None:
    """
    The bot will say anything you want, but using embeds.

    :param context: The hybrid command context.
    :param message: The message that should be repeated by the bot.
    """
    # TODO this should be stored with database
    raise NotImplementedError("This is currently no longer implemented")
    self.bot.config['spam_channel'] = channel.id
    message = "The bot's spam channel has been updated to: {}".format(
      channel.name)
    embed = discord.Embed(description=message, color=0x9C84EF)
    await context.send(embed=embed)

  @commands.hybrid_command(
    name="designate_status_channel",
    description="Give a text channel to designate it as the bot spam channel.",
  )
  @checks.is_owner()
  async def designate_status_channel(self, context: Context,
                                     channel: discord.TextChannel) -> None:
    """
    The bot will say anything you want, but using embeds.

    :param context: The hybrid command context.
    :param message: The message that should be repeated by the bot.
    """
    # TODO this should be stored with database
    raise NotImplementedError("This is currently no longer implemented")
    self.bot.config['bot_status_channel'] = channel.id

    message = "The bot's status channel has been updated to: {}".format(
      channel.name)
    embed = discord.Embed(description=message, color=0x9C84EF)
    await context.send(embed=embed)


class VisaCog(GuildedCog):

  def __init__(self, bot: Bot):
    super().__init__(bot)

    # if self.bot.config['test_mode'] == True:
    #   self.visa_length = datetime.timedelta(minutes=1)
    # else:
    #   self.visa_length = datetime.timedelta(days=7)
    days = 7
    hours = 0
    minutes = 0
    seconds = 0
    if self.bot.config['test_mode'] == True:
      days = 0
      hours = 0
      minutes = 1
      seconds = 0
    self.visa_length = 24 * 60 * 60 * days + 60 * 60 * hours + 60 * minutes + seconds
    self.role_name = "Visa"

  async def get_visa_role(self, fetched_guild=None) -> discord.Role:
    if fetched_guild is None:
      fetched_guild = await self.get_guild()
    visarole = discord.utils.get(fetched_guild.roles, name=self.role_name)
    return visarole

  @fetch_guild
  async def has_visa(self, member: discord.Member, fetched_guild=None) -> bool:
    # if fetched_guild is None:
    #   fetched_guild = await self.get_guild()
    visarole = await self.get_visa_role(fetched_guild)
    return visarole in member.roles

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
