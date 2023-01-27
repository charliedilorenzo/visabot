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

def get_now():
  return datetime.datetime.now((datetime.timezone.utc))

def str_datetime_to_datetime_obj(str_datetime: str) -> datetime.datetime:
  datetime_obj = datetime.datetime.strptime(str_datetime,
                                            "%Y-%m-%d %H:%M:%S.%f%z")
  return datetime_obj

async def user_to_member(user,guild: discord.Guild):
    # method to get member from either id or from user object
    if isinstance(user,int):
        return await guild.fetch_member(user)
    if isinstance(user, discord.User):
        return await guild.fetch_member(user.id)

def get_nick_or_name(member: discord.Member) -> str:
    nickname = member.nick
    if not nickname is None:
      return nickname
    else:
      return member.name

def get_at(member: discord.Member) -> str:
    at_member = "<@" + str(member.id) + ">"
    return at_member

async def get_visa_role(guild) -> discord.Role:
    visarole = discord.utils.get(guild.roles, name="Visa")
    return visarole

async def has_visa(member, guild) -> bool:
    visarole = await get_visa_role(guild)
    if visarole in member.roles:
      return True
    else:
      return False
    
async def get_all_visarole_members(guild: discord.Guild):
    visarole_members = []
    async for member in guild.fetch_members(limit=None):
        if await has_visa(member, guild):
            visarole_members.append(member)
    return visarole_members

