import os
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_together import ChatTogether
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
import database
from .fetch_db_messages import fetch_all_messages
from collections import Counter
from database.schema_manager import SchemaManager
import json
import uuid

# Load env
load_dotenv(dotenv_path='./.env')
CHROMA_HOST = os.getenv("CHROMA_HOST")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
api_key = os.getenv("TOGETHER_API_KEY")

# Ensure ChromaDB is running on your EC2
if not CHROMA_HOST:
    raise ValueError("CHROMA_HOST not set")
if not CHROMA_PORT:
    raise ValueError("CHROMA_PORT not set")

# Ensure API key is set
if not api_key:
    raise ValueError("TOGETHER_API_KEY is missing. Please check your .env file.")

# Initializing LLM + Embedding
llm = ChatTogether(model="mistralai/Mistral-7B-Instruct-v0.2", together_api_key=api_key)
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
collection = chroma_client.get_or_create_collection(name="slack-faqs")

# Define the query state schema
class QueryState(BaseModel):
    question: str
    category: str | None = None  # actual question category (used for escalation)
    intent: str | None = None  # 'should_respond' or 'skip'
    response: str | None = None

# Retrieve relevant context from ChromaDB
def retrieve_context(state: QueryState):
    # Query Chroma for relevant messages
    results = collection.query(
        query_texts=[state.question],
        n_results=20  # try 20 for more context (increasing helps the bot ! it's able to grab the appropriate channels :D)
    )

    # Join retrieved documents
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    print("Retrieved metadatas:", metadatas[0])

    # Assign the category from top result (you could do voting logic if needed)
    # extracted_category = metadatas[0].get("category") if metadatas else None
    # state.category = extracted_category
    context = "\n\n".join(documents)

    # Extract all categories from the top 20 results
    categories = [meta.get("category") for meta in metadatas if meta.get("category")]

    # Use majority voting to determine most relevant category
    category_counts = Counter(categories)
    most_common_category, count = category_counts.most_common(1)[0] if category_counts else (None, 0)

    print(f"Category votes: {category_counts}")
    print(f"Chosen category: {most_common_category}")

    # Assign the best category based on majority
    state.category = most_common_category

    print(f"context from chroma: {context}")
    print(f"Retrieved category: {state.category}")

    return QueryState(
        question=state.question,
        intent = state.intent,
        category=state.category,
        response=context
    )


# Define step 4: Generate response
def generate_response(state: QueryState):
    prompt = f"""You are a Slack assistant for RTC, otherwise known as Rewriting the Code. If RTC is ever mentioned, it is always referring to the organization Rewriting the Code. Use the context below to answer the user's question:
        
        Here is the question: {state.question}.
        
        It has been categorized as: {state.category}
        
        Relevant context from previous messages: {state.response}
        
        Please provide a comprehensive and context-aware answer by only using the provided information but DO NOT directly mention that you are referencing the context provided. Treat it as if it is knowledge you are passing along to the user in order to help out. DO NOT  If you don't know the answer, say \"I'm not sure.\" Do not make up details.
        """
    
    # Use the LLM to generate the final answer (using .invoke() as per deprecation notice)
    final_response = llm.invoke(prompt).content.strip() + " Please react with the appropriate emoji to indicate if this was helpful or not."
    
    return QueryState(question=state.question, category=state.category, intent=state.intent, response=final_response)

def create_and_store_embedding(files: list):
    all_messages = []

    # Load messages from uploaded files
    for file in files:
        file.seek(0)
        raw = file.read().decode("utf-8")
        parsed = json.loads(raw)
        all_messages.extend(parsed)

    texts, metadatas, ids = [], [], []

    for i, item in enumerate(all_messages):
        message = item.get("text", "")
        category = item.get("category", "Unknown")

        # same formatting logic as original create_and_store_embedding
        formatted = f"text: {message}\ncategory: {category}"
        texts.append(formatted)
        metadatas.append({"text": message, "category": category})
        ids.append(str(uuid.uuid4()))

    # Embed and store
    embeddings = embedding_model.embed_documents(texts)
    collection = chroma_client.get_or_create_collection(name="slack-faqs")
    collection.add(documents=texts, metadatas=metadatas, ids=ids, embeddings=embeddings)

    print(f"✅ Stored {len(texts)} embeddings from uploaded files in ChromaDB.")

# def create_and_store_embedding(state: QueryState):
#     all_messages = fetch_all_messages()
#     texts, metadatas, ids = [], [], []
#     for i, item in enumerate(all_messages):
#         message = item.get("text", "")
#         category = item.get("category", "Unknown")
#         texts.append(f"text: {message}\ncategory: {category}")
#         metadatas.append({"text": message, "category": category})
#         ids.append(f"msg_{i}")
#     embeddings = embedding_model.embed_documents(texts)
#
#     collection = chroma_client.get_or_create_collection(name="slack-faqs")
#     collection.add(documents=texts, metadatas=metadatas, ids=ids, embeddings=embeddings)
#
#     print(f"Stored {len(texts)} embeddings in ChromaDB.")
#
#     return state, ids

def delete_chroma_by_date(start_ts, end_ts):
    chroma_client = chromadb.HttpClient(host="localhost", port=8000)
    collection = chroma_client.get_or_create_collection("rtc")
    results = collection.get(include=["metadatas", "documents"])

    ids_to_delete = [
        doc_id for doc_id, metadata in zip(results['ids'], results['metadatas'])
        if metadata.get("timestamp") and start_ts <= metadata["timestamp"] <= end_ts
    ]

    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
        print(f"Deleted {len(ids_to_delete)} entries from Chroma between {start_ts}–{end_ts}")
        return len(ids_to_delete)
    else:
        print("No entries matched ChromaDB deletion range.")
        return 0


def should_respond(state: QueryState) -> QueryState:
    decision_prompt = f"""
You are a Slack bot that only responds to valid support questions.
Given the message below, determine if it's a question the bot should respond to:

Message:
{state.question}

Answer with ONLY 'yes' or 'no'. Do not explain.
"""
    answer = llm.invoke(decision_prompt).content.strip().lower()
    if answer.startswith("yes"):
        state.intent = "should_respond"
    else:
        state.intent = "skip"
    return state

def inspect_embeddings(ids=None):
    collection = chroma_client.get_or_create_collection(name="slack-faqs")

    # Get all if no specific IDs provided
    if ids is None:
        data = collection.get(include=["embeddings", "documents", "metadatas"])
    else:
        data = collection.get(ids=ids, include=["embeddings", "documents", "metadatas"])

    for doc, meta, embed in zip(data["documents"], data["metadatas"], data["embeddings"]):
        print("Document:", doc)
        print("Metadata:", meta)
        print("Embedding (first 5 dims):", embed[:5])
        print("------")

    return data
