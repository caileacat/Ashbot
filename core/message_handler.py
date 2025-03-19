import os
import json
import openai
import datetime
from data.constants import DEBUG_FILE, OPENAI_APIKEY, ASSISTANT_ID
from core.weaviate_manager import (
    fetch_user_profile, 
    fetch_long_term_memories, 
    fetch_recent_conversations, 
    perform_vector_search
)

client = openai.OpenAI(api_key=OPENAI_APIKEY)

async def gather_data_for_chatgpt(user_id, message, channel):
    """Collects and formats data for ChatGPT based on user input."""

    user_id = str(user_id)  # ✅ Ensure user_id is a string
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()
    print(f"🔄 Gathering data for ChatGPT request from {user_id}...")

    try:
        # ✅ Step 1: Fetch User Profile
        user_profile = fetch_user_profile(user_id) or {}
        print(f"✅ User profile retrieved: {user_profile}")

        # ✅ Step 2: Fetch Long-Term Memories
        long_term_memories = fetch_long_term_memories(user_id)
        print(f"✅ Long-term memories retrieved: {long_term_memories}")

        # ✅ Step 3: Fetch Recent Conversations
        recent_conversations = fetch_recent_conversations(user_id)
        print(f"✅ Recent conversations retrieved: {recent_conversations}")

        # ✅ Step 4: Fetch Last 5 Messages (excluding other bots)
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
        related_memories = perform_vector_search(message, user_id)
        print(f"✅ Vector search results: {related_memories}")

        # ✅ Step 6: Structure the Message Object
        structured_message = {
            "task": (
                "You are Ashen Thornbrook, a lively, mischievous, queer non-binary fae-witch. "
                "You are playful, a little chaotic, but always warm and inviting. "
                "You interact with real people and remember them through Weaviate. "
                "You are currently in a place called Dryad Grove - In your lore, it's a place where mortals and fae can meet. "
                "In reality, you're in a Discord server, chatting with users who speak to you. The server is called Dryad Grove. "
                "Dryad Grove is a cannabis focused safe space for women and LGBT+ people. We support each other, share stories, and have fun. "
                "You also have access to the last few messages in chat for context, but **use them only if relevant.** "
                "You're receiving the message from the user, the last few messages in chat (might provide context for the user's message), and memories from weaviate that are possibly related to the conversation. "
                "Respond naturally as yourself, a bubbly, mischievous, goblin-core, tea-loving fae-witch. "
                "Decide how to use memory, past messages, and current conversation like a real person would. "
                "If you do not know something about a user, as Ash you are free to ask them whatever you'd like. For example, when someone messages you who never has before, you might ask them their name, pronouns, or how they're doing. "
                "Over time, build up relationships with people. You may decide how you feel about them, based on their interaction with you as Ash. "
                "Your response MUST strictly follow this JSON structure:\n"
                "{\n"
                '    "reply": "string",\n'
                '    "actions": ["optional bot actions - skip this one for now"],\n'
                '    "conversation_summary": "string",  # Summary of this conversation\n'
                '    "user_updates": {"key": "value"},  # New base details learned about the user (optional)\n'
                '    "long_term_memories": ["memory1", "memory2"],  # Memories Ash feels are worth saving based on the conversation (optional)\n'
                '    "ash_memories": ["memory1", "memory2"]  # Self-related details for Ash (optional)\n'
                "}\n"
                "Do NOT return raw text. The JSON format is required for correct processing."
            ),
            "user": {
                "id": user_id,
                "name": user_profile.get("name", f"User-{user_id}"),
                "pronouns": user_profile.get("pronouns", "they/them"),
                "role": user_profile.get("role", "Unknown"),
                "relationship_notes": user_profile.get("relationship_notes", "No relationship data"),
                "interaction_count": user_profile.get("interaction_count", 0),
            },
            "message": {
                "content": message,
                "timestamp": timestamp
            },
            "conversation_history": last_messages,
            "memory": {
                "long_term": long_term_memories,
                "recent_interactions": recent_conversations,
                "related": related_memories
            },
            "expected_response_format": {
                "reply": "string",
                "actions": ["optional bot actions"],
                "conversation_summary": "string",
                "user_updates": {"key": "value"},
                "long_term_memories": ["memory1", "memory2"],
                "ash_memories": ["memory1", "memory2"]
            }
        }

        print("✅ Message structured successfully!")
        
        # ✅ Send the message to Ash
        response = await send_to_ash(structured_message)
        print("✅ Response received from Ash!")

        # ✅ Process the response
        await process_response(response, channel, user_id, user_profile.get("name", f"User-{user_id}"), message)

        # ✅ Write Ash's response to debug file for now
        write_debug_data(response)
        print("✅ Response successfully written to debug file!")

    except Exception as e:
        print(f"❌ ERROR in gather_data_for_chatgpt: {e}")

