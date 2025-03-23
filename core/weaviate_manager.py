import os
import time
import yaml
import json
import weaviate
import requests
import subprocess
import weaviate.classes as wvc
from datetime import datetime, timedelta
from weaviate.classes.query import Filter
from sentence_transformers import SentenceTransformer, util
from data.constants import WEAVIATE_URL, CAILEA_ID, BASE_MEMORIES, OPENAI_API_KEY

model = SentenceTransformer("all-MiniLM-L6-v2")

URLS =  [
        "http://localhost:8080/v1/meta",  # Works when calling from the host machine
        "http://weaviate:8080/v1/meta"    # Works when calling from inside the Docker network
        ]


def convert_lists_to_json(obj):
    """
    Converts list values to JSON strings before inserting into Weaviate.
    Ensures all list-based fields are properly formatted.
    """
    for key, value in obj.items():
        if isinstance(value, list):  # ✅ If it's a list, convert it to a JSON string
            obj[key] = json.dumps(value)
    return obj

def convert_json_to_lists(obj):
    """
    Converts JSON strings back to lists when retrieving from Weaviate.
    Ensures consistency in how lists are handled in memory.
    """
    for key, value in obj.items():
        if isinstance(value, str):  # ✅ If it's a string, check if it's a JSON list
            try:
                parsed_value = json.loads(value)
                if isinstance(parsed_value, list):
                    obj[key] = parsed_value  # ✅ Convert it back to a list
            except json.JSONDecodeError:
                pass  # Ignore if it's not valid JSON
    return obj

### **🔹 Helper: Connect to Weaviate**
def connect_to_weaviate():
    """Connects to Weaviate using the Python v4 client and ensures a stable connection."""
    try:
        client = weaviate.connect_to_local(headers={"X-OpenAI-Api-Key": OPENAI_API_KEY})
        print("✅ Connected to Weaviate successfully!")
        return client
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Weaviate: {e}")
        return None

### **🔹 Upsert User Memory (Profile & Long-Term Memory)**
def upsert_user_memory(user_id, name=None, pronouns=None, role=None, relationship_notes=None, new_memory=None, source=None, verified=None):
    """
    Inserts or updates user details and long-term memories into Weaviate.
    Accepts optional source and verified flags for memory origin tracking.
    """
    client = connect_to_weaviate()
    if not client:
        return False

    try:
        user_collection = client.collections.get("UserMemory")
        user_profile = user_collection.query.fetch_objects(
            filters=Filter.by_property("user_id").equal(user_id),
            limit=1
        )

        existing_user = user_profile.objects[0] if user_profile.objects else None

        memory_list = []
        if existing_user:
            existing_mem = existing_user.properties.get("memory", "[]")
            try:
                memory_list = json.loads(existing_mem) if isinstance(existing_mem, str) else existing_mem
            except Exception:
                memory_list = []

        if new_memory:
            memory_list.append(new_memory)
            print(f"[UserMemory] PROMOTED memory for {user_id}: \"{new_memory}\"")

        update_data = {
            "user_id": user_id,
            "name": name or (existing_user.properties.get("name") if existing_user else ""),
            "pronouns": pronouns or (existing_user.properties.get("pronouns") if existing_user else ""),
            "role": role or (existing_user.properties.get("role") if existing_user else ""),
            "relationship_notes": relationship_notes or (existing_user.properties.get("relationship_notes") if existing_user else ""),
            "memory": json.dumps(memory_list),
            "source": source or "promoted",
            "verified": verified if verified is not None else False
        }

        if existing_user:
            user_collection.data.replace(uuid=existing_user.uuid, properties=update_data)
            print(f"🔄 Updated UserMemory for {user_id}")
        else:
            user_collection.data.insert(properties=update_data)
            print(f"✅ Inserted new UserMemory for {user_id}")

    except Exception as e:
        print(f"❌ ERROR in upsert_user_memory: {e}")

    finally:
        client.close()

### **🔹 Insert Recent Conversation**
def insert_recent_conversation(user_id, summary):
    """Stores a conversation summary in Weaviate."""
    client = connect_to_weaviate()
    if not client:
        return False

    try:
        conversation_collection = client.collections.get("RecentConversations")
        conversation_collection.data.insert(properties={"user_id": user_id, "summary": summary})
        print(f"✅ Inserted RecentConversation for {user_id}")

    except Exception as e:
        print(f"❌ ERROR inserting recent conversation: {e}")

    finally:
        if client and client.is_connected():
            client.close()

