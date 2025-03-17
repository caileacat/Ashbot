import os
import time
import yaml
import json
import docker
import weaviate
import requests
import subprocess
import weaviate.classes as wvc  # ✅ Required for Weaviate v4 classes
from weaviate.collections.classes.grpc import Sort # ✅ Import the correct sorting classes
from weaviate.classes.query import Filter, Sort, MetadataQuery
from dotenv import load_dotenv

# ✅ Constants
WEAVIATE_URL = "http://localhost:8080"
DOCKER_CONTAINER_NAME = "weaviate"
DOCKER_IMAGE = "semitechnologies/weaviate"
DOCKER_PORT = 8080
GRPC_PORT = 50051

# ✅ Force loading `.env` from the project's root directory
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ✅ Load the .env file explicitly
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"✅ Loaded .env from: {dotenv_path}")
else:
    print(f"❌ .env file not found at: {dotenv_path}")

# ✅ Debug: Check if OPENAI_APIKEY is loaded
OPENAI_APIKEY = os.getenv("OPENAI_APIKEY")

if not OPENAI_APIKEY:
    print("❌ OPENAI_APIKEY is still not set! Check your .env file location and format.")
else:
    print("✅ OPENAI_APIKEY successfully loaded!")


def is_docker_running():
    """Check if Docker is running."""
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
        return "Server Version" in result.stdout
    except FileNotFoundError:
        return False

def start_docker():
    """Start Docker if it's not running (Windows-specific)."""
    print("🐳 Attempting to start Docker...")
    try:
        subprocess.run(["powershell", "-Command", "Start-Process 'C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe' -NoNewWindow"], check=True)
        time.sleep(10)  # Give Docker time to start
        return is_docker_running()
    except Exception as e:
        print(f"❌ Error starting Docker: {e}")
        return False

def connect_to_weaviate():
    """Establishes a fresh connection to Weaviate"""
    return weaviate.connect_to_local(
        host="localhost",
        port=8080,
        grpc_port=50051,  # ✅ Explicitly set gRPC port
    )

def fetch_user_profile(user_id):
    """Retrieves the full user profile from Weaviate."""
    try:
        client = weaviate.connect_to_local(port=8080, grpc_port=50051)
        user_profiles = client.collections.get("UserProfiles")

        response = user_profiles.query.fetch_objects(
            filters=Filter.by_property("user_id").equal(user_id),
            limit=1  # There should only be one user profile per user
        )

        return response.objects[0].properties if response.objects else None

    except Exception as e:
        print(f"❌ Error fetching user profile: {e}")
        return None

    finally:
        client.close()  # ✅ Ensures client always closes

def fetch_long_term_memories(user_id, limit=3):
    """Fetches long-term memories using hybrid search (vector + keyword)."""
    try:
        client = weaviate.connect_to_local()
        collection = client.collections.get("LongTermMemories")

        response = collection.query.hybrid(
            query=f"user {user_id}",
            alpha=0.7,  # Mixes keyword & vector search (0 = full keyword, 1 = full vector)
            return_properties=["memory", "reinforced_count"],
            filters=Filter.by_property("user_id").equal(user_id),
            return_metadata=MetadataQuery(creation_time=True),  # ✅ Fetch metadata timestamps
            limit=limit
        )

        client.close()

        if response.objects:
            return [
                {
                    **o.properties,
                    "timestamp": o.metadata.creation_time  # ✅ Correct metadata
                }
                for o in response.objects
            ]
        else:
            return []

    except Exception as e:
        print(f"❌ Error fetching long-term memories: {e}")
        return []

def fetch_recent_conversations(user_id, limit=3):
    """Retrieves the last `limit` recent conversations for a user."""
    try:
        client = weaviate.connect_to_local()
        recent_conversations = client.collections.get("RecentConversations")

        response = recent_conversations.query.fetch_objects(
            filters=Filter.by_property("user_id").equal(user_id),
            limit=limit,
            sort=Sort.by_property("_creationTimeUnix", ascending=False),  # ✅ FIXED!
            return_metadata=wvc.query.MetadataQuery(creation_time=True)  # ✅ Correct metadata query
        )

        client.close()

        if response.objects:
            return [
                {
                    **o.properties,
                    "timestamp": o.metadata.creation_time  # ✅ Correct timestamp handling
                }
                for o in response.objects
            ]
        else:
            print(f"⚠️ No recent conversations found for user `{user_id}`.")
            return []

    except Exception as e:
        print(f"❌ Error fetching recent conversations: {e}")
        return []

