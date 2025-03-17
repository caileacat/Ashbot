import os
import json
import asyncio
import discord
import logging
import datetime
import threading
import subprocess
import time
from dotenv import load_dotenv
from discord.ext import commands
from core.logging_manager import show_logging_menu
from core.weaviate_manager import weaviate_menu, start_weaviate, is_weaviate_running
from core.weaviate_manager import create_weaviate_container, initialize_weaviate_data

# ✅ Load environment variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
DOCKER_EXE_PATH = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"

# ✅ Set up logging (default to INFO)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ✅ Set up Discord bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Required for reading messages
bot = commands.Bot(command_prefix="/", intents=intents)

# ✅ Track bot state
bot_running = False
bot_thread = None

### 🐳 Docker Functions ###
def is_docker_running():
    """Check if Docker is running."""
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
        return "Server Version" in result.stdout
    except FileNotFoundError:
        return False

def start_docker():
    """Attempt to start Docker Desktop on Windows and wait for it."""
    print("🐳 Docker is not running. Attempting to start...")
    try:
        subprocess.run(["powershell", "-Command", f"Start-Process '{DOCKER_EXE_PATH}' -NoNewWindow"], check=True)
        print("⏳ Waiting for Docker to start...")

        for _ in range(30):  # Wait up to 30 seconds
            if is_docker_running():
                print("✅ Docker is now running!")
                return True
            time.sleep(1)

        print("❌ Docker did not start in time.")
        return False
    except Exception as e:
        print(f"❌ Error starting Docker: {e}")
        return False

### 🎭 Bot Event: On Ready ###
@bot.event
async def on_ready():
    """Triggered when the bot successfully logs in and registers commands correctly."""
    try:
        await asyncio.sleep(5)  # ✅ Allow Discord time to initialize
        print("🚀 Checking and syncing commands...")

        # ✅ Step 1: Sync all commands normally
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Logged in as {bot.user} | Commands Re-Synced")

    except discord.app_commands.errors.CommandAlreadyRegistered as e:
        print(f"⚠️ Command '{e.name}' is already registered. Skipping re-registration.")

    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

    # ✅ Step 2: Debugging - Print registered commands dynamically
    try:
        commands = await bot.tree.fetch_commands(guild=discord.Object(id=GUILD_ID))
        command_list = [cmd.name for cmd in commands]
        if command_list:
            print(f"📌 Registered commands: {command_list}")
    except Exception as e:
        print(f"❌ Error fetching registered commands: {e}")

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
    global bot_running

    # ✅ **Ensure Docker is running before anything else**
    print("🔄 Ensuring Docker is running...")
    if not is_docker_running():
        if not start_docker():
            print("🚨 Docker must be running for AshBot to work. Continuing anyway...")
    
    # ✅ **Ensure Weaviate is running properly before allowing AshBot to start**
    print("🔄 Ensuring Weaviate is running...")
    if not is_weaviate_running():
        print("🧠 Weaviate is not running. Attempting to start...")
        if not start_weaviate():
            print("❌ Weaviate failed to start, but you can manage it from the menu.")

    while True:
        time.sleep(3)  # ✅ Waits 3 seconds before re-printing the menu
        print("\n=== AshBot Menu ===")
        if bot_running:
            print("[S] Stop AshBot")  # ✅ Stop option at the top
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
    show_main_menu()
