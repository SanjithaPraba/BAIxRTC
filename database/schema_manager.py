from connection_pool import ConnectionPool
import logging
import os
from pathlib import Path
import json
from datetime import datetime #get class from module

class SchemaManager:
    """Handles database schema creation and updates."""

    def __init__(self):
        """Initialize SchemaManager with a connection from ConnectionPool."""
        self.pool = ConnectionPool()
        self.connection = self.pool.get_connection()
        self.cursor = self.connection.cursor()

    def create_tables(self):
        """Create all necessary tables for the Slack bot."""
        self.create_messages_table()
        self.connection.commit()
        logging.info("✅ Database tables created successfully.")

    def create_messages_table(self):
        """Create the messages table with one row per message."""
        self.cursor.execute("""
            CREATE TABLE messages (
                id SERIAL PRIMARY KEY,
                text VARCHAR(100000),
                username VARCHAR(50),
                ts VARCHAR(50),
                team VARCHAR(50),
                category VARCHAR(255)
            );
        """)

    def delete_messages_table(self):
        """Delete the messages table."""
        self.cursor.execute("DROP TABLE IF EXISTS messages;")

    def insert_message(self, message):
        """Insert a message into the messages table."""
        self.cursor.execute("""
            INSERT INTO messages (text, username, ts, team, category)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            message.get("text"),
            message.get("username"),
            message.get("ts"),
            message.get("team"),
            message.get("category")
        ))

    def process_channel_data(self, channel_data):
        """
        Process and insert message data from a list of messages.
        Each JSON object is a standalone message.
        """
        if not isinstance(channel_data, list):
            logging.error("Expected channel_data to be a list.")
            return

        for message in channel_data:
            self.insert_message(message)

    def add_jsons(self, channel_threads_directory: Path):
        """
        Process JSON files from the directory and insert the data into the database.
        Each JSON file is expected to contain a list of message objects.
        """
        if not channel_threads_directory.exists():
            logging.error(f"Directory {channel_threads_directory} does not exist.")
            return

        for json_file in os.listdir(channel_threads_directory):
            if json_file.endswith(".json"):
                file_path = channel_threads_directory / json_file
                with open(file_path, 'r') as f:
                    try:
                        channel_data = json.load(f)
                        self.process_channel_data(channel_data)
                    except json.JSONDecodeError as e:
                        logging.error(f"Error decoding JSON from {file_path}: {e}")
                    except Exception as e:
                        logging.error(f"Error processing file {file_path}: {e}")

        self.connection.commit()
        logging.info("✅ Message data inserted into the database.")

    def close_connection(self):
        """Release the database connection back to the pool."""
        self.cursor.close()
        self.connection.close()
        logging.info("🔌 Database connection closed.")

    #to be used for frontend - get the first and last timestamps, then convert to datetime
    def get_timerange(self):
        self.cursor.execute("SELECT MAX(ts) FROM messages")
        latest_ts = self.cursor.fetchone()[0]
        latest_date = datetime.fromtimestamp(latest_ts)
        self.cursor.execute("SELECT MIN(ts) FROM messages")
        earliest_ts = self.cursor.fetchone()[0]
        earliest_date = datetime.fromtimestamp(earliest_ts)
        return (str(earliest_date), str(latest_date))

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Get the directory where this file (schema_manager.py) is located
    current_dir = Path(__file__).parent

    # Get the parent directory (which contains both 'database' and 'JSON_processing')
    parent_dir = current_dir.parent

    # Build the path to the categorized messages directory
    channel_messages = parent_dir / "JSON_processing" / "data" / "categorized"
    
    schema_manager = SchemaManager()
    schema_manager.delete_messages_table()
    schema_manager.create_tables()
    schema_manager.add_jsons(channel_messages)
    schema_manager.close_connection()