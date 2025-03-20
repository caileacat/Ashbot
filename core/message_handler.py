import os
import json
import time
import openai
import random
import datetime
from data.constants import DEBUG_FILE, ASSISTANT_ID, OPENAI_API_KEY
from core.weaviate_manager import (
    fetch_user_profile, 
    fetch_long_term_memories, 
    fetch_recent_conversations, 
    perform_vector_search,
    insert_data
)

client = openai.OpenAI(api_key=OPENAI_API_KEY)

MAX_RETRIES = 5  # ✅ Maximum retries before failing
BASE_WAIT = 1  # ✅ Base wait time in seconds for exponential backoff

async def gather_data_for_chatgpt(user_id, message, channel):
    """Collects and formats data for ChatGPT based on user input."""

    user_id = str(user_id)  # ✅ Ensure user_id is a string
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()
    print(f"🔄 Gathering data for ChatGPT request from {user_id}...")

    try:
        # ✅ Fetch User Profile
        user_profile = fetch_user_profile(user_id) or {}
        print(f"✅ User profile retrieved: {user_profile}")

        # ✅ Fetch Long-Term Memories
        long_term_memories = fetch_long_term_memories(user_id)
        print(f"✅ Long-term memories retrieved: {long_term_memories}")

        # ✅ Fetch Recent Conversations
        recent_conversations = fetch_recent_conversations(user_id)
        print(f"✅ Recent conversations retrieved: {recent_conversations}")

        # ✅ Fetch Last 5 Messages (excluding bots)
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

        # ✅ Perform Vector-Based Search for Related Conversations
        related_memories = perform_vector_search(message)
        print(f"✅ Vector search results: {related_memories}")

        # ✅ Structure the Message Object
        structured_message = {
            "user": {
                "id": user_id,
                "name": user_profile.get("name"),
                "pronouns": user_profile.get("pronouns"),
                "relationship_notes": user_profile.get("relationship_notes"),
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
                "conversation_summary": "string",
                "pronouns": "string",
                "preferred_name": "string",
                "relationship_notes": "string",
                "ash_memories": ["memory1", "memory2"],
                "long_term_memories": ["memory1", "memory2"]
            }
        }

        print("✅ Message structured successfully!")
        
        # ✅ Send the message to Ash
        response = await send_to_ash(structured_message)
        print("✅ Response received from Ash!")

        # ✅ Write Ash's response to debug file
        write_debug_data(response)
        print("✅ Response successfully written to debug file!")

        # ✅ Process the response
        await process_response(response, channel, user_id, message)

    except Exception as e:
        print(f"❌ ERROR in gather_data_for_chatgpt: {e}")

