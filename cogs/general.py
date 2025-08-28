""""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.5.0
"""

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks
from base.cogclasses import ConfigedBot

class General(commands.Cog, name="general"):

  def __init__(self, bot: ConfigedBot):
    self.bot = bot

  @commands.hybrid_command(name="help",
                           description="List all commands the bot has loaded.")
  @checks.not_blacklisted()
  async def help(self, context: Context) -> None:
    prefix = self.bot.config.command_prefix
    embed = discord.Embed(title="Help",
                          description="List of available commands:",
                          color=0x9C84EF)
    # just to make it easier for me to remember there is owner help command
    if context.author.id == self.bot.config.dev_id:
      cog = self.bot.get_cog('owner'.lower())
      commands = cog.get_commands()
      for command in commands:
        if command.name == "ownerhelp":
          data = []
          description = command.description.partition('\n')[0]
          data.append(f"{prefix}{command.name} - {description}")
          help_text = "\n".join(data)
          embed.add_field(name=('owner').capitalize(),
                          value=f'```{help_text}```',
                          inline=False)
    for i in self.bot.cogs:
      cog = self.bot.get_cog(i.lower())
      if i == 'owner':
        continue
      elif i == 'visabot':
        embed = cog.get_help_blurb(embed)
        continue
      commands = cog.get_commands()
      data = []
      for command in commands:
        description = command.description.partition('\n')[0]
        data.append(f"{prefix}{command.name} - {description}")
      help_text = "\n".join(data)
      embed.add_field(name=i.capitalize(),
                      value=f'```{help_text}```',
                      inline=False)
    await context.send(embed=embed)

  @commands.hybrid_command(
    name="botinfo",
    description="Get some useful (or not) information about the bot.",
  )
  @checks.not_blacklisted()
  async def botinfo(self, context: Context) -> None:
    """
        Get some useful (or not) information about the bot.

        :param context: The hybrid command context.
        """
    embed = discord.Embed(
      description="Used [Krypton's](https://krypton.ninja) template",
      color=0x9C84EF)
    embed.set_author(name="Bot Information")
    embed.add_field(
      name="Bot Main Purpose",
      value=
      "People who join the server will be kicked automatically after 7 days if no mod intervenes. This is achieved through the \"visa\" role. In order to prevent autokicking, be nice and cool and ask a mod to remove your visa role if you've warmed up to the server."
    )
    embed.add_field(name="Owner:", value="Bernoulli#2628", inline=True)
    embed.add_field(
      name="Prefix:",
      value=
      f"/ (Slash Commands) or {self.bot.config.command_prefix} for normal commands",
      inline=False)
    embed.set_footer(text=f"Requested by {context.author}")
    await context.send(embed=embed)

  @commands.hybrid_command(
    name="serverinfo",
    description="Get some useful (or not) information about the server.",
  )
  @checks.not_blacklisted()
  async def serverinfo(self, context: Context) -> None:
    """
        Get some useful (or not) information about the server.

        :param context: The hybrid command context.
        """
    description = f"{context.guild}\n"
    description += "\n**Server Intro**:\n This server is for gamers and anime. We play a variety of games (with Game Nights on Fridays!) and host anime watching sessions.\n"
    description += f"**Member Count**:\n {context.guild.member_count}"
    # description += f"**Created at**:\n {context.guild.member_count}."

    embed = discord.Embed(title="**Server Name:**",
                          description=description,
                          color=0x9C84EF)
    if context.guild.icon is not None:
      embed.set_thumbnail(url=context.guild.icon.url)

    # embed.add_field(
    #   name="Server Intro",
    #   value=
    #   "This server is for gamers and anime. We play a variety of games (with Game Nights on Fridays!) and host anime watching sessions."
    # )
    # embed.add_field(name="Server ID", value=context.guild.id)
    # embed.add_field(name="Member Count", value=context.guild.member_count)
    embed.set_footer(text=f"Created at: {context.guild.created_at}")
    await context.send(embed=embed)

  @commands.hybrid_command(
    name="ping",
    description="Check if the bot is alive.",
  )
  @checks.not_blacklisted()
  async def ping(self, context: Context) -> None:
    """
        Check if the bot is alive.

        :param context: The hybrid command context.
        """
    embed = discord.Embed(
      title="🏓 Pong!",
      description=f"The bot latency is {round(self.bot.latency * 1000)}ms.",
      color=0x9C84EF)
    await context.send(embed=embed)


async def setup(bot):
  await bot.add_cog(General(bot))
