# ---------------------------
# VC Tracker Bot - Live + Final Summary in One Message (Safe Token)
# ---------------------------

import discord
from discord.ext import commands, tasks
import datetime
import os
from dotenv import load_dotenv

# ---------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------
load_dotenv()  # Reads your .env file
TOKEN = os.getenv("DISCORD_TOKEN")

# ---------------------------
# CONFIGURATION
# ---------------------------
GUILD_ID = 1460365410552516743
VC_LOG_CHANNEL_ID = 1462864794788036638
MY_ID = 811267159925588010
GF_ID = 652651964722577408

EMOJIS = {
    MY_ID: '💜',
    GF_ID: '❤️'
}

# ---------------------------
# INITIALIZE BOT
# ---------------------------
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------------------
# TRACKING VARIABLES
# ---------------------------
vc_session_active = False
vc_session_start = None
vc_message = None
vc_users_in_call = set()
vc_start_times = {}  # { user_id: datetime }
bot.individual_times = {}  # { user_id: total_seconds }

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def format_duration(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))

def log(message):
    with open("vc_tracker_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()}: {message}\n")

async def update_live_message(guild):
    global vc_message
    if not vc_message:
        return

    now = datetime.datetime.utcnow()
    my_time = bot.individual_times.get(MY_ID, 0)
    gf_time = bot.individual_times.get(GF_ID, 0)

    if MY_ID in vc_users_in_call:
        my_time += (now - vc_start_times.get(MY_ID, now)).total_seconds()
    if GF_ID in vc_users_in_call:
        gf_time += (now - vc_start_times.get(GF_ID, now)).total_seconds()

    my_member = guild.get_member(MY_ID)
    gf_member = guild.get_member(GF_ID)

    content = (
        f"{EMOJIS[MY_ID]} {my_member.display_name}: ⏱ {format_duration(my_time)}\n"
        f"{EMOJIS[GF_ID]} {gf_member.display_name}: ⏱ {format_duration(gf_time)}\n"
        f"Session started: {vc_session_start.strftime('%d-%m-%Y %H:%M:%S UTC')}"
    )

    try:
        await vc_message.edit(content=content)
    except discord.NotFound:
        vc_message = None

# ---------------------------
# EVENT: VOICE STATE UPDATE
# ---------------------------
@bot.event
async def on_voice_state_update(member, before, after):
    global vc_session_active, vc_session_start, vc_message, vc_users_in_call, vc_start_times

    if member.id not in [MY_ID, GF_ID]:
        return

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return

    # Track users currently in VC
    if after.channel is not None:
        vc_users_in_call.add(member.id)
        if member.id not in vc_start_times:
            vc_start_times[member.id] = datetime.datetime.utcnow()
    else:
        vc_users_in_call.discard(member.id)
        start_time = vc_start_times.pop(member.id, None)
        if start_time:
            duration = (datetime.datetime.utcnow() - start_time).total_seconds()
            bot.individual_times[member.id] = bot.individual_times.get(member.id, 0) + duration
            log(f"{member.display_name} left VC after {format_duration(duration)}")

    # Start session
    if not vc_session_active and vc_users_in_call:
        vc_session_active = True
        vc_session_start = datetime.datetime.utcnow()
        bot.individual_times = {}
        log(f"VC session started by {member.display_name}")

        channel = guild.get_channel(VC_LOG_CHANNEL_ID)
        if channel:
            my_member = guild.get_member(MY_ID)
            gf_member = guild.get_member(GF_ID)
            content = (
                f"{EMOJIS[MY_ID]} {my_member.display_name}: ⏱ 0:00:00\n"
                f"{EMOJIS[GF_ID]} {gf_member.display_name}: ⏱ 0:00:00\n"
                f"Session started: {vc_session_start.strftime('%d-%m-%Y %H:%M:%S UTC')}"
            )
            vc_message = await channel.send(content)

    # End session
    elif vc_session_active and not vc_users_in_call:
        vc_session_active = False
        session_end = datetime.datetime.utcnow()
        overall_duration = (session_end - vc_session_start).total_seconds()
        my_member = guild.get_member(MY_ID)
        gf_member = guild.get_member(GF_ID)

        summary = (
            f"{EMOJIS[MY_ID]} {my_member.display_name}: ⏱ {format_duration(bot.individual_times.get(MY_ID, 0))}\n"
            f"{EMOJIS[GF_ID]} {gf_member.display_name}: ⏱ {format_duration(bot.individual_times.get(GF_ID, 0))}\n"
            f"Session started: {vc_session_start.strftime('%d-%m-%Y %H:%M:%S UTC')}\n"
            f"Session ended: {session_end.strftime('%d-%m-%Y %H:%M:%S UTC')}\n"
            f"Total session duration: {format_duration(overall_duration)}"
        )

        log(f"VC session ended. Total duration: {format_duration(overall_duration)}")
        if vc_message:
            try:
                await vc_message.edit(content=summary)
            except discord.NotFound:
                pass
            vc_message = None

        channel = guild.get_channel(VC_LOG_CHANNEL_ID)
        if channel:

# ---------------------------
# LIVE UPDATE LOOP
# ---------------------------
@tasks.loop(seconds=30)
async def live_update_loop():
    if vc_session_active:
        guild = bot.get_guild(GUILD_ID)
        if guild:
            await update_live_message(guild)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    live_update_loop.start()
    log("Bot started and ready.")

# ---------------------------
# RUN BOT
# ---------------------------
from flask import Flask
from threading import Thread

app = Flask("")

@app.route("/")
def home():
    return "I'm alive"

def run():
    app.run(host="0.0.0.0", port=8080)

# Run the web server in a separate thread
Thread(target=run).start()
bot.run(TOKEN)
