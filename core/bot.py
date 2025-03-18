import os
import time
import asyncio
import discord
import logging
import datetime
import threading
import subprocess
from dotenv import load_dotenv
from discord.ext import commands
from core.startup import startup_sequence
from core.logging_manager import show_logging_menu
from core.weaviate_manager import (
    weaviate_menu, start_weaviate, is_weaviate_running,
    fetch_user_profile, fetch_long_term_memories, fetch_recent_conversations
)
from core.message_handler import send_to_chatgpt  # ✅ Import message handler

logger = logging.getLogger("discord")

# ✅ Load environment variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
DOCKER_EXE_PATH = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"

# ✅ Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ✅ Set up Discord bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Required for reading messages
bot = commands.Bot(command_prefix="/", intents=intents)

# ✅ Track bot state
bot_running = False
bot_thread = None

### 🎭 Bot Event: On Ready ###
@bot.event
async def on_ready():
    """Triggered when the bot starts and syncs commands."""
    try:
        await asyncio.sleep(3)
        print("🚀 Checking and syncing commands...")

        # ✅ Resync Commands (BUT DON'T CLEAR THEM)
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))

        # ✅ Delay before fetching commands (let Discord API catch up)
        await asyncio.sleep(2)

        # ✅ Debug: Fetch and print registered commands
        commands = await bot.tree.fetch_commands(guild=discord.Object(id=GUILD_ID))
        print(f"📌 Registered commands: {[cmd.name for cmd in commands]}")

        print(f"✅ Logged in as {bot.user} | Commands Re-Synced")
        print("✅ AshBot is fully ready and online!")

    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

@bot.event
async def on_disconnect():
    """Handles unexpected disconnections by attempting reconnection."""
    logger.warning("🔌 Lost connection to Discord! Attempting to reconnect...")

    for attempt in range(1, 6):  # Try reconnecting up to 5 times
        wait_time = min(5 * attempt, 60)  # Waits 5, 10, 15... up to 60 seconds
        await asyncio.sleep(wait_time)

        if bot.is_ready():
            logger.info("✅ Successfully reconnected to Discord!")
            return  # Exit loop if reconnect successful

        try:
            logger.info(f"🔄 Reconnection attempt {attempt}...")
            await bot.start(DISCORD_BOT_TOKEN)
        except Exception as e:
            logger.error(f"🚨 Reconnection failed on attempt {attempt}: {e}")

    logger.critical("❌ Could not reconnect after multiple attempts. Manual restart required.")

### 🗨️ Register the `/ash` command ###
@bot.tree.command(name="ash", description="Talk to Ash")
async def talk_to_ash(interaction: discord.Interaction, message: str):
    """Handles the /ash command."""
    
    await interaction.response.send_message("💨 Processing... Hang tight! 🌿", ephemeral=False)

    try:
        user_id = str(interaction.user.id)
        username = interaction.user.name
        timestamp = datetime.datetime.now(datetime.UTC).isoformat()

        # ✅ Check if Weaviate is running **before making requests**
        if not is_weaviate_running():
            await interaction.channel.send("⚠️ Weaviate is currently down! Using basic responses.")
            structured_message = {
                "user": {
                    "id": user_id,
                    "name": username,
                    "interaction_count": 0,
                },
                "user_message": message,
                "timestamp": timestamp,
                "conversation_context": [],
                "long_term_memories": [],
                "recent_conversations": [],
            }
        else:
            # ✅ Fetch User Data from Weaviate
            user_profile = fetch_user_profile(user_id) or {}
            long_term_memories = fetch_long_term_memories(user_id)
            recent_conversations = fetch_recent_conversations(user_id)

            # ✅ Fetch Last 5 Messages in the Channel
            last_messages = []
            async for msg in interaction.channel.history(limit=10):
                if msg.author.bot:
                    continue
                last_messages.append({
                    "user_id": str(msg.author.id),
                    "message": msg.content,
                    "timestamp": msg.created_at.isoformat()
                })
                if len(last_messages) == 5:
                    break  

            # ✅ Structure the message
            structured_message = {
                "user": {
                    "id": user_id,
                    "name": user_profile.get("name", username),
                    "pronouns": user_profile.get("pronouns", "they/them"),
                    "role": user_profile.get("role", "Unknown"),
                    "relationship_notes": user_profile.get("relationship_notes", "No relationship data"),
                    "interaction_count": user_profile.get("interaction_count", 0),
                },
                "user_message": message,
                "timestamp": timestamp,
                "conversation_context": last_messages,
                "long_term_memories": long_term_memories,
                "recent_conversations": recent_conversations,
            }

        # ✅ Log the data to `debug.txt`
        send_to_chatgpt(structured_message, user_id)

        # ✅ Notify that processing is done
        await interaction.channel.send(f"🌿 Got it, {username}! Let me think... (Data logged to debug.txt)")

    except Exception as e:
        print(f"❌ Error in /ash command: {e}")
        await interaction.channel.send("❌ Oops! My brain is too foggy right now. Try again in a bit.")

### 🛠️ Bot Controls (Start/Stop) ###
def run_bot():
    """Runs AshBot in a separate thread."""
    global bot_running
    bot_running = True
    bot.run(DISCORD_BOT_TOKEN)

def start_ashbot():
    """Starts AshBot in a separate thread so the menu remains available."""
    global bot_running, bot_thread
    if bot_running:
        print("⚠️ AshBot is already running.")
        return
    
    print("🚀 Starting AshBot...")
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

def stop_ashbot():
    """Stops AshBot gracefully."""
    global bot_running
    if not bot_running:
        print("⚠️ AshBot is already stopped.")
        return

    print("🛑 Stopping AshBot...")
    bot_running = False
    os._exit(0)  # Force stop for now (we will refine this later)

### 📝 Console Menu ###
def show_main_menu():
    """Displays the main menu for AshBot."""
    while True:
        time.sleep(3)
        print("\n=== AshBot Menu ===")
        if bot_running:
            print("[S] Stop AshBot")
        else:
            print("[A] Start AshBot")
            print("[D] Start AshBot with Watchdog")
        print("[W] Manage Weaviate")
        print("[C] Configure Logging")
        print("[X] Exit AshBot")

        choice = input("Select an option: ").strip().upper()
        if choice == "S" and bot_running:
            stop_ashbot()
        elif choice == "A" and not bot_running:
            start_ashbot()
        elif choice == "D" and not bot_running:
            start_ashbot()
        elif choice == "W":
            weaviate_menu()
        elif choice == "C":
            show_logging_menu()
        elif choice == "X":
            break

if __name__ == "__main__":
    if not is_weaviate_running():
        startup_sequence()
    show_main_menu()
