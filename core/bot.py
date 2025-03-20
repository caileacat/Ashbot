import os
import time
import random
import asyncio
import discord
import logging
import threading
from discord.ext import commands
from core.startup import startup_sequence
from core.message_handler import gather_data_for_chatgpt
from data.constants import GUILD_ID, DISCORD_BOT_TOKEN, ASH_EPHEMERAL_MESSAGES
from core.logging_manager import show_logging_menu
from core.weaviate_manager import (
    weaviate_menu, is_weaviate_running
)
from weaviate.classes.query import Filter

logger = logging.getLogger("discord")

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
        await asyncio.sleep(3)

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
    """Handles the /ash command and prevents the 'Bot didn't respond' warning with an ephemeral message."""

    user_id = str(interaction.user.id)
    channel = interaction.channel

    try:
        # ✅ Randomly select an ephemeral message
        ephemeral_message = random.choice(ASH_EPHEMERAL_MESSAGES)

        # ✅ Respond immediately with an ephemeral message
        await interaction.response.send_message(ephemeral_message, ephemeral=True)

        # ✅ Process the request asynchronously without an immediate public response
        asyncio.create_task(gather_data_for_chatgpt(user_id, message, channel))

    except Exception as e:
        print(f"❌ ERROR processing /ash command: {e}")

### 🛠️ Bot Controls (Start/Stop) ###
def run_bot():
    """Runs AshBot in a separate thread."""
    global bot_running
    logging.getLogger().setLevel(logging.WARNING)
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
    logging.getLogger("discord.client").setLevel(logging.WARNING)
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
        print("[W] Manage Weaviate")
        print("[C] Configure Logging")
        print("[X] Exit AshBot")

        choice = input("Select an option: ").strip().upper()
        if choice == "S" and bot_running:
            stop_ashbot()
        elif choice == "A" and not bot_running:
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
