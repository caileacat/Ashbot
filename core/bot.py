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
from discord import app_commands  # ✅ Required for slash commands
from discord.ext import commands
from core.startup import initialize_services  # ✅ Run startup checks from the menu
from core.weaviate_manager import weaviate_menu
from core.message_handler import send_to_chatgpt  # ✅ Import message handling
from core.logging_manager import show_logging_menu
from core.message_handler import send_console_message_to_chatgpt  # ✅ Import missing function


# ✅ Load environment variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))  # ✅ Ensure the bot is registered to the correct server
bot_running = False  # ✅ Track if the bot is running
bot_thread = None  # ✅ Track bot thread

# ✅ Set up logging (default to INFO)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ✅ Set up Discord bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Required for reading messages

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    """Triggered when the bot successfully logs in."""
    global bot_running
    bot_running = True  # ✅ Ensure tracking starts when bot is running

    try:
        await bot.tree.sync()  # ✅ Sync commands after bot is fully ready
        print(f"✅ Logged in as {bot.user} | Slash Commands Synced")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

# ✅ Slash Command: /ash
@bot.tree.command(name="ash", description="Talk to Ash")
async def talk_to_ash(interaction: discord.Interaction, message: str):
    """Handles the /ash command, capturing the message for debugging."""
    await interaction.response.defer()  # ✅ Acknowledge command immediately

    user_id = str(interaction.user.id)  # ✅ Get user details
    send_to_chatgpt(message, user_id)   # ✅ Calls main function

    await interaction.followup.send(f"📩 Debugging message: {message} (Logged to debug.txt)", ephemeral=True)

def run_bot():
    """Runs AshBot in a separate thread without blocking the menu."""
    global bot_running
    bot_running = True  # ✅ Mark bot as running

    asyncio.run(bot.start(DISCORD_BOT_TOKEN))  # ✅ Run bot in its own event loop

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
    bot_running = False  # ✅ Ensure bot_running updates globally

    # ✅ Close the bot properly
    asyncio.run(bot.close())

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

        choice = input("Select an option: ").strip().upper()

        if choice == "S" and bot_running:
            stop_ashbot()
        elif choice == "A" and not bot_running:
            print("🚀 Starting AshBot...")
            start_ashbot()
        elif choice == "D" and not bot_running:
            print("👀 Starting AshBot with Watchdog...")
            start_ashbot()
        elif choice == "W":
            weaviate_menu()
        elif choice == "C":
            show_logging_menu()
        elif choice == "X":
            print("👋 Exiting AshBot...")
            break
        else:
            # ✅ If input is NOT a command, assume it's a message to Ash
            print(f"📩 Preparing message to Ash: {choice}")
            send_console_message_to_chatgpt(choice)  # ✅ Calls console-specific function

        time.sleep(1)  # ✅ Small delay for readability

# ✅ Ensure both the bot and menu start correctly
if __name__ == "__main__":
    menu_thread = threading.Thread(target=show_main_menu, daemon=True)
    menu_thread.start()

    run_bot()  # ✅ Start bot in main thread
