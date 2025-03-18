import os
import json
import datetime
from data.constants import DEBUG_FILE
from core.weaviate_manager import fetch_user_profile, fetch_long_term_memories, fetch_recent_conversations, fetch_recent_conversations, perform_vector_search, perform_vector_search

async def gather_data_for_chatgpt(user_id, message, channel):
    """Collects and formats data for ChatGPT based on user input."""

    user_id = str(user_id)  # ✅ Ensure user_id is a string
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()
    print(f"🔄 Gathering data for ChatGPT request from {user_id}...")

    try:
        # ✅ Step 1: Fetch User Profile
        print("🔍 Fetching user profile...")
        user_profile = fetch_user_profile(user_id) or {}
        print(f"✅ User profile retrieved: {user_profile}")

        # ✅ Step 2: Fetch Long-Term Memories
        print("🔍 Fetching long-term memories...")
        long_term_memories = fetch_long_term_memories(user_id)
        print(f"✅ Long-term memories retrieved: {long_term_memories}")

        # ✅ Step 3: Fetch Recent Conversations
        print("🔍 Fetching recent conversations...")
        recent_conversations = fetch_recent_conversations(user_id)
        print(f"✅ Recent conversations retrieved: {recent_conversations}")

        # ✅ Step 4: Fetch Last 5 Messages (excluding AshBot)
        print("🔍 Fetching last 5 messages from channel...")
        last_messages = []
        async for msg in channel.history(limit=10):
            if msg.author.bot and msg.author.id != int(user_id):  # Ignore bots EXCEPT AshBot
                continue
            last_messages.append({
                "user_id": str(msg.author.id),
                "message": msg.content,
                "timestamp": msg.created_at.isoformat()
            })
            if len(last_messages) == 5:
                break  
        print(f"✅ Last messages collected: {last_messages}")

        # ✅ Step 5: Perform Vector-Based Search for Related Conversations
        print("🔍 Performing vector search for related conversations...")
        related_memories = perform_vector_search(message, user_id)
        print(f"✅ Vector search results: {related_memories}")

        # ✅ Step 6: Structure the Message Object
        print("🔍 Structuring message...")
        structured_message = {
            "user": {
                "id": user_id,
                "name": user_profile.get("name", f"User-{user_id}"),
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
            "related_conversations": related_memories,
        }

        print("✅ Message structured successfully!")
        
        # ✅ Send the message to `send_to_ash()`
        print("📨 Sending structured message to `send_to_ash()`...")
        send_to_ash(structured_message, user_id)
        print("✅ Message successfully processed!")

    except Exception as e:
        print(f"❌ ERROR in gather_data_for_chatgpt: {e}")

def send_console_message_to_chatgpt(message):
    """
    Handles messages typed directly in the console.
    Assumes it's from Cailea and fills in missing details.
    """
    user_id = "851181959933591554"  # ✅ Cailea's User ID
    send_to_ash(message, user_id)  # ✅ Pass it to the main function

def send_to_ash(structured_message, user_id):
    """
    Saves structured message to debug.txt (for now). 
    Later, will send to ChatGPT.
    """
    print("📂 Attempting to write structured message to debug.txt...")
    
    try:
        os.makedirs(os.path.dirname(DEBUG_FILE), exist_ok=True)
        
        # ✅ Clear file before writing (ensures old data is removed)
        with open(DEBUG_FILE, "w", encoding="utf-8") as debug_file:
            json.dump(structured_message, debug_file, indent=4, ensure_ascii=False, default=str)
        
        print(f"📝 Debug data successfully written to {DEBUG_FILE}")
    
    except Exception as e:
        print(f"❌ ERROR writing to debug file: {e}")

