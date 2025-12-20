"""OCR logs export functionality for support and improvement."""

import os
import json
import zipfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config import OCR_LOGS_DIR, DATA_DIR

import logging
logger = logging.getLogger(__name__)


def get_logs_summary() -> Dict[str, Any]:
    """
    Get a summary of OCR logs for display.

    Returns:
        Dictionary with counts and statistics about the logs
    """
    summary = {
        "total_scans": 0,
        "potential_patterns_count": 0,
        "performance_by_type": {},
        "log_files": []
    }

    try:
        # Count scan history
        scan_log = os.path.join(OCR_LOGS_DIR, "scan_history.jsonl")
        if os.path.exists(scan_log):
            with open(scan_log, 'r', encoding='utf-8') as f:
                summary["total_scans"] = sum(1 for _ in f)
            summary["log_files"].append("scan_history.jsonl")

        # Count potential patterns
        patterns_log = os.path.join(OCR_LOGS_DIR, "potential_patterns.jsonl")
        if os.path.exists(patterns_log):
            with open(patterns_log, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        summary["potential_patterns_count"] += len(entry.get("patterns", []))
                    except:
                        pass
            summary["log_files"].append("potential_patterns.jsonl")

        # Get performance stats
        perf_log = os.path.join(OCR_LOGS_DIR, "performance_stats.json")
        if os.path.exists(perf_log):
            with open(perf_log, 'r', encoding='utf-8') as f:
                perf_data = json.load(f)
                for doc_type, stats in perf_data.items():
                    if doc_type != "last_updated":
                        summary["performance_by_type"][doc_type] = {
                            "total": stats.get("total", 0),
                            "success_rate": stats.get("success_rate", 0)
                        }
            summary["log_files"].append("performance_stats.json")

        # Check for other log files
        for log_file in ["pattern_log.json", "pattern_stats.json"]:
            log_path = os.path.join(OCR_LOGS_DIR, log_file)
            if os.path.exists(log_path):
                summary["log_files"].append(log_file)

    except Exception as e:
        logger.error(f"Error getting logs summary: {e}")

    return summary


def prepare_logs_for_support(
    include_problematic_tickets: bool = True,
    output_dir: Optional[str] = None
) -> str:
    """
    Prepare OCR logs for sending to support.

    Creates a ZIP archive containing:
    - All OCR log files (scan_history, patterns, performance, etc.)
    - Metadata about the logs
    - Optionally: problematic tickets metadata (no images, just JSON)
    - README with instructions

    Args:
        include_problematic_tickets: Include problematic tickets metadata
        output_dir: Directory to save the ZIP file (defaults to DATA_DIR)

    Returns:
        Path to the created ZIP file

    Example:
        >>> zip_path = prepare_logs_for_support()
        >>> print(f"Send this file to support: {zip_path}")
    """
    if output_dir is None:
        output_dir = DATA_DIR

    # Create timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"ocr_logs_export_{timestamp}.zip"
    zip_path = os.path.join(output_dir, zip_filename)

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all OCR log files
            if os.path.exists(OCR_LOGS_DIR):
                for root, dirs, files in os.walk(OCR_LOGS_DIR):
                    for file in files:
                        if file.endswith(('.json', '.jsonl')):
                            file_path = os.path.join(root, file)
                            arcname = os.path.join('ocr_logs', file)
                            zipf.write(file_path, arcname)
                            logger.info(f"Added to archive: {file}")

            # Add problematic tickets metadata (not the images, just JSON)
            if include_problematic_tickets:
                problematic_dir = os.path.join(DATA_DIR, "tickets_problematiques")
                if os.path.exists(problematic_dir):
                    metadata_files = []
                    for file in os.listdir(problematic_dir):
                        if file.endswith('_metadata.json'):
                            file_path = os.path.join(problematic_dir, file)
                            arcname = os.path.join('problematic_metadata', file)
                            zipf.write(file_path, arcname)
                            metadata_files.append(file)

                    if metadata_files:
                        logger.info(f"Added {len(metadata_files)} problematic ticket metadata files")

            # Create summary file
            summary = get_logs_summary()
            summary_data = {
                "export_date": datetime.now().isoformat(),
                "total_scans": summary["total_scans"],
                "potential_patterns_count": summary["potential_patterns_count"],
                "performance_by_type": summary["performance_by_type"],
                "log_files_included": summary["log_files"],
                "include_problematic_metadata": include_problematic_tickets
            }

            summary_json = json.dumps(summary_data, indent=2, ensure_ascii=False)
            zipf.writestr('SUMMARY.json', summary_json)

            # Create README for support
            readme_content = f"""# OCR Logs Export pour Support
Date d'export : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

## Contenu de ce fichier

Ce fichier ZIP contient tous les logs nécessaires pour améliorer la détection OCR de l'application Gestio.

### Fichiers inclus :

1. **ocr_logs/** - Dossier contenant tous les logs OCR
   - `scan_history.jsonl` : Historique complet de tous les scans ({summary['total_scans']} scans)
   - `potential_patterns.jsonl` : Patterns potentiels détectés ({summary['potential_patterns_count']} patterns)
   - `performance_stats.json` : Statistiques de performance par type de document
   - `pattern_stats.json` : Statistiques de fiabilité de chaque pattern
   - `pattern_log.json` : Occurrences des patterns détectés

2. **problematic_metadata/** - Métadonnées des tickets problématiques
   - Contient uniquement les fichiers JSON (pas les images pour la confidentialité)
   - Permet d'identifier les cas où la détection a échoué

3. **SUMMARY.json** - Résumé de l'export avec statistiques clés

## Comment utiliser ces données

Ces logs permettent de :
- Identifier les patterns manquants dans le système
- Améliorer les taux de détection pour chaque type de document
- Découvrir de nouveaux formats de tickets/factures
- Optimiser les méthodes de détection existantes

## Statistiques de performance

"""

            # Add performance stats to README
            for doc_type, stats in summary.get("performance_by_type", {}).items():
                readme_content += f"\n- **{doc_type}** : {stats['total']} scans, {stats['success_rate']:.1f}% de réussite"

            readme_content += """

## Confidentialité

- ❌ Aucune image de ticket n'est incluse
- ❌ Aucune donnée personnelle sensible
- ✅ Uniquement des métadonnées techniques (montants, patterns, méthodes)
- ✅ Parfait pour améliorer l'algorithme sans risque

## Contact Support

Envoyez ce fichier à : [votre email de support]

Merci d'aider à améliorer Gestio !
"""

            zipf.writestr('README.txt', readme_content)

        logger.info(f"Logs export created successfully: {zip_path}")
        return zip_path

    except Exception as e:
        logger.error(f"Error creating logs export: {e}", exc_info=True)
        raise


def export_logs_to_desktop() -> str:
    """
    Export logs to user's desktop for easy access.

    Returns:
        Path to the exported ZIP file
    """
    desktop = os.path.expanduser("~/Desktop")
    if not os.path.exists(desktop):
        # Fallback to home directory if Desktop doesn't exist
        desktop = os.path.expanduser("~")

    return prepare_logs_for_support(output_dir=desktop)


if __name__ == "__main__":
    # Test the export
    try:
        zip_path = prepare_logs_for_support()
        print(f"✅ Export créé avec succès : {zip_path}")

        # Show summary
        summary = get_logs_summary()
        print(f"\n📊 Résumé :")
        print(f"  - Scans totaux : {summary['total_scans']}")
        print(f"  - Patterns potentiels : {summary['potential_patterns_count']}")
        print(f"  - Fichiers de logs : {len(summary['log_files'])}")
    except Exception as e:
        print(f"❌ Erreur : {e}")
