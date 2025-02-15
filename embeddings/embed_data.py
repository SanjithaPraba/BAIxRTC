import chromadb

# Create a synchronous ChromaDB client
client = chromadb.HttpClient(base_url='http://ec2-3-147-52-166.us-east-2.compute.amazonaws', port=8080)

# Example: Add and query embeddings
def run_sync_client():
    # Create a collection
    collection = client.create_collection("my-collection")
    
    # Add embeddings to the collection
    collection.add(
        ids=["id1", "id2"],
        embeddings=[[0.1, 0.2], [0.3, 0.4]],
        metadatas=[{"tag": "A"}, {"tag": "B"}],
    )

    # Query the collection
    results = collection.query(
        query_embeddings=[[0.1, 0.2]],
        n_results=2
    )

    print(results)

run_sync_client()
