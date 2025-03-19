import os
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# 🔹 Secrets
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
OPENAI_APIKEY = os.getenv("OPENAI_APIKEY", "")
ASSISTANT_ID = os.getenv("ASSISTANT_ID", "")
GUILD_ID = int(os.getenv("GUILD_ID", 0))
ASH_BOT_ID = int(os.getenv("ASH_BOT_ID", 0))
CAILEA_ID = int(os.getenv("CAILEA_ID", 0))
LEMON_ID = int(os.getenv("LEMON_ID", 0))
COMMUNITY_SUPPORT_ID = int(os.getenv("COMMUNITY_SUPPORT_ID", 0))

# 🔹 Debugging
DEBUG_FILE = "data/debug.txt"  # ✅ Temporarily logging here before ChatGPT

# 🔹 Weaviate Configuration
WEAVIATE_URL = "http://localhost:8080"
DOCKER_CONTAINER_NAME = "weaviate"
DOCKER_IMAGE = "semitechnologies/weaviate"
DOCKER_PORT = 8080
GRPC_PORT = 50051
