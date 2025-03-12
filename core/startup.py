import subprocess
import time
from alive_progress import alive_bar

DOCKER_EXE_PATH = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
WEAVIATE_URL = "http://localhost:8080"
DOCKER_CONTAINER_NAME = "weaviate"  # ✅ Name of the container
DOCKER_IMAGE = "semitechnologies/weaviate"  # ✅ Weaviate's Docker image
DOCKER_PORT = 8080  # ✅ Default REST API port
GRPC_PORT = 50051  # ✅ Default gRPC API port


def is_docker_running():
    """Checks if Docker is running."""
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
        return "Server Version" in result.stdout
    except FileNotFoundError:
        return False

def start_docker():
    """Starts Docker Desktop on Windows and visually waits for it to start."""
    print("🐳 Attempting to start Docker on Windows...")
    try:
        subprocess.run(["powershell", "-Command", f"Start-Process '{DOCKER_EXE_PATH}' -NoNewWindow"], check=True)

        # Progress bar while waiting for Docker
        print("⏳ Waiting for Docker to start...")
        with alive_bar(30, title="Starting Docker", spinner="waves") as bar:
            for _ in range(30):  # 30 seconds total
                if is_docker_running():
                    print("✅ Docker is now running!")
                    return True
                time.sleep(1)
                bar()  # Update progress bar

        print("❌ Docker did not start in time.")
        return False
    except Exception as e:
        print(f"❌ Error starting Docker: {e}")
        return False

def is_weaviate_running():
    """Checks if Weaviate is running."""
    try:
        result = subprocess.run(["docker", "ps", "--filter", "name=weaviate", "--format", "{{.Names}}"],
                                capture_output=True, text=True)
        return "weaviate" in result.stdout
    except FileNotFoundError:
        return False

def start_weaviate():
    """Starts Weaviate if it's not running, or starts an existing container."""
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

    # If no existing container, create a new one
    print("🚀 No existing Weaviate container found. Creating a new one...")
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

def initialize_services():
    """Ensures Docker and Weaviate are running."""
    if not is_docker_running():
        print("❌ Docker is not running. Attempting to start it...")
        if not start_docker():
            print("🚨 Failed to start Docker! Exiting...")
            return False

    if not is_weaviate_running():
        print("🧠 Weaviate is not running. Starting container...")
        if not start_weaviate():
            print("❌ Failed to start Weaviate.")
            return False

    print("✅ Weaviate is running!")
    return True

if __name__ == "__main__":
    initialize_services()
