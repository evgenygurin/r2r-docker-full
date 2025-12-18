"""Database connection and query management"""
import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any

class DatabaseManager:
    """Handles database connections and operations"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE query"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount

    def create_user(self, username: str, email: str, hashed_password: str) -> int:
        """Create new user record"""
        query = "INSERT INTO users (username, email, password) VALUES (?, ?, ?)"
        return self.execute_update(query, (username, email, hashed_password))

    def find_user_by_email(self, email: str) -> Dict[str, Any]:
        """Find user by email address"""
        query = "SELECT * FROM users WHERE email = ?"
        results = self.execute_query(query, (email,))
        return results[0] if results else None
