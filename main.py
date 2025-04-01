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
    voice_client = None
    try:
        voice_client = await channel.connect()
        
        # Optymalizacja parametrów FFmpeg
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -protocol_whitelist file,pipe,udp',
            'options': '-vn -bufsize 512k -threads 2'
        }
        
        # Konwersja do formatu WAV dla większej stabilności
        voice_client.play(discord.FFmpegPCMAudio(
            executable="ffmpeg",
            source="ffmpeg -i barka.mp3 -f wav pipe:1",
            pipe=True,
            **ffmpeg_options
        ))
        await asyncio.sleep(30)
        # Dodatkowe zabezpieczenie czasowe
        start_time = time.time()
        while voice_client.is_playing():
            if time.time() - start_time > 300:  # Maksymalnie 5 minut
                raise TimeoutError("Przekroczono czas odtwarzania")
            await asyncio.sleep(0.5)

    except Exception as e:
        print(f"Błąd odtwarzania: {str(e)}")
    finally:
        if voice_client:
            try:
                await voice_client.disconnect()
                await asyncio.sleep(2)  # Czekaj na pełne zamknięcie połączenia
            except:
                pass


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

    if current_time == "19:42":
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
