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

