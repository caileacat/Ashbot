import discord
import os
import logging
import threading  # ✅ Allows running the bot in a separate thread
import time  # ✅ Needed for adding delay before re-printing the menu
from dotenv import load_dotenv
from discord.ext import commands
from core.logging_manager import show_logging_menu
from core.weaviate_manager import weaviate_menu
from core.startup import initialize_services  # ✅ Run startup checks from the menu

# Load environment variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Set up logging (default to INFO)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Set up Discord bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Required for reading messages

bot = commands.Bot(command_prefix="/", intents=intents)
bot_running = False  # Track if the bot is running
bot_thread = None  # Track the bot thread

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

def show_main_menu():
    """Displays the main menu for AshBot, with a delay before re-printing."""
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
            stop_ashbot()  # Ensure bot stops when exiting
            break
        else:
            print("❌ Invalid selection. Please choose a valid option.")

@bot.event
async def on_ready():
    """Triggered when the bot successfully logs in."""
    print(f"✅ Logged in as {bot.user}")

if __name__ == "__main__":
    show_main_menu()