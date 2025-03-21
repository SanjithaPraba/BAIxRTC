from langchain_together import ChatTogether
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import categories
import numpy as np

CATEGORY_LIST = []

# Load API Key
load_dotenv()
api_key = os.getenv("TOGETHER_API_KEY")

# Ensure API key is set
if not api_key:
    raise ValueError("TOGETHER_API_KEY is missing. Please check your .env file.")

# Initialize LLM for Mistral NeMo
llm = ChatTogether(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    together_api_key=api_key,
)

# Define the state schema
class QueryState(BaseModel):
    question: str
    category: str | None = None
    response: str | None = None

# Define step 1: Categorizing the question
def categorize_question(state: QueryState):
    CATEGORY_LIST = categories.main()
    categories_str = ", ".join(CATEGORY_LIST)

    prompt = (
        f"Given the following categories: {categories_str}. "
        f"Categorize the following question: \"{state.question}\". "
        f"Respond with only the category name that best fits the question."
    )

    category = llm.invoke(prompt).content.strip()
    return QueryState(question=state.question, category=category)

# Debugging
if __name__ == "__main__":
    question = input("Enter a question: ")
    state = QueryState(question=question)
    result = categorize_question(state)
    print(result)