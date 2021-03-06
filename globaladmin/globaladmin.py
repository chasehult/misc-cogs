import discord
import logging
from redbot.core import commands, checks, Config
from redbot.core.utils.chat_formatting import box, pagify, inline

from tsutils import CogSettings, tsutils

logger = logging.getLogger('red.misc-cogs.authcog')

class GlobalAdmin(commands.Cog):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

        self.settings = GlobalAdminSettings("globaladmin")

    async def red_get_data_for_user(self, *, user_id):
        """Get a user's personal data."""
        data = "No data is stored for user with ID {}.\n".format(user_id)
        return {"user_data.txt": BytesIO(data.encode())}

    async def red_delete_data_for_user(self, *, requester, user_id):
        """Delete a user's personal data.

        No personal data is stored in this cog.
        """
        return

    @commands.group(aliases=['ga', 'gadmin'])
    @checks.is_owner()
    async def globaladmin(self, ctx):
        """Global Admin Commands"""

    @globaladmin.group(aliases=['auths'])
    async def perms(self, ctx):
        """Perm commands"""

    @perms.command()
    async def setdefault(self, ctx, perm_name, default: bool = False):
        """Set the default value of a permission"""
        self.register_perm(perm_name, default)
        await ctx.end(inline("Done."))

    def register_perm(self, perm_name, default=False):
        self.settings.add_perm(perm_name, default)

    @perms.command()
    async def reset(self, ctx, perm_name):
        """Restore defaults for a perm for all users"""
        if not await tsutils.confirm_message("Are you sure you want to reset this perm to defaults?"):
            return
        self.refresh_perm(perm_name)
        await ctx.end(inline("Done."))

    @perms.command()
    async def unregister(self, ctx, perm_name):
        """Completely remove a perm from storage"""
        if not await tsutils.confirm_message("Are you sure you want to unregister this perm?"):
            return
        self.refresh_perm(perm_name)
        self.rm_perm(perm_name)
        await ctx.end(inline("Done."))

    @perms.command(name="list")
    async def perm_list(self, ctx):
        """List the avaliable perms"""
        msg = "Perms:\n"
        for perm, default in self.settings.get_perms().items():
            msg += " - {}\t\t{}\n".format(perm, default)
        for page in pagify(msg):
            await ctx.send(box(page))

    @globaladmin.command(aliases=["setperm", "setadmin", "addadmin", "addperm"])
    async def grant(self, ctx, user: discord.User, perm, value: bool = True):
        """Grant a user a perm"""
        if self.settings.add_user_perm(user.id, perm, value):
            await ctx.send(inline("Invalid perm name."))
            return
        await ctx.send(inline("Done."))

    @globaladmin.command()
    async def deny(self, ctx, user: discord.User, perm, value: bool = False):
        """Deny a user a perm"""
        if self.settings.add_user_perm(user.id, perm, value):
            await ctx.send(inline("Invalid perm name."))
            return
        await ctx.send(inline("Done."))

    @globaladmin.command()
    async def listusers(self, ctx, perm_name):
        """List all users with a perm"""
        us = self.settings.get_users_with_perm(perm_name)
        us = [str(self.bot.get_user(u) or "Unknown ({})".format(u)) for u in us]
        if not us:
            await ctx.send(inline("No users have this perm."))
        for page in pagify("\n".join(us)):
            await ctx.send(box(page))



class GlobalAdminSettings(CogSettings):
    def make_default_settings(self):
        config = {
            'perms': {},
            'users': {},
        }
        return config

    def add_user_perm(self, user_id, perm, value=True):
        if perm not in self.bot_settings['perms']:
            return -1
        if user_id not in self.bot_settings['users']:
            self.bot_settings['users'][user_id] = {}
        self.bot_settings['users'][user_id][perm] = value
        self.save_settings()

    def add_perm(self, perm, default=False):
        self.bot_settings['perms'][perm] = default
        self.save_settings()

    def rm_perm(self, perm):
        if perm in self.bot_settings['perms']:
            del self.bot_settings['perms'][perm]
        self.save_settings()

    def refresh_perm(self, perm):
        for user in self.bot_settings['users']:
            if perm in self.bot_settings['users'][user]:
                del self.bot_settings['users'][user][perm]
        self.save_settings()

    def rm_user_perm(self, user_id, perm):
        if perm not in self.bot_settings['perms']:
            return -1
        if user_id not in self.bot_settings['users']:
            return
        if perm not in self.bot_settings['users'][user_id]:
            return
        del self.bot_settings['users'][user_id][perm]
        self.save_settings()

    def get_perm(self, user_id, perm, default=False):
        defaults = {}
        defaults.update(self.bot_settings['perms'])
        defaults.update(self.bot_settings['users'].get(user_id, {}))
        return defaults.get(perm, default)

    def get_perms(self):
        return self.bot_settings['perms']

    def get_users_with_perm(self, perm):
        out = []
        for user in self.bot_settings['users']:
            if perm in self.bot_settings['users'][user]:
                out.append(user)
        return out
