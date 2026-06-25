import os
import json
import random
import discord
from discord.ext import commands
from discord import app_commands

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
    except Exception:
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
    await bot.tree.sync()
    print(f"{bot.user} 로그인 완료!")

@bot.tree.command(name="닉변경", description="봇의 서버 닉네임을 변경합니다.")
@app_commands.describe(닉네임="새로운 봇 닉네임")
async def bot_nick_change(interaction: discord.Interaction, 닉네임: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 관리자만 사용할 수 있는 명령어입니다.",
            ephemeral=True
        )
        return

    if len(닉네임) > 32:
        await interaction.response.send_message(
            "❌ 닉네임은 32자 이하만 가능합니다.",
            ephemeral=True
        )
        return

    try:
        await interaction.guild.me.edit(nick=닉네임)

        await interaction.response.send_message(
            f"✅ 봇 닉네임을 **{닉네임}**(으)로 변경했어요!",
            ephemeral=True
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ 권한이 부족합니다. 봇에게 **닉네임 관리** 권한이 있는지 확인해주세요.",
            ephemeral=True
        )

    except Exception as e:
        print("봇 닉네임 변경 실패:", e)

        await interaction.response.send_message(
            "❌ 오류가 발생했습니다.",
            ephemeral=True
        )

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
