import json
import datetime

DEBUG_FILE = "data/debug.txt"  # ✅ Save debug output here

def send_console_message_to_chatgpt(message):
    """
    Handles messages typed directly in the console.
    Assumes it's from Cailea and fills in missing details.
    """
    user_id = "851181959933591554"  # ✅ Cailea's User ID
    send_to_chatgpt(message, user_id)  # ✅ Pass it to the main function

def send_to_chatgpt(message, user_id):
    """
    Handles formatting and logging messages intended for ChatGPT.
    Used for both Discord and Console messages.
    """
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()

    debug_data = {
        "user_message": {
            "content": message,
            "user_id": user_id,
            "timestamp": timestamp
        }
    }

    # ✅ Debug output to file
    try:
        with open(DEBUG_FILE, "w", encoding="utf-8") as debug_file:
            json.dump(debug_data, debug_file, indent=4, ensure_ascii=False)
        print(f"📝 Debug message written to {DEBUG_FILE}")
    except Exception as e:
        print(f"❌ Error writing debug message: {e}")
