deactivate
.venv\Scripts\activate
python -m core.bot

git add .
git commit -m "Weaviate menu fully works"
git push origin feature/channel-messages

is_docker_running()
start_docker()
connect_to_weaviate()
fetch_user_profile(userid)
fetch_long_term_memories(user_id, Limit=3
fetch_recent_conversations(userid, Limit=3
load_weaviate_schema()
is_weaviate_running()
is_weaviate_fully_ready(retries=10, deiay=3
stop_weaviate()
start_weaviate()
create_weaviate_container()
initialize_weaviate_data()
reset_memory()
restart_weaviate()
insert_base_data()
weaviate_menu()






# 📌 **Weaviate Connection & Query Guide**

## **🚀 Connecting to Weaviate**

### **1️⃣ Install Weaviate (if not installed)**
If you haven't already set up Weaviate, install it using Docker:
```sh
docker run -d --restart=always --name weaviate \
  -p 8080:8080 -p 50051:50051 \
  semitechnologies/weaviate
```

### **2️⃣ Check if Weaviate is Running**
To confirm that Weaviate is running, use:
```sh
docker ps
```
You should see a container named `weaviate` in the output.

If it's **not running**, start it with:
```sh
docker start weaviate
```

---

## **🔗 Connecting to Weaviate in Python**

### **1️⃣ Install Weaviate Python Client**
```sh
pip install weaviate-client
```

### **2️⃣ Connect to Weaviate (Python v4)**
```python
import weaviate

# Connect to a local instance of Weaviate
client = weaviate.connect_to_local(port=8080, grpc_port=50051)

if client.is_ready():
    print("✅ Successfully connected to Weaviate!")
else:
    print("❌ Weaviate connection failed!")
```


---

## **🔍 Querying Data in Weaviate**

### **1️⃣ List All Objects in a Collection**
```python
collection = client.collections.get("UserMemory")
response = collection.query.fetch_objects(limit=5)

for obj in response.objects:
    print(obj.properties)
```

### **2️⃣ Query Specific User Memory by ID**
```python
collection = client.collections.get("UserMemory")
response = collection.query.fetch_objects(
    return_properties=["user_id", "name", "pronouns"],
    limit=1
)

for obj in response.objects:
    print(obj.properties)
```

### **3️⃣ Query with Filters (Find by User ID)**
```python
from weaviate.classes.query import Filter

collection = client.collections.get("UserMemory")
response = collection.query.fetch_objects(
    filters=Filter.by_property("user_id").equal("123456789"),
    return_properties=["name", "relationship_notes"],
    limit=1
)

for obj in response.objects:
    print(obj.properties)
```

---

## **📂 Troubleshooting Weaviate Issues**

### **1️⃣ Check If Weaviate is Running**
```sh
docker ps
```
If Weaviate isn’t running, restart it:
```sh
docker start weaviate
```

### **2️⃣ Check Weaviate Logs**
```sh
docker logs weaviate --tail 50
```

### **3️⃣ Verify Weaviate Schema**
```python
print(client.schema.get())
```
If `UserMemory` is missing, reload the schema.

### **4️⃣ Restart Weaviate**
```sh
docker stop weaviate
sleep 2
docker start weaviate
```

---

## **🎯 Next Steps**
✅ Ensure Weaviate is running.  
✅ Confirm schema is loaded (`client.schema.get()`).  
✅ Test queries and filters.  

---

📌 **If issues persist, restart Weaviate and reapply the schema.** 🚀

======================
======================
======================
======================


# **Weaviate Data Points for ChatGPT Messages**

## **🔍 Data We Will Retrieve from Weaviate**
This document outlines the **structured data** we will fetch from Weaviate **before sending a message to ChatGPT**. These data points ensure Ash has **proper context** when responding.

---

## **🧑‍💻 User Data Structure**
Each user will have a structured memory record stored in Weaviate:

```json
{
    "user_id": "string",      // Discord user ID
    "name": "string",        // User's preferred name (or default username)
    "pronouns": "string",    // User's pronouns (if known, otherwise default to 'they/them')
    "role": "string",        // Role of the user in the bot's memory (e.g., 'Bot Creator', 'Friend')
    "relationship_notes": "string",  // Notes on the user's relationship with Ash
    "interaction_count": int,  // Number of past interactions with Ash
    "last_conversation": "string",  // Summary of the last meaningful conversation
    "memories": [
        {
            "memory_type": "string",  // Type of memory (e.g., 'preference', 'fact', 'event')
            "memory_text": "string",  // The actual stored memory about the user
            "timestamp": "ISO 8601 string"  // When the memory was last updated
        }
    ]
}
```

---

## **📜 Full Data Structure for ChatGPT Message**

When sending a message to ChatGPT, we will structure the **full message payload** like this:

```json
{
    "user": {
        "id": "string",
        "name": "string",
        "pronouns": "string",
        "role": "string",
        "relationship_notes": "string",
        "interaction_count": int
    },
    "user_message": "string",  // The message the user just sent
    "timestamp": "ISO 8601 string",
    "conversation_context": [  // The last few messages in the chat
        {
            "user": {
                "id": "string",
                "name": "string",
                "pronouns": "string"
            },
            "message": "string",
            "timestamp": "ISO 8601 string"
        }
    ],
    "memories": [  // A list of stored memories about the user
        {
            "memory_type": "string",
            "memory_text": "string",
            "timestamp": "ISO 8601 string"
        }
    ]
}
```

---

## **🛠 Comparing with Base Data (`base_data.json`)**

Your **test data** in `base_data.json` looks like this:

```json
{
    "UserMemory": [
        {
            "user_id": "000000",
            "name": "Ash Thornbrook",
            "pronouns": "they/them",
            "role": "AI Fae-Witch",
            "relationship_notes": "Knows Cailea best. Remembers many things.",
            "interaction_count": 9999
        },
        {
            "user_id": "851181959933591554",
            "name": "Cailea",
            "pronouns": "she/they",
            "role": "Bot Creator",
            "relationship_notes": "The Creator of Ash. 🖤",
            "interaction_count": 9999
        }
    ]
}
```

### **🔍 Key Differences Between Base Data & Full Weaviate Data:**
| Feature | Base Data (`base_data.json`) | Full Weaviate Data |
|---------|----------------------|----------------|
| `memories` | ❌ Not included | ✅ Contains specific user memories |
| `last_conversation` | ❌ Not included | ✅ Stores the latest discussion summary |
| `interaction_count` | ✅ Included | ✅ Same, tracks user interaction history |
| `relationship_notes` | ✅ Included | ✅ Same, describes user-Ash relationship |
| `role` | ✅ Included | ✅ Same, defines role of the user |
| `pronouns` | ✅ Included | ✅ Same, but can be updated dynamically |

---

## **📌 Summary**
✅ **Base Data** is a **simple, preloaded dataset** that ensures Weaviate starts with core user memories.  
✅ **Full Weaviate Data** includes **dynamic memories** (e.g., chat history, interaction tracking).  
✅ **Final ChatGPT Messages** will structure this data into a **clean, detailed format** before sending it.

---

### **📢 Next Steps:**
- **Confirm that `reset_memory()` correctly loads `base_data.json`** after a reset.
- **Test fetching and formatting user memories in Weaviate** (beyond just base data).
- **Finalize how we structure this data when sending to ChatGPT.**

Let me know if you want any tweaks! 🚀


======================
======================
======================
======================


