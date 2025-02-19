from connection_pool import ConnectionPool
import logging
import os
from pathlib import Path
import json

class SchemaManager:
    """Handles database schema creation and updates."""

    def __init__(self):
        """Initialize SchemaManager with a connection from ConnectionPool."""
        self.pool = ConnectionPool()
        self.connection = self.pool.get_connection()
        self.cursor = self.connection.cursor()

    def create_tables(self):
        """Create all necessary tables for the Slack bot."""
        self.create_threads_table()
        self.connection.commit()
        logging.info("✅ Database tables created successfully.")

    def create_threads_table(self):
        """Create the messages table."""
        self.cursor.execute("""
            CREATE TABLE threads (
                id SERIAL PRIMARY KEY,                
                thread_ts VARCHAR(50),               
                message VARCHAR(100000),                         
                replies JSONB,                         
                reply_count INT                        
            );
        """)
    def delete_threads_table(self):
        """Delete the threads table."""
        self.cursor.execute("DROP TABLE IF EXISTS threads;")

    def insert_message(self, message):
        """Insert a message (thread parent) into the threads table."""
        message_text = message.get("text")
        self.cursor.execute("""
            INSERT INTO threads (thread_ts, message, replies, reply_count)
            VALUES (%s, %s, %s, %s)
        """, (
            message.get("ts"),                         
            message_text,
            json.dumps([]),                            
            0                                     
        ))

    def insert_replies(self, thread_ts, replies):
        """Insert replies into the threads table, updating the replies and reply_count."""
        if replies:
            reply_count = len(replies)                 
            self.cursor.execute("""
                UPDATE threads
                SET replies = %s, reply_count = %s
                WHERE thread_ts = %s
            """, (
                json.dumps(replies),              
                reply_count,                          
                thread_ts                           
            ))

    def process_channel_data(self, channel_data):
        """Process and insert thread data from a list of threads."""
        if not isinstance(channel_data, list):
            logging.error("Expected channel_data to be a list.")
            return

        for thread in channel_data:
            if "message" in thread:
                self.insert_message(thread["message"]) #parent msg
                replies = thread.get("replies", [])
                if replies:
                    formatted_replies = []
                    for reply in replies:
                        formatted_replies.append({"text": reply.get("text")})
                    self.insert_replies(thread["message"]["ts"], formatted_replies)


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
    channel_threads = Path("JSON_processing/data/channel_threads")
    schema_manager = SchemaManager()
    schema_manager.delete_threads_table()
    schema_manager.create_tables()
    schema_manager.add_jsons(channel_threads)
    schema_manager.close_connection()