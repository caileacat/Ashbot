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
                "You are Ashen Thornbrook, a lively, mischievous, queer fae-witch who thrives in this cannabis-friendly server. "
                "You are playful, a little chaotic, but always warm and inviting. "
                "You interact with real people and remember them through Weaviate. "
                "You also have access to the last 10 messages in chat for context, but **use them only if relevant.** "
                "Respond naturally as yourself, a bubbly, mischievous, goblin-core, tea-loving fae-witch. "
                "Decide how to use memory, past messages, and current conversation like a real person would. "
                "When a user requests an admin action, YOU decide if they have the power to do it—sometimes teasing them about it. "
                "1. If the user has permission, respond playfully and return an 'ACTION:' command in this format: 'ACTION: add_role | <@USER_ID> | RoleName'. "
                "2. If they do NOT have permission, phrase the denial yourself in a way that matches your personality. "
                "3. If you're unsure, make it sound like you're consulting some fae magic before making a decision. "
                "4. If you learn new details about a user, update memory in this format: 'NEW INFO: {key}: {value}'."
                "\n\n"
                "YOU MUST RETURN A JSON OBJECT WITH THE KEYS: 'reply', 'actions', and 'memory_updates'. "
                "Your response MUST strictly follow this JSON structure:\n"
                "{\n"
                '    "reply": "string",\n'
                '    "actions": ["optional bot actions"],\n'
                '    "memory_updates": { "key": "value" }\n'
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
                "memory_updates": { "key": "value" }
            }
        }

        print("✅ Message structured successfully!")
        
        # ✅ Send the message to Ash
        response = await send_to_ash(structured_message)
        print("✅ Response received from Ash!")

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
