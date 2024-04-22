import discord
import random
from discord.ext import commands
import asyncio
import hashlib
import time
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

# Discord bot setup
intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Rate limiting variables
rate_limit_window = 60  # 1 minute
rate_limit_max_requests = 3
rate_limit_kick_duration = 300  # 5 minutes

# Behavioral analysis variables
behavioral_analysis_threshold = 5  # seconds

# Image verification variables
image_width = 200
image_height = 50
font_size = 24

# Hard-to-read font settings
distortion_amount = 0.5  # 0.0 to 1.0, higher values make the font more distorted
noise_amount = 0.2  # 0.0 to 1.0, higher values add more noise to the font

# List of hard-to-read fonts (using existing fonts)
hard_fonts = [
    'arial.ttf',  # Arial font
    'calibri.ttf',  # Calibri font
    'times.ttf',  # Times New Roman font
]

font_dir = 'fonts'


@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')


def generate_image(captcha_code):
    # Select a random hard-to-read font
    font_path = os.path.join(font_dir, random.choice(hard_fonts))

    # Create a new image with a white background
    image = Image.new('RGB', (image_width, image_height), (255, 255, 255))

    # Create a font object with a hard-to-read font
    font = ImageFont.truetype(font_path, font_size)

    # Draw the CAPTCHA code on the image with distortion and noise
    draw = ImageDraw.Draw(image)
    for i, char in enumerate(captcha_code):
        x = 10 + i * 30
        y = 10
        draw.text((x, y), char, font=font, fill=(0, 0, 0))
        draw.text((x + random.uniform(-distortion_amount, distortion_amount),
                   y + random.uniform(-distortion_amount, distortion_amount)), char, font=font,
                  fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

    # Add some noise to the image
    for _ in range(int(image_width * image_height * noise_amount)):
        x = random.randint(0, image_width)
        y = random.randint(0, image_height)
        draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

    # Save the image to a bytes buffer
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)

    return buffer


@bot.event
async def on_member_join(member):
    # Generate a random image with a CAPTCHA code
    captcha_code = "".join(
        random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*()") for _ in range(6))
    image = generate_image(captcha_code)

    # Send the image to the new member
    file = discord.File(fp=image, filename='captcha.png')
    await member.send("Please verify that you are human by entering the code in the image. You have 60 seconds to respond. If you fail, you will be kicked!", file=file)

    # Wait for the member to respond with the correct CAPTCHA code
    def check(message):
        return message.author == member and message.channel.type == discord.ChannelType.private

    try:
        start_time = time.time()  # Record the start time
        response = await bot.wait_for('message', timeout=60.0, check=check)
        end_time = time.time()  # Record the end time
        response_time = end_time - start_time  # Calculate the response time
        if response.content == captcha_code:
            await member.send("Verification successful You can now access the server.")
            if response_time < behavioral_analysis_threshold:
                await member.kick(reason='Suspicious behavior detected. Please try again.')
                await member.send("You have been kicked from the server for suspicious behavior.")
            else:
                return  # Allow the member to access the server
        else:
            await member.send("Warning: You entered an incorrect verification code. You have 1 attempt left. Please try again.")
            start_time = time.time()  # Record the start time
            response = await bot.wait_for('message', timeout=60.0, check=check)
            end_time = time.time()  # Record the end time
            response_time = end_time - start_time  # Calculate the response time
            if response.content == captcha_code:
                await member.send("Verification successful You can now access the server.")
                if response_time < behavioral_analysis_threshold:
                    await member.kick(reason='Suspicious behavior detected. Please try again.')
                    await member.send("You have been kicked from the server for suspicious behavior.")
                else:
                    return  # Allow the member to access the server
            else:
                await member.send("You didn't complete the verification in time. You will be kicked in 10 seconds.")
                await asyncio.sleep(10)
                await member.kick(reason='Failed to verify within 60 seconds.')
                await member.send("You have been kicked from the server for failing to complete the verification within 60 seconds.")
    except asyncio.TimeoutError:
        await member.send("You didn't complete the verification in time. You will be kicked in 10 seconds.")
        await asyncio.sleep(10)
        await member.kick(reason='Failed to verify within 60 seconds.')
        await member.send("You have been kicked from the server for failing to complete the verification within 60 seconds.")


# Run the bot with your Discord bot token
bot.run('your-discord-token-here')