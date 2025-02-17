from connection_pool import ConnectionPool
import json

class DataCRUD:
    """Handles CRUD operations for the database."""

    def __init__(self):
        """Initialize the DataAccess class with a database connection."""
        self.pool = ConnectionPool()
        self.connection = self.pool.get_connection()
        self.cursor = self.connection.cursor()

    def store_message(self, user_id: str, user_name: str, message: str, intent: str, entities: dict, ts: str, thread_ts: str = None):
        """Insert a parsed Slack message into the messages table."""
        self.cursor.execute("""
            INSERT INTO messages (user_id, user_name, message_text, intent, entities, ts, thread_ts)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ts) DO NOTHING;
        """, (user_id, user_name, message, intent, json.dumps(entities), ts, thread_ts))
        self.connection.commit()

    def store_faq(self, question: str, answer: str, keywords: list):
        """Insert a predefined FAQ into the faqs table."""
        self.cursor.execute("""
            INSERT INTO faqs (question, answer, keywords)
            VALUES (%s, %s, %s);
        """, (question, answer, keywords))
        self.connection.commit()

    def store_bot_response(self, user_id: str, user_message: str, bot_response: str, ts: str):
        """Log a chatbot interaction in the bot_responses table."""
        self.cursor.execute("""
            INSERT INTO bot_responses (user_id, user_message, bot_response, ts)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (ts) DO NOTHING;
        """, (user_id, user_message, bot_response, ts))
        self.connection.commit()

    def fetch_messages(self):
        """Retrieve all messages from the messages table."""
        self.cursor.execute("SELECT * FROM messages;")
        rows = self.cursor.fetchall()
        return rows

    def close_connection(self):
        """Close the database connection."""
        self.cursor.close()
        self.connection.close()