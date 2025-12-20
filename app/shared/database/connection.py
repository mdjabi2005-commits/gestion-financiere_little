"""Database connection management."""

import sqlite3
import logging
from typing import Optional
from config.database_config import DATABASE_PATH, DATABASE_TIMEOUT

logger = logging.getLogger(__name__)


def get_db_connection(timeout: float = DATABASE_TIMEOUT, db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Get a SQLite database connection.

    Args:
        timeout: Connection timeout in seconds
        db_path: Optional custom database path (for testing). If None, uses DATABASE_PATH from config.

    Returns:
        SQLite connection object

    Raises:
        sqlite3.Error: If connection fails
    """
    # Use custom path if provided (for tests), otherwise use production DATABASE_PATH
    actual_db_path = db_path if db_path is not None else DATABASE_PATH
    
    try:
        conn = sqlite3.connect(actual_db_path, timeout=max(timeout, 30.0))
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
        conn.execute("PRAGMA journal_mode = WAL")  # Enable WAL mode for concurrent access
        conn.execute("PRAGMA busy_timeout = 30000")  # 30 second busy timeout
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise


def close_connection(conn: Optional[sqlite3.Connection]) -> None:
    """
    Safely close a database connection.

    Args:
        conn: SQLite connection to close
    """
    if conn:
        try:
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Error closing connection: {e}")


def execute_query(
    query: str,
    params: tuple = (),
    fetch_one: bool = False,
    fetch_all: bool = False,
    commit: bool = False
):
    """
    Execute a database query with automatic connection management.

    Args:
        query: SQL query to execute
        params: Query parameters
        fetch_one: Return single row
        fetch_all: Return all rows
        commit: Commit changes after execution

    Returns:
        Query results or None
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)

        if commit:
            conn.commit()

        if fetch_one:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()

        return cursor

    except sqlite3.Error as e:
        logger.error(f"Query execution failed: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        close_connection(conn)
