"""File Management Service

Handles operations on transaction-associated files (move, delete, organize).
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import REVENUS_TRAITES, SORTED_DIR
from shared.database import get_db_connection
from shared.logging_config import get_logger

logger = get_logger(__name__)


def trouver_fichiers_associes(
    transaction: Dict[str, Any],
    base_dirs: Optional[List[str]] = None
) -> List[str]:
    """
    Find files associated with a transaction in the directory structure.

    Searches for receipts and supporting documents by transaction ID first,
    then falls back to category/subcategory matching for legacy files.

    The search looks for files:
    1. Named with transaction ID: {id}_1.ext, {id}_2.ext, etc.
    2. In directory: base_dir/categorie/sous_categorie/

    Supported file types: .jpg, .jpeg, .png, .pdf

    Args:
        transaction: Transaction dict with keys:
            - 'id': Transaction ID (for new ID-based naming)
            - 'categorie': Main category folder
            - 'sous_categorie': Subcategory folder
            - 'date': Optional date for matching (YYYY-MM-DD)
            - 'source': Transaction source (OCR, PDF, import_csv)
            - 'type': Transaction type (dépense, revenu)
        base_dirs: List of directories to search (defaults to [SORTED_DIR, REVENUS_TRAITES])

    Returns:
        List of up to 5 full file paths matching the transaction

    Example:
        >>> tx = {
        ...     'id': 42,
        ...     'categorie': 'Alimentation',
        ...     'sous_categorie': 'Epicerie',
        ...     'date': '2025-01-15',
        ...     'source': 'OCR',
        ...     'type': 'dépense'
        ... }
        >>> files = trouver_fichiers_associes(tx)
        >>> len(files) <= 5
        True
    """
    if base_dirs is None:
        base_dirs = [SORTED_DIR, REVENUS_TRAITES]

    fichiers_trouves = []
    
    transaction_id = transaction.get("id")
    categorie = transaction.get("categorie", "").strip()
    sous_categorie = (transaction.get("sous_categorie") or "").strip()
    date_transaction = transaction.get("date", "")
    source = transaction.get("source", "")

    # Determine search folder based on source
    if source in ["OCR", "import_csv"] and "dépense" in transaction.get("type", ""):
        dossiers_recherche = [SORTED_DIR]
    elif source in ["PDF", "import_csv"] and "revenu" in transaction.get("type", ""):
        dossiers_recherche = [REVENUS_TRAITES]
    else:
        dossiers_recherche = base_dirs

    # MÉTHODE 1: Recherche par ID de transaction (nouveau système)
    if transaction_id:
        for base_dir in dossiers_recherche:
            if not os.path.exists(base_dir):
                continue
                
            # Construire le chemin attendu
            chemin_attendu = os.path.join(base_dir, categorie, sous_categorie)
            
            if os.path.exists(chemin_attendu):
                # Chercher le fichier nommé exactement {id}.{extension}
                for fichier in os.listdir(chemin_attendu):
                    # Extraire le nom sans extension
                    nom_sans_ext, ext = os.path.splitext(fichier)
                    
                    # Vérifier si le nom correspond exactement à l'ID (format: {id}.extension)
                    if nom_sans_ext == str(transaction_id) and ext.lower() in ('.jpg', '.jpeg', '.png', '.pdf'):
                        chemin_complet = os.path.join(chemin_attendu, fichier)
                        fichiers_trouves.append(chemin_complet)
    
    # Si des fichiers ont été trouvés avec l'ID, les retourner
    if fichiers_trouves:
        return fichiers_trouves[:5]
    
    # MÉTHODE 2: Fallback sur l'ancien système (catégorie/sous-catégorie)
    # Pour compatibilité avec les anciens fichiers non encore migrés
    for base_dir in dossiers_recherche:
        if not os.path.exists(base_dir):
            continue

        # Build expected path: base/categorie/sous_categorie/
        chemin_attendu = os.path.join(base_dir, categorie, sous_categorie)

        if os.path.exists(chemin_attendu):
            # Search for all files in the directory
            for fichier in os.listdir(chemin_attendu):
                if fichier.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
                    # Ne pas inclure les fichiers déjà nommés avec un ID (éviter doublons)
                    if not re.match(r'^\d+_\d+\.', fichier):
                        chemin_complet = os.path.join(chemin_attendu, fichier)

                        # Optional: additional date verification
                        if date_transaction:
                            try:
                                # Extract date from filename if possible
                                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', fichier)
                                if date_match:
                                    date_fichier = date_match.group(1)
                                    if date_fichier in date_transaction:
                                        fichiers_trouves.append(chemin_complet)
                                        continue
                            except Exception:
                                pass

                        # If no date match, add anyway
                        fichiers_trouves.append(chemin_complet)

    return fichiers_trouves[:5]  # Limit to 5 files maximum



def supprimer_fichiers_associes(transaction: Dict[str, Any]) -> int:
    """
    Delete all files associated with a transaction.

    Removes files found for the transaction and cleans up empty directories.
    If subcategory folder becomes empty, it is deleted. If category folder
    becomes empty, it is also deleted.

    Args:
        transaction: Transaction dict with category and subcategory info

    Returns:
        Number of files successfully deleted

    Side effects:
        - Deletes files from filesystem
        - Removes empty directories
        - Logs all operations

    Example:
        >>> tx = {
        ...     'categorie': 'Alimentation',
        ...     'sous_categorie': 'Restaurant',
        ...     'date': '2025-01-15',
        ...     'source': 'OCR',
        ...     'type': 'dépense'
        ... }
        >>> count = supprimer_fichiers_associes(tx)
        >>> count >= 0
        True
    """
    fichiers = trouver_fichiers_associes(transaction)
    nb_supprimes = 0

    for fichier in fichiers:
        try:
            if os.path.exists(fichier):
                os.remove(fichier)
                nb_supprimes += 1
                logger.info(f"Fichier supprimé : {fichier}")

                # Delete parent directory if empty
                parent_dir = os.path.dirname(fichier)
                if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
                    logger.info(f"Dossier vide supprimé : {parent_dir}")

                    # Delete category directory if empty
                    cat_dir = os.path.dirname(parent_dir)
                    if os.path.exists(cat_dir) and not os.listdir(cat_dir):
                        os.rmdir(cat_dir)
                        logger.info(f"Dossier catégorie vide supprimé : {cat_dir}")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de {fichier} : {e}")

    return nb_supprimes


def deplacer_fichiers_associes(
    transaction_old: Dict[str, Any],
    transaction_new: Dict[str, Any]
) -> int:
    """
    Move files from an old transaction to a new one when category/subcategory changes.

    When a transaction's category or subcategory changes, this function
    relocates all associated files to the new directory structure.

    Only processes files for transactions with source 'OCR' or 'PDF'.

    Args:
        transaction_old: Original transaction dict with old category/subcategory
        transaction_new: Updated transaction dict with new category/subcategory

    Returns:
        Number of files successfully moved

    Side effects:
        - Moves files to new directory locations
        - Creates new directory structure if needed
        - Removes empty directories
        - Logs all operations

    Example:
        >>> old_tx = {
        ...     'categorie': 'Alimentation',
        ...     'sous_categorie': 'Epicerie',
        ...     'source': 'OCR',
        ...     'type': 'dépense'
        ... }
        >>> new_tx = {
        ...     'categorie': 'Courses',
        ...     'sous_categorie': 'Supermarché',
        ...     'source': 'OCR',
        ...     'type': 'dépense'
        ... }
        >>> moved = deplacer_fichiers_associes(old_tx, new_tx)
        >>> moved >= 0
        True
    """
    # Check if category or subcategory changed
    cat_changed = transaction_old.get("categorie") != transaction_new.get("categorie")
    souscat_changed = transaction_old.get("sous_categorie") != transaction_new.get("sous_categorie")

    if not (cat_changed or souscat_changed):
        return 0  # No movement necessary

    source = transaction_old.get("source", "")
    if source not in ["OCR", "PDF"]:
        return 0  # No files to move for this source

    # Find files of the old transaction
    fichiers = trouver_fichiers_associes(transaction_old)
    nb_deplaces = 0

    # Determine base directory based on source
    if source == "OCR":
        base_dir = SORTED_DIR
    else:  # PDF
        base_dir = REVENUS_TRAITES

    # Create the new path
    nouveau_chemin = os.path.join(
        base_dir,
        transaction_new.get("categorie", "").strip(),
        transaction_new.get("sous_categorie", "").strip()
    )

    # Create destination directory if needed
    os.makedirs(nouveau_chemin, exist_ok=True)

    for fichier in fichiers:
        try:
            if os.path.exists(fichier):
                nom_fichier = os.path.basename(fichier)
                nouveau_fichier = os.path.join(nouveau_chemin, nom_fichier)

                # Move the file
                shutil.move(fichier, nouveau_fichier)
                nb_deplaces += 1
                logger.info(f"Fichier déplacé : {fichier} -> {nouveau_fichier}")

                # Clean up empty directories
                ancien_dir = os.path.dirname(fichier)
                if os.path.exists(ancien_dir) and not os.listdir(ancien_dir):
                    os.rmdir(ancien_dir)
                    logger.info(f"Dossier vide supprimé : {ancien_dir}")

                    # Delete category directory if empty
                    cat_dir = os.path.dirname(ancien_dir)
                    if os.path.exists(cat_dir) and not os.listdir(cat_dir):
                        os.rmdir(cat_dir)
                        logger.info(f"Dossier catégorie vide supprimé : {cat_dir}")
        except Exception as e:
            logger.error(f"Erreur lors du déplacement de {fichier} : {e}")

    return nb_deplaces
