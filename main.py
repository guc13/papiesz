import discord
import os
import asyncio
import pytz
from datetime import datetime
from discord.ext import tasks
from keep_alive import keep_alive

# Konfiguracja Opus
if not discord.opus.is_loaded():
    discord.opus.load_opus('libopus.so.0')

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
client = discord.Client(intents=intents)

warsaw_tz = pytz.timezone('Europe/Warsaw')

# Lista ID dozwolonych serwerów (pobierz z sekretów)
ALLOWED_GUILD_IDS = list(
    map(int,
        os.getenv('ALLOWED_GUILD_IDS', '').split(',')))


async def play_barka(channel):
    try:
        voice_client = await channel.connect()
        voice_client.play(
            discord.FFmpegPCMAudio(executable="ffmpeg", source="barka.wav",pipe=True))

        while voice_client.is_playing():
            await asyncio.sleep(2)

        await voice_client.disconnect()
    except Exception as e:
        print(f"Błąd: {str(e)}")
        if voice_client:
            await voice_client.disconnect()


async def find_active_voice_channel():
    for guild in client.guilds:
        # Sprawdź czy serwer jest na liście dozwolonych
        if guild.id not in ALLOWED_GUILD_IDS:
            continue

        for channel in guild.voice_channels:
            if len(channel.members) > 0:
                print(
                    f"Znaleziono aktywny kanał: {channel.name} w {guild.name}")
                return channel
    return None


@tasks.loop(seconds=2)
async def check_time():
    current_time = datetime.now(warsaw_tz).strftime("%H:%M")

    if current_time == current_time:
        target_channel = await find_active_voice_channel()
        if target_channel:
            await play_barka(target_channel)
            await asyncio.sleep(180)
        else:
            print("Brak aktywnych kanałów w wybranych serwerach")


@client.event
async def on_ready():
    print(f'Bot aktywny na {len(ALLOWED_GUILD_IDS)} wybranych serwerach:')
    for guild_id in ALLOWED_GUILD_IDS:
        guild = client.get_guild(guild_id)
        if guild:
            print(f"- {guild.name} (ID: {guild.id})")
    check_time.start()


keep_alive()
client.run(os.getenv('DISCORD_TOKEN'))
