from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from pydantic import BaseModel


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
    #predict is deprecated but this is likely going to end up in a script of its own anyway so we can fix it then
    category = llm.predict(f"Categorize this question: {state.question}") 
    return QueryState(question=state.question, category=category)


# Define step 2: Store embeddings (Placeholder)
def store_embedding(state: QueryState):
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
workflow.add_node("store_embedding", store_embedding)
workflow.add_node("retrieve_context", retrieve_context)
workflow.add_node("generate_response", generate_response)

# Define edges between nodes
workflow.add_edge("categorize", "store_embedding")
workflow.add_edge("store_embedding", "retrieve_context")
workflow.add_edge("retrieve_context", "generate_response")

# Set entry and output points
workflow.set_entry_point("categorize")
workflow.set_finish_point("generate_response")  # <-- FIXED LINE

# Compile the graph
rag_bot = workflow.compile()

# Example: Running the workflow
input_question = QueryState(question="How do I update my payment info?")
response = rag_bot.invoke(input_question)
print(response)