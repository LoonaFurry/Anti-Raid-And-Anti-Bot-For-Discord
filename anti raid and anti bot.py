import discord
from discord.ext import commands
import random
import string
import time
import asyncio

intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_member_join(member):
    join_times = []
    join_times.append(time.time())
    if len(join_times) > 2 and join_times[-1] - join_times[0] < 10:
        await member.kick(reason='Raid protection activated')
        join_times.clear()
        channel = await member.create_dm()
        if channel is not None:
            await channel.send('You have been kicked by the raid protection. Please try again later.')
    else:
        join_times = join_times[-2:]

    channel = await member.create_dm()
    if channel is None:
        print(f'Failed to create DM channel with {member.name}')
        return

    # Generate a random verification code
    verification_code = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=12))
    print(f'Sending verification code {verification_code} to {member.name}')
    await channel.send(f'Welcome to the server, {member.name}! Please verify that you are not a bot by sending me the following code in 60 second: {verification_code}')

    # Wait for the member to send the verification code
    def check(m):
        return m.author == member and m.content == verification_code

    try:
        await bot.wait_for('message', check=check, timeout=60.0)
        await member.send('Thank you for verifying yourself! You are now a member of the server.')
    except asyncio.TimeoutError:
        await member.kick(reason='Failed to verify within 60 seconds')

bot.run('your-discord-token-here')