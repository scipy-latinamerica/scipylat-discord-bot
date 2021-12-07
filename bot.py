# snake.bot

import asyncio
import discord
import sentry_sdk
import sys
from decouple import config
from discord.ext import commands
from src.conference import ROLES, CHANNELS, create_channel, get_or_create_role, roles_msg
from src.icons import icon_check, icon_1, icon_2, icon_3, icon_time
from src.helpers import get_destination
from src.bot_logging import logger
from src.cogs import Reminders, Greetings


DISCORD_TOKEN = config("DISCORD_TOKEN")
SENTRY_TOKEN = config("SENTRY_TOKEN", default=None)

if SENTRY_TOKEN:
    sentry_sdk.init(SENTRY_TOKEN, traces_sample_rate=1.0)

bot = commands.Bot(command_prefix="scibot!", intents=discord.Intents.all())

bot.add_cog(Greetings(bot))
# bot.add_cog(Reminders(bot))
# bot.add_cog(cogs.Schedules(bot))


@bot.event
async def on_error(event, *args, **kwargs):
    """Don't ignore the error, causing Sentry to capture it."""
    logger.exception("Exception while handling event. event={event!r}, args={args!r}, kwargs={kwargs!r}")
    if SENTRY_TOKEN:
        _, e, traceback = sys.exc_info()
        sentry_sdk.capture_exception(e)
        logger.info(f"Exception sent to Sentry. e={e!r}")


@bot.event
async def on_message(message):
    if not message.author.bot and message.content.lower() == "ping":
        await message.channel.send("pong")
    await bot.process_commands(message)


@bot.group(name="config", invoke_without_command=True)
async def config_group(ctx, *args):
    await ctx.channel.send(
        "Comandos Disponíveis:\n"
        "**info**\n - Mostrar informações dos canais\n"
        "**roles**\n - Cria todos os roles necessários\n"
        "**canais**\n - Cria todos os canais necessários\n"
        "**reset-roles**\n - Deleta todos os roles criados pelo bot\n"
        "**reset-canais**\n - Deleta todos os canais criados pelo bot\n"
    )


@config_group.command(name="info")
@commands.has_role("Moderator")
async def info(ctx: commands.Context):
    await ctx.channel.send(
        content=(f"Guild ID: `{ctx.guild.id}`\nChannel ID: `{ctx.channel.id}`\n")
    )


@config_group.command(name="roles")
@commands.has_role("Moderator")
async def config_roles(ctx: commands.Context):
    logger.info("Configurando roles")
    tracking_message = await ctx.channel.send(roles_msg.format(icon_1, icon_2, icon_3))

    roles = await ctx.guild.fetch_roles()
    roles = {role.name: role for role in roles}
    logger.info(f"{len(roles)} roles encontrados. roles={','.join(roles.keys())!r}")

    await tracking_message.edit(content=(roles_msg.format(icon_check, icon_2, icon_3)))

    logger.info("Criando roles")
    for role in ROLES:
        try:
            roles[role.name] = await get_or_create_role(name=role.name, guild=ctx.guild,
                                                        permissions=role.permissions, colour=role.colour)
            logger.info(f"Role {role.name} created.")
        except Exception as e:
            logger.info(f"Problem while creating role {role.name}. Skipping it for now.")
            logger.exception(f"Exception sent to Sentry. e={e!r}")

    await tracking_message.edit(content=(roles_msg.format(icon_check, icon_check, icon_3)))

    logger.info("Configurando permissões")
    positions = {roles[role.name]: role.position for role in ROLES}
    positions[ctx.guild.me.top_role] = 999
    await ctx.guild.edit_role_positions(positions)

    await tracking_message.edit(content=(roles_msg.format(icon_check, icon_check, icon_check)))


@config_group.command(name="canais")
@commands.has_role("Moderator")
async def config_channels(ctx: commands.Context):

    track_message = await ctx.channel.send("""Criando Categorias e Canais""")

    for channel in CHANNELS:
        channel_message = await ctx.channel.send(
            """Channel {} being created. {}""".format(channel.name, icon_time)
        )
        await create_channel(channel, ctx)
        await channel_message.edit(
            content=(
                """Channel {} being created. {}""".format(channel.name, icon_check)
            )
        )

    await track_message.edit(content=("""Criando Categorias e Canais {}""".format(icon_check)))


@bot.command(name="msg", brief="Send a msg to a channel [#channel] [msg]")
@commands.has_role("Moderator")
async def sendmsg(ctx, *args):

    if len(args) < 2:
        logger.warning("Missing destination channel and message")
        return

    destination, destination_type = get_destination(ctx, args[0])

    if not destination:
        logger.warning(
            f"Destination not found. args={args!r}"
        )
        return

    message = " ".join(args[1:])

    logger.info(f"Message sent. Destination={destination}, message={message}")
    await destination.send(message)


@config_group.command(name="reset-canais")
@commands.has_role("Moderator")
async def reset_channels(ctx: commands.Context):
    guild = ctx.guild

    channels = await guild.fetch_channels()
    managed_channels = [channel.name for channel in CHANNELS] + [channel.category for channel in CHANNELS]
    managed_channels = list(set(managed_channels))
    channels_to_be_deleted = [channel for channel in channels if channel.name in managed_channels]
    await asyncio.gather(*[
        channel.delete() for channel in channels_to_be_deleted
    ])
    logger.info(f"Channels deleted: {channels_to_be_deleted}")


@config_group.command(name="reset-roles")
@commands.has_role("Moderator")
async def reset_roles(ctx: commands.Context):
    guild = ctx.guild

    roles = await guild.fetch_roles()
    managed_roles = [role.name for role in ROLES]
    roles_to_be_deleted = [role for role in roles if role.name in managed_roles]
    await asyncio.gather(*[
        role.delete() for role in roles_to_be_deleted
    ])
    logger.info(f"Roles deleted: {roles_to_be_deleted}")


@bot.event
async def on_ready():
    logger.info("Show is starting!")
    logger.info("We have logged in as {0.user}".format(bot))


if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
