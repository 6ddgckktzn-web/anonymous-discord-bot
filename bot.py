import os
import json
import random
import asyncio
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("TOKEN")

ANON_CHANNEL_ID = 1519593563178926150
LOG_CHANNEL_ID = 1519618833860526110

NICK_FILE = "anon_nicks.json"
MESSAGE_FILE = "anon_messages.json"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
send_lock = asyncio.Lock()

EMOJIS = ["🌸", "🌙", "☁️", "🫧", "🍓", "⭐", "🎀", "🩷", "🦋", "🐳"]
PREFIXES = ["벚꽃", "달빛", "구름", "별빛", "솜사탕", "딸기", "새벽", "하늘", "은하", "포근한"]
SUFFIXES = ["토끼", "고래", "젤리", "푸딩", "모찌", "고양이", "쿠키", "리본", "나비", "벨루가"]

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def create_random_nick():
    return f"{random.choice(EMOJIS)}{random.choice(PREFIXES)}{random.choice(SUFFIXES)}"

def get_user_nick(user_id):
    data = load_json(NICK_FILE)
    uid = str(user_id)

    if uid not in data:
        while True:
            nick = create_random_nick()
            if nick not in data.values():
                break

        data[uid] = nick
        save_json(NICK_FILE, data)

    return data[uid]

def set_user_nick(user_id, nickname):
    data = load_json(NICK_FILE)

    if nickname in data.values() and data.get(str(user_id)) != nickname:
        return False

    data[str(user_id)] = nickname
    save_json(NICK_FILE, data)
    return True

def save_message_map(sent_message_id, user_id, nickname):
    data = load_json(MESSAGE_FILE)
    data[str(sent_message_id)] = {
        "user_id": str(user_id),
        "nickname": nickname
    }
    save_json(MESSAGE_FILE, data)

def get_reply_nick(message):
    if not message.reference:
        return None

    ref_id = message.reference.message_id
    if not ref_id:
        return None

    data = load_json(MESSAGE_FILE)
    info = data.get(str(ref_id))

    if not info:
        return None

    return info.get("nickname")

async def send_log(message, nickname):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if not log_channel:
        return

    attachment_names = [a.filename for a in message.attachments]

    log_text = (
        "🗑️ 익명 메시지 로그\n"
        f"실제 유저: {message.author} / {message.author.id}\n"
        f"익명닉: {nickname}\n"
        f"내용: {message.content if message.content else '(내용 없음)'}"
    )

    if attachment_names:
        log_text += "\n첨부파일: " + ", ".join(attachment_names)

    await log_channel.send(log_text)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} 로그인 완료!")

@bot.tree.command(name="닉변", description="익명 닉네임을 직접 변경합니다.")
@app_commands.describe(닉네임="바꾸고 싶은 익명 닉네임")
async def change_nick(interaction: discord.Interaction, 닉네임: str):
    if len(닉네임) > 20:
        await interaction.response.send_message("❌ 닉네임은 20자 이하로 해줘!", ephemeral=True)
        return

    success = set_user_nick(interaction.user.id, 닉네임)

    if not success:
        await interaction.response.send_message("❌ 이미 사용 중인 닉네임이야!", ephemeral=True)
        return

    await interaction.response.send_message(
        f"✨ 익명 닉네임이 `{닉네임}` 으로 변경됐어!",
        ephemeral=True
    )

@bot.tree.command(name="랜덤닉변", description="익명 닉네임을 랜덤으로 변경합니다.")
async def random_nick(interaction: discord.Interaction):
    data = load_json(NICK_FILE)

    while True:
        nickname = create_random_nick()
        if nickname not in data.values():
            break

    data[str(interaction.user.id)] = nickname
    save_json(NICK_FILE, data)

    await interaction.response.send_message(
        f"✨ 새 익명 닉네임: `{nickname}`",
        ephemeral=True
    )

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != ANON_CHANNEL_ID:
        return

    nickname = get_user_nick(message.author.id)
    reply_nick = get_reply_nick(message)

    files = []
    for attachment in message.attachments:
        try:
            files.append(await attachment.to_file())
        except Exception as e:
            print("첨부파일 변환 실패:", e)

    try:
        await send_log(message, nickname)
    except Exception as e:
        print("로그 전송 실패:", e)

    try:
        await message.delete()
    except Exception as e:
        print("원본 메시지 삭제 실패:", e)

    content = message.content or ""

    if reply_nick:
        content = f"↳ {reply_nick}에게\n{content}"

    if not content and not files:
        return

    async with send_lock:
        bot_member = message.guild.me

        try:
            await bot_member.edit(nick=nickname)
            await asyncio.sleep(0.7)
        except Exception as e:
            print("봇 닉네임 변경 실패:", e)

        sent = await message.channel.send(
            content=content if content else None,
            files=files
        )

        save_message_map(sent.id, message.author.id, nickname)

bot.run(TOKEN)
