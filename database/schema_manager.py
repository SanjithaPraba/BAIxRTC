from connection_pool import ConnectionPool
import logging

class SchemaManager:
    """Handles database schema creation and updates."""

    def __init__(self):
        """Initialize SchemaManager with a connection from ConnectionPool."""
        self.pool = ConnectionPool()
        self.connection = self.pool.get_connection()
        self.cursor = self.connection.cursor()

    def create_tables(self):
        """Create all necessary tables for the Slack bot."""
        self._create_messages_table()
        self._create_faqs_table()
        self._create_bot_responses_table()
        self.connection.commit()
        logging.info("✅ Database tables created successfully.")

    def _create_messages_table(self):
        """Create the messages table."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50),
                user_name VARCHAR(100),
                message_text TEXT NOT NULL,
                intent VARCHAR(100),
                entities JSONB,
                ts VARCHAR(50) UNIQUE NOT NULL,
                thread_ts VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    def _create_faqs_table(self):
        """Create the faqs table."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS faqs (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                keywords TEXT[],
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    def _create_bot_responses_table(self):
        """Create the bot_responses table."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_responses (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50),
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                ts VARCHAR(50) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    def close_connection(self):
        """Release the database connection back to the pool."""
        self.cursor.close()
        self.connection.close()
        logging.info("🔌 Database connection closed.")

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    schema_manager = SchemaManager()
    schema_manager.create_tables()
    schema_manager.close_connection()