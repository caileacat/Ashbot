import sys
import os
import json

# Ensure we can import weaviate_manager
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.weaviate_manager import (
    fetch_user_profile,
    fetch_long_term_memories,
    fetch_recent_conversations,
    perform_vector_search,  # ✅ Vector-based search (for both memories & conversations)
)
from data.constants import CAILEA_ID

def test_queries(user_id, message=None):
    """
    Runs all queries and prints results for debugging.
    If a message is provided, it will also test vector-based search.
    """
    print("\n🔍 Running Query Tests for User:", user_id)

    # ✅ Test User Profile
    user_profile = fetch_user_profile(user_id)
    print("\n🔹 User Profile:", user_profile)

    # ✅ Fix: Convert JSON-encoded memory back to list if necessary
    if isinstance(user_profile.get("memory"), str):
        try:
            user_profile["memory"] = json.loads(user_profile["memory"])
        except json.JSONDecodeError:
            user_profile["memory"] = []

    # ✅ Test Long-Term Memories
    long_term_memories = fetch_long_term_memories(user_id)
    print("\n🔹 Long-Term Memories:", long_term_memories)

    # ✅ Test Recent Conversations
    recent_conversations = fetch_recent_conversations(user_id)
    print("\n🔹 Recent Conversations:", recent_conversations)

    # ✅ Test Vector-Based Search (if a message is provided)
    if message:
        related_conversations = perform_vector_search(message)
        print("\n🔹 Related Conversations (Vector Search):", related_conversations)
