import discord
from discord import Guild, Permissions, Colour
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Role:
    name: str
    colour: Colour
    position: int = 0
    permissions: Optional[List[Permissions]] = None


organizadores_permissions = Permissions.all()
organizadores_permissions.administrator = False
others_permissions = discord.Permissions()

ROLES = [
    Role(name="organizadores", permissions=organizadores_permissions, position=80, colour=Colour.purple()),
    Role(name="voluntarios", position=70, colour=Colour.magenta()),
    Role(name="cdc", position=60, colour=Colour.blue()),
    Role(name="participantes", position=50, colour=Colour.gold()),
    Role(name="membros", position=40, colour=Colour.red())
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