def insert_data(class_name, objects):
    """
    Inserts multiple objects into Weaviate.
    Ensures lists are converted to JSON strings before insertion.
    """
    client = connect_to_weaviate()
    if not client:
        print(f"❌ Failed to connect to Weaviate for inserting into {class_name}.")
        return False

    try:
        collection = client.collections.get(class_name)
        print(f"📥 Inserting into {class_name}: {len(objects)} records...")

        for obj in objects:
            # ✅ Ensure all lists are converted to JSON strings
            obj = convert_lists_to_json(obj)

            try:
                collection.data.insert(properties=obj)
                print(f"✅ Successfully inserted into {class_name}: {obj}")

            except Exception as e:
                print(f"❌ ERROR inserting into {class_name}: {e}")

    except Exception as e:
        print(f"❌ ERROR accessing collection {class_name}: {e}")

    finally:
        client.close()

### **🔹 Perform Vector-Based Search**
def perform_vector_search(query_text):
    """
    Searches Weaviate for memories or conversations that are similar to the given query.
    Uses vector similarity instead of direct lookups.
    """
    client = connect_to_weaviate()
    if not client:
        return []

    try:
        user_collection = client.collections.get("UserMemory")
        response = user_collection.query.near_text(query=query_text, limit=5)

        relevant_memories = [obj.properties for obj in response.objects]
        print(f"✅ Found {len(relevant_memories)} contextually relevant memories.")
        return relevant_memories

    except Exception as e:
        print(f"❌ ERROR in vector search: {e}")
        return []

    finally:
        client.close()

### **🔹 Fetch User Profile**
def fetch_user_profile(user_id):
    """
    Retrieves user profile data from Weaviate and converts JSON-encoded lists back to Python lists.
    """
    try:
        client = connect_to_weaviate()
        collection = client.collections.get("UserMemory")

        response = collection.query.fetch_objects(
            filters=weaviate.classes.query.Filter.by_property("user_id").equal(user_id),
            return_properties=["user_id", "name", "pronouns", "role", "relationship_notes", "memory"]
        )

        if response.objects:
            user_data = response.objects[0].properties  # ✅ Extract first matching user
            
            # ✅ Convert JSON string back to a list
            if isinstance(user_data.get("memory"), str):
                try:
                    user_data["memory"] = json.loads(user_data["memory"])
                except json.JSONDecodeError:
                    user_data["memory"] = []  # ✅ Default to empty list if it fails

            return user_data

        return {}  # ✅ Return empty if no user found

    except Exception as e:
        print(f"❌ ERROR fetching user profile: {e}")
        return {}

### **🔹 Fetch Long-Term Memories**
def fetch_long_term_memories(user_id):
    """Fetches long-term memories from Weaviate and ensures proper format handling."""
    client = connect_to_weaviate()
    if not client:
        return []

    try:
        # ✅ Use proper Weaviate filter class
        filter_condition = Filter.by_property("user_id").equal(user_id)

        memory_collection = client.collections.get("UserMemory")
        results = memory_collection.query.fetch_objects(
            limit=1,
            return_properties=["memory"],
            filters=filter_condition  # ✅ Correct filter usage
        )

        if results.objects:
            memory_data = results.objects[0].properties.get("memory", "[]")
            return json.loads(memory_data) if isinstance(memory_data, str) else memory_data  # ✅ Ensure proper format

    except Exception as e:
        print(f"❌ ERROR fetching long-term memories: {e}")

    finally:
        client.close()

    return []

### **🔹 Fetch Recent Conversations**
def fetch_recent_conversations(user_id, limit=3):
    """
    Retrieves the most recent conversations a user has had with Ash.
    """
    client = connect_to_weaviate()
    if not client:
        return []

    try:
        conversation_collection = client.collections.get("RecentConversations")
        response = conversation_collection.query.fetch_objects(
            filters=Filter.by_property("user_id").equal(user_id),
            limit=limit
        )

        conversations = [obj.properties for obj in response.objects]
        print(f"✅ Retrieved {len(conversations)} recent conversations for {user_id}")
        return conversations

    except Exception as e:
        print(f"❌ ERROR fetching recent conversations: {e}")
        return []

    finally:
        client.close()

### **🔹 Insert a New Self-Memory for Ash**
def add_ash_memory(new_memory):
    """
    Adds a new memory for Ash, reinforcing existing ones if applicable.
    """
    client = connect_to_weaviate()
    if not client:
        return False

    try:
        ash_collection = client.collections.get("AshMemories")
        response = ash_collection.query.fetch_objects(
            filters=Filter.by_property("memory").equal(new_memory),
            limit=1
        )

        if response.objects:
            existing_memory = response.objects[0]
            new_count = existing_memory.properties["reinforced_count"] + 1

            ash_collection.data.replace(uuid=existing_memory.uuid, properties={
                "memory": new_memory,
                "reinforced_count": new_count
            })
            print(f"🔄 Reinforced Ash memory: {new_memory}")

        else:
            ash_collection.data.insert(properties={"memory": new_memory, "reinforced_count": 1})
            print(f"✅ Added new Ash memory: {new_memory}")

    except Exception as e:
        print(f"❌ ERROR adding Ash memory: {e}")

    finally:
        client.close()

