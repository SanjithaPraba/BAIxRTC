import os
from dotenv import load_dotenv
from langchain_together import ChatTogether

# Load API Key
load_dotenv()
api_key = os.getenv("TOGETHER_API_KEY")

# Ensure API key is set
if not api_key:
    raise ValueError("TOGETHER_API_KEY is missing. Please check your .env file.")

# Initialize Mistral LLM
llm = ChatTogether(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    together_api_key=api_key,
)

def generate_categories(messages, num_categories=10):
    """Asks the LLM to generate a list of categories from the dataset."""
    prompt = f"""Analyze the following Slack messages and generate {num_categories} distinct categories:
    {messages[:500]}  # Avoid sending too much data
    Categories:"""

    response = llm.invoke(prompt).content.strip()
    categories = response.split("\n")
    categories = [cat.strip("- ") for cat in categories if cat]
    return categories
