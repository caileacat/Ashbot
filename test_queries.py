import sys
import os

# Ensure we can import weaviate_manager
sys.path.append(os.path.abspath(os.path.dirname(__file__)))  # Adjusts path

from core.weaviate_manager import fetch_user_profile, fetch_long_term_memories, fetch_recent_conversations

def test_queries(user_id):
    """Runs all queries and prints results for debugging."""
    print("\n🔍 Testing Queries for User:", user_id)

    # Test User Profile
    user_profile = fetch_user_profile(user_id)
    print("\n🔹 User Profile:", user_profile)

    # Test Long-Term Memories
    long_term_memories = fetch_long_term_memories(user_id)
    print("\n🔹 Long-Term Memories:", long_term_memories)

    # Test Recent Conversations
    recent_conversations = fetch_recent_conversations(user_id)
    print("\n🔹 Recent Conversations:", recent_conversations)

if __name__ == "__main__":
    test_user_id = "851181959933591554"  # Replace with a valid user ID
    test_queries(test_user_id)
