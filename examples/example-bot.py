# snake.bot

import discord
from decouple import config
DISCORD_TOKEN = config("DISCORD_TOKEN")
client = discord.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


if __name__ == '__main__':
    client.run(DISCORD_TOKEN)
