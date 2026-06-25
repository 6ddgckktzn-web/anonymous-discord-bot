import os
import json
import random
import discord
from discord.ext import commands

TOKEN = os.getenv("TOKEN")

ANON_CHANNEL_ID = 1519593563178926150
NICK_FILE = "anon_nicks.json"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# --------------------
# 닉네임 재료
# --------------------

EMOJIS = [
    "🌸", "🌙", "☁️", "🫧", "🍓",
    "⭐", "🎀", "🩷", "🦋", "🐳"
]

PREFIXES = [
    "벚꽃", "달빛", "구름", "별빛", "솜사탕",
    "딸기", "새벽", "하늘", "은하", "포근한"
]

SUFFIXES = [
    "토끼", "고래", "젤리", "푸딩", "모찌",
    "고양이", "쿠키", "리본", "나비", "벨루가"
]

# --------------------
# 저장
# --------------------

def load_data():
    try:
        with open(NICK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(NICK_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )

# --------------------
# 랜덤닉 생성
# --------------------

def create_random_nick():

    emoji = random.choice(EMOJIS)
    prefix = random.choice(PREFIXES)
    suffix = random.choice(SUFFIXES)

    return f"{emoji}{prefix}{suffix}"

def get_user_nick(user_id):

    data = load_data()

    uid = str(user_id)

    if uid not in data:

        while True:

            nick = create_random_nick()

            if nick not in data.values():
                break

        data[uid] = nick
        save_data(data)

    return data[uid]

# --------------------
# 시작
# --------------------

@bot.event
async def on_ready():
    print(f"{bot.user} 로그인 완료!")

# --------------------
# 익명 채팅
# --------------------

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.channel.id != ANON_CHANNEL_ID:
        return

    nickname = get_user_nick(
        message.author.id
    )

    try:
        await message.delete()
    except:
        pass

    guild = message.guild
bot_member = guild.me

old_nick = bot_member.nick

try:
    await bot_member.edit(nick=nickname)
except Exception as e:
    print("봇 닉네임 변경 실패:", e)

await message.channel.send(message.content)

try:
    await bot_member.edit(nick=old_nick)
except Exception as e:
    print("봇 닉네임 복구 실패:", e)

bot.run(TOKEN)
