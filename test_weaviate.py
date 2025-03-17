import weaviate

client = weaviate.connect_to_local()

# Fetch the schema from Weaviate
schema = client.collections.get("LongTermMemories").config.get()
print(schema)
client.close()
