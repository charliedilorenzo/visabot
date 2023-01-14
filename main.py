import discord
import datetime
import math
from discord.ext import tasks
import json
import os
from keep_alive import keep_alive

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

  async def get_dev_member(self):
    guild = await self.get_guild()
    dev_member = await guild.fetch_member(self.dev_user_id)
    return dev_member

  def get_last(self) -> datetime.datetime:
    last_around = str_datetime_to_datetime_obj(self.timestamp_before_online)
    return last_around

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
      minutes = 5
      seconds = 0
    self.visa_length_static = [days, hours, minutes, seconds]
    self.purge_gif = 'get_deleted_pleb.gif'
    self.guild_id = data['GUILD_ID']
    self.spam_channel = data['SPAM_CHANNEL']
    self.bot_id = data['BOT_ID']
    self.dev_user_id = data['DEV_ID']

    self.tracker_file = "var_tracker.json"
    if test_mode:
        self.tracker_file = "test_" + self.tracker_file
    
    if not os.path.exists(self.tracker_file):
      now = get_now()
      init_data = {'LAST_TIME_OF_ACTION': str(now), 'ASSIGNED': []}
      with open(self.tracker_file, 'w') as openfile:
        json.dump(init_data, openfile)
    data = self.get_json_data()
    self.timestamp_before_online = data['LAST_TIME_OF_ACTION']
    # just in case to avoid infinite loops
    self.error_counter = 0

  async def has_visa(self, member) -> bool:
    visarole = await self.get_visa_role()
    if visarole in member.roles:
      return True
    else:
      return False
  
  async def send_to_spam(self, message):
    spam_channel = await self.get_admin_spam_channel()
    await spam_channel.send(message)

  
  async def report_error(self):
    dev = await self.get_dev_member()
    dev_at = self.get_at(dev)
    await self.send_to_spam(
      'Visabot has error - {} get on and fix it you dummy'.format(dev_at))
  
  def time_left_value(self, member: discord.Member) -> int:
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
    time = self.time_left_value(member)
    # seconds = time % 60
    time = math.floor(time / 60)
    minutes = time % 60
    time = math.floor(time / 60)
    hours = time % 24
    time = math.floor(time / 24)
    days = time
    return (
      ' ~{} Days, {} Hours, and {} Minutes remaining on your visa. \n You have to reach out if you don\'t want it to expire'
    ).format(days, hours, minutes)

  async def purge_all_overstayed_visa(self) -> bool:
    guild = await self.get_guild()
    success = True
    execution_executed = False
    kick_list = []
    visarole = await self.get_visa_role()
    async for member in guild.fetch_members(limit=None):
      if await self.has_visa(member):
        kick_list.append(member)

    for member in kick_list:
      if self.time_left_value(member) <= 0:
        name = self.get_at(member)
        try:
          await guild.kick(member)
          await self.send_to_spam('{}\'s visa has expired.'.format(name))
          execution_executed = True
        except:
          await self.send_to_spam(
            "{} has a higher role and does not need a visa.".format(name))
          await member.remove_roles(visarole)
          refetch_member = await guild.fetch_member(member.id)
          # check if we added visa role
          if await self.has_visa(refetch_member):
            success = False
            await self.send_to_spam(
              "Attempt to remove visa from {} has failed.".format(name))
          else:
            await self.send_to_spam(
              "Visa has been removed from {}. You are considered a permanent member of the server"
              .format(name))

    if execution_executed:
      await self.send_to_spam('Commencing execution:')
      with open(self.purge_gif, 'rb') as f:
        picture = discord.File(f)
        spam_channel = await self.get_admin_spam_channel()
        await spam_channel.send(file=picture)
    return success

  async def add_visa_after_offline(self) -> bool:
    guild = await self.get_guild()
    last_around = self.get_last()
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
    basic_activity = discord.Activity(created_at=now,name="you",start=now,type=discord.ActivityType.watching,status=discord.Status.online)
    await client.change_presence(activity=basic_activity)
     
    success = await self.add_visa_after_offline()
    if success:
      pass
    else:
      await self.send_to_spam('Adding Visas has failed')
      await self.report_error()

      
    success = await self.purge_all_overstayed_visa()
    if success:
      pass
    else:
      await self.send_to_spam('Purge has failed')
      await self.report_error()

  async def on_message(self, message):
    guild = await self.get_guild()
    # wrong guild
    if message.guild != guild:
      return
    cleaned = message.clean_content
    guild = await self.get_guild()
    visabot = await guild.fetch_member(self.bot_id)
    if message.author == client.user:
      return
    elif ( self.get_at(visabot)) in message.content:
      await message.channel.send('oh no im a little baby')
    elif cleaned.startswith("!visa"):
      # only works for one @
      # this can be made to error but I'm leaving it so that people can spam me
      if "@" in message.content:
        start = message.content.index("<") + 2
        end = message.content.index(">")
        id = int(message.content[start:end])
        member = await guild.fetch_member(id)
        if not (await self.has_visa(member)):
          await message.channel.send(
            '{} is considered a permanent member of the server.'.format(
              self.get_nick_or_name(member)))
        else:
          await message.channel.send("{} has {}".format(
            self.get_nick_or_name(member), self.time_left_message(member)))
      else:
        author_id = message.author.id
        member = await guild.fetch_member(author_id)
        if not await self.has_visa(member):
          await message.channel.send(
            'You are considered a permanent member of the server.')
        else:
          await message.channel.send("{} {}".format(
            "You", self.time_left_message(member)))

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

  async def on_disconnect(self):
    now = get_now()
    self.update_var_json({'LAST_TIME_OF_ACTION': str(now)})
    await self.send_to_spam('Visabot is going offline')

  async def on_error(self, event_method: str, /, *args, **kwargs) -> None:
    await self.report_error()
    await self.send_to_spam('During method: {}'.format(event_method))
    self.error_counter += 1
    if self.error_counter > 10:
      await self.send_to_spam('Visabot is going offline')
      await client.close()
    return await super().on_error(event_method, *args, **kwargs)

  async def on_shard_connect(self):
    await self.send_to_spam('Visabot Online')

  async def on_shared_resumed(self):
    await self.send_to_spam('Visabot Online')

test_mode = True

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

if not test_mode:
  keep_alive()
try:
  client.run(BOT_TOKEN)
except:
  print("BLOCKED BY RATE LIMITING - RESTARTING NOW")
  os.system('kill 1')
  os.system('python restarter.py')
