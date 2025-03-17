import subprocess
import time
from alive_progress import alive_bar
from core.weaviate_manager import is_docker_running, start_docker, is_weaviate_running, start_weaviate, create_weaviate_container, initialize_weaviate_data  # ✅ Use centralized Weaviate functions

DOCKER_EXE_PATH = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"

def initialize_services():
    """Ensures Docker and Weaviate are running properly before starting the bot."""
    
    # Step 1: Ensure Docker is running
    if not is_docker_running():
        print("❌ Docker is not running. Attempting to start it...")
        if not start_docker():
            print("🚨 Failed to start Docker! Exiting...")
            return False

    # Step 2: Check Weaviate status
    if is_weaviate_running():
        print("✅ Weaviate is already running.")
        return True

    print("🧠 Weaviate is NOT running. Checking if a container exists...")

    # Step 3: See if a container exists but is stopped
    existing_containers = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True, text=True
    ).stdout.split()

    if "weaviate" in existing_containers:
        print("🔄 Weaviate container found but stopped. Restarting...")
        if start_weaviate():
            print("✅ Weaviate restarted successfully!")
            return True
        else:
            print("❌ Failed to start existing Weaviate container.")
            return False

    # Step 4: If no container exists, create and initialize a new one
    print("🚀 No existing Weaviate container found. Creating a new one...")
    if not create_weaviate_container():
        print("❌ Failed to create Weaviate container.")
        return False

    # Step 5: Initialize schema and base data
    print("📜 Initializing Weaviate schema and base data...")
    if not initialize_weaviate_data():
        print("❌ Weaviate schema/data initialization failed!")
        return False

    print("✅ Weaviate is fully set up and ready!")
    return True

if __name__ == "__main__":
    initialize_services()
