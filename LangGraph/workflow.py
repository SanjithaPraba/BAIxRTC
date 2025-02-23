from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
import categories

CATEGORY_LIST = []

# Load API Key
load_dotenv()
api_key = os.getenv("TOGETHER_API_KEY")

# Initialize LLM
llm = ChatOpenAI(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    openai_api_base="https://api.together.xyz/v1",
    openai_api_key=api_key,
)

# Define the state schema
class QueryState(BaseModel):
    question: str
    category: str | None = None
    response: str | None = None

# Define step 1: Categorizing the question
def categorize_question(state: QueryState):
    # Generate 10 categories
    #Will eventually be a part of "Update" workflow
    #NEED TO CHANGE THIS LINE LATER TO SET CATEGORY_LIST FROM DATABASE AND UPDATE CATEGORIES IN ANOTHER SCRIPT
    CATEGORY_LIST = categories.main()

    #predict is deprecated but this is likely going to end up in a script of its own anyway so we can fix it then
    categories_str = ", ".join(CATEGORY_LIST)

    # Compose a prompt that includes the list of available categories and the question
    prompt = (
        f"Given the following categories: {categories_str}. "
        f"Categorize the following question: \"{state.question}\". "
        f"Respond with only the category name that best fits the question."
    )

    # Use the LLM to determine the category
    category = llm.predict(prompt).strip()
    return QueryState(question=state.question, category=category)


# Define step 2: Store embeddings (Placeholder) --> Will move into "UPDATE" workflow
def create_and_store_embedding(state: QueryState):
    all_messages = categories.fetch_all_messages()
    
    texts = [f"Message: {item['message']}\nCategory: {item['category']}" for item in all_messages]
    metadatas = [{"message": item["message"], "category": item["category"]} for item in all_messages]

    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    # Create (or load) a Chroma vector store collection.
    vector_store = Chroma.from_texts(
        texts, 
        embedding_model, 
        metadatas=metadatas, 
        collection_name="messages_collection"
    )

    print("Embeddings have been stored in Chroma!")
    return vector_store

    return state


# Define step 3: Retrieve relevant context (Placeholder)
def retrieve_context(state: QueryState):
    return state


# Define step 4: Generate response
def generate_response(state: QueryState):
    response = f"Generated response for: {state.question}"
    return QueryState(question=state.question, category=state.category, response=response)


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