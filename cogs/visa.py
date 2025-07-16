""""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.5.0
"""

from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context

from helpers import checks
import discord
import math
import os
import random
from .cogclasses import VisaCog


# TODO add last offline to db or somethings
# Here we name the cog and create a new class for the cog.
# TODO make another cog with some kind of polls function?
class Visabot(VisaCog, name="visabot"):

  def get_help_blurb(self, embed: discord.Embed) -> str:
    prefix = self.bot.config['prefix']
    commands_list = self.get_commands()
    # pretty much manual cause im lazy
    data = []
    unlisted = ['designate_spam_channel', 'designate_status_channel']
    for command in commands_list:
      if command.name in unlisted:
        continue
      description = command.description.partition('\n')[0]
      data.append(f"{prefix}{command.name} - {description}")
      if command.name == "visa":
        data.append(f"")
        for other_command in command.walk_commands():
          description = other_command.description.partition('\n')[0]
          data.append(
            f"{prefix}{command.name} {other_command.name} - {description}")
    help_text = "\n".join(data)
    embed.add_field(name=self.__cog_name__.capitalize(),
                    value=f'```{help_text}```',
                    inline=False)
    return embed

  def __init__(self, bot: Bot):
    super().__init__(bot)

  def time_left_value_seconds(self, member: discord.Member) -> int:
    now = self.get_now()
    joined = member.joined_at
    seconds_diff = (now - joined).total_seconds()
    if seconds_diff > self.visa_length:
      return 0
    else:
      return self.visa_length - int(seconds_diff)

  def time_left_message(self, member: discord.Member) -> str:
    time = self.time_left_value_seconds(member)
    time = math.floor(time / 60)
    minutes = time % 60
    time = math.floor(time / 60)
    hours = time % 24
    time = math.floor(time / 24)
    days = time
    return (
      ' ~{} Days, {} Hours, and {} Minutes remaining on your visa.').format(
        days, hours, minutes)

  async def visa_status_message(self,
                                members: list,
                                channel: discord.TextChannel,
                                fetched_guild=None) -> bool:
    if fetched_guild == None:
      fetched_guild = await self.get_guild()
    extra_warning = False
    message = ""
    non_permanent_detected = False
    for member in members:
      time_left_val = self.time_left_value_seconds(member)
      if await self.has_visa(member, fetched_guild):
        non_permanent_detected = True
        message += "{} has {} \n".format(self.get_nick_or_name(member),
                                         self.time_left_message(member))
        if time_left_val < 60 * 60 * 12:
          extra_warning = True
      else:
        message += "{} is considered a permanent member of the server.\n".format(
          self.get_nick_or_name(member))
    if extra_warning:
      with open(self.warning_gif, 'rb') as f:
        picture = discord.File(f)
        await channel.send(file=picture)
    if non_permanent_detected:
      message += "\nYou have to reach out if you don\'t want your visa to expire, otherwise you will be **kicked** from the server automatically."
    return message

  async def send_random_delete_gif(self, channel: discord.TextChannel) -> str:
    purge_directory = os.path.join(self.main_dir, "purge_gifs")
    delete_gifs = []
    for file in os.listdir(purge_directory):
      if file.endswith(".gif"):
        delete_gifs.append(purge_directory + "/" + file)
    gif = random.choice(delete_gifs)
    with open(gif, 'rb') as f:
      picture = discord.File(f)
      await channel.send(file=picture)

  @commands.hybrid_group(
    name="visa",
    description=
    "Get information about visa duration/status:     !visa, !visa all, !visa <@another>, !visa another#1234",
  )
  @checks.not_blacklisted()
  async def visa(self, context: Context):
    """
        Lets you add or remove a user from not being able to use the bot.

        :param context: The hybrid command context.
        """
    if not self.correct_guild_check(context.guild):
      return
    member = ""
    message = context.message
    if message.content == "!visa":
      member = await self.user_to_member(context.author.id, context.guild)
    elif "@" in message.content:
      # this will error if anything other than a properly formatted user id is after the at and in between the "<" and ">"
      start = message.content.index("<") + 2
      end = message.content.index(">")
      id = int(message.content[start:end])
      member = await context.guild.fetch_member(id)
    else:
      # only looking for name # discriminator
      start = message.content.index(" ") + 1
      after_visa_content = message.content[start:len(message.content)]
      found = False
      async for member in context.guild.fetch_members(limit=None):
        name = member.name + "#" + member.discriminator
        if after_visa_content == name:
          found = True
          # member is assigned properly
          break
      if not found:
        embed = discord.Embed(
          description=
          f"Member {after_visa_content} not found. Make sure you have the correct \"name#discriminator\" combination.",
          color=0x9C84EF)
        await context.send(embed=embed)
        return

    if member != "":
      message = await self.visa_status_message([member], context.channel,
                                               context.guild)
      embed = discord.Embed(description=f"{message}", color=0x9C84EF)
      total = len((await self.get_visa_role(context.guild)).members)
      embed.set_footer(
        text=
        f"There {'is' if total == 1 else 'are'} {total} {'member' if total == 1 else 'member'} with the Visa role."
      )
      await context.send(embed=embed)
    elif context.invoked_subcommand is None:
      embed = discord.Embed(
        description=
        "You need to specify a subcommand.\n\n**Subcommands:**\n`add` - Add a user to the blacklist.\n`remove` - Remove a user from the blacklist.",
        color=0xE02B2B)
      await context.send(embed=embed)

  @visa.command(
    base="visa",
    name="all",
    description="Shows all Visa members and their durations.",
  )
  @checks.not_blacklisted()
  async def visa_all(self, context: Context) -> None:
    """
        Lists all members with the visa role and calculates their remaining duration

        :param context: The hybrid command context.
        """
    if not self.correct_guild_check(context.guild):
      return
    visa_members = await self.get_all_visarole_members(context.guild)
    if len(visa_members) == 0:
      message = "No one with a visa role has been found. You are all safe... for now..."
      embed = discord.Embed(description=f"{message}", color=0x9C84EF)
      embed.set_footer(text=f"Time to vibe with all the other citizens.")
    else:
      message = await self.visa_status_message(visa_members, context.channel,
                                               context.guild)
      embed = discord.Embed(description=f"{message}", color=0x9C84EF)
      total = len((await self.get_visa_role(context.guild)).members)
      embed.set_footer(
        text=
        f"There {'is' if total == 1 else 'are'} {total} {'member' if total == 1 else 'member'} with the Visa role."
      )
    await context.send(embed=embed)

  @visa.command(
    base="visa",
    name="self",
    description="Gives author's visa duration/status.",
  )
  @checks.not_blacklisted()
  async def visa_self(self, context: Context) -> None:
    """
        If the member has a Visa role their visa duration is given. If they are not a visa member, states they are not.

        :param context: The hybrid command context.
        """
    if not self.correct_guild_check(context.guild):
      return
    member = await self.user_to_member(context.author.id, context.guild)
    message = await self.visa_status_message([member], context.channel,
                                             context.guild)
    embed = discord.Embed(description=f"{message}", color=0x9C84EF)
    total = len((await self.get_visa_role(context.guild)).members)
    embed.set_footer(
      text=
      f"There {'is' if total == 1 else 'are'} {total} {'member' if total == 1 else 'member'} with the Visa role."
    )
    await context.send(embed=embed)

  @visa.command(
    base="visa",
    name="other",
    description="Gives the visa duration/status of another.",
  )
  @checks.not_blacklisted()
  async def visa_other(self, context: Context, user: discord.User) -> None:
    """
        If the member has a Visa role their visa duration is given. If they are not a visa member, states they are not.

        :param context: The hybrid command context.
        """
    if not self.correct_guild_check(context.guild):
      return
    member = await self.user_to_member(user, context.guild)
    message = await self.visa_status_message([member], context.channel,
                                             context.guild)
    embed = discord.Embed(description=f"{message}", color=0x9C84EF)
    total = len((await self.get_visa_role(context.guild)).members)
    embed.set_footer(
      text=
      f"There {'is' if total == 1 else 'are'} {total} {'member' if total == 1 else 'member'} with the Visa role."
    )
    await context.send(embed=embed)
    # TODO when people ask for my visa tell them im super cool i will never get kicked by visabot but say it cool
  @visa.command(
    base="visa",
    name="timer",
    description="Gives the default inital visa timer.",
  )
  @checks.not_blacklisted()
  async def visa_timer(self, context: Context) -> None:
    """
        Gives it in days, hours, minutes, seconds

        :param context: The hybrid command context.
        """
    visa_time = self.visa_length
    seconds = visa_time % 60
    visa_time = math.floor(visa_time / 60)
    minutes = visa_time % 60
    visa_time = math.floor(visa_time / 60)
    hours = visa_time % 60
    visa_time = math.floor(visa_time / 60)
    days = visa_time % 60
    visa_time = math.floor(visa_time / 60)

    timer_message = "{} Days, {} Hours, {} Minutes, {} Seconds".format(
      days, hours, minutes, seconds)
    embed = discord.Embed(
      description=f"The timer is currently set to: {timer_message}",
      color=0x9C84EF)
    total = len((await self.get_visa_role(context.guild)).members)
    embed.set_footer(
      text=
      f"There {'is' if total == 1 else 'are'} {total} {'member' if total == 1 else 'member'} with the Visa role."
    )
    await context.send(embed=embed)

  @commands.hybrid_command(
    name="kickgif", description="Sends a random autokick gif to the channel.")
  @checks.not_blacklisted()
  async def kickgif(self, context: Context) -> None:
    await self.send_random_delete_gif(context.channel)

  @commands.Cog.listener()
  async def on_member_join(self, member):
    guild = member.guild
    if not self.correct_guild_check(guild):
      return
    member_id = member.id
    member = await guild.fetch_member(member_id)
    visarole = await self.get_visa_role(guild)
    await member.add_roles(visarole)
    now = self.get_now()
    name = self.get_at(member)
    warning_message = ("{} has been given a visa. \n You have {}.").format(
      name, self.time_left_message(member))
    spam_channel = await self.get_spam_channel()
    await spam_channel.send("{}".format(name))
    embed = discord.Embed(description=f"{warning_message}")
    total = await self.get_visa_total()
    embed.set_footer(
      text=
      f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} with the Visa role."
    )
    await spam_channel.send(embed=embed)
    self.update_var_json({'LAST_TIME_OF_ACTION': str(now)})

  @commands.Cog.listener()
  async def on_message(self, message):
    # all of these are for memes and testing
    guild = message.guild
    if not self.correct_guild_check(guild):
      return
    delete_me_messages = [
      "delete me", "kill me", "what would it look like if i got deleted?",
      "what would it look like if i got deleted", "end me", "show me my end",
      "execute me", "destroy me", "let it end"
    ]
    # prevent infinite recursion
    if message.author == self.bot.user:
      return
    visabot = await guild.fetch_member(self.bot.config['application_id'])
    if message.content.lower() in delete_me_messages:
      await self.send_random_delete_gif(message.channel)
    # sometimes "<@&" in message.content instead?
    elif (self.get_at(visabot)) in message.content:
      if (message.author.id == self.bot.config['dev_id']):
        await message.channel.send('kashikomarimashita Charlie-sama ')
        return
      await message.channel.send('oh no im a little baby')

  async def add_visa_after_offline(self) -> bool:
    guild = await self.bot.fetch_guild(self.bot.config['guild_id'])
    last_around = self.get_last_around()
    joined_during_offline_members = []
    print(self.bot.config["spam_channel"])
    spam_channel = await self.get_spam_channel()
    async for member in guild.fetch_members(limit=None):
      if (last_around - member.joined_at).total_seconds() <= 0:
        joined_during_offline_members.append(member)
    visarole = await self.get_visa_role(guild)
    success = True
    for member in joined_during_offline_members:
      if not (await self.has_visa(member, guild)):
        name = self.get_at(member)
        await member.add_roles(visarole)
        await spam_channel.send("{}".format(name))
        warning_message = ("{} has been given a visa. \n You have {}.").format(
          name, self.time_left_message(member))
        embed = discord.Embed(description=f"{warning_message}")
        total = await self.get_visa_total()
        embed.set_footer(
          text=
          f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} with the Visa role."
        )
        await spam_channel.send(embed=embed)
        refetch_member = await guild.fetch_member(member.id)
        # check if we added visa role
        if not (await self.has_visa(refetch_member, guild)):
          success = False
    return success

  @commands.Cog.listener()
  async def on_ready(self):
    success = await self.add_visa_after_offline()
    if not success:
      spam_channel = await self.get_spam_channel()
      await spam_channel.send('Adding Visas has failed')
      await self.report_error()

    success = await self.purge_all_overstayed_visa()
    if not success:
      spam_channel = await self.get_spam_channel()
      await spam_channel.send('Purge has failed')
      await self.report_error()
    self.purge_visas_background_task.start()
    status_channel = await self.get_bot_status_channel()
    await status_channel.send("Visabot Online")
    return

  @commands.Cog.listener()
  async def on_disconnect(self):
    status_channel = await self.get_bot_status_channel()
    await status_channel.send("Visabot Offline")

  async def attempt_kick_visarole_member(self, member: discord.Member,
                                         guild: discord.Guild) -> bool:
    # returns [success, was_kicked]
    if not self.correct_guild_check(guild):
      return
    name = self.get_at(member)
    visarole = await self.get_visa_role(guild)
    spam_channel = await self.get_spam_channel()

    # the message and result on true error
    message = "An error has occured: likely {} that visabot attempted to kick is still on the server.".format(
      name)
    result = [False, False]
    try:
      await guild.kick(member)
      refetch_member = await guild.fetch_member(member.id)
      # here is a success since we cannot find the member they have been properly kicked from the server
    except discord.NotFound:
      message = '{}\'s visa has expired. They have been kicked.'.format(name)
      result = [True, True]
      # visabot attempted to kick someone with higher perms, that is probably not an error in visabot
    except discord.Forbidden:
      message = "{} has a higher role and does not need a visa.\n".format(name)
      await member.remove_roles(visarole)
      refetch_member = await guild.fetch_member(member.id)
      # check if we added visa role
      if await self.has_visa(refetch_member, guild):
        message += "An error has occured where a permanent member of the server, {}, has retained their visa role after attempted of removal of visa role".format(
          name)
        result = [False, False]
      else:
        message += "Visa has been removed from {}. You are considered a permanent member of the server".format(
          name)
        result = [True, False]

    embed = discord.Embed(description=f"{message}", color=0x9C84EF)
    total = await self.get_visa_total()
    embed.set_footer(
      text=
      f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} with the Visa role."
    )
    await spam_channel.send(embed=embed)
    return result

  async def purge_all_overstayed_visa(self) -> bool:
    success = True
    execution_executed = False
    guild = self.bot.get_guild(self.bot.config['guild_id'])
    kick_list = await self.get_all_visarole_members(guild)
    spam_channel = await self.get_spam_channel()
    for member in kick_list:
      if self.time_left_value_seconds(member) <= 0:
        tracker_bools = await self.attempt_kick_visarole_member(member, guild)
        single_success = tracker_bools[0]
        single_execution = tracker_bools[1]
        success = single_success and success
        execution_executed = execution_executed or single_execution
    if execution_executed:
      await spam_channel.send('Commencing execution:')
      await self.send_random_delete_gif(spam_channel)
    return success

  @tasks.loop(seconds=300)  # task runs every 5 minutes
  async def purge_visas_background_task(self):
    print("Purging Visas")
    success = await self.purge_all_overstayed_visa()
    if success:
      pass
    else:
      spam_channel = await self.get_spam_channel()
      await spam_channel.send('Purge has failed')
      await self.report_error()
    now = self.get_now()
    self.update_var_json({'LAST_TIME_OF_ACTION': str(now)})

  @purge_visas_background_task.before_loop
  async def before_purge_background_task(self):
    await self.bot.wait_until_ready()  # wait until the bot logs in


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot):
  await bot.add_cog(Visabot(bot))
