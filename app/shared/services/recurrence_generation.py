"""
Recurrence Generation Service

Handles automatic generation of recurring transactions.
"""

import sqlite3
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
from dateutil.relativedelta import relativedelta

from shared.database import get_db_connection
from shared.logging_config import get_logger

logger = get_logger(__name__)


def generate_occurrences_for_recurrence(
    recurrence_id: int,
    start_date: date,
    end_date: date
) -> List[Dict]:
    """
    Génère les occurrences d'une récurrence entre deux dates.
    
    IMPORTANT : Génère SEULEMENT les occurrences passées (<=aujourd'hui),
    pas les futures.
    
    Args:
        recurrence_id: ID de la récurrence dans la table recurrences
        start_date: Date de début de génération
        end_date: Date de fin de génération (généralement aujourd'hui)
        
    Returns:
        Liste de dictionnaires représentant les transactions à créer
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Récupérer la récurrence
    rec = cursor.execute("""
        SELECT type, categorie, sous_categorie, montant, date_debut, date_fin, frequence, description
        FROM recurrences
        WHERE id = ? AND statut = 'active'
    """, (recurrence_id,)).fetchone()
    
    conn.close()
    
    if not rec:
        return []
    
    type_rec, categorie, sous_categorie, montant, date_debut_str, date_fin_str, frequence, description = rec
    
    # Convertir dates
    from dateutil.parser import parse
    date_debut = parse(date_debut_str).date()
    date_fin_rec = parse(date_fin_str).date() if date_fin_str else None
    
    # IMPORTANT : Ne générer que jusqu'à aujourd'hui (pas de futures)
    today = date.today()
    end_date = min(end_date, today)
    
    # Générer occurrences
    occurrences = []
    current_date = max(date_debut, start_date)
    
    while current_date <= end_date:
        # Vérifier si on dépasse la date de fin de la récurrence
        if date_fin_rec and current_date > date_fin_rec:
            break
            
        occurrences.append({
            'type': type_rec,
            'categorie': categorie,
            'sous_categorie': sous_categorie or '',
            'montant': montant,
            'date': current_date.isoformat(),
            'source': 'récurrente_auto',  # IMPORTANT : récurrente_auto (avec accent)
            'description': description or f'Récurrence auto - {categorie}'
        })
        
        # Calculer prochaine occurrence
        if frequence == 'hebdomadaire':
            current_date += timedelta(weeks=1)
        elif frequence == 'mensuelle':
            current_date += relativedelta(months=1)
        elif frequence == 'annuelle':
            current_date += relativedelta(years=1)
        else:
            break
    
    return occurrences


def backfill_all_recurrences() -> int:
    """
    Génère toutes les occurrences manquantes pour toutes les récurrences actives.
    
    IMPORTANT : Ne génère que les transactions PASSÉES (jusqu'à aujourd'hui).
    
    Returns:
        Nombre de transactions créées
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Récupérer toutes les récurrences actives
    recurrences = cursor.execute("""
        SELECT id, date_debut, date_fin
        FROM recurrences
        WHERE statut = 'active'
    """).fetchall()
    
    today = date.today()
    total_created = 0
    
    for rec_id, date_debut_str, date_fin_str in recurrences:
        from dateutil.parser import parse
        date_debut = parse(date_debut_str).date()
        
        # IMPORTANT : Générer seulement jusqu'à aujourd'hui
        occurrences = generate_occurrences_for_recurrence(rec_id, date_debut, today)
        
        # Vérifier quelles occurrences existent déjà
        for occ in occurrences:
            # Check if transaction already exists
            # Check if transaction already exists
            existing = cursor.execute("""
                SELECT id FROM transactions
                WHERE categorie = ? AND sous_categorie = ? 
                  AND date = ? AND source = 'récurrente_auto'
            """, (occ['categorie'], occ['sous_categorie'], occ['date'])).fetchone()
            
            if not existing:
                # Créer la transaction avec source=récurrente_auto
                cursor.execute("""
                    INSERT INTO transactions
                    (type, categorie, sous_categorie, montant, date, source, description)
                    VALUES (?, ?, ?, ?, ?, 'récurrente_auto', ?)
                """, (
                    occ['type'],
                    occ['categorie'],
                    occ['sous_categorie'],
                    occ['montant'],
                    occ['date'],
                    occ['description']
                ))
                total_created += 1
    
    conn.commit()
    conn.close()
    
    logger.info(f"Backfill completed: {total_created} transactions created")
    return total_created


