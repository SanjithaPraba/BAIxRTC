from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import categories
import numpy as np

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

#optional main method for debugging purposes
if __name__ == "__main__":
    question = input("enter a question")
    state = QueryState(question=question)
    result = categorize_question(state)
    