import os
import json
import requests
import datetime
from data.constants import DEBUG_FILE, ASHBRAIN_API_URL
from core.weaviate_manager import (
    fetch_user_profile,
    fetch_long_term_memories,
    fetch_recent_conversations,
    perform_vector_search,
    insert_data
)

# ✅ Query Local LLM

def send_to_ash(structured_message):
    """Sends structured message to AshBrain and receives a reply."""
    from data.constants import ASHBRAIN_API_URL

    try:
        payload = {
            "mode": structured_message.get("mode", "muse"),
            "message": structured_message["message"]["content"]
        }

        response = requests.post(f"{ASHBRAIN_API_URL}/route", json=payload, timeout=10)
        response.raise_for_status()

        return {
            "reply": response.text.strip(),
            "conversation_summary": "",
            "pronouns": structured_message["user"].get("pronouns"),
            "preferred_name": structured_message["user"].get("name"),
            "relationship_notes": structured_message["user"].get("relationship_notes"),
            "ash_memories": [],
            "long_term_memories": []
        }

    except Exception as e:
        return {
            "reply": f"❌ Failed to reach AshBrain: {e}",
            "conversation_summary": "",
            "pronouns": None,
            "preferred_name": None,
            "relationship_notes": None,
            "ash_memories": [],
            "long_term_memories": []
        }

# ✅ Main Data Gatherer

async def gather_data_for_local_llm(user_id, message, channel):
    user_id = str(user_id)
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()
    print(f"🔄 Gathering data for local LLM request from {user_id}...")

    try:
        user_profile = fetch_user_profile(user_id) or {}
        long_term_memories = fetch_long_term_memories(user_id)
        recent_conversations = fetch_recent_conversations(user_id)
        related_memories = perform_vector_search(message)

        last_messages = []
        async for msg in channel.history(limit=10):
            if msg.author.bot and msg.author.id != int(user_id):
                continue
            last_messages.append({
                "user_id": str(msg.author.id),
                "message": msg.content,
                "timestamp": msg.created_at.isoformat()
            })
            if len(last_messages) == 5:
                break

        structured_message = {
            "user": {
                "user_id": user_id,
                "name": user_profile.get("name", "Mooncat"),
                "pronouns": user_profile.get("pronouns", "she/her"),
                "relationship_notes": user_profile.get("relationship_notes", "")
            },
            "memory": {
                "long_term": long_term_memories,
                "recent_interactions": recent_conversations,
                "related": related_memories
            },
            "conversation_history": last_messages,
            "message": {"content": message}
        }

        response = send_to_ash(structured_message)
        write_debug_data(response)
        await process_response(response, channel, user_id, message)
        await process_memory_updates(response, user_id, message)

    except Exception as e:
        print(f"❌ ERROR in gather_data_for_local_llm: {e}")

# ✅ Debug Writer

def write_debug_data(response_data):
    print("📂 Writing Ash's response to debug.txt...")
    try:
        os.makedirs(os.path.dirname(DEBUG_FILE), exist_ok=True)
        with open(DEBUG_FILE, "w", encoding="utf-8") as debug_file:
            json.dump(response_data, debug_file, indent=4, ensure_ascii=False)
        print(f"📝 Debug data successfully written to {DEBUG_FILE}")
    except Exception as e:
        print(f"❌ ERROR writing to debug file: {e}")

# ✅ Response Processor

async def process_response(response, channel, user_id, user_message):
    print("📌 Processing response...")
    if "reply" in response:
        await send_reply_to_channel(response["reply"], channel, user_id, user_message)

async def send_reply_to_channel(reply, channel, user_id, user_message):
    print(f"DEBUG - Raw Reply from Ash: {reply}")
    cleaned_reply = reply.strip()
    if f"**<@{user_id}>:**" in cleaned_reply and "**Ash:**" in cleaned_reply:
        formatted_message = cleaned_reply
    else:
        formatted_message = (
            f"**<@{user_id}>:**\n"
            f"> {user_message}\n\n"
            f"**Ash:**\n"
            f"{cleaned_reply}"
        )
    try:
        await channel.send(formatted_message)
        print("✅ Reply sent to channel!")
    except Exception as e:
        print(f"❌ ERROR sending reply to channel: {e}")

# ✅ Memory Handler (for future compatibility)

async def process_memory_updates(response, user_id, original_message):
    try:
        print("🧠 Checking memory updates...")
        if response.get("ash_memories"):
            for mem in response["ash_memories"]:
                insert_data(mem, class_name="AshMemory", user_id="0")
        if response.get("long_term_memories"):
            for mem in response["long_term_memories"]:
                insert_data(mem, class_name="UserMemory", user_id=user_id)
        if response.get("conversation_summary"):
            insert_data({"text": response["conversation_summary"], "source": "summary", "timestamp": datetime.datetime.now().isoformat()}, class_name="RecentConversation", user_id=user_id)

        print("✅ Memory updates processed.")

    except Exception as e:
        print(f"❌ ERROR during memory update processing: {e}")