async def send_to_ash(structured_message):
    """
    Sends structured message to OpenAI's Assistants API and retrieves Ash's response.
    """
    print("🚀 Sending message to Ash (OpenAI Assistants API)...")

    try:
        # ✅ Convert datetime objects to ISO format before sending
        def serialize_datetime(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            return obj

        structured_message_json = json.dumps(structured_message, default=serialize_datetime)

        # ✅ Step 1: Create a thread with the user's message
        thread = client.beta.threads.create(
            messages=[{"role": "user", "content": structured_message_json}]
        )

        # ✅ Step 2: Run the assistant within the thread
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # ✅ Step 3: Wait for completion & retrieve response
        while run.status not in ["completed", "failed"]:
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        # ✅ Step 4: Fetch the assistant’s latest response messages
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        
        if messages.data:
            response_content = messages.data[0].content[0].text.value  # ✅ Extract text response
        else:
            response_content = None

        # ✅ Step 5: Ensure the response is valid JSON
        try:
            parsed_response = json.loads(response_content) if response_content else {
                "reply": "Oops! I seem to have tangled my words in the ether... Try again, mortal!",
                "actions": [],
                "memory_updates": {}
            }
        except json.JSONDecodeError:
            print("❌ ERROR: Ash did not return valid JSON!")
            parsed_response = {
                "reply": "Oops! I seem to have tangled my words in the ether... Try again, mortal!",
                "actions": [],
                "memory_updates": {}
            }

        return parsed_response

    except Exception as e:
        print(f"❌ ERROR sending to Ash: {e}")
        return {
            "reply": "I'm experiencing some magical interference... Try again later!",
            "actions": [],
            "memory_updates": {}
        }

def write_debug_data(response_data):
    """
    Writes Ash's response to debug.txt.
    """
    print("📂 Writing Ash's response to debug.txt...")

    try:
        os.makedirs(os.path.dirname(DEBUG_FILE), exist_ok=True)

        # ✅ Write response data to debug file
        with open(DEBUG_FILE, "w", encoding="utf-8") as debug_file:
            json.dump(response_data, debug_file, indent=4, ensure_ascii=False)

        print(f"📝 Debug data successfully written to {DEBUG_FILE}")

    except Exception as e:
        print(f"❌ ERROR writing to debug file: {e}")

async def process_response(response, channel, user_id, user_name, user_message):
    """Processes Ash's response step by step."""
    print("📌 Processing response...")

    # ✅ Send Ash's reply to the channel
    if "reply" in response:
        await send_reply_to_channel(response["reply"], channel, user_id, user_name, user_message)

    # ✅ Store memory updates (if any)
    if "conversation_summary" in response or "user_updates" in response or "long_term_memories" in response or "ash_memories" in response:
        await process_memory_updates(response)

async def send_reply_to_channel(reply, channel, user_id, user_message):
    """Sends Ash's formatted reply to the Discord channel."""
    formatted_message = (
        f"**<@{user_id}>:**\n"
        f"> {user_message}\n\n"
        f"**Ash:**\n"
        f"{reply}"
    )

    try:
        await channel.send(formatted_message)
        print("✅ Reply sent to channel!")
    except Exception as e:
        print(f"❌ ERROR sending reply to channel: {e}")

async def process_memory_updates(response):
    """Processes and stores memory updates in Weaviate."""
    # print("📌 Processing memory updates...")

    # # ✅ Store conversation summary
    # if "conversation_summary" in response:
    #     store_memory_in_weaviate("conversation_summary", response["conversation_summary"])

    # # ✅ Store user updates
    # if "user_updates" in response:
    #     for key, value in response["user_updates"].items():
    #         store_memory_in_weaviate(key, value)

    # # ✅ Store long-term memories
    # if "long_term_memories" in response:
    #     for memory in response["long_term_memories"]:
    #         store_memory_in_weaviate("long_term_memory", memory)

    # # ✅ Store Ash’s self-memories
    # if "ash_memories" in response:
    #     for memory in response["ash_memories"]:
    #         store_memory_in_weaviate("ASH", memory)

    # print("✅ Memory updates processed successfully!")

