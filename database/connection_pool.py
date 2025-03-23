import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

class ConnectionPool:
    """Manages database connections efficiently."""

    def __init__(self):
        """Initialize the connection pool with database credentials."""
        self.host = os.getenv("DB_HOST")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.port = os.getenv("DB_PORT")
        print("Host:", self.host)
        print("Database:", self.database)
        print("User:", self.user)
        print("Port:", self.port)
        self.connection = None  # Placeholder for active connection

    def get_connection(self):
        """Establish and return a new database connection."""
        if self.connection is None or self.connection.closed:
            self.connection = psycopg2.connect(
                host=self.host,
                port = self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
        return self.connection

    def close_connection(self):
        """Close the active database connection."""
        if self.connection and not self.connection.closed:
            self.connection.close()
            print("✅ Database connection closed.")