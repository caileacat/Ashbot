import weaviate
import os
import subprocess
import time
import requests
import yaml
import json
from weaviate.classes.init import AdditionalConfig, Timeout
import weaviate.classes as wvc  # ✅ Required for Weaviate v4 classes
from weaviate.classes.query import Filter

# ✅ Constants
WEAVIATE_URL = "http://localhost:8080"
DOCKER_CONTAINER_NAME = "weaviate"
DOCKER_IMAGE = "semitechnologies/weaviate"
DOCKER_PORT = 8080
GRPC_PORT = 50051

def connect_to_weaviate():
    """Establishes a fresh connection to Weaviate"""
    return weaviate.connect_to_local(
        host="localhost",
        port=8080,
        grpc_port=50051,  # ✅ Explicitly set gRPC port
    )

def fetch_user_memory(user_id):
    """Fetches memory about a specific user from Weaviate."""
    try:
        client = weaviate.connect_to_local(port=8080, grpc_port=50051)

        # ✅ Define the query to fetch user memory
        user_memory_collection = client.collections.get("UserMemory")

        response = user_memory_collection.query.fetch_objects(
            return_properties=[
                "name", "pronouns", "role", "relationship_notes", "interaction_count",
                "last_conversation", "memories"
            ],
            filters=Filter.by_property("user_id").equal(user_id),
            limit=1  # ✅ Only fetch the most relevant entry
        )

        client.close()  # ✅ Always close the client after querying

        # ✅ Check if we found data
        if not response.objects:
            print(f"⚠️ No memory found for user `{user_id}`.")
            return None

        # ✅ Extract and return the user memory object
        user_data = response.objects[0].properties
        return user_data

    except Exception as e:
        print(f"❌ Error retrieving user memory: {e}")
        return None

def load_weaviate_schema():
    """Forces Weaviate to use the correct schema format."""
    client = weaviate.connect_to_local()

    try:
        # ✅ Delete old schema to FORCE proper application
        existing_collections = [col.name for col in client.collections.list_all()]
        for collection in existing_collections:
            client.collections.delete(collection)
            print(f"🗑️ Deleted existing collection: {collection}")

        # ✅ Load schema from YAML
        with open("data/weaviate_schema.yaml", "r", encoding="utf-8") as file:
            schema = yaml.safe_load(file)

        # ✅ Recreate all collections
        for collection in schema["classes"]:
            print(f"🚀 Creating collection: {collection['class']}")
            client.collections.create(collection)

        print("✅ Weaviate schema loaded successfully!")

    except Exception as e:
        print(f"❌ Error loading Weaviate schema: {e}")

    finally:
        client.close()

def is_weaviate_running_quick():
    """A fast check to see if Weaviate is responding."""
    try:
        response = requests.get(f"{WEAVIATE_URL}/v1/meta", timeout=1)  # ✅ Shorter timeout
        return response.status_code == 200
    except requests.RequestException:
        return False

def is_weaviate_fully_ready(retries=10, delay=2):
    """A deeper check that waits until Weaviate is fully online."""
    for attempt in range(retries):
        if is_weaviate_running_quick():
            return True  # ✅ Weaviate is ready!
        
        print(f"⏳ Waiting for Weaviate to fully start... ({attempt + 1}/{retries})")
        time.sleep(delay)

    print("❌ Weaviate check failed after multiple attempts.")
    return False

def stop_weaviate():
    """Stops the Weaviate container immediately without waiting."""
    if not is_weaviate_running_quick():
        print("⚠️ Weaviate is already stopped.")
        return True

    print("🛑 Stopping Weaviate...")
    try:
        subprocess.run(["docker", "stop", DOCKER_CONTAINER_NAME], check=True)
        print("✅ Weaviate successfully stopped.")
        return True
    except Exception as e:
        print(f"❌ Error stopping Weaviate: {e}")
        return False

def start_weaviate():
    """Ensures Weaviate is running efficiently without unnecessary waits."""
    
    # 🔍 Step 1: Quick Check - Is Weaviate already running?
    if is_weaviate_running_quick():
        print("✅ Weaviate is already running.")
        return True

    print("🚀 Starting a fresh Weaviate instance...")

    # 🛑 Step 2: Check for existing stopped container & remove it
    existing_containers = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True, text=True
    ).stdout.split()

    if DOCKER_CONTAINER_NAME in existing_containers:
        print("🛑 Removing old Weaviate container...")
        subprocess.run(["docker", "rm", "-f", DOCKER_CONTAINER_NAME], check=True)

    # 🚀 Step 3: Start a new Weaviate container
    try:
        subprocess.run([
            "docker", "run", "-d", "--restart=always",
            "--name", DOCKER_CONTAINER_NAME,
            "-p", "8080:8080",
            "-p", "50051:50051",
            DOCKER_IMAGE
        ], check=True)

        print("⏳ Waiting for Weaviate to fully start...")

        # 🔄 Step 4: Ensure Weaviate is fully ready before returning success
        if is_weaviate_fully_ready():
            print("✅ Weaviate started successfully and is ready to use!")
            return True
        else:
            print("❌ Weaviate started, but is not responding correctly.")
            return False

    except Exception as e:
        print(f"❌ Error starting Weaviate: {e}")
        return False
    