def generate_future_occurrences(months_ahead: int = 12) -> int:
    """
    Génère les occurrences futures pour toutes les récurrences actives.
    
    Args:
        months_ahead: Nombre de mois à l'avance à générer
        
    Returns:
        Nombre de transactions créées
    """
    today = date.today()
    end_date = today + relativedelta(months=months_ahead)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    recurrences = cursor.execute("""
        SELECT id FROM recurrences WHERE statut = 'active'
    """).fetchall()
    
    total_created = 0
    
    for (rec_id,) in recurrences:
        occurrences = generate_occurrences_for_recurrence(rec_id, today, end_date)
        
        for occ in occurrences:
            existing = cursor.execute("""
                SELECT id FROM transactions
                WHERE categorie = ? AND sous_categorie = ? 
                  AND date = ? AND source = 'récurrente'
            """, (occ['categorie'], occ['sous_categorie'], occ['date'])).fetchone()
            
            if not existing:
                cursor.execute("""
                    INSERT INTO transactions
                    (type, categorie, sous_categorie, montant, date, source, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    occ['type'],
                    occ['categorie'],
                    occ['sous_categorie'],
                    occ['montant'],
                    occ['date'],
                    occ['source'],
                    occ['description']
                ))
                total_created += 1
    
    conn.commit()
    conn.close()
    
    logger.info(f"Future generation completed: {total_created} transactions created")
    return total_created


def sync_recurrences_to_echeances() -> int:
    """
    Synchronise les récurrences actives vers la table echeances.
    
    Génère les occurrences futures (jusqu'à fin du mois suivant) dans echeances
    avec type_echeance='récurrente'.
    
    Returns:
        Nombre d'échéances créées
    """
    today = date.today()
    # Générer jusqu'à la fin du mois suivant
    fin_mois_suivant = (today.replace(day=1) + relativedelta(months=2)) - timedelta(days=1)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Récupérer toutes les récurrences actives
    recurrences = cursor.execute("""
        SELECT id, type, categorie, sous_categorie, montant, 
               date_debut, date_fin, frequence, description
        FROM recurrences
        WHERE statut = 'active'
    """).fetchall()
    
    total_created = 0
    
    for rec in recurrences:
        rec_id, type_rec, categorie, sous_cat, montant, date_debut_str, date_fin_str, frequence, description = rec
        
        from dateutil.parser import parse
        date_debut = parse(date_debut_str).date()
        date_fin_rec = parse(date_fin_str).date() if date_fin_str else None
        
        # Générer les occurrences futures
        current = date_debut
        while current <= fin_mois_suivant:
            # Seulement les dates futures (>= aujourd'hui)
            if current >= today:
                # Vérifier date de fin
                if date_fin_rec and current > date_fin_rec:
                    break
                
                # Vérifier si déjà présent dans echeances
                existing = cursor.execute("""
                    SELECT id FROM echeances
                    WHERE categorie = ? AND date_echeance = ? 
                      AND type_echeance = 'récurrente'
                      AND recurrence_id = ?
                """, (categorie, current.isoformat(), rec_id)).fetchone()
                
                if not existing:
                    cursor.execute("""
                        INSERT INTO echeances 
                        (type, categorie, sous_categorie, montant, date_echeance, 
                         type_echeance, description, statut, recurrence_id)
                        VALUES (?, ?, ?, ?, ?, 'récurrente', ?, 'active', ?)
                    """, (
                        type_rec,
                        categorie,
                        sous_cat or '',
                        montant,
                        current.isoformat(),
                        description or f'Récurrence {frequence}',
                        rec_id
                    ))
                    total_created += 1
            
            # Avancer selon la fréquence
            if frequence == 'hebdomadaire':
                current += timedelta(weeks=1)
            elif frequence == 'mensuelle':
                current += relativedelta(months=1)
            elif frequence == 'annuelle':
                current += relativedelta(years=1)
            else:
                break
    
    conn.commit()
    conn.close()
    
    logger.info(f"Sync recurrences to echeances: {total_created} created")
    return total_created


def cleanup_past_echeances() -> int:
    """
    Supprime les échéances passées (récurrentes et prévues).
    
    Returns:
        Nombre d'échéances supprimées
    """
    today = date.today()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Supprimer les échéances récurrentes passées
    cursor.execute("""
        DELETE FROM echeances
        WHERE date_echeance < ?
          AND type_echeance = 'récurrente'
    """, (today.isoformat(),))
    
    deleted_recurrentes = cursor.rowcount
    
    # Optionnel: Marquer les échéances prévues passées comme 'expirée'
    cursor.execute("""
        UPDATE echeances
        SET statut = 'expirée'
        WHERE date_echeance < ?
          AND type_echeance = 'prévue'
          AND statut = 'active'
    """, (today.isoformat(),))
    
    expired_prevues = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    logger.info(f"Cleanup: {deleted_recurrentes} récurrentes supprimées, {expired_prevues} prévues expirées")
    return deleted_recurrentes + expired_prevues


def refresh_echeances() -> None:
    """
    Rafraîchit les échéances: nettoie les passées et synchronise les récurrences.
    
    Cette fonction doit être appelée au démarrage de l'application.
    """
    cleanup_past_echeances()
    sync_recurrences_to_echeances()
    logger.info("Echeances refresh completed")
