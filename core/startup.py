import subprocess
from core.weaviate_manager import (
    is_docker_running,
    start_docker,
    is_weaviate_running,
    is_weaviate_fully_ready,
    initialize_weaviate_data,
    start_weaviate
)

def startup_sequence():
    """Ensures Docker and Weaviate are properly initialized before launching the bot."""
    print("🔄 [Startup] Running startup sequence...")

    # ✅ Step 1: Check Docker
    print("🔍 Checking if Docker is running...")
    if not is_docker_running():
        print("🐳 Docker is not running. Trying to start it...")
        if not start_docker():
            print("❌ Failed to start Docker. Exiting.")
            return False
    print("✅ [Startup] Docker is running.")

    # ✅ Step 2: Check Weaviate
    print("🔍 Checking if Weaviate is running...")
    if is_weaviate_running():
        print("✅ [Startup] Weaviate is running and ready.")
        return True  # Everything is already working!

    print("🛠 [Startup] Weaviate is not running. Attempting to start...")

    # ✅ Step 3: If Weaviate is missing, fully reset it (similar to `reset_memory()`)
    if not start_weaviate():
        print("🗑 Removing any existing Weaviate container before starting fresh...")
        subprocess.run(["docker", "rm", "-f", "weaviate"], capture_output=True, text=True)
        subprocess.run(["docker", "volume", "rm", "ashbot_weaviate_data"], capture_output=True, text=True)

        print("📥 Pulling latest Weaviate image via docker-compose...")
        subprocess.run(["docker-compose", "pull", "weaviate"], capture_output=True, text=True)

        print("🚀 Starting Weaviate stack using docker-compose...")
        result = subprocess.run(["docker-compose", "up", "-d"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ [Startup] Failed to create Weaviate container: {result.stderr}")
            return False

    # ✅ Step 4: Wait for Weaviate to be fully ready
    print("⏳ Waiting for Weaviate to become available...")
    if not is_weaviate_fully_ready():
        print("❌ Weaviate did not start correctly. Check logs.")
        return False

    # ✅ Step 5: Initialize Weaviate schema & insert base data
    print("📜 Initializing schema & inserting base data...")
    if not initialize_weaviate_data():
        print("❌ Failed to initialize Weaviate data.")
        return False

    print("🎉 [Startup] Weaviate is fully initialized and ready!")
    return True

