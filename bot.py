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


def load_data():
    try:
        with open(NICK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_data(data):
    with open(NICK_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


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


async def get_or_create_webhook(channel):
    webhooks = await channel.webhooks()

    for webhook in webhooks:
        if webhook.name == WEBHOOK_NAME:
            return webhook

    return await channel.create_webhook(
        name=WEBHOOK_NAME
    )


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} 로그인 완료!")


# ---------------------------------
# 관리자 전용: 봇 서버 닉네임 변경
# ---------------------------------

@bot.tree.command(
    name="닉변경",
    description="봇의 서버 닉네임을 변경합니다."
)
@app_commands.describe(
    닉네임="새로운 봇 닉네임"
)
async def bot_nick_change(
    interaction: discord.Interaction,
    닉네임: str
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 관리자만 사용할 수 있는 명령어입니다.",
            ephemeral=True
        )
        return

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ 서버 안에서만 사용할 수 있습니다.",
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
        bot_member = interaction.guild.me

        await bot_member.edit(
            nick=닉네임
        )

        await interaction.response.send_message(
            f"✅ 봇 닉네임을 **{닉네임}**(으)로 변경했어요!",
            ephemeral=True
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ 권한이 부족합니다.\n"
            "봇에게 **닉네임 변경** 권한이 있는지 확인해주세요.",
            ephemeral=True
        )

    except Exception as e:
        print("봇 닉네임 변경 실패:", e)

        await interaction.response.send_message(
            "❌ 닉네임 변경 중 오류가 발생했습니다.",
            ephemeral=True
        )


# ---------------------------------
# 관리자 전용: 모든 익명닉 초기화
# ---------------------------------

@bot.tree.command(
    name="전체닉초기화",
    description="모든 이용자의 익명 닉네임을 초기화합니다."
)
async def reset_all_nicks(
    interaction: discord.Interaction
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 관리자만 사용할 수 있는 명령어입니다.",
            ephemeral=True
        )
        return

    try:
        old_data = load_data()
        reset_count = len(old_data)

        save_data({})

        await interaction.response.send_message(
            "✅ 모든 익명 닉네임을 초기화했습니다.\n"
            f"초기화된 이용자 수: **{reset_count}명**\n\n"
            "각 이용자는 다음 메시지를 작성할 때 "
            "새로운 랜덤 닉네임을 받습니다.",
            ephemeral=True
        )

    except Exception as e:
        print("전체 닉네임 초기화 실패:", e)

        await interaction.response.send_message(
            "❌ 익명 닉네임 초기화 중 오류가 발생했습니다.",
            ephemeral=True
        )


# ---------------------------------
# 익명 메시지 처리
# ---------------------------------

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != ANON_CHANNEL_ID:
        return

    nickname = get_user_nick(
        message.author.id
    )

    files = []

    for attachment in message.attachments:
        try:
            file = await attachment.to_file()
            files.append(file)

        except Exception as e:
            print(
                "첨부파일 변환 실패:",
                attachment.filename,
                e
            )

    content = message.content or None

    try:
        await message.delete()

    except Exception as e:
        print("원본 메시지 삭제 실패:", e)

    if not content and not files:
        return

    try:
        webhook = await get_or_create_webhook(
            message.channel
        )

        await webhook.send(
            content=content,
            username=nickname,
            files=files,
            wait=True,
            allowed_mentions=discord.AllowedMentions.none()
        )

    except Exception as e:
        print("Webhook 전송 실패:", e)


if not TOKEN:
    raise RuntimeError(
        "Railway의 Variables에 TOKEN이 설정되어 있지 않습니다."
    )

bot.run(TOKEN)