def load_weaviate_schema():
    """
    Loads Weaviate schema from YAML file.
    """
    import yaml

    client = connect_to_weaviate()

    try:
        with open("data/weaviate_schema.yaml", "r", encoding="utf-8") as file:
            schema = yaml.safe_load(file)

        for collection in schema["classes"]:
            class_name = collection["class"]
            existing = client.collections.exists(class_name)

            if not existing:
                properties = [
                    weaviate.Property(name=prop["name"], data_type=prop["dataType"][0])
                    for prop in collection["properties"]
                ]
                client.collections.create(name=class_name, properties=properties)
                print(f"✅ Created collection: {class_name}")
            else:
                print(f"⚠️ Collection {class_name} already exists. Skipping.")

    except Exception as e:
        print(f"❌ Error loading Weaviate schema: {e}")

    finally:
        client.close()

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
    """Check if Weaviate is running and responsive."""
    urls = [
        "http://localhost:8080/v1/meta",  # Works when calling from the host machine
        "http://weaviate:8080/v1/meta"    # Works when calling from inside the Docker network
    ]

    for url in URLS:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"✅ Weaviate is running and reachable at {url}")
                return True
        except requests.exceptions.RequestException:
            print(f"⚠️ Weaviate is NOT reachable at {url}")

    return False

