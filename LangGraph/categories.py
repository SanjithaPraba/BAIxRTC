import psycopg2
import os
import json
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from RTC_db.connection_pool import ConnectionPool

# Initialize Mistral LLM
llm = ChatOpenAI(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    openai_api_base="https://api.together.xyz/v1",
    openai_api_key= os.getenv("TOGETHER_API_KEY"),
)

pool = ConnectionPool()

def fetch_all_messages():
    """
    Pulls everything from the 'threads' table.
    Parses the replies (if JSON) and returns a list of message texts.
    """
    conn = pool.get_connection()
    with conn.cursor() as cur:
        # Grab all columns
        cur.execute("SELECT * FROM threads;")
        rows = cur.fetchall()

        # Get column names for reference (if you want them)
        colnames = [desc[0] for desc in cur.description]

        # Build a list of message texts
        messages = []
        for row in rows:
            record = dict(zip(colnames, row))

            # If 'replies' is a JSON string, parse it
            if "replies" in record and record["replies"] and isinstance(record["replies"], str):
                try:
                    record["replies"] = json.loads(record["replies"])
                except json.JSONDecodeError:
                    pass  # or handle error

            # Append the main message text
            # (This uses the 'message' column from 'threads')
            messages.append(record["message"])

    return messages

# Fetch all messages



def generate_categories(messages, num_categories=10):
    """Asks the LLM to generate a list of categories from the dataset."""
    prompt = f"""Analyze the following Slack messages and generate {num_categories} distinct categories:
    {messages[:500]}  # Avoid sending too much data
    Categories:"""

    response = llm.predict(prompt).strip()
    categories = response.split("\n")
    categories = [cat.strip("- ") for cat in categories if cat]
    return categories


def main():
    slack_messages = fetch_all_messages()
    # Generate 10 categories
    print(f"Fetched {len(slack_messages)} messages.")
    categories = generate_categories(slack_messages, num_categories=10)
    return categories


