from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds
from decouple import config
from discord.ext import commands, tasks
from src.bot_logging import logger
import discord
import json

from src.msgs.common import (
    auth_instructions,
    auth_already_confirmed,
    auth_email_not_found,
    auth_welcome,
)

from .helpers import only_log_exceptions, logchannel, http_get_json

DISCORD_GUILD_ID = config("DISCORD_GUILD_ID")
DISCORD_AUTH_CHANNEL_ID = config("DISCORD_AUTH_CHANNEL_ID")

SPREADSHEET_ID = config('SPREADSHEET_ID')
SPREADSHEET_CLIENT_JSON = config('SPREADSHEET_CLIENT_JSON')

creds = ServiceAccountCreds(scopes=[
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
], **json.load(open(SPREADSHEET_CLIENT_JSON)))


async def spreadsheet_participantes():
    aiogoogle = Aiogoogle(service_account_creds=creds)
    async with aiogoogle:
        spreadsheets_client = await aiogoogle.discover("sheets", "v4")
        res = await aiogoogle.as_service_account(
            spreadsheets_client.spreadsheets.values.get(spreadsheetId=SPREADSHEET_ID,
                                                        range="A1:S5000")
        )
    return res.get('values', [])


class InviteTracker:

    ROLE_INVITE_MAP = [
        ("palestrantes", ["7kBSy9cz"]),
        ("voluntarios", ["QCcz5QFc"]),
    ]

    def __init__(self, bot, guild):
        self.bot = bot
        self.guild = guild

        self.old_invites = {}
        self.invites = {}
        self.invite_codes = {}

    async def code_roles_list(self):
        invite_codes = {}
        code_role_ids = {}

        # Available roles
        roles = await self.guild.fetch_roles()
        roles = {role.name: role.id for role in roles}

        # Fetch role ID from role name
        for role, invite in self.ROLE_INVITE_MAP:
            invite_codes.update({code: role for code in invite})

        for code, role_name in invite_codes.items():
            code_role_ids[code] = roles[role_name]

        return code_role_ids

    async def get_invites(self):
        invites = await self.guild.invites()
        return {invite.code: invite.uses for invite in invites}

    async def sync(self):
        invites = await self.get_invites()
        self.old_invites = self.invites
        self.invites = invites

    def diff(self):
        diff = {}
        for code, uses in self.invites.items():
            old_uses = self.old_invites.get(code, 0)
            if uses > old_uses:
                diff[code] = uses - old_uses
                logger.info(f"Invite code used. code={code}, before={old_uses}, after={uses}")
        return diff

    async def check_new_user(self, member):
        if not self.invite_codes:
            self.invite_codes = await self.code_roles_list()

        await self.sync()
        invite_diff = self.diff()

        for code, uses in invite_diff.items():

            try:
                new_role = discord.Object(self.invite_codes.get(code))
            except TypeError:
                return None

            if new_role and uses == 1:
                logger.info(
                    f"Added role to member. member={member.display_name}, role={new_role}"
                )
                await member.add_roles(new_role)
                return new_role
            elif uses > 1:
                logger.warning(
                    "Two or more users joined server between invite tracker updates."
                )
        return None


class Greetings(commands.Cog):
    AUTH_CHANNEL_ID = config("DISCORD_AUTH_CHANNEL_ID", cast=int)
    AUTH_START_EMOJI = "👍"
    ATTENDEES_ROLE_NAME = "membros"

    def __init__(self, bot):
        self.bot = bot
        self._guild = None

        self.index = {}
        self._atteendee_role = None
        self._attendees = []

        self.rebuild_index.start()

    async def get_guild(self):
        if not self._guild:
            self._guild = await self.bot.fetch_guild(config("DISCORD_GUILD_ID"))
        return self._guild

    @tasks.loop(minutes=2)
    @only_log_exceptions
    async def rebuild_index(self):
        attendees = await spreadsheet_participantes()
        self.index = {attendee[2].lower(): attendee for attendee in attendees}
        attendees_len = len(self.index.keys())
        logger.info(f"Index updated. total={attendees_len}")

    async def get_attendee_role(self, guild: discord.Guild, attendee_role) -> discord.Role:
        """Retorna role de participante"""
        if not self._atteendee_role:
            guild = await self.get_guild()
            roles = await guild.fetch_roles()
            self._atteendee_role = discord.utils.get(roles, name=attendee_role)
        return self._atteendee_role

    def search_attendee(self, query):
        return self.index.get(query.strip().lower())

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        joined_with_invite_code = await self.invite_tracker.check_new_user(member)
        if joined_with_invite_code:
            return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        Quando usuário reagir a mensagem no canal de texto #credencimento, o bot enviará
        uma mensagem diretamente para o usuário pedindo email para confirmação.
        """
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        guild = await self.get_guild()
        user = await guild.fetch_member(payload.user_id)
        if (
            user.bot
            or payload.channel_id != self.AUTH_CHANNEL_ID
        ):
            return

        if payload.emoji.name != self.AUTH_START_EMOJI:
            message = await channel.fetch_message(payload.message_id)
            reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)
            await reaction.clear()
            return

        if len(user.roles) == 1:
            await user.send(auth_instructions.format(name=user.name))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.channel.type != discord.ChannelType.private:
            return

        guild = await self.get_guild()
        member = await guild.fetch_member(message.author.id)

        if not member:
            logger.info(f"User not in Scipy Latin America server. user={message.author.name}, content={message.content}")
            return

        if len(member.roles) != 1:
            await message.author.send(auth_already_confirmed)
            logger.info(f"User already authenticated. user={message.author.name}, content={message.content}")
            return

        logger.info(f"Authenticating user. user={message.author.name}, id={message.author.id}, content={message.content}")

        profile = self.search_attendee(message.content)

        if not profile:
            logger.info(f"User not found on index. user_id={message.author.id}, content={message.content!r}")
            await message.add_reaction("❌")
            await message.author.send(auth_email_not_found.format(query=message.content))
            await logchannel(self.bot, (
                f"❌ Inscrição não encontrada - {message.author.mention}"
                f"\n`{message.content}`"
            ))
            return

        role = await self.get_attendee_role(member.guild, attendee_role="participantes")

        await member.add_roles(role)
        await message.add_reaction("✅")
        await logchannel(self.bot, f"✅ {member.mention} confirmou sua inscrição")
        logger.info(f"User authenticated. user={message.author.name}")

    @commands.Cog.listener()
    async def on_ready(self):
        # Invite Tracker
        guild = await self.get_guild()
        self.invite_tracker = InviteTracker(self.bot, guild)
        await self.invite_tracker.sync()
        logger.info(f"Invite tracker synced. invites={self.invite_tracker.invites!r}")
