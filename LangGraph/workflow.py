from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

#Load API Key
load_dotenv()
api_key = os.getenv("TOGETHER_API_KEY")

# Initialize LLM
llm = ChatOpenAI(
    model="mistral-7b",
    openai_api_base="https://api.together.xyz/v1",
    openai_api_key=os.getenv("TOGETHER_API_KEY"),
)

# Define step 1: Categorizing the question
def categorize_question(state):
    question = state["question"]
    category = llm.predict(f"Categorize this question: {question}")
    return {"category": category, "question": question}

# Define step 2: Store embeddings (Placeholder)
def store_embedding(state):
    return state

# Define step 3: Retrieve relevant context (Placeholder)
def retrieve_context(state):
    return state

# Define step 4: Generate response
def generate_response(state):
    return {"response": f"Generated response for: {state['question']}"}

# Build the LangGraph workflow
workflow = StateGraph()
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
workflow.set_output_node("generate_response")

# Compile the graph
rag_bot = workflow.compile()

# Example: Running the workflow
input_question = {"question": "How do I update my payment info?"}
response = rag_bot.invoke(input_question)
print(response)