# Here we name the cog and create a new class for the cog.
class Visabot(commands.Cog, name="visabot"):
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
        # super().__init__(bot)
        self.bot = bot
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
    async def get_spam_channel(self) -> discord.TextChannel:
        guild = await self.bot.fetch_guild(self.bot.config['guild_id'])
        return await guild.fetch_channel(self.bot.config['spam_channel'])
    
    async def report_error(self):
        guild = await self.get_guild()
        dev_at = get_at(await guild.fetch_member(self.bot.config['dev_id']))
        spam_channel = self.get_spam_channel()
        await spam_channel.send('Visabot has error - {} get on and fix it you dummy'.format(dev_at))

    # uses config to determine guild
    async def get_bot_status_channel(self) -> discord.TextChannel:
        guild = await self.bot.fetch_guild(self.bot.config['guild_id'])
        return guild.fetch_channel(self.bot.config['bot_status_channel'])
    
    async def get_visa_total(self) -> int:
        guild = await self.get_guild()
        total = len(await get_all_visarole_members(guild))
        return total

    def correct_guild_check(self, guild):
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
        last_around = str_datetime_to_datetime_obj(self.timestamp_before_online)
        return last_around

    # TODO designate spam channel command

    # TODO designate bot status channel command


    def time_left_value_seconds(self, member: discord.Member) -> int:
        now = get_now()
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
        ' ~{} Days, {} Hours, and {} Minutes remaining on your visa.'
        ).format(days, hours, minutes)

    async def visa_status_message(self, members: list, guild:discord.Guild, channel: discord.TextChannel) -> bool:
        extra_warning = False
        message = ""
        for member in members:
            time_left_val = self.time_left_value_seconds(member)
            if await has_visa(member,guild):
                message += "{} has {} \n".format(get_nick_or_name(member),
                                                    self.time_left_message(member))
                if time_left_val < 60 * 60 * 12:
                    extra_warning = True
            else:
                message +=  "{} is considered a permanent member of the server.\n".format(
                get_nick_or_name(member))
        if extra_warning:
            with open(self.warning_gif, 'rb') as f:
                picture = discord.File(f)
                await channel.send(file=picture)
        message += "\nYou have to reach out if you don\'t want your visa to expire, otherwise you will be **kicked** from the server automatically."
        return message
    
    def get_random_delete_gif(self) -> str:
        purge_directory = self.main_dir + "/purge_gifs"
        delete_gifs = []
        for file in os.listdir(purge_directory):
            if file.endswith(".gif"):
                delete_gifs.append(purge_directory + "/" + file)
        random_gif = random.choice(delete_gifs)
        return random_gif

    async def attempt_kick_visarole_member(self, member: discord.Member, guild: discord.Guild) -> bool:
        # returns [success, was_kicked]
        if not self.correct_guild_check(guild):
            return 
        name = get_at(member)
        visarole = await get_visa_role(guild)
        spam_channel = await self.get_spam_channel()

        # the message and result on true error
        message = "An error has occured: likely {} that visabot attempted to kick is still on the server.".format(name)
        result = [False, False]
        try:
            await guild.kick(member)
            refetch_member = await guild.fetch_member(member.id)
            # here is a success since we cannot find the member they have been properly kicked from the server
        except discord.NotFound:
            message = '{}\'s visa has expired. They have been kicked.'.format(name)
            result = [True,True]
            # visabot attempted to kick someone with higher perms, that is probably not an error in visabot
        except discord.Forbidden:
            message = "{} has a higher role and does not need a visa.\n".format(name)
            await member.remove_roles(visarole)
            refetch_member = await guild.fetch_member(member.id)
            # check if we added visa role
            if await has_visa(refetch_member, guild):
                message += "An error has occured where a permanent member of the server, {}, has retained their visa role after attempted of removal of visa role".format(name)
                result = [False, False]
            else:
                message += "Visa has been removed from {}. You are considered a permanent member of the server".format(name)
                result =  [True, False]
        
        embed = discord.Embed(
            description=f"{message}",
            color=0x9C84EF
        )
        total = await self.get_visa_total()
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} with the Visa role."
        )
        await spam_channel.send(embed=embed)
        return result

    async def purge_all_overstayed_visa(self) -> bool:
        success = True
        execution_executed = False
        guild = self.bot.get_guild(self.bot.config['guild_id'])
        kick_list = await get_all_visarole_members(guild)
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
            random_purge_gif = self.get_random_delete_gif()
            with open(random_purge_gif, 'rb') as f:
                picture = discord.File(f)
                await spam_channel.send(file=picture)
        return success

    @commands.hybrid_group(
        name="visa",
        description="Get information about your visa duration/status.",
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
            member = await user_to_member(context.author.id,context.guild)
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
                    description=f"Member {after_visa_content} not found. Make sure you have the correct \"name#discriminator\" combination.",
                    color=0x9C84EF
                )
                await context.send(embed=embed)
                return
        
        if member != "":
            message = await self.visa_status_message([member], context.guild,context.channel)
            embed = discord.Embed(
                description=f"{message}",
                color=0x9C84EF
            )
            total = len((await get_visa_role(context.guild)).members)
            embed.set_footer(
                text=f"There {'is' if total == 1 else 'are'} {total} {'member' if total == 1 else 'member'} with the Visa role."
            )
            await context.send(embed=embed)
        elif context.invoked_subcommand is None:
            embed = discord.Embed(
                description="You need to specify a subcommand.\n\n**Subcommands:**\n`add` - Add a user to the blacklist.\n`remove` - Remove a user from the blacklist.",
                color=0xE02B2B
            )
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
        visa_members = await get_all_visarole_members(context.guild)
        message = await self.visa_status_message(visa_members, context.guild,context.channel)
        embed = discord.Embed(
            description=f"{message}",
            color=0x9C84EF
        )
        total = len((await get_visa_role(context.guild)).members)
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} {total} {'member' if total == 1 else 'member'} with the Visa role."
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
        member = await user_to_member(context.author.id,context.guild)
        message = await self.visa_status_message([member], context.guild,context.channel)
        embed = discord.Embed(
            description=f"{message}",
            color=0x9C84EF
        )
        total = len((await get_visa_role(context.guild)).members)
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} {total} {'member' if total == 1 else 'member'} with the Visa role."
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
        member = await user_to_member(user,context.guild)
        message = await self.visa_status_message([member], context.guild,context.channel)
        embed = discord.Embed(
            description=f"{message}",
            color=0x9C84EF
        )
        total = len((await get_visa_role(context.guild)).members)
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} {total} {'member' if total == 1 else 'member'} with the Visa role."
        )
        await context.send(embed=embed)

    # TODO add delete_gif send command

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        if not self.correct_guild_check(guild):
            return
        member_id = member.id
        member = await guild.fetch_member(member_id)
        visarole = await get_visa_role(guild)
        await member.add_roles(visarole)
        now = get_now()
        name = get_at(member)
        warning_message = ("{} has been given a visa. \n You have {}.").format(name, self.time_left_message(member))
        spam_channel = await self.get_spam_channel()
        embed = discord.Embed(
            description=f"{warning_message}"
        )
        total = await self.get_visa_total()
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} with the Visa role."
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
            random_purge_gif = self.get_random_delete_gif()
            with open(random_purge_gif, 'rb') as f:
                picture = discord.File(f)
                await message.channel.send(file=picture)
        # sometimes "<@&" in message.content instead?
        elif (get_at(visabot)) in message.content:
            if (message.author.id == self.bot.config['dev_id']):
                await message.channel.send('kashikomarimashita Charlie-sama ')
                return
            await message.channel.send('oh no im a little baby')

    async def add_visa_after_offline(self) -> bool:
        guild = await self.bot.fetch_guild(self.bot.config['guild_id'])
        last_around = self.get_last_around()
        joined_during_offline_members = []
        spam_channel = await self.get_spam_channel()
        async for member in guild.fetch_members(limit=None):
            if (last_around - member.joined_at).total_seconds() <= 0:
                joined_during_offline_members.append(member)
        visarole = await get_visa_role(guild)
        success = True
        for member in joined_during_offline_members:
            if not (await has_visa(member,guild)):
                name = get_at(member)
                await member.add_roles(visarole)
                warning_message = ("{} has been given a visa. \n You have {}.").format(name, self.time_left_message(member))
                embed = discord.Embed(
                    description=f"{warning_message}"
                )
                total = await self.get_visa_total()
                embed.set_footer(
                    text=f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} with the Visa role."
                )
                await spam_channel.send(warning_message)
                refetch_member = await guild.fetch_member(member.id)
                # check if we added visa role
                if not (await has_visa(refetch_member,guild)):
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
        return

    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.purge_visas_background_task.start()

    @tasks.loop(seconds=60)  # task runs every 5 minutes
    async def purge_visas_background_task(self):
        # TODO get this working then change back to 5 minutes
        # if not self.correct_guild_check(context.guild):
        #     return 
        print("Purging Visas")
        success = await self.purge_all_overstayed_visa()
        if success:
            pass
        else:
            spam_channel = await self.get_spam_channel()
            await spam_channel.send('Purge has failed')
            await self.report_error()
        now = get_now()
        self.update_var_json({'LAST_TIME_OF_ACTION': str(now)})

    @purge_visas_background_task.before_loop
    async def before_purge_background_task(self):
        await self.bot.wait_until_ready()  # wait until the bot logs in


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot):
    await bot.add_cog(Visabot(bot))