def load_weaviate_schema():
    """Loads the Weaviate schema from YAML file, ensuring Weaviate is fully ready first."""
    client = connect_to_weaviate()
    
    if not client:
        print("❌ Unable to connect to Weaviate.")
        return False

    schema_path = "data/weaviate_schema.yaml"
    if not os.path.exists(schema_path):
        print(f"❌ Schema file not found: {schema_path}. Ensure it exists before running RESET.")
        return False

    # ✅ Wait for leader election (Weaviate might need time)
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{WEAVIATE_URL}/v1/meta", timeout=3)
            if response.status_code == 200:
                print("✅ Weaviate leader elected. Ready to load schema.")
                break
        except requests.RequestException:
            print(f"⏳ Waiting for Weaviate leader election... ({attempt + 1}/{max_attempts})")
            time.sleep(2)
    else:
        print("❌ Weaviate leader was not elected in time. Aborting schema load.")
        return False

    try:
        with open(schema_path, "r", encoding="utf-8") as file:
            schema = yaml.safe_load(file)

        # ✅ Get list of existing collections
        existing_collections = [col.name for col in client.collections.list_all()]

        for collection in schema["classes"]:
            collection_name = collection["class"]

            if collection_name not in existing_collections:
                print(f"🚀 Creating collection: {collection_name}")

                properties = [
                    wvc.config.Property(
                        name=prop["name"],
                        data_type=wvc.config.DataType[prop["dataType"][0].upper()],
                    )
                    for prop in collection["properties"]
                ]

                client.collections.create(
                    name=collection_name,
                    properties=properties
                )

                print(f"✅ Collection '{collection_name}' created successfully.")
            else:
                print(f"⚠️ Collection '{collection_name}' already exists. Skipping.")

        client.close()
        print("✅ Weaviate schema loaded successfully!")
        return True

    except Exception as e:
        print(f"❌ Error loading Weaviate schema: {e}")
        client.close()
        return False

def is_weaviate_running():
    """Check if Weaviate is running inside Docker."""
    try:
        result = subprocess.run(["docker", "ps", "--filter", f"name={DOCKER_CONTAINER_NAME}", "--format", "{{.Names}}"],
                                capture_output=True, text=True)
        return DOCKER_CONTAINER_NAME in result.stdout.strip()
    except FileNotFoundError:
        return False

def is_weaviate_fully_ready(retries=10, delay=3):
    """Check if Weaviate is fully initialized and the leader is elected."""
    print("⏳ Checking if Weaviate is fully ready...")
    for attempt in range(retries):
        try:
            response = requests.get(f"{WEAVIATE_URL}/v1/meta", timeout=2)
            if response.status_code == 200:
                leader_check = requests.get(f"{WEAVIATE_URL}/v1/schema")
                if leader_check.status_code == 200:
                    print("✅ Weaviate leader elected. Ready to load schema.")
                    return True
                elif leader_check.status_code == 403:
                    print("⏳ Leader not found yet. Retrying...")
            else:
                print("⏳ Weaviate is starting. Waiting...")
        except requests.RequestException:
            print("⏳ Weaviate not reachable. Waiting...")
        time.sleep(delay)
    print("❌ Weaviate failed to become ready in time.")
    return False

def stop_weaviate():
    """Stops the Weaviate container without removing it."""
    try:
        print("🛑 Stopping Weaviate...")
        subprocess.run(["docker", "compose", "stop"], check=True)
        print("✅ Weaviate container stopped successfully.")
    except Exception as e:
        print(f"❌ Error stopping Weaviate: {e}")

def start_weaviate():
    """Starts Weaviate if a container exists, otherwise triggers container creation."""
    
    if is_weaviate_running():
        print("✅ Weaviate is already running.")
        return True

    # 🔍 Step 1: Check for existing container
    existing_containers = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True, text=True
    ).stdout.split()

    if "weaviate" in existing_containers:
        print("♻️ Restarting existing Weaviate container...")
        try:
            subprocess.run(["docker", "start", "weaviate"], check=True)
            if is_weaviate_fully_ready():
                print("✅ Weaviate restarted successfully!")
                return True
        except Exception as e:
            print(f"❌ Error restarting Weaviate: {e}")
            return False
    else:
        print("🚨 No existing Weaviate container found. Creating a new one...")
        return create_weaviate_container()

