"""Database schema initialization and migration."""

import sqlite3
import logging
from .connection import get_db_connection, close_connection

logger = logging.getLogger(__name__)


def init_db(db_path: str = None) -> None:
    """
    Initialize or update the SQLite database with the 'transactions' table.

    Creates the table if it doesn't exist and adds missing columns to existing tables.
    
    Args:
        db_path: Optional custom database path (for testing). If None, uses production DATABASE_PATH.
    """
    conn = None
    try:
        conn = get_db_connection(db_path=db_path)
        cursor = conn.cursor()

        # Create the table with the correct schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                categorie TEXT NOT NULL,
                sous_categorie TEXT,
                description TEXT,
                montant REAL NOT NULL,
                date TEXT NOT NULL,
                source TEXT DEFAULT 'Manuel',
                recurrence TEXT,
                date_fin TEXT
            )
        """)

        # Update the table if it exists with old schema
        # Add 'source' column if missing
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN source TEXT DEFAULT 'Manuel'")
            logger.info("Added 'source' column to transactions table")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add 'recurrence' column if missing
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN recurrence TEXT DEFAULT 'Aucune'")
            logger.info("Added 'recurrence' column to transactions table")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add 'date_fin' column if missing
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN date_fin TEXT DEFAULT ''")
            logger.info("Added 'date_fin' column to transactions table")
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.commit()
        logger.info("Database initialized successfully")

    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        close_connection(conn)


def migrate_database_schema() -> None:
    """
    Migrate database schema from old column names to new ones.

    Handles migration from French column names (Catégorie, Sous-catégorie, etc.)
    to English-friendly names (categorie, sous_categorie, etc.).
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if table exists with old schema
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [col[1] for col in cursor.fetchall()]

        # If old columns exist, migrate
        if "Catégorie" in columns or "Sous-catégorie" in columns:
            logger.info("Migrating database schema...")

            # Create new table with correct schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    categorie TEXT NOT NULL,
                    sous_categorie TEXT,
                    description TEXT,
                    montant REAL NOT NULL,
                    date TEXT NOT NULL,
                    source TEXT DEFAULT 'Manuel',
                    recurrence TEXT,
                    date_fin TEXT
                )
            """)

            # Copy data mapping old names to new
            cursor.execute("""
                INSERT INTO transactions_new
                (id, type, categorie, sous_categorie, description, montant, date, source, recurrence, date_fin)
                SELECT
                    id,
                    type,
                    "Catégorie" AS categorie,
                    "Sous-catégorie" AS sous_categorie,
                    description,
                    montant,
                    "Date" AS date,
                    COALESCE("Source", 'Manuel') AS source,
                    COALESCE("Récurrence", 'Aucune') AS recurrence,
                    date_fin
                FROM transactions
            """)

            # Drop old table
            cursor.execute("DROP TABLE transactions")

            # Rename new table
            cursor.execute("ALTER TABLE transactions_new RENAME TO transactions")

            conn.commit()
            logger.info("Migration completed successfully!")
        else:
            logger.info("Schema is already up to date")

    except Exception as e:
        logger.error(f"Migration error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        close_connection(conn)


def create_indexes() -> None:
    """Create indexes for frequently queried columns."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Index on date for chronological queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_date
            ON transactions(date DESC)
        """)

        # Index on type for filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_type
            ON transactions(type)
        """)

        # Index on categorie for filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_categorie
            ON transactions(categorie)
        """)

        conn.commit()
        logger.info("Database indexes created successfully")

    except sqlite3.Error as e:
        logger.error(f"Index creation failed: {e}")
        if conn:
            conn.rollback()
    finally:
        close_connection(conn)
