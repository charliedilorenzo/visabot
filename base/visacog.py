import datetime

import discord
from discord import Member
from discord.ext.commands import Bot

from base.guildedcog import GuildedCog


class VisaCog(GuildedCog):

    def __init__(self, bot: Bot):
        super().__init__(bot)
        if self.bot.config.test_mode == True:
            self.visa_length = datetime.timedelta(minutes=1)
        else:
            self.visa_length = datetime.timedelta(days=7)
        self.role_name = "Visa"

    async def get_all_visarole_members(self, fetched_guild=None):
        if fetched_guild is None:
            fetched_guild = self.guild
        visarole_members = []
        async for member in fetched_guild.fetch_members(limit=None):
            if await self.has_visa(member):
                visarole_members.append(member)
        return visarole_members

    async def get_visa_total(self, fetched_guild=None) -> int:
        if fetched_guild is None:
            fetched_guild = self.guild
        total = len(await self.get_all_visarole_members(fetched_guild))
        return total

    async def get_visa_role(self) -> discord.Role:
        visarole: discord.Role = discord.utils.get(
            self.guild.roles, name=self.role_name
        )
        return visarole

    async def has_visa(self, member: Member) -> bool:
        visarole = await self.get_visa_role()
        return visarole in member.roles

    async def attempt_kick_visarole_member(
        self, member: discord.Member, guild: discord.Guild
    ) -> bool:
        # returns [success, was_kicked]
        if not self.is_correct_guild_check(guild):
            return
        name = self.get_at(member)
        visarole = await self.get_visa_role()
        spam_channel = await self.get_spam_channel()

        # the message and result on true error
        message = f"An error has occured: likely {name} who visabot attempted to kick is still on the server."
        result = [False, False]
        try:
            await guild.kick(member)
            refetch_member = await guild.fetch_member(member.id)
            # here is a success since we cannot find the member they have been properly kicked from the server
        except discord.NotFound:
            message = f"{name}'s visa has expired. They have been kicked."
            result = [True, True]
            # visabot attempted to kick someone with higher perms, that is probably not an error in visabot
        except discord.Forbidden:
            message = f"{name} has a higher role and does not need a visa.\n"
            await member.remove_roles(visarole)
            refetch_member = await guild.fetch_member(member.id)
            # check if we added visa role
            if await self.has_visa(refetch_member, guild):
                message += f"An error has occured where a permanent member of the server, {name}, has retained their visa role after attempted of removal of visa role"
                result = [False, False]
            else:
                message += f"Visa has been removed from {name}. You are considered a permanent member of the server"
                result = [True, False]

        embed = discord.Embed(description=f"{message}", color=0x9C84EF)
        total = await self.get_visa_total()
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} with the Visa role."
        )
        await spam_channel.send(embed=embed)
        return result

    async def purge_all_overstayed_visa(self) -> bool:
        success = True
        # TODO add back purging visa
        return success
        execution_executed = False
        guild = self.bot.guild
        kick_list = await self.get_all_visarole_members(guild)
        spam_channel = await self.get_spam_channel()
        for member in kick_list:
            if self.time_left_value_seconds(member) <= 0:
                tracker_bools = await self.attempt_kick_visarole_member(member, guild)
                single_success = tracker_bools[0]
                single_execution = tracker_bools[1]
                success = single_success and success
                execution_executed = execution_executed or single_execution
        else:
            execution_executed = True
        if execution_executed:
            await spam_channel.send("Commencing execution:")
            await self.send_random_delete_gif(spam_channel)
        return success
        return success
        return success
        return success
