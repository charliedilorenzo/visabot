"""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.5.0
"""

import asyncio
import json
import logging
import os
import platform
import sys

import aiosqlite
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context
from pathlib import Path
import exceptions
import dotenv
from distutils.util import strtobool
EXPECTED_ENV_VALUES = set([
    "SERVER",
    "TOKEN"
])

env_values = dotenv.dotenv_values(".env")

found_env_keys = EXPECTED_ENV_VALUES.intersection(set(env_values.keys()))
missing_env_keys = EXPECTED_ENV_VALUES - found_env_keys
if missing_env_keys:
  # something like - 'SERVER', 'TOKEN'
  missing_keys_string = '\', \''.join(missing_env_keys)
  print(f"Env requires keys: '{missing_keys_string}'")
  sys.exit(1)


test_mode = strtobool(env_values.get("TEST", True)) == 1
prefix = env_values.get("COMMAND_PREFIX", "visabot")
server = env_values["SERVER"]
token = env_values["TOKEN"]
# sys.exit(0)
config = {}
config["test_mode"] = test_mode
config["token"] = token
config["server_id"] = server

intents = discord.Intents.all()
#theoretically redundant but just in case
intents.message_content = True
intents.members = True
intents.presences = True
intents.guilds = True

bot = Bot(command_prefix=commands.when_mentioned_or(prefix),
          intents=intents,
          help_command=None)


# Setup both of the loggers
class LoggingFormatter(logging.Formatter):
  # Colors
  black = "\x1b[30m"
  red = "\x1b[31m"
  green = "\x1b[32m"
  yellow = "\x1b[33m"
  blue = "\x1b[34m"
  gray = "\x1b[38m"
  # Styles
  reset = "\x1b[0m"
  bold = "\x1b[1m"

  COLORS = {
    logging.DEBUG: gray + bold,
    logging.INFO: blue + bold,
    logging.WARNING: yellow + bold,
    logging.ERROR: red,
    logging.CRITICAL: red + bold
  }

  def format(self, record):
    log_color = self.COLORS[record.levelno]
    format = "(black){asctime}(reset) (levelcolor){levelname:<8}(reset) (green){name}(reset) {message}"
    format = format.replace("(black)", self.black + self.bold)
    format = format.replace("(reset)", self.reset)
    format = format.replace("(levelcolor)", log_color)
    format = format.replace("(green)", self.green + self.bold)
    formatter = logging.Formatter(format, "%Y-%m-%d %H:%M:%S", style="{")
    return formatter.format(record)


logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(LoggingFormatter())
# File handler
file_handler = logging.FileHandler(filename="discord.log",
                                   encoding="utf-8",
                                   mode="w")
file_handler_formatter = logging.Formatter(
  "[{asctime}] [{levelname:<8}] {name}: {message}",
  "%Y-%m-%d %H:%M:%S",
  style="{")
file_handler.setFormatter(file_handler_formatter)

# Add the handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)
bot.logger = logger


async def init_db():
  async with aiosqlite.connect(
      f"{os.path.realpath(os.path.dirname(__file__))}/database/database.db"
  ) as db:
    with open(
        f"{os.path.realpath(os.path.dirname(__file__))}/database/schema.sql"
    ) as file:
      await db.executescript(file.read())
    await db.commit()


"""
Create a bot variable to access the config file in cogs so that you don't need to import it every time.

The config is available using the following code:
- bot.config # In this file
- self.bot.config # In cogs
"""
bot.config = config


@bot.event
async def on_ready() -> None:
  """
    The code in this event is executed when the bot is ready.
    """
  bot.logger.info(f"Logged in as {bot.user.name}")
  bot.logger.info(f"discord.py API version: {discord.__version__}")
  bot.logger.info(f"Python version: {platform.python_version()}")
  bot.logger.info(
    f"Running on: {platform.system()} {platform.release()} ({os.name})")
  bot.logger.info("-------------------")
  basic_activity = discord.Activity(name="you",
                                    type=discord.ActivityType.watching,
                                    status=discord.Status.online)
  await bot.change_presence(activity=basic_activity)
  # TODO what the heck was this for
  if config.get("sync_commands_globally"):
    bot.logger.info("Syncing commands globally...")
    await bot.tree.sync()
  # TODO add visa retroactively
  # TODO purge overstayed visa


