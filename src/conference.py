
import discord
from discord import PermissionOverwrite, ChannelType, Guild, Permissions, Colour

from dataclasses import dataclass, field
from typing import List, Optional


organizers_permissions = Permissions.all()
organizers_permissions.administrator = False
others_permissions = discord.Permissions()


@dataclass
class Role:
    name: str
    colour: Colour
    position: int = 0
    permissions: Optional[List[Permissions]] = None


ROLES = [
    Role(name="organizadores", permissions=organizers_permissions, position=80, colour=Colour.purple()),
    Role(name="palestrantes", position=70, colour=Colour.orange()),
    Role(name="voluntarios", position=70, colour=Colour.magenta()),
    Role(name="cdc", position=60, colour=Colour.blue()),
    Role(name="participantes", position=50, colour=Colour.gold()),
    Role(name="membros", position=40, colour=Colour.red())
]

everyone_except_organizers = [role for role in ROLES if role.name not in ['organizadores']]
organizers = [role for role in ROLES if role.name in ['organizadores']]
organizers_and_volunteers = [role for role in ROLES if role.name in ['organizadores', 'palestrantes', 'voluntarios', 'cdc']]
everyone_except_membros = [role for role in ROLES if role.name not in ['membros', ]]

# !important!: remember to reset the permissions of role @everyone


@dataclass
class Channel:
    name: str
    category: str = "default"
    position: int = 0
    restrict_access: bool = False
    voice: bool = False
    read_only_roles: List[Role] = field(default_factory=list)
    read_and_write_roles: List[Role] = field(default_factory=list)


CHANNELS = [
    Channel(
        name="boas-vindas",
        read_only_roles=everyone_except_organizers,
        read_and_write_roles=organizers
    ),
    Channel(
        name="bienvenidas",
        read_only_roles=everyone_except_organizers,
        read_and_write_roles=organizers
    ),
    Channel(
        name="regras",
        read_only_roles=everyone_except_organizers,
        read_and_write_roles=organizers
    ),
    Channel(
        name="reglas",
        read_only_roles=everyone_except_organizers,
        read_and_write_roles=organizers
    ),
    Channel(
        name="credenciamento-registro",
        read_only_roles=everyone_except_organizers,
        read_and_write_roles=organizers
    ),

    Channel(
        name="board",
        category="ORGANIZADORES",
        position=1,
        restrict_access=True,
        read_and_write_roles=organizers
    ),
    Channel(
        name="dev",
        category="ORGANIZADORES",
        position=1,
        restrict_access=True,
        read_and_write_roles=organizers
    ),
    Channel(
        name="log",
        category="ORGANIZADORES",
        position=1,
        restrict_access=True,
        read_and_write_roles=organizers
    ),
    Channel(
        name="meeting",
        category="ORGANIZADORES",
        position=1,
        restrict_access=True, voice=True,
        read_and_write_roles=organizers
    ),
    Channel(
        name="voluntarios-es",
        category="VOLUNTARIOS",
        position=2,
        restrict_access=True,
        read_and_write_roles=organizers_and_volunteers
    ),
    Channel(
        name="voluntarios-pt",
        category="VOLUNTARIOS",
        position=2,
        restrict_access=True,
        read_and_write_roles=organizers_and_volunteers
    ),
    Channel(
        name="palestrantes-ponentes",
        category="VOLUNTARIOS",
        position=2,
        restrict_access=True,
        read_and_write_roles=organizers_and_volunteers
    ),
    Channel(
        name="meeting-voluntarios",
        category="VOLUNTARIOS",
        position=2,
        restrict_access=True,
        voice=True,
        read_and_write_roles=organizers_and_volunteers
    ),
    Channel(
        name="jobs-fair",
        category="JOBS",
        position=3,
        restrict_access=True,
        voice=True,
        read_and_write_roles=everyone_except_membros
    ),
    Channel(
        name="geral",
        category="SCIPY LATIN AMERICA CONFERENCE",
        position=4,
        restrict_access=True,
        read_and_write_roles=everyone_except_membros
    ),
    Channel(
        name="keynotes",
        category="SCIPY LATIN AMERICA CONFERENCE",
        position=4,
        restrict_access=True,
        read_and_write_roles=everyone_except_membros
    ),
    Channel(
        name="sala-ciranda",
        category="SCIPY LATIN AMERICA CONFERENCE",
        position=4,
        restrict_access=True,
        read_and_write_roles=everyone_except_membros
    ),
    Channel(
        name="sala-frevo",
        category="SCIPY LATIN AMERICA CONFERENCE",
        position=4,
        restrict_access=True,
        read_and_write_roles=everyone_except_membros
    ),
    Channel(
        name="sala-manguebeat",
        category="SCIPY LATIN AMERICA CONFERENCE",
        position=4,
        restrict_access=True,
        read_and_write_roles=everyone_except_membros
    ),
    Channel(
        name="relampago",
        category="SCIPY LATIN AMERICA CONFERENCE",
        position=4,
        restrict_access=True,
        read_and_write_roles=everyone_except_membros
    ),
    Channel(
        name="pt-assuntos-aleatorios",
        category="SCIPY LATIN AMERICA CONFERENCE",
        position=4,
        restrict_access=True,
        read_and_write_roles=everyone_except_membros
    ),
    Channel(
        name="es-asuntos-aleatorios",
        category="SCIPY LATIN AMERICA CONFERENCE",
        position=4,
        restrict_access=True,
        read_and_write_roles=everyone_except_membros
    )
]