def create_weaviate_container():
    """Creates a brand-new Weaviate container using Docker Compose."""
    try:
        subprocess.run(["docker", "compose", "up", "-d"], check=True)

        if is_weaviate_fully_ready():
            print("✅ New Weaviate container created and started successfully!")
            initialize_weaviate_data()  # 🚀 Initialize after creation
            return True

    except Exception as e:
        print(f"❌ Error creating Weaviate container: {e}")
        return False

    return False

def initialize_weaviate_data():
    """Ensures Weaviate has the correct schema and base data after a fresh start."""
    print("📜 Loading schema into Weaviate...")
    if not load_weaviate_schema():
        print("❌ Schema loading failed. Please check the schema file.")
        return False

    print("📂 Inserting base data...")
    if not insert_base_data():  # ✅ Now this check will work correctly
        print("❌ Failed to insert base data. Weaviate may be incomplete.")
        return False  # ✅ Return failure if data insertion didn't work

    print("🎉 Weaviate is fully initialized with schema and base data!")
    return True

def reset_memory():
    """Resets Weaviate by stopping, deleting volumes, and restarting everything cleanly."""
    if is_weaviate_running():
        print("⚠️ Cannot reset memory while Weaviate is running. Stopping first...")
        stop_weaviate()

    confirmation = input("To confirm removal of all of Ash's memories, type: KILL ASH\n> ")
    if confirmation != "KILL ASH":
        print("❌ Memory reset aborted.")
        return False

    print("⚠️ Resetting ALL Weaviate memory...")

    try:
        print("🛑 Stopping and removing Weaviate data...")
        subprocess.run(["docker", "compose", "down", "-v"], check=True)  # ✅ Fully removes volumes
        print("✅ Weaviate container and data removed.")

        print("🚀 Restarting fresh Weaviate instance...")
        return create_weaviate_container()

    except Exception as e:
        print(f"❌ Error resetting Weaviate: {e}")
        return False

def restart_weaviate():
    """Restarts Weaviate using Docker Compose."""
    if not is_weaviate_running():
        print("⚠️ Cannot restart Weaviate because it's not running. Starting it instead.")
        return start_weaviate()

    print("🔄 Restarting Weaviate...")
    try:
        subprocess.run(["docker", "compose", "restart", "weaviate"], check=True)
        print("✅ Weaviate restarted successfully!")
        return True

    except Exception as e:
        print(f"❌ Error restarting Weaviate: {e}")
        return False

def insert_base_data():
    """Inserts core data into Weaviate, ensuring correct data types."""
    base_data_path = "data/base_data.json"

    if not os.path.exists(base_data_path):
        print(f"❌ Base data file not found: {base_data_path}")
        return False  # ✅ Explicit failure return

    try:
        client = weaviate.connect_to_local()
        with open(base_data_path, "r", encoding="utf-8") as file:
            base_data = json.load(file)

        failed_inserts = 0  # ✅ Track failures

        for collection_name, data_list in base_data.items():
            try:
                collection = client.collections.get(collection_name)
            except Exception:
                print(f"⚠️ Skipping {collection_name} - Collection does not exist in Weaviate.")
                continue

            for data in data_list:
                print(f"📥 Inserting into {collection_name}: {data}")

                if collection_name == "LongTermMemories" and "reinforced_count" in data:
                    data["reinforced_count"] = int(data["reinforced_count"])  # 🔥 Ensure integer

                try:
                    collection.data.insert(data)
                except Exception as e:
                    print(f"❌ Failed to insert data into {collection_name}: {e}")
                    failed_inserts += 1  # ✅ Count failed inserts

        client.close()  # ✅ Close connection properly

        if failed_inserts > 0:
            print(f"❌ {failed_inserts} data entries failed to insert. Weaviate may be incomplete.")
            return False  # ✅ Return failure only if something went wrong

        print("✅ Base data inserted successfully!")
        return True  # ✅ Explicit success return

    except Exception as e:
        print(f"❌ Error inserting base data: {e}")
        return False  # ✅ Ensure function always returns a boolean

def weaviate_menu():
    """Displays the Weaviate Management Menu with optimized checks."""
    while True:
        # ✅ Use quick check for displaying the menu
        weaviate_running = is_weaviate_running()
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
        weaviate_running = is_weaviate_running()

if __name__ == "__main__":
    weaviate_menu()
