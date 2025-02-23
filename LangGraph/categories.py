import psycopg2
import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Initialize Mistral LLM
llm = ChatOpenAI(
    model="mistral-7b",
    openai_api_base="https://api.together.xyz/v1",
    openai_api_key=os.getenv("TOGETHER_API_KEY"),
)

# Load environment variables
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Connect to Amazon RDS
conn = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    sslmode="require"
)

def fetch_all_messages():
    with conn.cursor() as cur:
        cur.execute("SELECT message_json FROM slack_data_table;")
        rows = cur.fetchall()
        messages = [json.loads(row[0])["text"] for row in rows]  # Extract only text
    return messages

# Fetch all messages
slack_messages = fetch_all_messages()
print(f"Fetched {len(slack_messages)} messages")

def generate_categories(messages, num_categories=10):
    """Asks the LLM to generate a list of categories from the dataset."""
    prompt = f"""Analyze the following Slack messages and generate {num_categories} distinct categories:
    {messages[:500]}  # Avoid sending too much data
    Categories:"""

    response = llm.predict(prompt).strip()
    categories = response.split("\n")  # Split into a list
    categories = [cat.strip("- ") for cat in categories if cat]  # Clean formatting
    return categories

# Generate 10 categories
categories = generate_categories(slack_messages, num_categories=10)
print("Generated Categories:", categories)