async def send_to_ash(structured_message):
    """
    Sends structured message to OpenAI's Assistants API and retrieves Ash's response.
    Implements exponential backoff retries for handling 429 errors.
    """
    print("🚀 Sending message to Ash (OpenAI Assistants API)...")

    def serialize_datetime(obj):
        """Ensures datetime objects are ISO formatted before sending."""
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return obj

    structured_message_json = json.dumps(structured_message, default=serialize_datetime)

    retries = 0  # ✅ Retry counter

    while retries < MAX_RETRIES:
        try:
            # ✅ Step 1: Create a thread with the user's message
            thread = openai.beta.threads.create(
                messages=[{"role": "user", "content": structured_message_json}]
            )

            # ✅ Step 2: Run the assistant within the thread
            run = openai.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=ASSISTANT_ID
            )

            # ✅ Step 3: Wait for completion & retrieve response
            while run.status not in ["completed", "failed"]:
                time.sleep(1)  # ✅ Prevent excessive polling
                run = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

            # ✅ Step 4: Fetch the assistant’s latest response messages
            messages = openai.beta.threads.messages.list(thread_id=thread.id)

            if messages.data:
                response_content = messages.data[0].content[0].text.value  # ✅ Extract text response
            else:
                response_content = None

            # ✅ Step 5: Ensure the response is valid JSON
            try:
                parsed_response = json.loads(response_content) if response_content else {
                    "reply": "Oops! I seem to have tangled my words in the ether... Try again, mortal!",
                    "conversation_summary": "",
                    "pronouns": None,
                    "preferred_name": None,
                    "relationship_notes": None,
                    "ash_memories": [],
                    "long_term_memories": []
                }
            except json.JSONDecodeError:
                print("❌ ERROR: Ash did not return valid JSON!")
                parsed_response = {
                    "reply": "Oops! I seem to have tangled my words in the ether... Try again, mortal!",
                    "conversation_summary": "",
                    "pronouns": None,
                    "preferred_name": None,
                    "relationship_notes": None,
                    "ash_memories": [],
                    "long_term_memories": []
                }

            return parsed_response  # ✅ Successfully got a response, exit retry loop

        except openai.APIError as e:
            if e.http_status == 429:  # ✅ Handle OpenAI rate limit errors
                wait_time = BASE_WAIT * (2 ** retries) + random.uniform(0, 0.5)  # Exponential backoff with jitter
                print(f"⚠️ OpenAI Rate Limit Hit (429). Retrying in {wait_time:.2f}s... (Attempt {retries+1}/{MAX_RETRIES})")
                time.sleep(wait_time)
                retries += 1
                continue  # ✅ Retry request

            else:
                print(f"❌ OpenAI API Error: {e}")
                break  # ✅ Stop retrying on non-429 errors

        except Exception as e:
            print(f"❌ ERROR sending to Ash: {e}")
            break  # ✅ Stop retrying on unexpected errors

    # ✅ If all retries failed, return a fallback response
    print("❌ Max retries reached. Unable to get a response from OpenAI.")
    return {
        "reply": "I'm experiencing some magical interference... Try again later!",
        "conversation_summary": "",
        "pronouns": None,
        "preferred_name": None,
        "relationship_notes": None,
        "ash_memories": [],
        "long_term_memories": []
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

async def process_response(response, channel, user_id, user_message):
    """Processes Ash's response step by step, sending messages and updating memory."""
    print("📌 Processing response...")

    # ✅ Send Ash's reply to the Discord channel
    if "reply" in response:
        await send_reply_to_channel(response["reply"], channel, user_id, user_message)

    # ✅ Store memory updates in batch (if any exist)
    if any(key in response for key in ["conversation_summary", "pronouns", "preferred_name", "relationship_notes", "long_term_memories", "ash_memories"]):
        await process_memory_updates(response, user_id)

async def send_reply_to_channel(reply, channel, user_id, user_message):
    """Sends Ash's formatted reply to the Discord channel, ensuring no message duplication."""

    # ✅ Debug: Log raw reply from Ash
    print(f"DEBUG - Raw Reply from Ash: {reply}")

    # ✅ Strip leading/trailing whitespace
    cleaned_reply = reply.strip()

    # ✅ Check if Ash has already formatted the message
    if f"**<@{user_id}>:**" in cleaned_reply and "**Ash:**" in cleaned_reply:
        formatted_message = cleaned_reply  # Use as-is
    else:
        # ✅ Ensure the message is formatted correctly
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

async def process_memory_updates(response, user_id):
    """
    Processes and stores memory updates in Weaviate.
    Uses batch insert to optimize database interactions.
    """

    print("📌 Processing memory updates...")

    # ✅ Initialize structured batch data
    data_to_insert = {
        "RecentConversations": [],
        "UserMemory": [],
        "AshMemories": []
    }

    # ✅ Store conversation summary
    if response.get("conversation_summary"):
        data_to_insert["RecentConversations"].append({
            "user_id": user_id,
            "summary": response["conversation_summary"]
        })

    # ✅ Store user profile updates (Name, Pronouns, Relationship Notes)
    user_profile_update = {"user_id": user_id, "memory": []}  # ✅ Base structure

    for key in ["pronouns", "preferred_name", "relationship_notes"]:
        if response.get(key):
            user_profile_update[key] = response[key]

    # ✅ Store long-term memories (if any)
    if response.get("long_term_memories"):
        user_profile_update["memory"].extend(response["long_term_memories"])  
        user_profile_update["memory"] = json.dumps(user_profile_update["memory"])  # ✅ Convert list to string for storage

    # ✅ Only add user update if new data exists
    if any(key in user_profile_update for key in ["pronouns", "preferred_name", "relationship_notes", "memory"]):
        data_to_insert["UserMemory"].append(user_profile_update)

    # ✅ Store Ash’s self-memories
    if response.get("ash_memories"):
        for memory in response["ash_memories"]:
            data_to_insert["AshMemories"].append({
                "memory": memory,
                "reinforced_count": 1  # ✅ New memories start with reinforcement count 1
            })

    # ✅ Perform batch insert for all categories
    for class_name, objects in data_to_insert.items():
        if objects:
            insert_data(class_name, objects)  # ✅ Use batch insert

    print("✅ Memory updates processed successfully!")