"""OCR logging functions for tracking pattern detection and performance."""

import json
import os
import logging
from datetime import datetime
from typing import List, Optional

from config import (
    OCR_LOGS_DIR, LOG_PATH, OCR_PERFORMANCE_LOG, PATTERN_STATS_LOG,
    OCR_SCAN_LOG, POTENTIAL_PATTERNS_LOG
)

logger = logging.getLogger(__name__)

# Ensure OCR logs directory exists
os.makedirs(OCR_LOGS_DIR, exist_ok=True)


def log_pattern_occurrence(pattern_name: str) -> None:
    """
    Record each OCR-detected keyword in a JSON log.

    Args:
        pattern_name: Name of the detected pattern/keyword
    """
    try:
        data = {}
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

        data[pattern_name] = data.get(pattern_name, 0) + 1

        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[OCR-LOG] Error logging pattern occurrence: {e}")


def log_ocr_scan(
    document_type: str,
    filename: str,
    montants_detectes: List[float],
    montant_choisi: float,
    categorie: str,
    sous_categorie: str,
    patterns_detectes: Optional[List[str]] = None,
    success_level: str = "exact",
    methode_detection: str = "UNKNOWN"
) -> None:
    """
    Log a complete OCR scan operation with all detected information.

    Args:
        document_type: Type of document scanned
        filename: Name of the scanned file
        montants_detectes: List of all amounts detected
        montant_choisi: The final selected amount
        categorie: Transaction category
        sous_categorie: Transaction subcategory
        patterns_detectes: List of detected patterns
        success_level: Level of success ("exact", "partial", "failed")
        methode_detection: Detection method used
    """
    try:
        logger.info(f"[OCR-LOG] Recording scan: {filename}, type={document_type}, success={success_level}")

        # 1. Record in scan history (JSONL format)
        scan_entry = {
            "timestamp": datetime.now().isoformat(),
            "document_type": document_type,
            "filename": filename,
            "montants_detectes": [float(m) for m in montants_detectes] if montants_detectes else [],
            "montant_choisi": float(montant_choisi),
            "categorie": categorie,
            "sous_categorie": sous_categorie,
            "patterns_detectes": patterns_detectes or [],
            "success_level": success_level,
            "methode_detection": methode_detection,
            "result": {
                "success": success_level in ["exact", "partial"]
            },
            "extraction": {
                "montant_final": float(montant_choisi),
                "categorie_final": categorie
            }
        }

        logger.debug(f"[OCR-LOG] Writing to {OCR_SCAN_LOG}")
        with open(OCR_SCAN_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(scan_entry, ensure_ascii=False) + "\n")
        logger.debug("[OCR-LOG] Scan history recorded")

        # 2. Update performance statistics
        logger.debug("[OCR-LOG] Updating performance stats...")
        update_performance_stats(document_type, success_level)

        # 3. Update pattern statistics
        if patterns_detectes:
            logger.debug(f"[OCR-LOG] Updating pattern stats ({len(patterns_detectes)} patterns)...")
            update_pattern_stats(patterns_detectes, success_level)

        logger.info("[OCR-LOG] OCR log completed successfully")

    except Exception as e:
        logger.error(f"[OCR-LOG] Error recording scan: {e}", exc_info=True)


