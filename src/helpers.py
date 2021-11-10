import discord


async def get_destination(ctx, cmd_str):
    _id = int(cmd_str[2:-1])
    if cmd_str.startswith("<#"):
        return discord.utils.get(ctx.guild.channels, id=_id), "channel"
    elif cmd_str.startswith("<@"):
        return discord.utils.get(ctx.guild.members, id=_id), "member"
    else:
        await ctx.channel.send(f"Channel/Member not found! **{cmd_str}**.")
        return None, None
