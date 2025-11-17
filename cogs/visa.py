""" "
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.5.0
"""

import datetime
import random

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord.member import Member
from discord.message import Message

from base.visacog import VisaCog
from bots.basebot import BaseBot
from exceptions import VisaKickFailure
from utils import MEDIA_PATH, checks
from utils.time_helpers import get_now


# TODO add last offline to db or somethings
class Visabot(VisaCog, name="visabot"):

    def __init__(self, bot: BaseBot):
        super().__init__(bot)

    # TODO this should perhaps be moved to guildedcog
    def get_help_blurb(self, embed: discord.Embed) -> str:
        prefix = self.bot.config.command_prefix
        commands_list = self.get_commands()
        # pretty much manual cause im lazy
        data = []
        unlisted = ["designate_spam_channel", "designate_status_channel"]
        for command in commands_list:
            if command.name in unlisted:
                continue
            description = command.description.partition("\n")[0]
            data.append(f"{prefix}{command.name} - {description}")
            if command.name == "visa":
                data.append("")
                for other_command in command.walk_commands():
                    description = other_command.description.partition("\n")[0]
                    data.append(
                        f"{prefix}{command.name} {other_command.name} - {description}"
                    )
        help_text = "\n".join(data)
        embed.add_field(
            name=self.__cog_name__.capitalize(),
            value=f"```{help_text}```",
            inline=False,
        )
        return embed

    def time_left_value_seconds(self, member: discord.Member) -> datetime.timedelta:
        now = get_now()
        joined = member.joined_at
        seconds_diff = datetime.timedelta(seconds=(now - joined).total_seconds())
        return max(self.visa_length - seconds_diff, datetime.timedelta(seconds=0))

    def time_left_message(self, member: discord.Member) -> str:
        time = self.time_left_value_seconds(member)
        return f"{time} remaining on your visa."

    async def visa_status_message(
        self, members: list, channel: discord.TextChannel, fetched_guild=None
    ) -> bool:
        if fetched_guild == None:
            fetched_guild = self.guild
        message = ""
        extra_warning = False
        non_permanent_detected = False
        for member in members:
            time_left_val = self.time_left_value_seconds(member)
            if await self.has_visa(member):
                non_permanent_detected = True
                message += f"{self.get_nick_or_name(member)} has {self.time_left_message(member)}\n"
                if time_left_val < self.visa_length:
                    extra_warning = True
            else:
                message += f"{self.get_nick_or_name(member)} is considered a permanent member of the server.\n"
        if extra_warning:
            with open(self.warning_gif, "rb") as f:
                picture = discord.File(f)
                await channel.send(file=picture)
        if non_permanent_detected:
            message += "\nYou have to reach out if you don't want your visa to expire, otherwise you will be **kicked** from the server automatically."
        return message

    async def send_random_delete_gif(self, channel: discord.TextChannel) -> str:
        purge_directory = MEDIA_PATH / "purge_gifs"
        gif_file = random.choice(list(purge_directory.iterdir()))
        with open(gif_file, "rb") as f:
            picture = discord.File(f)
            await channel.send(file=picture)

    @commands.hybrid_group(
        name="visa",
        description="Get information about visa duration/status",
    )
    @checks.not_blacklisted()
    @checks.is_correct_guild()
    async def visa(self, context: Context):
        """
        Hybrid command group for Visa commands
        """
        return

    @visa.command(
        base="visa",
        name="all",
        description="Shows all Visa members and their durations.",
    )
    @checks.not_blacklisted()
    @checks.is_correct_guild()
    async def visa_all(self, context: Context) -> None:
        """
        Lists all members with the visa role and calculates their remaining duration

        :param context: The hybrid command context.
        """
        visa_members = await self.get_all_visarole_members()
        if len(visa_members) == 0:
            message = (
                "No one with a visa role has been found. You are all safe... for now..."
            )
            embed = discord.Embed(description=f"{message}", color=0x9C84EF)
            embed.set_footer(text=f"Time to vibe with all the other citizens.")
        else:
            message = await self.visa_status_message(
                visa_members, context.channel, context.guild
            )
            embed = discord.Embed(description=f"{message}", color=0x9C84EF)
            total = len((await self.get_visa_role()).members)
            embed.set_footer(
                text=f"There {'is' if total == 1 else 'are'} {total} {'member' if total == 1 else 'members'} with the Visa role."
            )
        await context.send(embed=embed)

    @visa.command(
        base="visa",
        name="self",
        description="Gives author's visa duration/status.",
    )
    @checks.not_blacklisted()
    @checks.is_correct_guild()
    async def visa_self(self, context: Context) -> None:
        """
        If the member has a Visa role their visa duration is given. If they are not a visa member, states they are not.

        :param context: The hybrid command context.
        """
        member = await self.user_to_member(context.author.id)
        message = await self.visa_status_message(
            [member], context.channel, context.guild
        )
        embed = discord.Embed(description=f"{message}", color=0x9C84EF)
        total = len((await self.get_visa_role()).members)
        await context.send(embed=embed)

    @visa.command(
        base="visa",
        name="other",
        description="Gives the visa duration/status of another.",
    )
    @checks.not_blacklisted()
    @checks.is_correct_guild()
    async def visa_other(self, context: Context, member: Member) -> None:
        """
        Check the visa duration on a specific user

        :param context: The hybrid command context.
        """
        message = await self.visa_status_message(
            [member], context.channel, context.guild
        )
        embed = discord.Embed(description=f"{message}", color=0x9C84EF)
        total = len((await self.get_visa_role()).members)
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} {total} {'member' if total == 1 else 'members'} with the Visa role."
        )
        await context.send(embed=embed)
        # TODO when people ask for my visa tell them im super cool i will never get kicked by visabot but say it cool

    @visa.command(
        base="visa",
        name="timer",
        description="Gives the default inital visa timer.",
    )
    @checks.not_blacklisted()
    @checks.is_correct_guild()
    async def visa_timer(self, context: Context) -> None:
        """
        Gives it in days, hours, minutes, seconds

        :param context: The hybrid command context.
        """
        embed = discord.Embed(
            description=f"The timer is currently set to: {self.visa_length}",
            color=0x9C84EF,
        )
        total = len((await self.get_visa_role()).members)
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} {total} {'member' if total == 1 else 'member'} with the Visa role."
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="kickgif", description="Sends a random autokick gif to the channel."
    )
    @checks.not_blacklisted()
    @checks.is_correct_guild()
    async def kickgif(self, context: Context) -> None:
        await self.send_random_delete_gif(context.channel)

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        guild = member.guild
        if not self.is_correct_guild_check(guild):
            return
        member_id = member.id
        member = await guild.fetch_member(member_id)
        visarole = await self.get_visa_role()
        await member.add_roles(visarole)
        name = self.get_at(member)
        warning_message = f"{name} has been given a visa. \n You have {self.time_left_message(member)}."
        await self.spam_channel.send(name)
        embed = discord.Embed(description=f"{warning_message}")
        total = await self.get_visa_total()
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} with the Visa role."
        )
        await self.spam_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        # all of these are for memes and testing
        guild = message.guild
        if not self.is_correct_guild_check(guild):
            return
        delete_me_messages = [
            "delete me",
            "kill me",
            "what would it look like if i got deleted?",
            "what would it look like if i got deleted",
            "end me",
            "show me my end",
            "execute me",
            "destroy me",
            "let it end",
        ]
        # prevent infinite recursion
        if message.author == self.bot.user:
            return
        if message.content.lower() in delete_me_messages:
            await self.send_random_delete_gif(message.channel)
        elif (self.get_at(self.visabot)) in message.content:
            if self.bot.config.dev_id and message.author.id == self.bot.config.dev_id:
                await message.channel.send("kashikomarimashita Charlie-sama ")
                return
            await message.channel.send(
                f"You called {self.get_nick_or_name(message.author)}?"
            )

    async def add_visa_after_offline(self):
        # TODO reenable when we add visa to DB
        return
        # guild = await self.bot.fetch_guild(self.bot.config['server_id'])
        # last_around = self.get_last_around()
        # joined_during_offline_members = []
        # print(self.bot.config["spam_channel"])
        # async for member in guild.fetch_members(limit=None):
        #   if (last_around - member.joined_at).total_seconds() <= 0:
        #     joined_during_offline_members.append(member)
        # visarole = await self.get_visa_role(guild)
        # success = True
        # for member in joined_during_offline_members:
        #   if not (await self.has_visa(member, guild)):
        #     name = self.get_at(member)
        #     await member.add_roles(visarole)
        #     await self.spam_channel.send(name)
        #     warning_message = f"{name} has been given a visa. \n You have {self.time_left_message(member)}.")
        #     embed = discord.Embed(description=f"{warning_message}")
        #     total = await self.get_visa_total()
        #     embed.set_footer(
        #       text=
        #       f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} with the Visa role."
        #     )
        #     await self.spam_channel.send(embed=embed)
        #     refetch_member = await guild.fetch_member(member.id)
        #     # check if we added visa role
        #     if not (await self.has_visa(refetch_member, guild)):
        #       success = False
        # if not success:
        #     raise VisaKickFailure("Adding Visas has failed")
        # return success

    @commands.Cog.listener()
    async def on_ready(self):
        await super().on_ready()
        self.visabot = self.bot.user
        self.logger.info(f"Using guild '{self.guild}'")
        self.logger.info(f"Visabot is {self.visabot}")
        await self.add_visa_after_offline()
        await self.purge_all_overstayed_visa()
        self.purge_visas_background_task.start()
        await self.bot_status_channel.send("Visabot Online")
        return

    @commands.Cog.listener()
    async def on_disconnect(self):
        await self.bot_status_channel.send("Visabot Offline")

    @tasks.loop(seconds=300)  # task runs every 5 minutes
    async def purge_visas_background_task(self):
        self.logger.info("Purging Visas")
        await self.purge_all_overstayed_visa()

    @purge_visas_background_task.before_loop
    async def before_purge_background_task(self):
        await self.bot.wait_until_ready()  # wait until the bot logs in


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot):
    await bot.add_cog(Visabot(bot))
