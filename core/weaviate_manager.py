import weaviate
import subprocess
import time
import requests

WEAVIATE_URL = "http://localhost:8080"
DOCKER_CONTAINER_NAME = "weaviate"
DOCKER_IMAGE = "semitechnologies/weaviate"
DOCKER_PORT = 8080
GRPC_PORT = 50051

def is_weaviate_running():
    """Checks if Weaviate is running."""
    try:
        response = requests.get(f"{WEAVIATE_URL}/v1/meta", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def stop_weaviate():
    """Stops the Weaviate container."""
    if not is_weaviate_running():
        print("⚠️ Weaviate is already stopped.")
        return True
    
    print("🛑 Stopping Weaviate...")
    try:
        subprocess.run(["docker", "stop", DOCKER_CONTAINER_NAME], check=True)
        return not is_weaviate_running()
    except Exception as e:
        print(f"❌ Error stopping Weaviate: {e}")
        return False
    
def start_weaviate():
    """Starts Weaviate if it's not running, or starts the existing container."""
    if is_weaviate_running():
        print("✅ Weaviate is already running.")
        return True

    # Check if a Weaviate container exists
    existing_containers = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True, text=True
    ).stdout.split()

    if DOCKER_CONTAINER_NAME in existing_containers:
        print("🧠 Weaviate container exists but is stopped. Restarting it...")
        try:
            subprocess.run(["docker", "start", DOCKER_CONTAINER_NAME], check=True)
            time.sleep(5)
            return is_weaviate_running()
        except Exception as e:
            print(f"❌ Error starting existing Weaviate container: {e}")
            return False

    # If there's an existing container but it's broken, remove it
    print("🛑 Removing conflicting Weaviate container...")
    try:
        subprocess.run(["docker", "rm", DOCKER_CONTAINER_NAME], check=True)
    except Exception as e:
        print(f"❌ Error removing existing container: {e}")
        return False

    # Create a new container if none exists
    print("🚀 Creating a new Weaviate container...")
    try:
        subprocess.run([
            "docker", "run", "-d", "--restart=always",
            "--name", DOCKER_CONTAINER_NAME,
            "-p", f"{DOCKER_PORT}:8080",
            "-p", f"{GRPC_PORT}:50051",
            DOCKER_IMAGE
        ], check=True)
        time.sleep(5)
        return is_weaviate_running()
    except Exception as e:
        print(f"❌ Error creating new Weaviate container: {e}")
        return False

def restart_weaviate():
    """Restarts Weaviate by stopping and starting the existing container."""
    if not is_weaviate_running():
        print("⚠️ Cannot restart Weaviate because it's not running. Starting it instead.")
        return start_weaviate()

    print("🔄 Restarting Weaviate...")
    try:
        subprocess.run(["docker", "restart", DOCKER_CONTAINER_NAME], check=True)
        time.sleep(5)
        return is_weaviate_running()
    except Exception as e:
        print(f"❌ Error restarting Weaviate: {e}")
        return False

def reset_memory():
    """Resets Weaviate memory by deleting all data. Only available when Weaviate is OFF."""
    if is_weaviate_running():
        print("⚠️ Cannot reset memory while Weaviate is running. Stop Weaviate first.")
        return False
    
    confirmation = input("To confirm removal of all of Ash's memories, type: KILL ASH\n> ")
    if confirmation != "KILL ASH":
        print("❌ Memory reset aborted. Incorrect confirmation input.")
        return False
    
    print("⚠️ Resetting ALL Weaviate memory...")
    try:
        client = weaviate.WeaviateClient(WEAVIATE_URL)
        client.collections.delete("UserMemory")
        print("✅ Memory reset successfully.")
        return True
    except Exception as e:
        print(f"❌ Error resetting memory: {e}")
        return False

def weaviate_menu():
    """Displays the Weaviate Management Menu with only valid options."""
    while True:
        status_emoji = "🟢" if is_weaviate_running() else "🔴"
        print(f"\n=== {status_emoji} Weaviate Management Menu {status_emoji} ===")
        if is_weaviate_running():
            print("[S] Stop Weaviate")
            print("[R] Restart Weaviate")
        else:
            print("[W] Start Weaviate")
            print("[RESET] Reset ALL Memory to default")
        print("[X] Back")

        choice = input("Select an option: ").strip().upper()

        if choice == "W" and not is_weaviate_running():
            start_weaviate()
        elif choice == "S" and is_weaviate_running():
            stop_weaviate()
        elif choice == "R" and is_weaviate_running():
            restart_weaviate()
        elif choice == "RESET" and not is_weaviate_running():
            reset_memory()
        elif choice == "X":
            print("🔙 Returning to Main Menu...")
            break
        else:
            print("❌ Invalid selection. Please choose a valid option.")

if __name__ == "__main__":
    weaviate_menu()
