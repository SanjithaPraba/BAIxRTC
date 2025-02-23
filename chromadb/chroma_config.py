import chromadb
chroma_client = chromadb.HttpClient(host='18.116.43.210', port=8000)
response = chroma_client.heartbeat()
print(response)