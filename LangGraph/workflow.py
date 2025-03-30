from dotenv import load_dotenv
# Loading Together API Key and Chroma Host and Port
load_dotenv(dotenv_path="./.env")

from langgraph.graph import StateGraph
from langchain_together import ChatTogether
import os
from pydantic import BaseModel
from fetch_db_messages import fetch_all_messages
import pickle
import chromadb
from chromadb import HttpClient
from chromadb.config import Settings
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

api_key = os.getenv("TOGETHER_API_KEY")

# Ensure API key is set
if not api_key:
    raise ValueError("TOGETHER_API_KEY is missing. Please check your .env file.")

# Initialize LLM
llm = ChatTogether(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    together_api_key=api_key,
)

# Define the state schema
class QueryState(BaseModel):
    question: str
    category: str | None = None
    response: str | None = None

# Define step 2: Store embeddings (Placeholder) --> Will move into "UPDATE" workflow and store in Chroma rather than local vector store FAISS
def create_and_store_embedding(state: QueryState):
    # Fetch messages (each item is a dictionary containing 'text' and 'category')
    all_messages = fetch_all_messages()  # returns a list of dicts
    # why is it not returning a list of dicts

    if not all_messages:
        print("No messages found in the database.")
        return state

    texts = []
    metadatas = []
    ids = []
    i = 0
    for item in all_messages:
        # Extract message text and category from the dictionary.
        message = item.get("text", "")
        category = item.get("category", "Unknown")

        texts.append(f"text: {message}\ncategory: {category}")
        metadatas.append({"text": message, "category": category})
        ids.append(f"msg_{i}")
        i+=1

    # Initialize embedding model
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    # Step 1: Embed the texts
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    embeddings = embedding_model.embed_documents(texts)

    # Fetch host and port from env
    CHROMA_HOST = os.getenv("CHROMA_HOST")
    CHROMA_PORT = os.getenv("CHROMA_PORT")

    print("CHROMA_HOST:", repr(CHROMA_HOST))
    print("CHROMA_PORT:", repr(CHROMA_PORT))

    # Step 2: Connect to ChromaDB running on your EC2 (update host/port if needed)
    if not CHROMA_HOST:
        raise ValueError("CHROMA_HOST not set")
    if not CHROMA_PORT:
        raise ValueError("CHROMA_PORT not set")

    print(f"Connecting to Chroma at http://{CHROMA_HOST}:{CHROMA_PORT}")
    # Initialize the client with settings
    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

    # Step 3: Create or get a collection
    collection = chroma_client.get_or_create_collection(name="slack-faqs")

    print(f"Number of texts: {len(texts)}")
    print(f"Number of metadatas: {len(metadatas)}")
    print(f"Number of ids: {len(ids)}")
    print(f"Number of embeddings: {len(embeddings)}")

    # Step 4: Add the embeddings
    collection.add(
        documents=texts,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings
    )

    print(f"{len(texts)} embeddings have been stored in ChromaDB on EC2!")
    return state


# Define step 3: Retrieve relevant context (Placeholder)
def retrieve_context(state: QueryState):
    # Load stored embeddings
    with open("local_embeddings.pkl", "rb") as f:
        vector_store = pickle.load(f)

    # Generate embedding for the query
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    query_embedding = embedding_model.embed_query(state.question)

    # Search for relevant messages
    results = vector_store.similarity_search_by_vector(query_embedding, k=3)  # Top 3 matches

    # Format results for LLM response
    context = "\n".join([res.metadata["text"] for res in results])
    print(f"Retrieved Context:\n{context}")

    return QueryState(question=state.question, category=state.category, response=context)


# Define step 4: Generate response
def generate_response(state: QueryState):

    # Compose a detailed prompt incorporating the question, its category, and retrieved context.
    prompt = (
        f"You are a helpful assistant. "
        f"Here is the question: \"{state.question}\".\n\n"
        f"It has been categorized as: \"{state.category}\".\n\n"
        f"Relevant context from previous messages:\n{state.response}\n\n"
        f"Based on the above, please provide a comprehensive and context-aware answer."
    )
    
    # Use the LLM to generate the final answer (using .invoke() as per deprecation notice)
    final_response = llm.invoke(prompt).content.strip()
    
    return QueryState(question=state.question, category=state.category, response=final_response)

# Build the LangGraph workflow
workflow = StateGraph(QueryState)  # Initialize with state schema

# Add nodes
#workflow.add_node("categorize", categorize_question)
workflow.add_node("create_and_store_embedding", create_and_store_embedding)
workflow.add_node("retrieve_context", retrieve_context)
workflow.add_node("generate_response", generate_response)

# Define edges between nodes
#workflow.add_edge("categorize", "create_and_store_embedding")
workflow.add_edge("create_and_store_embedding", "retrieve_context")
workflow.add_edge("retrieve_context", "generate_response")

# Set entry and output points
workflow.set_entry_point("create_and_store_embedding")
workflow.set_finish_point("generate_response")  # <-- FIXED LINE

# Compile the graph
rag_bot = workflow.compile()

# Example: Running the workflow
input_question = QueryState(question="Does RTC have affinity groups? If so, for what groups?")
response = rag_bot.invoke(input_question)
print(response)