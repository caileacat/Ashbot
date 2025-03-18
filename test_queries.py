import sys
import os

# Ensure we can import weaviate_manager
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.weaviate_manager import (
    fetch_user_profile,
    fetch_long_term_memories,
    fetch_recent_conversations,
    perform_vector_search,  # ✅ New: Vector-based search
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

if __name__ == "__main__":
    test_user_id = input("Enter User ID to test: ") or CAILEA_ID # Allows dynamic input
    test_message = input("Enter a message for vector search (or leave blank): ").strip() or None

    test_queries(test_user_id, test_message)
