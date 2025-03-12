import discord
import os
import logging
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

def start_ashbot():
    """Starts AshBot and sets online status."""
    global bot_running
    if bot_running:
        print("⚠️ AshBot is already running.")
        return
    
    print("🚀 Starting AshBot...")
    bot_running = True
    bot.run(DISCORD_BOT_TOKEN)  # Blocking call, bot stays running

def stop_ashbot():
    """Stops AshBot and sets offline status."""
    global bot_running
    if not bot_running:
        print("⚠️ AshBot is already stopped.")
        return

    print("🛑 Stopping AshBot...")
    bot_running = False
    os._exit(0)  # Hard exit to ensure bot stops

def show_main_menu():
    """Displays the main menu for AshBot."""
    
    # ✅ Run startup checks inside the menu
    startup_successful = initialize_services()
    if not startup_successful:
        print("❌ Startup failed. Exiting...")
        return

    while True:
        print("\n=== AshBot Menu ===")
        if (ASHBOT_IS_RUNNING) print("[S] Stop AshBot")  # ✅ Stop option at the top
        if (not ASHBOT_IS_RUNNING) print("[A] Start AshBot")
        if (not ASHBOT_IS_RUNNING) print("[D] Start AshBot with Watchdog")
        print("[W] Manage Weaviate")
        print("[C] Configure Logging")
        print("[X] Exit AshBot")

        choice = input("Select an option: ").strip().upper()

        if choice == "S" and ASHBOT_IS_RUNNING:
            stop_ashbot()
        elif choice == "A" and not(ASHBOT_IS_RUNNING):
            print("🚀 Starting/Stopping AshBot...")
            start_ashbot()
        elif choice == "D" and not(ASHBOT_IS_RUNNING):
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
            print("❌ Invalid selection. Please choose a valid option.")

@bot.event
async def on_ready():
    """Triggered when the bot successfully logs in."""
    print(f"✅ Logged in as {bot.user}")

if __name__ == "__main__":
    show_main_menu()
