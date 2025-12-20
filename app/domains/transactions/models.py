"""Data models for database entities."""

from dataclasses import dataclass, asdict
from datetime import date
from typing import Optional, Dict, Any


@dataclass
class Transaction:
    """
    Transaction data model.

    Attributes:
        type: Transaction type ('Revenu' or 'Dépense')
        categorie: Main category
        sous_categorie: Subcategory (optional)
        description: Transaction description
        montant: Amount
        date: Transaction date
        source: Data source (default: 'Manuel')
        recurrence: Recurrence type (default: 'Aucune')
        date_fin: End date for recurring transactions (optional)
        id: Transaction ID (None for new transactions)
    """

    type: str
    categorie: str
    montant: float
    date: date
    sous_categorie: Optional[str] = None
    description: Optional[str] = ""
    source: str = "Manuel"
    recurrence: str = "Aucune"
    date_fin: Optional[date] = None
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary."""
        data = asdict(self)
        # Convert date objects to strings
        if isinstance(data['date'], date):
            data['date'] = data['date'].isoformat()
        if data.get('date_fin') and isinstance(data['date_fin'], date):
            data['date_fin'] = data['date_fin'].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """Create transaction from dictionary."""
        # Convert date strings to date objects
        if isinstance(data.get('date'), str):
            from datetime import datetime
            data['date'] = datetime.fromisoformat(data['date']).date()
        if data.get('date_fin') and isinstance(data['date_fin'], str):
            from datetime import datetime
            data['date_fin'] = datetime.fromisoformat(data['date_fin']).date()
        return cls(**data)

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> 'Transaction':
        """Create transaction from database row."""
        return cls.from_dict(dict(row))

    def __str__(self) -> str:
        """String representation."""
        return f"{self.type}: {self.categorie} - {self.montant}€ ({self.date})"

    def is_recurring(self) -> bool:
        """Check if transaction is recurring."""
        return self.recurrence and self.recurrence != "Aucune"

    def is_revenue(self) -> bool:
        """Check if transaction is revenue."""
        return self.type.lower() == "revenu"

    def is_expense(self) -> bool:
        """Check if transaction is expense."""
        return self.type.lower() == "dépense"
