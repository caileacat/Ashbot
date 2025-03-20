import subprocess
import logging
from core.weaviate_manager import (
    is_docker_running,
    is_weaviate_running,
    is_weaviate_fully_ready,
)

def startup_sequence():
    """Checks if Docker and Weaviate are running and reports their status to the console."""
    print("🔄 [Startup] Running startup sequence...")

    # ✅ Step 1: Check if Docker is running
    print("🔍 Checking if Docker is running...")
    if is_docker_running():
        print("✅ [Startup] Docker is running.")
    else:
        print("⚠️ [Warning] Docker is NOT running. Weaviate will not work!")

    # ✅ Step 2: Check if Weaviate exists
    print("🔍 Checking if Weaviate container exists...")
    weaviate_containers = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True, text=True
    ).stdout.split("\n")

    if "weaviate" in weaviate_containers:
        print("✅ Weaviate container exists.")
    else:
        print("⚠️ [Warning] Weaviate container is MISSING. Run RESET to recreate it!")

    # ✅ Step 3: Check if Weaviate is running
    print("🔍 Checking if Weaviate is running...")
    if is_weaviate_running():
        print("✅ Weaviate is running.")
    else:
        print("⚠️ [Warning] Weaviate is NOT running.")

    # ✅ Step 4: Check if Weaviate is fully ready
    print("⏳ Checking Weaviate readiness...")
    if is_weaviate_fully_ready():
        print("✅ Weaviate is fully ready.")
    else:
        print("⚠️ [Warning] Weaviate is NOT fully ready. Schema or data might be missing.")

    print("🎉 [Startup] Status check complete. Use RESET if Weaviate is missing or broken.")
    
    import logging    
    
    # ✅ Set up logging
    logging.basicConfig(level=logging.WARNING)
