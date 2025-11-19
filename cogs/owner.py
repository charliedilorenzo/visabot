""" "
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.5.0
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Bot, Context

from bots.basebot import BaseBot
from cogs.base.guildedcog import GuildedCog
from utils import checks, db_manager


class Owner(GuildedCog, name="owner"):

    def __init__(self, bot: BaseBot):
        super().__init__(bot)

    def help_blurb(self, context: Context) -> str:
        prefix = self.bot.config.command_prefix
        # just to make it easier for me to remember there is owner help command
        if context.author.id == self.bot.config.dev_id:
            cog = self.bot.get_cog("owner".lower())
            commands = cog.get_commands()
            for command in commands:
                if command.name == "ownerhelp":
                    data = []
                    description = command.description.partition("\n")[0]
                    data.append(f"{prefix}{command.name} - {description}")
                    help_text = "\n".join(data)
            return help_text
        return None

    @commands.command(
        name="ownerhelp",
        description="List all commands from the 'Owner' cog.",
    )
    @checks.is_owner()
    @checks.not_blacklisted()
    @checks.is_correct_guild()
    async def ownerhelp(self, context: Context) -> None:
        prefix = self.bot.config["prefix"]
        embed = discord.Embed(
            title="Help", description="List of available commands:", color=0x9C84EF
        )
        name = "owner"
        cog = self.bot.get_cog(name)
        commands = cog.get_commands()
        data = []
        for command in commands:
            description = command.description.partition("\n")[0]
            data.append(f"{prefix}{command.name} - {description}")
        help_text = "\n".join(data)
        owner_guilded = ["designate_spam_channel"]
        name = "visabot"
        cog = self.bot.get_cog(name)
        commands = cog.get_commands()
        for command in commands:
            if command.name in owner_guilded:
                description = command.description.partition("\n")[0]
                data.append(f"{prefix}{command.name} - {description}")
        help_text = "\n".join(data)
        embed.add_field(
            name=name.capitalize(), value=f"```{help_text}```", inline=False
        )
        await context.send(embed=embed)

    @commands.command(
        name="sync",
        description="Synchonizes the slash commands.",
    )
    @app_commands.describe(scope="The scope of the sync. Can be `global` or `guild`")
    @checks.is_correct_guild()
    async def sync(self, context: Context, scope: str) -> None:
        """
        Synchonizes the slash commands.

        :param context: The command context.
        :param scope: The scope of the sync. Can be `global` or `guild`.
        """

        if scope == "global":
            await context.bot.tree.sync()
            embed = discord.Embed(
                description="Slash commands have been globally synchronized.",
                color=0x9C84EF,
            )
            await context.send(embed=embed)
            return
        elif scope == "guild":
            context.bot.tree.copy_global_to(guild=context.guild)
            await context.bot.tree.sync(guild=context.guild)
            embed = discord.Embed(
                description="Slash commands have been synchronized in this guild.",
                color=0x9C84EF,
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description="The scope must be `global` or `guild`.", color=0xE02B2B
        )
        await context.send(embed=embed)

    @commands.command(
        name="unsync",
        description="Unsynchonizes the slash commands.",
    )
    @app_commands.describe(
        scope="The scope of the sync. Can be `global`, `current_guild` or `guild`"
    )
    @checks.is_owner()
    @checks.is_correct_guild()
    async def unsync(self, context: Context, scope: str) -> None:
        """
        Unsynchonizes the slash commands.

        :param context: The command context.
        :param scope: The scope of the sync. Can be `global`, `current_guild` or `guild`.
        """

        if scope == "global":
            context.bot.tree.clear_commands(guild=None)
            await context.bot.tree.sync()
            embed = discord.Embed(
                description="Slash commands have been globally unsynchronized.",
                color=0x9C84EF,
            )
            await context.send(embed=embed)
            return
        elif scope == "guild":
            context.bot.tree.clear_commands(guild=context.guild)
            await context.bot.tree.sync(guild=context.guild)
            embed = discord.Embed(
                description="Slash commands have been unsynchronized in this guild.",
                color=0x9C84EF,
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description="The scope must be `global` or `guild`.", color=0xE02B2B
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="load",
        description="Load a cog",
    )
    @app_commands.describe(cog="The name of the cog to load")
    @checks.is_owner()
    @checks.is_correct_guild()
    async def load(self, context: Context, cog: str) -> None:
        """
        The bot will load the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to load.
        """
        try:
            await self.bot.load_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not load the `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Successfully loaded the `{cog}` cog.", color=0x9C84EF
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="unload",
        description="Unloads a cog.",
    )
    @app_commands.describe(cog="The name of the cog to unload")
    @checks.is_owner()
    @checks.is_correct_guild()
    async def unload(self, context: Context, cog: str) -> None:
        """
        The bot will unload the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to unload.
        """
        try:
            await self.bot.unload_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not unload the `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Successfully unloaded the `{cog}` cog.", color=0x9C84EF
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="reload",
        description="Reloads a cog.",
    )
    @app_commands.describe(cog="The name of the cog to reload")
    @checks.is_owner()
    @checks.is_correct_guild()
    async def reload(self, context: Context, cog: str) -> None:
        """
        The bot will reload the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to reload.
        """
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not reload the `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Successfully reloaded the `{cog}` cog.", color=0x9C84EF
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="shutdown",
        description="Make the bot shutdown.",
    )
    @checks.is_owner()
    @checks.is_correct_guild()
    async def shutdown(self, context: Context) -> None:
        """
        Shuts down the bot.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(description="Shutting down. Bye! :wave:", color=0x9C84EF)
        await context.send(embed=embed)
        await self.bot.close()

    @commands.hybrid_command(
        name="say",
        description="The bot will say anything you want.",
    )
    @app_commands.describe(message="The message that should be repeated by the bot")
    @checks.is_owner()
    @checks.is_correct_guild()
    async def say(self, context: Context, *, message: str) -> None:
        """
        The bot will say anything you want.

        :param context: The hybrid command context.
        :param message: The message that should be repeated by the bot.
        """
        await context.send(message)

    @commands.hybrid_command(
        name="embed",
        description="The bot will say anything you want, but within embeds.",
    )
    @app_commands.describe(message="The message that should be repeated by the bot")
    @checks.is_owner()
    @checks.is_correct_guild()
    async def embed(self, context: Context, *, message: str) -> None:
        """
        The bot will say anything you want, but using embeds.

        :param context: The hybrid command context.
        :param message: The message that should be repeated by the bot.
        """
        embed = discord.Embed(description=message, color=0x9C84EF)
        await context.send(embed=embed)

    @commands.hybrid_group(
        name="blacklist",
        description="Get the list of all blacklisted users.",
    )
    @checks.is_owner()
    @checks.is_correct_guild()
    async def blacklist(self, context: Context) -> None:
        """
        Lets you add or remove a user from not being able to use the bot.

        :param context: The hybrid command context.
        """
        if context.invoked_subcommand is None:
            embed = discord.Embed(
                description="You need to specify a subcommand.\n\n**Subcommands:**\n`add` - Add a user to the blacklist.\n`remove` - Remove a user from the blacklist.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @blacklist.command(
        base="blacklist",
        name="show",
        description="Shows the list of all blacklisted users.",
    )
    @checks.is_owner()
    @checks.is_correct_guild()
    async def blacklist_show(self, context: Context) -> None:
        """
        Shows the list of all blacklisted users.

        :param context: The hybrid command context.
        """
        blacklisted_users = await db_manager.get_blacklisted_users()
        if len(blacklisted_users) == 0:
            embed = discord.Embed(
                description="There are currently no blacklisted users.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return

        embed = discord.Embed(title="Blacklisted Users", color=0x9C84EF)
        users = []
        for bluser in blacklisted_users:
            user = self.bot.get_user(int(bluser[0])) or await self.bot.fetch_user(
                int(bluser[0])
            )
            users.append(f"• {user.mention} ({user}) - Blacklisted <t:{bluser[1]}>")
        embed.description = "\n".join(users)
        await context.send(embed=embed)

    @blacklist.command(
        base="blacklist",
        name="add",
        description="Lets you add a user from not being able to use the bot.",
    )
    @app_commands.describe(user="The user that should be added to the blacklist")
    @checks.is_owner()
    @checks.is_correct_guild()
    async def blacklist_add(self, context: Context, user: discord.User) -> None:
        """
        Lets you add a user from not being able to use the bot.

        :param context: The hybrid command context.
        :param user: The user that should be added to the blacklist.
        """
        user_id = user.id
        if await db_manager.is_blacklisted(user_id):
            embed = discord.Embed(
                description=f"**{user.name}** is already in the blacklist.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)
            return
        total = await db_manager.add_user_to_blacklist(user_id)
        embed = discord.Embed(
            description=f"**{user.name}** has been successfully added to the blacklist",
            color=0x9C84EF,
        )
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} in the blacklist"
        )
        await context.send(embed=embed)

    @blacklist.command(
        base="blacklist",
        name="remove",
        description="Lets you remove a user from not being able to use the bot.",
    )
    @app_commands.describe(user="The user that should be removed from the blacklist.")
    @checks.is_owner()
    @checks.is_correct_guild()
    async def blacklist_remove(self, context: Context, user: discord.User) -> None:
        """
        Lets you remove a user from not being able to use the bot.

        :param context: The hybrid command context.
        :param user: The user that should be removed from the blacklist.
        """
        user_id = user.id
        if not await db_manager.is_blacklisted(user_id):
            embed = discord.Embed(
                description=f"**{user.name}** is not in the blacklist.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        total = await db_manager.remove_user_from_blacklist(user_id)
        embed = discord.Embed(
            description=f"**{user.name}** has been successfully removed from the blacklist",
            color=0x9C84EF,
        )
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} in the blacklist"
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="designate_spam_channel",
        description="Give a text channel to designate it as the bot spam channel.",
    )
    @checks.is_owner()
    async def designate_spam_channel(
        self, context: Context, channel: discord.TextChannel
    ) -> None:
        """
        Designate a channel that the bot will spam for specifically

        :param context: The hybrid command context.
        :param message: The message that should be repeated by the bot.
        """
        # TODO this should be stored with database
        raise NotImplementedError("This is currently no longer implemented")
        self.bot.config.spam_channel = channel.id
        message = f"The bot's spam channel has been updated to: '{channel.name}'"
        embed = discord.Embed(description=message, color=0x9C84EF)
        await context.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Owner(bot))
