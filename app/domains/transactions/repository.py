"""Repository pattern for database operations."""

import sqlite3
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import date
from shared.database import get_db_connection
from .models import Transaction
from shared.exceptions import DatabaseError
from config.logging_config import get_logger

logger = get_logger(__name__)


class TransactionRepository:
    """Repository for transaction database operations."""

    @staticmethod
    def get_all(sort_by: str = "date", ascending: bool = False) -> pd.DataFrame:
        """
        Get all transactions as DataFrame.

        Args:
            sort_by: Column to sort by
            ascending: Sort order

        Returns:
            DataFrame with all transactions
        """
        conn = None
        try:
            conn = get_db_connection()
            query = "SELECT * FROM transactions"
            df = pd.read_sql_query(query, conn)

            if not df.empty and sort_by in df.columns:
                df = df.sort_values(by=sort_by, ascending=ascending)

            return df

        except sqlite3.Error as e:
            logger.error(f"Error fetching transactions: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_by_id(transaction_id: int) -> Optional[Transaction]:
        """
        Get transaction by ID.

        Args:
            transaction_id: Transaction ID

        Returns:
            Transaction object or None
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
            row = cursor.fetchone()

            if row:
                return Transaction.from_row(row)
            return None

        except sqlite3.Error as e:
            logger.error(f"Error fetching transaction {transaction_id}: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def insert(transaction: Transaction) -> Optional[int]:
        """
        Insert new transaction with normalized categories.

        Args:
            transaction: Transaction to insert

        Returns:
            ID of inserted transaction or None on error
        """
        from domains.transactions.service import normalize_category, normalize_subcategory

        logger.info(f"Inserting transaction: {transaction.description[:50] if transaction.description else 'N/A'}")
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Normalize category and subcategory
            normalized_category = normalize_category(transaction.categorie)
            normalized_subcategory = normalize_subcategory(transaction.sous_categorie)

            cursor.execute("""
                INSERT INTO transactions
                (type, categorie, sous_categorie, description, montant, date, source, recurrence, date_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction.type,
                normalized_category,
                normalized_subcategory,
                transaction.description,
                transaction.montant,
                transaction.date.isoformat() if isinstance(transaction.date, date) else transaction.date,
                transaction.source,
                transaction.recurrence,
                transaction.date_fin.isoformat() if transaction.date_fin and isinstance(transaction.date_fin, date) else transaction.date_fin
            ))

            conn.commit()
            transaction_id = cursor.lastrowid
            logger.info(f"Transaction inserted successfully: ID={transaction_id}, Amount={transaction.montant}€")
            return transaction_id

        except sqlite3.Error as e:
            logger.error(f"Error inserting transaction: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise DatabaseError(f"Failed to insert transaction: {e}") from e
        finally:
            if conn:
                conn.close()

    @staticmethod
    def insert_batch(transactions: List[Transaction]) -> int:
        """
        Insert multiple transactions with normalized categories.

        Args:
            transactions: List of transactions to insert

        Returns:
            Number of transactions inserted
        """
        from domains.transactions.service import normalize_category, normalize_subcategory

        logger.info(f"Inserting batch of {len(transactions)} transactions")
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Normalize categories for all transactions
            data = [(
                t.type,
                normalize_category(t.categorie),
                normalize_subcategory(t.sous_categorie),
                t.description,
                t.montant,
                t.date.isoformat() if isinstance(t.date, date) else t.date,
                t.source,
                t.recurrence,
                t.date_fin.isoformat() if t.date_fin and isinstance(t.date_fin, date) else t.date_fin
            ) for t in transactions]

            cursor.executemany("""
                INSERT INTO transactions
                (type, categorie, sous_categorie, description, montant, date, source, recurrence, date_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)

            conn.commit()
            count = cursor.rowcount
            logger.info(f"Batch insert successful: {count} transactions added")
            return count

        except sqlite3.Error as e:
            logger.error(f"Error inserting batch: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise DatabaseError(f"Failed to insert batch of {len(transactions)} transactions: {e}") from e
        finally:
            if conn:
                conn.close()

    @staticmethod
    def update(transaction: Transaction) -> bool:
        """
        Update existing transaction with normalized categories.

        Args:
            transaction: Transaction with updated values (must have id)

        Returns:
            True if successful, False otherwise
        """
        from domains.transactions.service import normalize_category, normalize_subcategory

        if not transaction.id:
            logger.error("Cannot update transaction without ID")
            return False

        logger.info(f"Updating transaction ID={transaction.id}: {transaction.description[:50] if transaction.description else 'N/A'}")
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Normalize category and subcategory
            normalized_category = normalize_category(transaction.categorie)
            normalized_subcategory = normalize_subcategory(transaction.sous_categorie)

            cursor.execute("""
                UPDATE transactions
                SET type = ?, categorie = ?, sous_categorie = ?, description = ?,
                    montant = ?, date = ?, source = ?, recurrence = ?, date_fin = ?
                WHERE id = ?
            """, (
                transaction.type,
                normalized_category,
                normalized_subcategory,
                transaction.description,
                transaction.montant,
                transaction.date.isoformat() if isinstance(transaction.date, date) else transaction.date,
                transaction.source,
                transaction.recurrence,
                transaction.date_fin.isoformat() if transaction.date_fin and isinstance(transaction.date_fin, date) else transaction.date_fin,
                transaction.id
            ))

            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Transaction ID={transaction.id} updated successfully")
            else:
                logger.warning(f"Transaction ID={transaction.id} not found for update")
            return success

        except sqlite3.Error as e:
            logger.error(f"Error updating transaction: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise DatabaseError(f"Failed to update transaction ID={transaction.id}: {e}") from e
        finally:
            if conn:
                conn.close()

    @staticmethod
    def update_category(transaction_id: int, new_category: str, new_subcategory: str = None) -> bool:
        """
        Update category and subcategory for a specific transaction (for drag & drop).

        Args:
            transaction_id: ID of transaction to update
            new_category: New category name (will be normalized)
            new_subcategory: Optional new subcategory (will be normalized)

        Returns:
            True if successful, False otherwise
        """
        from domains.transactions.service import normalize_category, normalize_subcategory

        if not transaction_id:
            logger.error("Cannot update transaction without ID")
            return False

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Normalize categories
            normalized_categorie = normalize_category(new_category)
            normalized_sous_categorie = normalize_subcategory(new_subcategory) if new_subcategory else None

            # Update only category fields
            if normalized_sous_categorie:
                cursor.execute("""
                    UPDATE transactions
                    SET categorie = ?, sous_categorie = ?
                    WHERE id = ?
                """, (normalized_categorie, normalized_sous_categorie, transaction_id))
            else:
                cursor.execute("""
                    UPDATE transactions
                    SET categorie = ?
                    WHERE id = ?
                """, (normalized_categorie, transaction_id))

            conn.commit()
            logger.info(f"Updated category for transaction ID {transaction_id} to {normalized_categorie}/{normalized_sous_categorie}")
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Failed to update transaction category: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def delete(transaction_id: int, delete_files: bool = True) -> bool:
        """
        Delete transaction by ID and optionally delete associated files.

        Args:
            transaction_id: Transaction ID to delete
            delete_files: If True, delete associated files for OCR/PDF transactions

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Deleting transaction ID={transaction_id}, delete_files={delete_files}")
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get transaction data before deleting (for file cleanup)
            if delete_files:
                transaction = TransactionRepository.get_by_id(transaction_id)
                if transaction and transaction.source in ["OCR", "PDF"]:
                    try:
                        from shared.services import supprimer_fichiers_associes
                        supprimer_fichiers_associes(transaction.to_dict())
                        logger.info(f"Deleted associated files for transaction {transaction_id}")
                    except Exception as e:
                        logger.warning(f"Could not delete associated files: {e}")

            cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            conn.commit()

            success = cursor.rowcount > 0
            if success:
                logger.info(f"Transaction ID={transaction_id} deleted successfully")
            else:
                logger.warning(f"Transaction ID={transaction_id} not found for deletion")
            return success

        except sqlite3.Error as e:
            logger.error(f"Error deleting transaction: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise DatabaseError(f"Failed to delete transaction ID={transaction_id}: {e}") from e
        finally:
            conn.close()

    @staticmethod
    def get_recurring() -> List[Transaction]:
        """
        Get all recurring transactions.

        Returns:
            List of recurring transactions
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM transactions
                WHERE recurrence IS NOT NULL AND recurrence != 'Aucune'
            """)

            rows = cursor.fetchall()
            return [Transaction.from_row(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Error fetching recurring transactions: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_by_date_range(start_date: date, end_date: date) -> List[Transaction]:
        """
        Get transactions within date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of transactions
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM transactions
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC
            """, (start_date.isoformat(), end_date.isoformat()))

            rows = cursor.fetchall()
            return [Transaction.from_row(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Error fetching transactions by date range: {e}")
            return []
        finally:
            if conn:
                conn.close()
