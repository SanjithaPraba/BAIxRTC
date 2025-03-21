from langgraph.graph import StateGraph
from langchain_together import ChatTogether
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import categories
import pickle
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from query_categorization import categorize_question

# Loading Together API Key
load_dotenv()
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
    # Fetch messages (each item is assumed to be a string)
    all_messages = categories.fetch_all_messages()  # returns a list of strings

    if not all_messages:
        print("No messages found in the database.")
        return state

    texts = []
    metadatas = []
    for item in all_messages:
        # If the item is not a dict, assume it's a string message.
        if isinstance(item, dict):
            message = item.get("message", "")
            category = item.get("category", "Unknown")
        else:
            message = item
            category = "Unknown"  # Default category if not provided

        texts.append(f"Message: {message}\nCategory: {category}")
        metadatas.append({"message": message, "category": category})

    # Initialize embedding model
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Create FAISS vector store (local storage)
    vector_store = FAISS.from_texts(texts, embedding_model, metadatas=metadatas)

    # Save locally using pickle
    with open("local_embeddings.pkl", "wb") as f:
        pickle.dump(vector_store, f)

    print("Embeddings have been stored locally!")
    return state

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
    context = "\n".join([res.metadata["message"] for res in results])
    print(f"Retrieved Context:\n{context}")

    return QueryState(question=state.question, category=state.category, response=context)

    return state


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

    # response = f"Generated response for: {state.question}"
    # return QueryState(question=state.question, category=state.category, response=response)


# Build the LangGraph workflow
workflow = StateGraph(QueryState)  # Initialize with state schema

# Add nodes
workflow.add_node("categorize", categorize_question)
workflow.add_node("create_and_store_embedding", create_and_store_embedding)
workflow.add_node("retrieve_context", retrieve_context)
workflow.add_node("generate_response", generate_response)

# Define edges between nodes
workflow.add_edge("categorize", "create_and_store_embedding")
workflow.add_edge("create_and_store_embedding", "retrieve_context")
workflow.add_edge("retrieve_context", "generate_response")

# Set entry and output points
workflow.set_entry_point("categorize")
workflow.set_finish_point("generate_response")  # <-- FIXED LINE

# Compile the graph
rag_bot = workflow.compile()

# Example: Running the workflow
input_question = QueryState(question="Anybody secure an AirBnB in Seattle?")
response = rag_bot.invoke(input_question)
print(response)