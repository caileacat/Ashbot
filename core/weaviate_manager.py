import weaviate
import subprocess
import time
import requests
import json
import datetime

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
    """Stops the Weaviate container and ensures the client connection is closed."""
    if not is_weaviate_running():
        print("⚠️ Weaviate is already stopped.")
        return True

    print("🛑 Stopping Weaviate...")
    try:
        client = weaviate.connect_to_custom(
            http_host="localhost",
            http_port=8080,
            http_secure=False,
            grpc_host="localhost",
            grpc_port=50051,
            grpc_secure=False,
            skip_init_checks=True
        )
        client.close()  # ✅ Explicitly close the connection before stopping Weaviate
        subprocess.run(["docker", "stop", DOCKER_CONTAINER_NAME], check=True)
        return not is_weaviate_running()
    except Exception as e:
        print(f"❌ Error stopping Weaviate: {e}")
        return False
    
def start_weaviate():
    """Starts Weaviate by creating a fresh container if needed."""
    print("🚀 Creating a new Weaviate container...")

    try:
        subprocess.run([
            "docker", "run", "-d", "--restart=always",
            "--name", DOCKER_CONTAINER_NAME,
            "-p", f"{DOCKER_PORT}:8080",
            "-p", f"{GRPC_PORT}:50051",
            "-e", "ENABLE_MODULES=text2vec-openai",  # ✅ Ensures OpenAI vectorizer is loaded
            "-e", "QUERY_DEFAULTS_LIMIT=100",
            "-e", "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true",
            DOCKER_IMAGE
        ], check=True)
        time.sleep(5)
        return is_weaviate_running()
    except Exception as e:
        print(f"❌ Error creating new Weaviate container: {e}")
        return False

def reset_memory():
    """Resets Weaviate memory by deleting the container, creating a new one, and reinitializing core memories."""
    if is_weaviate_running():
        stop_weaviate()

    confirmation = input("To confirm removal of all of Ash's memories, type: KILL ASH\n> ")
    if confirmation != "KILL ASH":
        print("❌ Memory reset aborted. Incorrect confirmation input.")
        return False

    print("⚠️ Resetting ALL Weaviate memory by deleting and recreating the container...")
    try:
        subprocess.run(["docker", "rm", "-f", DOCKER_CONTAINER_NAME], check=True)
        start_weaviate()
        initialize_core_memories()
        print("✅ Memory reset and container recreated successfully.")
        return True
    except Exception as e:
        print(f"❌ Error resetting memory: {e}")
        return False

def initialize_core_memories():
    """Re-inserts core user memories into Weaviate, ensuring the schema exists."""
    print("🔄 Initializing core memories...")
    client = weaviate.connect_to_custom(
        http_host="localhost",
        http_port=8080,
        http_secure=False,
        grpc_host="localhost",
        grpc_port=50051,
        grpc_secure=False,
        skip_init_checks=True
    )

    schema = client.collections.list_all()
    if "UserMemory" not in schema:
        print("⚠️ Schema missing! Creating UserMemory schema...")
        client.collections.create(
            name="UserMemory",
            vectorizer_config=weaviate.classes.config.Configure.Vectorizer.text2vec_openai(),
            properties=[
                weaviate.classes.config.Property(name="user_id", data_type=weaviate.classes.config.DataType.TEXT),
                weaviate.classes.config.Property(name="memory_type", data_type=weaviate.classes.config.DataType.TEXT),
                weaviate.classes.config.Property(name="memory_text", data_type=weaviate.classes.config.DataType.TEXT),
                weaviate.classes.config.Property(name="relationship_notes", data_type=weaviate.classes.config.DataType.TEXT),
                weaviate.classes.config.Property(name="interaction_count", data_type=weaviate.classes.config.DataType.INT),
                weaviate.classes.config.Property(name="last_interaction", data_type=weaviate.classes.config.DataType.DATE)
            ]
        )
        print("✅ UserMemory schema created.")

    core_memories = {
        "851181959933591554": {"name": "Cailea", "role": "Boss and Closest Friend"},
        "424042103346298880": {"name": "Lemon", "role": "Cailea's Partner, Fun Prankster Friend"},
        "0": {"identity": "Ashen 'Ash' Thornbrook", "role": "Mischievous Non-Binary Fae-Witch"}
    }

    try:
        for user_id, memory in core_memories.items():
            memory_text = json.dumps(memory, ensure_ascii=False)
            timestamp = datetime.datetime.utcnow().isoformat()
            client.collections.get("UserMemory").data.insert({
                "user_id": user_id,
                "memory_type": "core",
                "memory_text": memory_text,
                "timestamp": timestamp
            })
            print(f"✅ Memory initialized for user {user_id}.")
        print("🎉 All core memories initialized successfully!")
    except Exception as e:
        print(f"❌ Error inserting core memories: {e}")

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
            reset_memory()
        elif choice == "RESET":
            reset_memory()
        elif choice == "X":
            print("🔙 Returning to Main Menu...")
            break
        else:
            print("❌ Invalid selection. Please choose a valid option.")

if __name__ == "__main__":
    weaviate_menu()
