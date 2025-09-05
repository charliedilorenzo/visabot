"""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.5.0
"""

from discord.errors import DiscordException
from discord.ext import commands


class UserBlacklisted(commands.CheckFailure):
    """
    Thrown when a user is attempting something, but is blacklisted.
    """

    def __init__(self, message="User is blacklisted!"):
        self.message = message
        super().__init__(self.message)


class UserNotOwner(commands.CheckFailure):
    """
    Thrown when a user is attempting something, but is not an owner of the bot.
    """

    def __init__(self, message="User is not an owner of the bot!"):
        self.message = message
        super().__init__(self.message)


class IncorrectGuild(commands.CheckFailure):
    """
    Thrown when a user attempts to run a command on a guild that the server is not monitering
    """

    def __init__(self, message="Command run in incorrect guild!"):
        self.message = message
        super().__init__(self.message)


class VisaKickFailure(DiscordException):
    def __init__(self, message="Kicking a user witha a visa has failed"):
        self.message = message
        super().__init__(self.message)
