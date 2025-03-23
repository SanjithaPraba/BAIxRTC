from connection_pool import ConnectionPool
import logging
import os
from pathlib import Path
import json
from LangGraph import message_categorizer

class SchemaManager:
    """Handles database schema creation and updates."""

    def __init__(self):
        """Initialize SchemaManager with a connection from ConnectionPool."""
        self.pool = ConnectionPool()
        self.connection = self.pool.get_connection()
        self.cursor = self.connection.cursor()
        self.categorizer = message_categorizer.MessageCategorizer(Path("/Users/emilyzhou/PycharmProjects/BAIxRTC/database/categories.json"))

    def create_tables(self):
        """Create all necessary tables for the Slack bot."""
        self.create_threads_table()
        self.connection.commit()
        logging.info("✅ Database tables created successfully.")

    # t ype: original question, reply, follow up question
    def create_threads_table(self):
        self.cursor.execute("""
            CREATE TABLE threads (
                id SERIAL PRIMARY KEY,
                thread_ts VARCHAR(50), 
                message VARCHAR(100000),
                prev_message_id INT,
                category VARCHAR(100)
            );
        """)

    def delete_threads_table(self):
        """Delete the threads table."""
        self.cursor.execute("DROP TABLE IF EXISTS threads;")
        self.connection.commit()
        print("✅ threads table cleared")

    def insert_message(self, message, prev_msg_data):
        message_text = message.get("text")
        category = self.categorizer.classify(message_text)

        self.cursor.execute("""
            INSERT INTO threads (thread_ts, message, prev_message_id, category)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            prev_msg_data[0],   #thread id
            message_text,
            prev_msg_data[1],   #prev msg id
            category            #generated
        ))
        prev_msg_data[0] = self.cursor.fetchone() #store msg id to pass on

    def process_channel_data(self, channel_data):
        """Process and insert thread data from a list of threads."""
        if not isinstance(channel_data, list):
            logging.error("Expected channel_data to be a list.")
            return

        prev_msg_data = [None, None]  # holds thread_ts, prev_msg_id
        for thread in channel_data:
            if "message" in thread:
                prev_msg_data[0] = thread["message"]["ts"]  # thread_ts
                self.insert_message(thread["message"], prev_msg_data)  # ✅ Fixed method name
                replies = thread.get("replies", [])
                if replies:
                    for reply in replies:
                        self.insert_message(reply, prev_msg_data)

    def add_jsons(self, channel_threads_directory: Path): #adapted after rtc-parse code
        """Process JSON files from the directory and insert the data into the database."""
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
        logging.info("✅ Thread data inserted into the database.")


    def close_connection(self):
        """Release the database connection back to the pool."""
        self.cursor.close()
        self.connection.close()
        logging.info("🔌 Database connection closed.")

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    channel_threads = Path("../JSON_processing/data/channel_threads")
    schema_manager = SchemaManager()
    schema_manager.delete_threads_table()
    schema_manager.create_tables()
    schema_manager.add_jsons(channel_threads)
    schema_manager.close_connection()