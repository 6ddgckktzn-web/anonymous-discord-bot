import os
import json
import random
import discord
from discord.ext import commands

TOKEN = os.getenv("TOKEN")

ANON_CHANNEL_ID = 1519620992014745621
NICK_FILE = "anon_nicks.json"
WEBHOOK_NAME = "익명게시판봇"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

EMOJIS = ["🌸", "🌙", "☁️", "🫧", "🍓", "⭐", "🎀", "🩷", "🦋", "🐳"]
PREFIXES = ["벚꽃", "달빛", "구름", "별빛", "솜사탕", "딸기", "새벽", "하늘", "은하", "포근한"]
SUFFIXES = ["토끼", "고래", "젤리", "푸딩", "모찌", "고양이", "쿠키", "리본", "나비", "벨루가"]

def load_data():
    try:
        with open(NICK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(NICK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def create_random_nick():
    return f"{random.choice(EMOJIS)}{random.choice(PREFIXES)}{random.choice(SUFFIXES)}"

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

async def get_or_create_webhook(channel):
    webhooks = await channel.webhooks()

    for webhook in webhooks:
        if webhook.name == WEBHOOK_NAME:
            return webhook

    return await channel.create_webhook(name=WEBHOOK_NAME)

@bot.event
async def on_ready():
    print(f"{bot.user} 로그인 완료!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != ANON_CHANNEL_ID:
        return

    nickname = get_user_nick(message.author.id)

    files = []
    for attachment in message.attachments:
        try:
            files.append(await attachment.to_file())
        except Exception as e:
            print("첨부파일 변환 실패:", e)

    content = message.content if message.content else None

    try:
        await message.delete()
    except Exception as e:
        print("원본 메시지 삭제 실패:", e)

    if not content and not files:
        return

    try:
        webhook = await get_or_create_webhook(message.channel)

        await webhook.send(
            content=content,
            username=nickname,
            files=files,
            wait=True
        )

    except Exception as e:
        print("Webhook 전송 실패:", e)

bot.run(TOKEN)
