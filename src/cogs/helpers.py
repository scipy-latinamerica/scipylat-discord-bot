import asyncio
import httpx
from functools import wraps
from src.bot_logging import logger
from decouple import config


DISCORD_LOG_CHANNEL_ID = config("DISCORD_LOG_CHANNEL_ID")


def only_log_exceptions(function):
    @wraps(function)
    async def wrapper(*args, **kwargs):
        try:
            return await function(*args, **kwargs)
        except Exception:
            logger.exception(f"Error while calling {function!r}")
    return wrapper


async def logchannel(bot, msg):
    channel = await bot.fetch_channel(DISCORD_LOG_CHANNEL_ID)
    await channel.send(msg)


async def http_get_json(semaphore, client, url, params, retry=3):
    async with semaphore:
        try:
            response = await client.get(url, params=params)
        except httpx.ReadTimeout:
            if retry > 0:
                await asyncio.sleep(20)
                return await http_get_json(semaphore, client, url, params, retry - 1)
            logger.exception("Erro")
        return response.json()
