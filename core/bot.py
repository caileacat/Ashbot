import os
import json
import time  # ✅ Needed for adding delay before re-printing the menu
import discord
import logging
import asyncio
import aiohttp  # ✅ Required for setting timeout
import datetime
import threading  # ✅ Allows running the bot in a separate thread
from dotenv import load_dotenv
from discord.ext import commands
from core.startup import initialize_services  # ✅ Run startup checks from the menu
from core.weaviate_manager import weaviate_menu
from core.message_handler import send_to_chatgpt  # ✅ Import message handling
from core.logging_manager import show_logging_menu

# ✅ Load environment variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ✅ Set up logging (default to INFO)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ✅ Set up Discord bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Required for reading messages

bot_running = False  # ✅ Track if the bot is running
bot_thread = None  # ✅ Track the bot thread

# ✅ Create the bot instance
bot = commands.Bot(command_prefix="/", intents=intents)

async def configure_http():
    """Configures the HTTP settings for Discord bot without deprecated timeout settings."""
    bot.http.connector = aiohttp.TCPConnector(limit=None)  # ✅ Sets unlimited connections

@bot.event
async def on_ready():
    """Triggered when the bot successfully logs in."""
    await configure_http()  # ✅ Set HTTP settings after bot is ready
    print(f"✅ Logged in as {bot.user}")

def run_bot():
    """Runs AshBot in a separate thread without causing event loop issues."""
    global bot_running
    bot_running = True

    loop = asyncio.new_event_loop()  # ✅ Create a fresh event loop for the thread
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(bot.start(DISCORD_BOT_TOKEN))  # ✅ Properly starts bot
    except KeyboardInterrupt:
        loop.run_until_complete(bot.close())
    finally:
        loop.close()  # ✅ Ensures event loop is properly closed

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

    # ✅ Close the bot properly
    loop = asyncio.get_event_loop()
    loop.call_soon_threadsafe(asyncio.create_task, bot.close())

def show_main_menu():
    """Displays the main menu for AshBot."""
    global bot_running

    # ✅ Run startup checks inside the menu
    startup_successful = initialize_services()
    if not startup_successful:
        print("❌ Startup failed. Exiting...")
        return

    while True:
        time.sleep(3)  # ✅ Waits 3 seconds before re-printing the menu
        print("\n=== AshBot Menu ===")
        if bot_running:
            print("[S] Stop AshBot")
        else:
            print("[A] Start AshBot")
            print("[D] Start AshBot with Watchdog")
        print("[W] Manage Weaviate")
        print("[C] Configure Logging")
        print("[X] Exit AshBot")

        choice = input("Select an option: ").strip()

        if choice.upper() == "S" and bot_running:
            stop_ashbot()
        elif choice.upper() == "A" and not bot_running:
            print("🚀 Starting AshBot...")
            start_ashbot()
        elif choice.upper() == "D" and not bot_running:
            print("👀 Starting AshBot with Watchdog...")
            start_ashbot()
        elif choice.upper() == "W":
            weaviate_menu()
        elif choice.upper() == "C":
            show_logging_menu()
        elif choice.upper() == "X":
            print("👋 Exiting AshBot...")
            break
        else:
            # ✅ If input is NOT a command, assume it's a message to Ash
            print(f"📩 Preparing message to Ash: {choice}")
            send_to_chatgpt(choice)  # ✅ Calls our debugging function

        time.sleep(1)  # ✅ Small delay for readability

if __name__ == "__main__":
    show_main_menu()
