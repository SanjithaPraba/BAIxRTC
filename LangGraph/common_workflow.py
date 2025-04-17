import os
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_together import ChatTogether
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from .fetch_db_messages import fetch_all_messages

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

# Define the state schema
class QueryState(BaseModel):
    question: str
    category: str | None = None
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
    context = "\n\n".join(documents)

    print(f"Retrieved Context from Chroma:\n{context}")

    return QueryState(
        question=state.question,
        category=state.category,
        response=context
    )


# Define step 4: Generate response
def generate_response(state: QueryState):
    prompt = f"""You are a Slack assistant for RTC, otherwise known as Rewriting the Code. If RTC is ever mentioned, it is always referring to the organization Rewriting the Code. Use the context below to answer the user's question:
        
        Here is the question: {state.question}.
        
        It has been categorized as: {state.category}
        
        Relevant context from previous messages: {state.response}
        
        Please provide a comprehensive and context-aware answer by only using the provided information but DO NOT directly mention that you are referencing the context provided. Treat it as if it is knowledge you are passing along to the user in order to help out. If you don't know the answer, say \"I'm not sure.\" Do not make up details.
        """
    
    # Use the LLM to generate the final answer (using .invoke() as per deprecation notice)
    final_response = llm.invoke(prompt).content.strip() + " Please react with the appropriate emoji to indicate if this was helpful or not."
    
    return QueryState(question=state.question, category=state.category, response=final_response)

def create_and_store_embedding(state: QueryState):
    all_messages = fetch_all_messages()
    texts, metadatas, ids = [], [], []
    for i, item in enumerate(all_messages):
        message = item.get("text", "")
        category = item.get("category", "Unknown")
        texts.append(f"text: {message}\ncategory: {category}")
        metadatas.append({"text": message, "category": category})
        ids.append(f"msg_{i}")
    embeddings = embedding_model.embed_documents(texts)

    collection = chroma_client.get_or_create_collection(name="slack-faqs")
    collection.add(documents=texts, metadatas=metadatas, ids=ids, embeddings=embeddings)

    print(f"Stored {len(texts)} embeddings in ChromaDB.")

    return state, ids

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
        state.category = "should_respond"
    else:
        state.category = "skip"
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
