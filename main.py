import discord
import datetime
import math
from discord.ext import tasks, commands
import json
import os
from keep_alive import keep_alive
import random


def get_now():
  return datetime.datetime.now((datetime.timezone.utc))


def str_datetime_to_datetime_obj(str_datetime: str) -> datetime.datetime:
  datetime_obj = datetime.datetime.strptime(str_datetime,
                                            "%Y-%m-%d %H:%M:%S.%f%z")
  return datetime_obj


class MyClient(discord.Client):

  async def get_guild(self) -> discord.Guild:
    guild = await client.fetch_guild(self.guild_id)
    return guild

  async def get_visa_role(self) -> discord.Role:
    guild = await self.get_guild()
    visarole = discord.utils.get(guild.roles, name="Visa")
    return visarole

  async def get_admin_spam_channel(self) -> discord.TextChannel:
    guild = await self.get_guild()
    spam_channel = await guild.fetch_channel(self.spam_channel)
    return spam_channel

  def get_nick_or_name(self, member: discord.Member) -> str:
    nickname = member.nick
    if not nickname is None:
      return nickname
    else:
      return member.name

  def get_at(self, member: discord.Member) -> str:
    at_member = "<@" + str(member.id) + ">"
    return at_member

  def get_json_data(self) -> dict:
    with open(self.tracker_file, 'r') as openfile:
      data = json.load(openfile)
    return data

  def update_var_json(self, new_data: dict) -> bool:
    data = self.get_json_data()
    data.update(new_data)
    with open(self.tracker_file, "w") as outfile:
      json.dump(data, outfile)

    return True

  async def get_dev_member(self) -> discord.Member:
    guild = await self.get_guild()
    dev_member = await guild.fetch_member(self.dev_user_id)
    return dev_member

  def get_last_around(self) -> datetime.datetime:
    last_around = str_datetime_to_datetime_obj(self.timestamp_before_online)
    return last_around

  async def get_all_visarole_members(self):
    visarole_members = []
    guild = await self.get_guild()
    async for member in guild.fetch_members(limit=None):
      if await self.has_visa(member):
        visarole_members.append(member)
    return visarole_members

  def __init__(self, data: dict, test_mode: bool, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # just manually set timeframe here
    days = 7
    hours = 0
    minutes = 0
    seconds = 0
    if test_mode:
      days = 0
      hours = 0
      minutes = 1
      seconds = 0
    self.warning_gif = "visabot_is_watching_you.gif"
    self.visa_length_static = [days, hours, minutes, seconds]
    self.guild_id = data['GUILD_ID']
    self.spam_channel = data['SPAM_CHANNEL']
    self.bot_id = data['BOT_ID']
    self.dev_user_id = data['DEV_ID']
    self.bot_status_channel = data['BOT_STATUS_CHANNEL']
    #for while on replit
    if test_mode == True
      self.main_dir = os.getcwd()
    #for while on replit
    else:
      self.main_dir = "/home/runner/visabot"

    self.tracker_file = "var_tracker.json"
    if test_mode:
      self.tracker_file = "test_" + self.tracker_file

    # this should never run but just in case
    if not os.path.exists(self.tracker_file):
      now = get_now()
      init_data = {'LAST_TIME_OF_ACTION': str(now), 'ASSIGNED': []}
      with open(self.tracker_file, 'w') as openfile:
        json.dump(init_data, openfile)
    data = self.get_json_data()
    self.timestamp_before_online = data['LAST_TIME_OF_ACTION']
    # just in case to avoid infinite loops
    self.error_counter = 0

  async def send_to_spam(self, message):
    spam_channel = await self.get_admin_spam_channel()
    await spam_channel.send(message)

  def time_left_value_seconds(self, member: discord.Member) -> int:
    now = get_now()
    joined = member.joined_at
    seconds_diff = (now - joined).total_seconds()

    # currently this is just hard coded
    days = self.visa_length_static[0]
    hours = self.visa_length_static[1]
    minutes = self.visa_length_static[2]
    seconds = self.visa_length_static[3]

    visa_length = 60 * 60 * 24 * days + 60 * 60 * hours + 60 * minutes + seconds

    if seconds_diff > visa_length:
      return 0
    else:
      return visa_length - int(seconds_diff)

  def time_left_message(self, member: discord.Member) -> str:
    time = self.time_left_value_seconds(member)
    # seconds = time % 60
    time = math.floor(time / 60)
    minutes = time % 60
    time = math.floor(time / 60)
    hours = time % 24
    time = math.floor(time / 24)
    days = time
    return (
      ' ~{} Days, {} Hours, and {} Minutes remaining on your visa. \n You have to reach out if you don\'t want it to expire, otherwise you will be **kicked** from the server.'
    ).format(days, hours, minutes)

  def get_random_delete_gif(self) -> str:
    purge_directory = self.main_dir + "/purge_gifs"
    delete_gifs = []
    for file in os.listdir(purge_directory):
      if file.endswith(".gif"):
        delete_gifs.append(purge_directory + "/" + file)
    random_gif = random.choice(delete_gifs)
    return random_gif

  async def attempt_kick_visarole_member(self, member) -> bool:
    # returns [success, was_kicked]
    guild = await self.get_guild()
    name = self.get_at(member)
    visarole = await self.get_visa_role()
    # attempt to kick
    try:
      await guild.kick(member)
      refetch_member = await guild.fetch_member(member.id)
    # here is a success since we cannot find the member they have been properly kicked from the server
    except discord.NotFound:
      await self.send_to_spam(
        '{}\'s visa has expired. They have been kicked.'.format(name))
      return [True, True]
    # visabot attempted to kick someone with higher perms, that is probably not an error in visabot
    except discord.Forbidden:
      await self.send_to_spam(
        "{} has a higher role and does not need a visa.".format(name))
      await member.remove_roles(visarole)
      refetch_member = await guild.fetch_member(member.id)
      # check if we added visa role
      if await self.has_visa(refetch_member):
        await self.send_to_spam(
          "An error has occured where a permanent member of the server, {}, has retained their visa role after attempted     removal of visa role"
          .format(name))
        return [False, False]
      else:
        await self.send_to_spam(
          "Visa has been removed from {}. You are considered a permanent member of the server"
          .format(name))
        return [True, False]
    # there is no reason we should be here. likely the refetch member was successful and a member wasn't kicked when they should've been
    await self.send_to_spam(
      "An error has occured: likely {} that visabot attempted to kick is still on the server."
      .format(name))
    return [False, False]

  async def purge_all_overstayed_visa(self) -> bool:
    success = True
    execution_executed = False
    kick_list = await self.get_all_visarole_members()
    for member in kick_list:
      if self.time_left_value_seconds(member) <= 0:
        tracker_bools = await self.attempt_kick_visarole_member(member)
        single_success = tracker_bools[0]
        single_execution = tracker_bools[1]
        success = single_success and success
        execution_executed = execution_executed or single_execution

    if execution_executed:
      await self.send_to_spam('Commencing execution:')
      random_purge_gif = self.get_random_delete_gif()
      with open(random_purge_gif, 'rb') as f:
        picture = discord.File(f)
        spam_channel = await self.get_admin_spam_channel()
        await spam_channel.send(file=picture)
    return success

  async def visa_status_message(self, members: list, channel) -> bool:
    extra_warning = False
    for member in members:
      time_left_val = self.time_left_value_seconds(member)
      has_visa_message = "{} has {}".format(self.get_nick_or_name(member),
                                            self.time_left_message(member))
      no_visa_message = (
        "{} is considered a permanent member of the server.".format(
          self.get_nick_or_name(member)))
      has_visa = await self.has_visa(member)
      if has_visa:
        await channel.send(has_visa_message)
        if time_left_val < 60 * 60 * 12:
          extra_warning = True
      else:
        await channel.send(no_visa_message)
    if extra_warning:
      with open(self.warning_gif, 'rb') as f:
        picture = discord.File(f)
        await channel.send(file=picture)
    return True

  async def has_visa(self, member) -> bool:
    visarole = await self.get_visa_role()
    if visarole in member.roles:
      return True
    else:
      return False

  async def on_message(self, message):
    guild = await self.get_guild()
    # this is just for memes
    delete_me_messages = [
      "delete me", "kill me", "what would it look like if i got deleted?",
      "what would it look like if i got deleted", "end me", "show me my end",
      "execute me", "destroy me", "let it end"
    ]
    # wrong guild
    if message.guild != guild:
      return
    # prevent infinite recursion
    if message.author == client.user:
      return
    cleaned = message.clean_content
    visabot = await guild.fetch_member(self.bot_id)
    if message.content.lower() in delete_me_messages:
      random_purge_gif = self.get_random_delete_gif()
      with open(random_purge_gif, 'rb') as f:
        picture = discord.File(f)
        await message.channel.send(file=picture)
    elif (self.get_at(visabot)) in message.content:
      await message.channel.send('oh no im a little baby')
    elif cleaned.startswith("!visa"):
      # only works for one @
      # this can be made to error but I'm leaving it so that people can spam me
      if message.content == "!visa":
        author_id = message.author.id
        member = await guild.fetch_member(author_id)
      elif "@" in message.content:
        # this will error if anything other than a properly formatted user id is after the at and in between the "<" and ">"
        start = message.content.index("<") + 2
        end = message.content.index(">")
        id = int(message.content[start:end])
        member = await guild.fetch_member(id)
      else:
        # only looking for name # discriminator
        start = message.content.index(" ") + 1
        after_visa_content = message.content[start:len(message.content)]
        if after_visa_content == "all":
          visarole_members = await self.get_all_visarole_members()
          if visarole_members == []:
            await message.channel.send(
              "No one with a visa role has been found. You are all safe... for now..."
            )
            return
          await self.visa_status_message(visarole_members, message.channel)
          return
        else:
          found = False
          async for member in guild.fetch_members(limit=None):
            name = member.name + "#" + member.discriminator
            if after_visa_content == name:
              found = True
              break
          if not found:
            await message.channel.send(
              "Member {} not found. Make sure you have the correct \"name#discriminator\" combination."
              .format(after_visa_content))
            return
      await self.visa_status_message([member], message.channel)

  async def report_online(self):
    guild = await self.get_guild()
    status_channel = await guild.fetch_channel(self.bot_status_channel)
    await status_channel.send('Visabot Online')

  async def report_offline(self):
    guild = await self.get_guild()
    status_channel = await guild.fetch_channel(self.bot_status_channel)
    await status_channel.send('Visabot going Offline')

  async def report_error(self):
    dev = await self.get_dev_member()
    dev_at = self.get_at(dev)
    await self.send_to_spam(
      'Visabot has error - {} get on and fix it you dummy'.format(dev_at))

  async def add_visa_after_offline(self) -> bool:
    guild = await self.get_guild()
    last_around = self.get_last_around()
    joined_during_offline_members = []
    async for member in guild.fetch_members(limit=None):
      if (last_around - member.joined_at).total_seconds() <= 0:
        joined_during_offline_members.append(member)
    visarole = await self.get_visa_role()
    success = True
    for member in joined_during_offline_members:
      if not (await self.has_visa(member)):
        name = self.get_at(member)
        await member.add_roles(visarole)
        warning_message = ("{} has been given a visa. \n You have {}.").format(
          name, self.time_left_message(member))
        await self.send_to_spam(warning_message)
        refetch_member = await guild.fetch_member(member.id)
        # check if we added visa role
        if not (await self.has_visa(refetch_member)):
          success = False
    now = get_now()
    self.update_var_json({'LAST_TIME_OF_ACTION': str(now)})
    return success

  async def on_ready(self):
    print(f'We have logged in as {client.user}')
    now = get_now()
    basic_activity = discord.Activity(created_at=now,
                                      name="you",
                                      start=now,
                                      type=discord.ActivityType.watching,
                                      status=discord.Status.online)
    await client.change_presence(activity=basic_activity)

    success = await self.add_visa_after_offline()
    if not success:
      await self.send_to_spam('Adding Visas has failed')
      await self.report_error()

    success = await self.purge_all_overstayed_visa()
    if not success:
      await self.send_to_spam('Purge has failed')
      await self.report_error()

  async def on_member_join(self, member: discord.Member):
    guild = await self.get_guild()
    member_id = member.id
    member = await guild.fetch_member(member_id)
    visarole = await self.get_visa_role()
    await member.add_roles(visarole)
    now = get_now()
    name = self.get_at(member)
    warning_message = ("{} has been given a visa. \n You have {}.").format(
      name, self.time_left_message(member))
    await self.send_to_spam(warning_message)
    self.update_var_json({'LAST_TIME_OF_ACTION': str(now)})

  async def setup_hook(self) -> None:
    # start the task to run in the background
    self.purge_visas_background_task.start()

  @tasks.loop(seconds=300)  # task runs every 60 seconds
  async def purge_visas_background_task(self):
    print("Attempting Purge at {}".format(get_now()))
    success = await self.purge_all_overstayed_visa()
    if success:
      pass
    else:
      await self.send_to_spam('Purge has failed')
      await self.report_error()
    now = get_now()
    self.update_var_json({'LAST_TIME_OF_ACTION': str(now)})

  @purge_visas_background_task.before_loop
  async def before_purge_background_task(self):
    await self.wait_until_ready()  # wait until the bot logs in

  async def on_error(self, event_method: str, *args, **kwargs) -> None:
    # ratelimit_blurb = "The owner of this website (discord.com) has banned you temporarily from accessing this website"
    await self.report_error()
    guild = await self.get_guild()
    status_channel = await guild.fetch_channel(self.bot_status_channel)
    await status_channel.send('Visabot has an error')

    await self.send_to_spam('During method: {}'.format(event_method))
    self.error_counter += 1
    if self.error_counter > 10:
      self.report_offline()
      await client.close()
    return await super().on_error(event_method, *args, **kwargs)

  async def on_disconnect(self):
    print("DISCONNECT")
    now = get_now()
    self.update_var_json({'LAST_TIME_OF_ACTION': str(now)})
    await self.report_offline()

  async def on_resumed(self):
    print("RESUME")
    await self.report_online()

  async def on_connect(self):
    print("CONNECT")
    await self.report_online()

  async def on_shard_disconnect(self):
    print("DISCONNECT SHARD")
    await self.report_offline()

  async def on_shard_connect(self):
    print("CONNECT SHARD")
    await self.report_online()

  async def on_shared_resumed(self):
    print("RESUME SHARD")
    await self.report_online()


test_mode = False

config_file = 'config.json'
if test_mode:
  config_file = "test_" + config_file

with open(config_file, 'r') as f:
  data = json.load(f)
  print(data)
  BOT_TOKEN = data['TOKEN']

intents = discord.Intents.all()
#theoretically redundant but just in case
intents.message_content = True
intents.members = True
intents.presences = True
intents.guilds = True

# intents.
client = MyClient(data, test_mode, intents=intents)

print("here")

# TODO
# @client.hybrid_group(fallback="get")
# async def visa(self, ctx, member_name):
#   found = False
#   guild = await self.get_guild()
#   async for member in guild.fetch_members(limit=None):
#     name = member.name + "#" + member.discriminator
#     if member_name == name:
#       found = True
#       break
#   if not found:
#     await self.send_to_spam(
#       "Member {} not found. Make sure you have the correct \"name#discriminator\" combination."
#       .format(member_name))
#     return
#   await self.visa_status_message([member], await self.get_admin_spam_channel)

# @visa.command()
# async def all(ctx, name):
#   await ctx.send(f"Created tag: {name}")

# @visa.command()
# async def at(ctx, name):
#   await ctx.send(f"Created tag: {name}")

if not test_mode:
  try:
    keep_alive()
  except:
    print("Website doesn't work?")
    os.system('kill 1')
    os.system('python restarter.py')
try:
  client.run(BOT_TOKEN)
except:
  print("BLOCKED BY RATE LIMITING - RESTARTING NOW")
  os.system('kill 1')
  os.system('python restarter.py')