roles_msg = """
{} Conferindo *roles* existentes!!!
{} Criando novos *roles*
{} Configurando permissões
"""


async def get_or_create_role(
    name: str, guild: Guild, permissions: Permissions, colour: Colour
):
    existing_roles = await guild.fetch_roles()
    role = discord.utils.get(existing_roles, name=name)
    role_params = {
        'name': name,
        'colour': colour
    }
    if not role:
        if permissions:
            role_params.update({'permissions': permissions})
        role = await guild.create_role(**role_params)

    return role


async def create_channel(channel, ctx):

    params = {
        "name": channel.name,
        "guild": ctx.guild,
        "type": discord.ChannelType.voice if channel.voice else discord.ChannelType.text,
        "position": channel.position,
        "read_only_roles": channel.read_only_roles,
        "read_and_write_roles": channel.read_and_write_roles,
    }

    if channel.category != "default":
        params["category"] = await create_category(channel, ctx)

    await get_or_create_channel(**params)


async def create_category(channel, ctx):
    if channel.category == "default":
        return None

    overwrites = (
        {ctx.guild.default_role: PermissionOverwrite(read_messages=False)}
        if channel.restrict_access
        else None
    )

    category = await get_or_create_channel(
        channel.category,
        ctx.guild,
        type=ChannelType.category,
        overwrites=overwrites,
        position=channel.position,
    )
    return category


async def get_or_create_channel(
    name: str,
    guild: Guild,
    type: ChannelType = ChannelType.text,
    read_only_roles=[],
    read_and_write_roles=[],
    **kwargs
):
    methods = {
        ChannelType.category: guild.create_category,
        ChannelType.text: guild.create_text_channel,
        ChannelType.voice: guild.create_voice_channel,
    }
    method = methods.get(type)
    if not method:
        raise Exception("Channel type unknown")

    search_kwargs = {}
    if "category" in kwargs:
        search_kwargs["category_id"] = kwargs["category"].id

    existing_channels = await guild.fetch_channels()
    channel = discord.utils.get(
        existing_channels, name=name, type=type, **search_kwargs
    )
    if not channel:
        channel = await method(name=name, **kwargs)

    existing_roles = await guild.fetch_roles()

    for role in read_only_roles:
        role = discord.utils.get(existing_roles, name=role.name)
        overwrite = discord.PermissionOverwrite()
        overwrite.send_messages = False
        overwrite.read_messages = True
        await channel.set_permissions(role, overwrite=overwrite)

    for role in read_and_write_roles:
        role = discord.utils.get(existing_roles, name=role.name)
        overwrite = discord.PermissionOverwrite()
        overwrite.send_messages = True
        overwrite.read_messages = True
        overwrite.read_message_history = True
        await channel.set_permissions(role, overwrite=overwrite)

    return channel
