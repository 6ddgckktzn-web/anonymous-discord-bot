import os
import discord
from discord.ext import commands

TOKEN = os.getenv("TOKEN")

ANON_CHANNEL_ID = 1519593563178926150

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

@bot.event
async def on_ready():
    print(f"{bot.user} 로그인 완료!")

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.channel.id != ANON_CHANNEL_ID:
        return

    try:
        await message.delete()
    except:
        pass

    await message.channel.send(
        f"🌸 익명\n\n{message.content}"
    )

bot.run(TOKEN)
