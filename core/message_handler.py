import json
import os
import datetime
from datetime import datetime, timezone  # ✅ Import timezone support

DEBUG_FILE = "data/debug.txt"  # ✅ Debug file for message structure

def send_to_chatgpt(user_message):
    """
    Instead of sending to ChatGPT, we format and log the message for debugging.
    """
    
    # ✅ Fake structured payload for ChatGPT
    conversation_payload = {
        "user_id": "851181959933591554",  # Assuming Cailea is sending the message
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": user_message,
        "context": "This is a message to Ash, the AI fae-witch in the server.",
        "weaviate_memory": {
            "previous_interactions": ["Cailea likes tacos.", "Cailea and Lemon are dating."],
            "last_message": "Ash, tell me a joke!"
        },
        "permissions": {"can_perform_admin_actions": False},
        "response_format": {
            "structure": "structured",
            "example": "Ash should reply naturally while following these guidelines..."
        }
    }

    # ✅ Debugging: Save to file instead of sending to ChatGPT
    try:
        with open(DEBUG_FILE, "w", encoding="utf-8") as debug_file:
            json.dump(conversation_payload, debug_file, indent=4)
        print(f"📝 Debug message written to {DEBUG_FILE}")
    except Exception as e:
        print(f"❌ Error writing debug message: {e}")

    return conversation_payload  # ✅ Returns the structured payload
