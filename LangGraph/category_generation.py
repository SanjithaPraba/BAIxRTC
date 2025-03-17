import psycopg2
import os
import json
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Initialize Mistral LLM
llm = ChatOpenAI(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    openai_api_base="https://api.together.xyz/v1",
    openai_api_key= os.getenv("TOGETHER_API_KEY"),
)

def generate_categories(messages, num_categories=10):
    """Asks the LLM to generate a list of categories from the dataset."""
    prompt = f"""Analyze the following Slack messages and generate {num_categories} distinct categories:
    {messages[:500]}  # Avoid sending too much data
    Categories:"""

    response = llm.predict(prompt).strip()
    categories = response.split("\n")
    categories = [cat.strip("- ") for cat in categories if cat]
    return categories