def is_weaviate_fully_ready(retries=5, delay=3):
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
    """Stops Weaviate using docker-compose, ensuring it is fully stopped."""
    print("🛑 Attempting to stop Weaviate...")

    # ✅ Step 1: Check if Weaviate is running
    if not is_weaviate_running():
        print("✅ Weaviate is already stopped.")
        return True

    try:
        # ✅ Step 2: Try stopping with Docker Compose
        print("📌 Stopping Weaviate using docker-compose...")
        result = subprocess.run(["docker-compose", "stop", "weaviate"], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Weaviate has been stopped successfully.")
        else:
            print(f"❌ Failed to stop Weaviate with docker-compose: {result.stderr}")

        # ✅ Step 3: Verify Weaviate is actually stopped
        if not is_weaviate_running():
            return True  # Successfully stopped

    except Exception as e:
        print(f"❌ Error stopping Weaviate: {e}")

    # ✅ Step 4: Fallback to stopping with `docker stop`
    print("🔪 Force stopping Weaviate using docker stop...")
    result = subprocess.run(["docker", "stop", "weaviate"], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Weaviate stopped successfully using docker stop.")
    else:
        print(f"❌ Failed to stop Weaviate with docker stop: {result.stderr}")

    # ✅ **Final check (Only ONE confirmation message!)**
    if is_weaviate_running():
        print("❌ Weaviate is still running. Check logs for errors.")
        return False

    print("✅ Weaviate is now fully stopped.")
    return True

def start_weaviate():
    """Starts Weaviate if a container exists, otherwise let the caller handle creation."""
    
    if is_weaviate_running():
        print("✅ Weaviate is already running.")
        return True

    # 🔍 Check for existing stopped Weaviate container
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

    print("⚠️ Weaviate container does not exist. Caller should create a new one.")
    return False  # ✅ This prevents the recursive loop

def create_weaviate_container():
    """Ensure Weaviate is running using docker-compose, not standalone."""
    print("🔄 Checking Docker and Weaviate setup...")

    # ✅ Ensure Docker is running
    if not is_docker_running():
        print("🐳 Docker is not running. Trying to start it...")
        if not start_docker():
            print("❌ Failed to start Docker. Weaviate cannot run.")
            return False

    # ✅ Check if Weaviate is already running
    if is_weaviate_running():
        print("✅ Weaviate is already running.")
        return True

    # 🗑 Remove any stopped Weaviate container **if it exists**
    print("🗑 Removing any existing Weaviate container before starting fresh...")
    subprocess.run(["docker-compose", "down", "-v"], check=False)  # Removes old container and volume

    # 📥 Pull the latest images (Ensures everything is up-to-date)
    print("📥 Pulling latest Weaviate image via docker-compose...")
    result = subprocess.run(["docker-compose", "pull"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error pulling Weaviate image: {result.stderr}")
        return False

    # 🚀 Start Weaviate using `docker-compose up`
    print("🚀 Starting Weaviate stack using docker-compose...")
    result = subprocess.run(["docker-compose", "up", "--build", "-d"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error starting Weaviate stack: {result.stderr}")
        return False

    # ✅ Wait for Weaviate to be fully ready
    print("⏳ Waiting for Weaviate to become available...")
    for _ in range(10):
        if is_weaviate_running():
            print("🎉 Weaviate (with schema) is fully initialized and ready!")
            return True
        time.sleep(3)

    print("❌ Weaviate did not fully start in time.")
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
    """Fully resets Weaviate by deleting all data, ensuring container removal, and restarting cleanly with schema & base data."""
    
    # ✅ Step 1: Ensure Weaviate is stopped
    if is_weaviate_running():
        print("⚠️ Cannot reset memory while Weaviate is running. Stopping first...")
        stop_weaviate()

    # ✅ Step 2: Confirmation prompt
    confirmation = input("To confirm removal of all of Ash's memories, type: KILL ASH\n> ")
    if confirmation != "KILL ASH":
        print("❌ Memory reset aborted.")
        return False

    print("⚠️ Resetting ALL memory...")

    try:
        # ✅ Step 3: Stop and remove all Weaviate-related resources
        print("🛑 Stopping and removing Weaviate data...")
        subprocess.run(["docker", "compose", "down", "-v"], check=True)  # ✅ Removes volumes & network
        subprocess.run(["docker", "rm", "-f", "weaviate"], capture_output=True, text=True)  # ✅ Ensures the container is removed
        print("✅ Weaviate container and data removed.")

        # ✅ Step 4: Restart fresh Weaviate stack using docker-compose
        print("🚀 Restarting fresh Weaviate instance...")
        if not create_weaviate_container():
            print("❌ Failed to recreate Weaviate.")
            return False

        # ✅ Step 5: Initialize Weaviate schema & insert base data
        print("📜 Initializing schema & inserting base data...")
        if not initialize_weaviate_data():
            print("❌ Failed to initialize Weaviate data.")
            return False

        print("🎉 Weaviate reset complete! Ready to go.")
        return True

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
    try:
        for collection_name, data_list in BASE_MEMORIES.items():
            # ✅ Convert lists to JSON before inserting
            formatted_data = [convert_lists_to_json(entry) for entry in data_list]

            if formatted_data:
                insert_data(collection_name, formatted_data)  # ✅ Use updated insert_data

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
            print("[Q] Query Weaviate Data")
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
        elif choice == "Q":
            test_user_id = input("Enter User ID to query: ").strip() or CAILEA_ID
            test_message = input("Enter a message for vector search (or leave blank): ").strip() or None
            import test_queries
            test_queries.test_queries(test_user_id, test_message)
        elif choice == "RESET" and not weaviate_running:
            reset_memory()
        elif choice == "X":
            print("🔙 Returning to Main Menu...")
            break
        else:
            print("❌ Invalid selection. Please choose a valid option.")

        # ✅ Refresh menu status
        weaviate_running = is_weaviate_running()

def promote_memory_to_learned(user_id, recent_memories, threshold=3, similarity_cutoff=0.9):
    print(f"[Memory Promotion] Checking for learned memory promotion for user: {user_id}")

    try:
        user_data = fetch_user_profile(user_id)
        existing_texts = user_data.get("memory", [])
        print(f"[Memory Promotion] Existing memories: {len(existing_texts)}")

        count_map = {}
        for mem in recent_memories:
            text = mem.get("text")
            timestamp = mem.get("timestamp")
            print(f"🔎 Memory candidate: \"{text}\" at {timestamp}")

            if not text:
                print("⚠️ Skipping: No text.")
                continue

            if timestamp and isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except Exception:
                    print("⚠️ Skipping: Bad timestamp format.")
                    continue

            if timestamp and (datetime.now() - timestamp > timedelta(days=10)):
                print("⏳ Skipping: Too old.")
                continue

            count_map[text] = count_map.get(text, 0) + 1

        print(f"[Memory Promotion] Frequency map: {count_map}")

        for memory_text, count in count_map.items():
            print(f"🧪 Checking \"{memory_text}\" ({count} mentions)")
            if count < threshold:
                print("❌ Not enough repetitions.")
                continue

            memory_embedding = model.encode(memory_text, convert_to_tensor=True)

            if existing_texts:
                existing_embeddings = model.encode(existing_texts, convert_to_tensor=True)
                similarities = util.cos_sim(memory_embedding, existing_embeddings)
                max_sim = similarities.max().item()
                print(f"🔁 Max similarity to existing: {max_sim:.2f}")

                if similarities.size(0) > 0 and max_sim > similarity_cutoff:
                    print(f"❌ Too similar to existing memory. Skipping: \"{memory_text}\"")
                    continue

            print(f"✅ PROMOTING: {memory_text}")
            upsert_user_memory(user_id, new_memory=memory_text, source="promoted", verified=False)

    except Exception as e:
        print(f"❌ ERROR during memory promotion: {e}")


if __name__ == "__main__":
    weaviate_menu()
