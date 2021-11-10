import discord
from discord import PermissionOverwrite, ChannelType, Guild
from dataclasses import dataclass


@dataclass
class Channel:
    name: str
    category: str = "default"
    position: int = 0
    restrict_access: bool = False
    voice: bool = False


CHANNELS = [
    Channel(name="boas-vindas"),
    Channel(name="bienvenidas"),
    Channel(name="regras"),
    Channel(name="reglas"),
    Channel(name="credenciamento"),

    Channel(name="board", category="ORGANIZADORES", position=1, restrict_access=True),
    Channel(name="dev", category="ORGANIZADORES", position=1, restrict_access=True),
    Channel(name="meeting", category="ORGANIZADORES", position=1, restrict_access=True, voice=True),

    Channel(name="perguntas", category="VOLUNTARIOS", position=2, restrict_access=True),
    Channel(name="voluntarios-es", category="VOLUNTARIOS", position=2, restrict_access=True),
    Channel(name="voluntarios-pt", category="VOLUNTARIOS", position=2, restrict_access=True),
    Channel(name="report", category="VOLUNTARIOS", position=2, restrict_access=True),
    Channel(name="meeting-voluntarios", category="VOLUNTARIOS", position=2, restrict_access=True, voice=True),

    Channel(name="jobs-fair", category="JOBS", position=3, restrict_access=True, voice=True),

    Channel(name="geral", category="SCIPY LATIN AMERICA CONFERENCE", position=4, restrict_access=True),
    Channel(name="keynotes", category="SCIPY LATIN AMERICA CONFERENCE", position=4, restrict_access=True),
    Channel(name="track-ciranda", category="SCIPY LATIN AMERICA CONFERENCE", position=4, restrict_access=True),
    Channel(name="track-frevo", category="SCIPY LATIN AMERICA CONFERENCE", position=4, restrict_access=True),
    Channel(name="pt-assuntos-aleatorios", category="SCIPY LATIN AMERICA CONFERENCE", position=4, restrict_access=True),
    Channel(name="es-asuntos-aleatorios", category="SCIPY LATIN AMERICA CONFERENCE", position=4, restrict_access=True),
    Channel(name="traducoes-simultaneas-pt", category="VOLUNTARIOS", position=4, restrict_access=True, voice=True),
    Channel(name="traducoes-simultaneas-es", category="VOLUNTARIOS", position=4, restrict_access=True, voice=True),

    # SCIPY.LAT
    # - todos
    # - argentina
    # - brasil
    # - bolivia
    # - chile
    # - colombia
    # - solicite-sua-embaixada

    # BAR
    # - solicite-uma-mesa

]


async def create_channel(channel, ctx):

    params = {
        "name": channel.name,
        "guild": ctx.guild,
        "type": discord.ChannelType.voice if channel.voice else discord.ChannelType.text,
        "position": channel.position,
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

    return channel
