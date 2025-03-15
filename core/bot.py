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
@bot.event
async def on_ready():
    """Triggered when the bot successfully logs in."""
    try:
        await asyncio.sleep(5)  # ✅ Wait a few seconds to let Discord register the bot
        print("🚀 Clearing and re-syncing commands...")

        # ✅ Clear & Re-sync Commands
        bot.tree.clear_commands(guild=discord.Object(id=GUILD_ID))
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))

        print(f"✅ Logged in as {bot.user} | Commands Re-Synced")

        # ✅ Debugging: Print registered commands
        commands = await bot.tree.fetch_commands(guild=discord.Object(id=GUILD_ID))
        if not commands:
            print("❌ No commands registered!")
        else:
            print(f"📌 Registered commands: {[cmd.name for cmd in commands]}")

    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

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

### 🔮 Slash Command: /ash ###
@bot.tree.command(name="ash", description="Talk to Ash")
async def talk_to_ash(interaction: discord.Interaction, message: str):
    """Handles the /ash command, filtering messages after Ash last spoke."""
    print("🚀 `/ash` command was called!")  # ✅ DEBUG LINE
    await interaction.response.defer()  # ✅ Acknowledge command immediately

    user_id = str(interaction.user.id)
    username = interaction.user.name  
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()

    last_messages = []
    try:
        async for msg in interaction.channel.history(limit=10):  # Grab 10 to filter messages
            last_messages.append(msg)  # ✅ Keep all messages for processing
    except Exception as e:
        print(f"❌ Error retrieving channel history: {e}")

    # ✅ Step 1: Find the last message from Ash
    last_ash_index = None
    for i, msg in enumerate(last_messages):
        if msg.author == bot.user:  # ✅ If Ash sent this message, mark the index
            last_ash_index = i
            break  # ✅ Stop at the most recent Ash message

    # ✅ Step 2: Include only messages that came AFTER Ash last spoke
    filtered_messages = []
    for i, msg in enumerate(last_messages):
        if last_ash_index is not None and i <= last_ash_index:
            continue  # ✅ Skip messages before or by Ash

        if msg.author.bot:
            continue  # ✅ Skip other bot messages (except Ash)

        filtered_messages.append({
            "user_id": str(msg.author.id),
            "message": msg.content,
            "timestamp": msg.created_at.isoformat()
        })

    # ✅ Step 3: If the only messages were from Ash, send an empty history
    if not filtered_messages:
        conversation_context = "No recent conversation available."
    else:
        conversation_context = [
            {
                "user": {"id": msg["user_id"], "name": "Unknown", "pronouns": "they/them"},
                "message": msg["message"],
                "timestamp": msg["timestamp"]
            }
            for msg in filtered_messages
        ]

    # ✅ Step 4: Structure the final message
    structured_message = {
        "user": {"id": user_id, "name": username, "pronouns": "they/them"},
        "user_message": message,
        "timestamp": timestamp,
        "conversation_context": conversation_context
    }

    # ✅ Step 5: Write to debug.txt instead of sending to ChatGPT
    debug_file_path = "data/debug.txt"
    try:
        with open(debug_file_path, "w", encoding="utf-8") as debug_file:
            json.dump(structured_message, debug_file, indent=4, ensure_ascii=False)
        print(f"📝 Debug message written to {debug_file_path}")
    except Exception as e:
        print(f"❌ Error writing debug message: {e}")

    await interaction.followup.send(f"📩 Debugging message: `{message}` (Logged to debug.txt)", ephemeral=True)

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
