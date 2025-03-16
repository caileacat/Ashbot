import os
import json
import asyncio
import discord
import logging
import datetime
import threading  # ✅ Allows running the bot in a separate thread
import time  # ✅ Needed for adding delay before re-printing the menu
from dotenv import load_dotenv
from discord.ext import commands
from core.logging_manager import show_logging_menu
from core.weaviate_manager import weaviate_menu
from core.startup import initialize_services  # ✅ Run startup checks from the menu

# ✅ Load environment variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))

# ✅ Set up logging (default to INFO)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ✅ Set up Discord bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Required for reading messages
bot = commands.Bot(command_prefix="/", intents=intents)

# ✅ Track bot state
bot_running = False
bot_thread = None

### 🎭 Bot Event: On Ready ###
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

@bot.tree.command(name="ash", description="Talk to Ash")
async def talk_to_ash(interaction: discord.Interaction, message: str):
    """Handles the /ash command, ensuring the response doesn't expire before we reply."""
    print("🚀 `/ash` command was called!")  # ✅ DEBUG LINE

    try:
        # ✅ Immediately respond so the interaction doesn't expire
        await interaction.response.send_message("💨 Brb, hitting the bong... give me a sec. ✨", ephemeral=False)
        
        # ✅ Get user details
        user_id = str(interaction.user.id)
        username = interaction.user.name  
        timestamp = datetime.datetime.now(datetime.UTC).isoformat()

        # ✅ Fetch memory from Weaviate
        from core.weaviate_manager import fetch_user_memory
        user_memory = fetch_user_memory(user_id)

        # ✅ Fetch last five messages in the channel (excluding bots)
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

        # ✅ Replace user IDs with placeholders (Weaviate implementation pending)
        formatted_messages = [
            {
                "user": {
                    "id": msg["user_id"],
                    "name": "Unknown",
                    "pronouns": "they/them"
                },
                "message": msg["message"],
                "timestamp": msg["timestamp"]
            }
            for msg in last_messages
        ]

        # ✅ Structure the message
        structured_message = {
            "user": {
                "id": user_id,
                "name": user_memory["name"] if user_memory else username,
                "pronouns": user_memory["pronouns"] if user_memory else "they/them",
                "role": user_memory["role"] if user_memory else "Unknown",
                "relationship_notes": user_memory["relationship_notes"] if user_memory else "No relationship data",
                "interaction_count": user_memory["interaction_count"] if user_memory else 0
            },
            "user_message": message,
            "timestamp": timestamp,
            "conversation_context": formatted_messages
        }

        # ✅ Write to debug.txt
        debug_file_path = "data/debug.txt"
        with open(debug_file_path, "w", encoding="utf-8") as debug_file:
            json.dump(structured_message, debug_file, indent=4, ensure_ascii=False)
        print(f"📝 Debug message written to {debug_file_path}")

        # ✅ Send Ash's "real" response as a NEW message
        await interaction.channel.send(f"🌿 Back from my sesh! Here's what I got:\n\n📩 `{message}` (Logged to debug.txt)")

    except Exception as e:
        print(f"❌ Error in /ash command: {e}")
        await interaction.channel.send("❌ Oops! My brain is too foggy right now. Try again in a bit.")

### 📝 Console Menu ###
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
