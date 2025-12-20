"""
Custom Exceptions for Gestion Financière V4

This module defines all custom exceptions for the application.
Each exception provides clear error context for better debugging and user feedback.

Usage:
    from shared.exceptions import DatabaseError, ValidationError
    
    if not data:
        raise ValidationError("Data cannot be empty")
"""


class GestioException(Exception):
    """
    Base exception for all application-specific exceptions.
    
    All custom exceptions should inherit from this class.
    This allows catching all app-specific errors with a single except clause.
    
    Example:
        try:
            # Some operation
        except GestioException as e:
            # Handle any app error
            logger.error(f"Application error: {e}")
    """
    pass


class DatabaseError(GestioException):
    """
    Database operation errors.
    
    Raised when database operations fail (connection, query, transaction, etc.).
    
    Common causes:
        - Connection failure
        - SQL syntax error
        - Constraint violation (unique, foreign key)
        - Transaction rollback
        - Database locked
        - Table/column not found
    
    Example:
        >>> from shared.exceptions import DatabaseError
        >>> try:
        ...     cursor.execute("INVALID SQL")
        ... except sqlite3.Error as e:
        ...     raise DatabaseError(f"Query failed: {e}")
    """
    pass


class OCRError(GestioException):
    """
    OCR processing and ticket parsing errors.
    
    Raised when OCR extraction or ticket parsing fails.
    
    Common causes:
        - Tesseract not installed
        - Image file corrupted or unreadable
        - Text extraction failed
        - No amount/date detected
        - Invalid ticket format
        - Unsupported image format
    
    Example:
        >>> from shared.exceptions import OCRError
        >>> if not ocr_text:
        ...     raise OCRError("OCR extraction returned empty text")
    """
    pass


class ValidationError(GestioException):
    """
    Data validation errors.
    
    Raised when input data fails validation checks.
    
    Common causes:
        - Negative amount when positive required
        - Invalid date format
        - Missing required fields
        - Category doesn't exist
        - Invalid email/phone format
        - Amount exceeds maximum
    
    Example:
        >>> from shared.exceptions import ValidationError
        >>> if montant <= 0:
        ...     raise ValidationError("Amount must be positive")
        >>> if not categorie:
        ...     raise ValidationError("Category is required")
    """
    pass


class ServiceError(GestioException):
    """
    Business logic and service layer errors.
    
    Raised when business operations fail (calculations, exports, recurrence, etc.).
    
    Common causes:
        - CSV export failed
        - Recurrence generation error
        - Category normalization failed
        - Revenue calculation error
        - File service operation failed
        - Business rule violation
    
    Example:
        >>> from shared.exceptions import ServiceError
        >>> if not transactions:
        ...     raise ServiceError("No transactions to export")
    """
    pass


class FileOperationError(GestioException):
    """
    File system operation errors.
    
    Raised when file operations fail (read, write, move, delete, etc.).
    
    Common causes:
        - File not found
        - Permission denied
        - Disk full
        - File in use/locked
        - Invalid path
        - Copy/move failed
    
    Example:
        >>> from shared.exceptions import FileOperationError
        >>> if not os.path.exists(filepath):
        ...     raise FileOperationError(f"File not found: {filepath}")
    """
    pass


class ConfigurationError(GestioException):
    """
    Application configuration errors.
    
    Raised when configuration is missing, invalid, or corrupted.
    
    Common causes:
        - Missing environment variable
        - Invalid config file path
        - Config file corrupted or invalid YAML/JSON
        - Required directory doesn't exist
        - Invalid pattern configuration
    
    Example:
        >>> from shared.exceptions import ConfigurationError
        >>> if not DATA_DIR:
        ...     raise ConfigurationError("DATA_DIR environment variable not set")
    """
    pass


# Exception hierarchy summary:
# GestioException (base)
# ├── DatabaseError (DB operations)
# ├── OCRError (OCR/parsing)
# ├── ValidationError (input validation)
# ├── ServiceError (business logic)
# ├── FileOperationError (file I/O)
# └── ConfigurationError (app config)