@bot.event
async def on_message(message: discord.Message) -> None:
  """
    The code in this event is executed every time someone sends a message, with or without the prefix

    :param message: The message that was sent.
    """
  if message.author == bot.user or message.author.bot:
    return
  await bot.process_commands(message)
  # TODO add for dev is immortal bissh


@bot.event
async def on_command_completion(context: Context) -> None:
  """
    The code in this event is executed every time a normal command has been *successfully* executed.

    :param context: The context of the command that has been executed.
    """
  full_command_name = context.command.qualified_name
  split = full_command_name.split(" ")
  executed_command = str(split[0])
  if context.guild is not None:
    bot.logger.info(
      f"Executed {executed_command} command in {context.guild.name} (ID: {context.guild.id}) by {context.author} (ID: {context.author.id})"
    )
  else:
    bot.logger.info(
      f"Executed {executed_command} command by {context.author} (ID: {context.author.id}) in DMs"
    )


@bot.event
async def on_command_error(context: Context, error) -> None:
  """
    The code in this event is executed every time a normal valid command catches an error.

    :param context: The context of the normal command that failed executing.
    :param error: The error that has been faced.
    """
  if isinstance(error, commands.CommandOnCooldown):
    minutes, seconds = divmod(error.retry_after, 60)
    hours, minutes = divmod(minutes, 60)
    hours = hours % 24
    embed = discord.Embed(
      description=
      f"**Please slow down** - You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
      color=0xE02B2B)
    await context.send(embed=embed)
  elif isinstance(error, exceptions.UserBlacklisted):
    """
        The code here will only execute if the error is an instance of 'UserBlacklisted', which can occur when using
        the @checks.not_blacklisted() check in your command, or you can raise the error by yourself.
        """
    embed = discord.Embed(
      description="You are blacklisted from using the bot!", color=0xE02B2B)
    await context.send(embed=embed)
    bot.logger.warning(
      f"{context.author} (ID: {context.author.id}) tried to execute a command in the guild {context.guild.name} (ID: {context.guild.id}), but the user is blacklisted from using the bot."
    )
  elif isinstance(error, exceptions.UserNotOwner):
    """
        Same as above, just for the @checks.is_owner() check.
        """
    embed = discord.Embed(description="You are not the owner of the bot!",
                          color=0xE02B2B)
    await context.send(embed=embed)
    bot.logger.warning(
      f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the guild {context.guild.name} (ID: {context.guild.id}), but the user is not an owner of the bot."
    )
  elif isinstance(error, commands.MissingPermissions):
    embed = discord.Embed(description="You are missing the permission(s) `" +
                          ", ".join(error.missing_permissions) +
                          "` to execute this command!",
                          color=0xE02B2B)
    await context.send(embed=embed)
  elif isinstance(error, commands.BotMissingPermissions):
    embed = discord.Embed(description="I am missing the permission(s) `" +
                          ", ".join(error.missing_permissions) +
                          "` to fully perform this command!",
                          color=0xE02B2B)
    await context.send(embed=embed)
  elif isinstance(error, commands.MissingRequiredArgument):
    embed = discord.Embed(
      title="Error!",
      # We need to capitalize because the command arguments have no capital letter in the code.
      description=str(error).capitalize(),
      color=0xE02B2B)
    await context.send(embed=embed)
  else:
    raise error


async def load_cogs() -> None:
  """
    The code in this function is executed whenever the bot will start.
    """
  for file in os.listdir(
      f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
    if file.endswith(".py"):
      extension = file[:-3]
      try:
        await bot.load_extension(f"cogs.{extension}")
        bot.logger.info(f"Loaded extension '{extension}'")
      except Exception as e:
        exception = f"{type(e).__name__}: {e}"
        bot.logger.error(f"Failed to load extension {extension}\n{exception}")


asyncio.run(init_db())
asyncio.run(load_cogs())

if not test_mode:
  try:
    keep_alive()
  except:
    print("Website doesn't work?")
    os.system('kill 1')
    os.system('python restarter.py')
try:
  bot.run(config["token"])
except KeyboardInterrupt:
  print('Interrupted')
  sys.exit(0)
except:
  print("BLOCKED BY RATE LIMITING - RESTARTING NOW")
  os.system('kill 1')
  os.system('python restarter.py')
