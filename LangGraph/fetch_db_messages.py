import psycopg2
import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_together import ChatTogether


# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from LangGraph.connection_pool import ConnectionPool

parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from database.connection_pool import ConnectionPool

pool = ConnectionPool()

def fetch_all_messages():
    """
    Pulls everything from the 'messages' table and returns a list of dictionaries,
    each containing the 'text' and 'category' fields.
    """
    conn = pool.get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM messages;")
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]

        messages = []
        for row in rows:
            record = dict(zip(colnames, row))
            messages.append({
                "text": record.get("text"),
                "category": record.get("category")
            })

    return messages


def main():
    slack_messages = fetch_all_messages()
    print(f"Fetched {len(slack_messages)} messages.")
    return slack_messages