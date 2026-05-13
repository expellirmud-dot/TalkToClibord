
# Test Module 3 - Database connection and query utilities
import sqlite3
from contextlib import contextmanager
from typing import List, Tuple, Any

class DatabaseManager:
    """Database manager for SQLite operations.
    
    Provides methods for:
    - Connection management
    - Query execution
    - Transaction handling
    - Data migration
    
    Attributes:
        db_path: Path to the SQLite database file
        connection: Active database connection
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
        
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[Tuple]:
        """Execute a SQL query and return results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def create_table(self, table_name: str, schema: str) -> bool:
        """Create a new table with given schema."""
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
        try:
            self.execute_query(query)
            return True
        except Exception as e:
            print(f"Error creating table: {e}")
            return False
    
    def insert_data(self, table_name: str, data: Dict[str, Any]) -> bool:
        """Insert a record into the specified table."""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        try:
            self.execute_query(query, tuple(data.values()))
            return True
        except Exception as e:
            print(f"Error inserting data: {e}")
            return False