def update_performance_stats(document_type: str, success_level: str) -> None:
    """
    Update global performance statistics.

    Args:
        document_type: Type of document processed
        success_level: Success level ("exact", "partial", "failed")
    """
    try:
        # Load existing stats
        stats = {}
        if os.path.exists(OCR_PERFORMANCE_LOG):
            with open(OCR_PERFORMANCE_LOG, "r", encoding="utf-8") as f:
                stats = json.load(f)

        # Initialize if necessary
        if document_type not in stats:
            stats[document_type] = {
                "total": 0,
                "success": 0,
                "partial": 0,
                "failed": 0,
                "success_rate": 0.0,
                "correction_rate": 0.0
            }

        # Update counters
        stats[document_type]["total"] += 1
        if success_level == "exact":
            stats[document_type]["success"] += 1
        elif success_level == "partial":
            stats[document_type]["partial"] += 1
        else:
            stats[document_type]["failed"] += 1

        # Calculate rates
        total = stats[document_type]["total"]
        stats[document_type]["success_rate"] = (
            stats[document_type]["success"] / total * 100 if total > 0 else 0
        )
        stats[document_type]["correction_rate"] = (
            stats[document_type]["failed"] / total * 100 if total > 0 else 0
        )

        # Add update timestamp
        stats["last_updated"] = datetime.now().isoformat()

        # Save
        with open(OCR_PERFORMANCE_LOG, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[OCR-LOG] Error updating performance stats: {e}")


def update_pattern_stats(patterns_detectes: List[str], success_level: str) -> None:
    """
    Update statistics for each detected pattern.

    Args:
        patterns_detectes: List of detected patterns
        success_level: Success level of the scan
    """
    try:
        # Load existing stats
        stats = {}
        if os.path.exists(PATTERN_STATS_LOG):
            with open(PATTERN_STATS_LOG, "r", encoding="utf-8") as f:
                stats = json.load(f)

        # Update each pattern
        for pattern in patterns_detectes:
            if pattern not in stats:
                stats[pattern] = {
                    "total_detections": 0,
                    "success_count": 0,
                    "partial_count": 0,
                    "failure_count": 0,
                    "success_rate": 0.0,
                    "reliability_score": 0.0
                }

            stats[pattern]["total_detections"] += 1

            if success_level == "exact":
                stats[pattern]["success_count"] += 1
            elif success_level == "partial":
                stats[pattern]["partial_count"] += 1
            else:
                stats[pattern]["failure_count"] += 1

            # Calculate success rate
            total = stats[pattern]["total_detections"]
            success = stats[pattern]["success_count"] + stats[pattern]["partial_count"]
            stats[pattern]["success_rate"] = (success / total * 100) if total > 0 else 0

            # Reliability score (weighted by detection count)
            weight = min(total / 10, 1.0)
            stats[pattern]["reliability_score"] = stats[pattern]["success_rate"] * weight

        # Save
        with open(PATTERN_STATS_LOG, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[OCR-LOG] Error updating pattern stats: {e}")


def determine_success_level(montants_detectes: List[float], montant_choisi: float) -> str:
    """
    Determine the success level of OCR detection.

    Args:
        montants_detectes: List of detected amounts
        montant_choisi: The chosen final amount

    Returns:
        "exact": Chosen amount is first in the list (total success)
        "partial": Chosen amount is in the list but not first (partial success)
        "failed": Chosen amount is not in the list (failure)
    """
    if not montants_detectes:
        return "failed"

    if montants_detectes[0] == montant_choisi:
        return "exact"
    elif montant_choisi in montants_detectes:
        return "partial"
    else:
        return "failed"


def log_potential_patterns(
    filename: str,
    potential_patterns: List[dict],
    montant_final: float,
    methode_detection: str
) -> None:
    """
    Log potential new patterns detected in OCR text for future improvements.

    This helps identify patterns that are not yet in our known patterns list,
    allowing continuous improvement of the OCR system.

    Args:
        filename: Name of the scanned file
        potential_patterns: List of potential patterns detected
        montant_final: The final selected amount
        methode_detection: Detection method used

    Example entry:
        {
            "timestamp": "2025-11-18T10:30:00",
            "filename": "ticket_123.jpg",
            "montant_final": 12.50,
            "methode_detection": "D-FALLBACK",
            "patterns": [
                {
                    "pattern": "PAYÉ",
                    "line": "PAYÉ : 12,50€",
                    "amount": "12,50",
                    "raw_label": "Payé"
                }
            ]
        }
    """
    try:
        # Only log if there are potential patterns
        if not potential_patterns:
            return

        logger.info(f"[OCR-LOG] Recording {len(potential_patterns)} potential patterns from {filename}")

        # Create log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "filename": filename,
            "montant_final": float(montant_final),
            "methode_detection": methode_detection,
            "patterns": potential_patterns
        }

        # Append to JSONL file
        with open(POTENTIAL_PATTERNS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        logger.debug(f"[OCR-LOG] Logged {len(potential_patterns)} potential patterns to {POTENTIAL_PATTERNS_LOG}")

    except Exception as e:
        logger.error(f"[OCR-LOG] Error logging potential patterns: {e}", exc_info=True)