def restart_weaviate():
    """Restarts Weaviate efficiently and ensures it is fully ready before continuing."""
    
    # 🔍 Step 1: Quick Check - Is Weaviate already running?
    if not is_weaviate_running_quick():
        print("⚠️ Cannot restart Weaviate because it's not running. Starting it instead.")
        return start_weaviate()

    print("🔄 Restarting Weaviate...")

    try:
        # 🛑 Step 2: Stop Weaviate first
        stop_weaviate()

        # 🚀 Step 3: Restart Weaviate container
        subprocess.run(["docker", "restart", DOCKER_CONTAINER_NAME], check=True)
        
        print("⏳ Waiting for Weaviate to fully restart...")

        # 🔄 Step 4: Wait for Weaviate to be fully responsive
        if is_weaviate_fully_ready():
            print("✅ Weaviate restarted successfully and is ready to use!")
            return True
        else:
            print("❌ Weaviate restarted but is not responding correctly.")
            return False

    except Exception as e:
        print(f"❌ Error restarting Weaviate: {e}")
        return False

def reset_memory():
    """Resets Weaviate memory by deleting all data and restoring the core schema and base data."""
    if is_weaviate_running_quick():
        print("⚠️ Cannot reset memory while Weaviate is running. Stop Weaviate first.")
        return False

    confirmation = input("To confirm removal of all of Ash's memories, type: KILL ASH\n> ")
    if confirmation != "KILL ASH":
        print("❌ Memory reset aborted. Incorrect confirmation input.")
        return False

    print("⚠️ Resetting ALL Weaviate memory...")

    # Stop Weaviate first
    stop_weaviate()

    # Remove the container
    try:
        subprocess.run(["docker", "rm", "-f", DOCKER_CONTAINER_NAME], check=True)
        print("✅ Weaviate container removed.")
    except Exception as e:
        print(f"❌ Error removing Weaviate container: {e}")
        return False

    # Restart Weaviate
    if not start_weaviate():
        print("❌ Failed to restart Weaviate.")
        return False

    # 🔄 **Wait Until Weaviate is Fully Ready**
    if not is_weaviate_fully_ready():
        print("❌ Weaviate failed to come online after reset.")
        return False

    # 📜 Load schema
    try:
        load_weaviate_schema()
        print("✅ Weaviate schema successfully applied!")
    except Exception as e:
        print(f"❌ Error applying schema: {e}")
        return False

    # 📂 Insert base data
    try:
        insert_base_data()
        print("✅ Base data successfully inserted into Weaviate.")
    except Exception as e:
        print(f"❌ Error inserting base data: {e}")
        return False

    print("🎉 Weaviate has been fully reset with core data!")
    return True

def insert_base_data():
    """Inserts core data into Weaviate, ensuring correct data types."""
    base_data_path = "data/base_data.json"

    if not os.path.exists(base_data_path):
        print(f"❌ Base data file not found: {base_data_path}")
        return False

    try:
        client = weaviate.connect_to_local()

        with open(base_data_path, "r", encoding="utf-8") as file:
            base_data = json.load(file)

        for collection_name, data_list in base_data.items():
            try:
                collection = client.collections.get(collection_name)
            except Exception:
                print(f"⚠️ Skipping {collection_name} - Collection does not exist in Weaviate.")
                continue

            for data in data_list:
                # ✅ Debug print the data before inserting
                print(f"📥 Inserting into {collection_name}: {data}")

                # ✅ Force `reinforced_count` to be an integer
                if collection_name == "LongTermMemories":
                    if "reinforced_count" in data:
                        data["reinforced_count"] = int(data["reinforced_count"])  # 🔥 FORCE INTEGER!

                collection.data.insert(data)

        print("✅ Base data inserted successfully!")

    except Exception as e:
        print(f"❌ Error inserting base data: {e}")

    finally:
        client.close()

def weaviate_menu():
    """Displays the Weaviate Management Menu with optimized checks."""
    while True:
        # ✅ Use quick check for displaying the menu
        weaviate_running = is_weaviate_running_quick()
        status_emoji = "🟢" if weaviate_running else "🔴"
        print(f"\n=== {status_emoji} Weaviate Management Menu {status_emoji} ===")

        if weaviate_running:
            print("[S] Stop Weaviate")
            print("[R] Restart Weaviate")
        else:
            print("[W] Start Weaviate")
            print("[RESET] Reset ALL Memory to default")
        print("[X] Back")

        choice = input("Select an option: ").strip().upper()

        if choice == "W" and not weaviate_running:
            start_weaviate()
        elif choice == "S" and weaviate_running:
            stop_weaviate()
        elif choice == "R" and weaviate_running:
            restart_weaviate()
        elif choice == "RESET" and not weaviate_running:
            reset_memory()
        elif choice == "X":
            print("🔙 Returning to Main Menu...")
            break
        else:
            print("❌ Invalid selection. Please choose a valid option.")

        # ✅ Refresh menu status
        weaviate_running = is_weaviate_running_quick()

if __name__ == "__main__":
    weaviate_menu()
