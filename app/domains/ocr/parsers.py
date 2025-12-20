"""
Refactored OCR Parser with Better Debuggability

This module breaks down the OCR parsing into clear, testable steps
with detailed logging at each stage for easier debugging.
"""

import re
from typing import Dict, List, Any, Tuple
from datetime import datetime
from dateutil import parser as date_parser

from shared.utils import safe_convert
from shared.logging_config import get_logger
from .pattern_manager import get_pattern_manager

logger = get_logger(__name__)


def _normalize_ocr_text(text: str) -> List[str]:
    """
    Normalize OCR text into clean lines.
    
    IMPORTANT: Ne PAS corriger O→0 car cela casse les patterns (MONTANT → M0NTANT)
    
    Args:
        text: Raw OCR text
    
    Returns:
        List of normalized lines
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    def normalize_line(l: str) -> str:
        # Ne faire AUCUNE correction O→0 ou I→1
        # Car cela casse les keywords: MONTANT→M0NTANT, TOTAL→T0TAL
        return l.strip()
    
    normalized = [normalize_line(l) for l in lines]
    logger.debug(f"Normalized {len(lines)} lines")
    return normalized


def _detect_amount_method_a(lines: List[str]) -> Tuple[List[float], List[str]]:
    """
    METHOD A: Detect amounts using direct total patterns.
    
    Args:
        lines: Normalized OCR text lines
    
    Returns:
        Tuple of (amounts found, patterns that matched)
    """
    logger.info("🔍 METHOD A: Looking for TOTAL/MONTANT patterns...")
    
    pattern_mgr = get_pattern_manager()
    total_patterns = pattern_mgr.get_amount_patterns()
    
    montants = []
    patterns_matched = []
    
    # Import function from old parser
    from domains.ocr.parsers_OLD_BACKUP import get_montant_from_line
    
    for pattern_config in total_patterns:
        # Extraire pattern string si c'est un dict
        if isinstance(pattern_config, dict):
            pattern = pattern_config.get('pattern', '')
        else:
            pattern = pattern_config
        
        # get_montant_from_line est déjà case-insensitive et cherche sur ligne suivante
        montant, matched = get_montant_from_line(pattern, lines, allow_next_line=True)
        
        if matched and montant > 0:
            montants.append(round(montant, 2))
            patterns_matched.append(pattern)
            logger.info(f"  ✅ Pattern '{pattern}' → {montant}€")
    
    if montants:
        logger.info(f"✅ METHOD A: Found {len(montants)} amounts: {montants}")
    else:
        logger.warning("⚠️  METHOD A: No amounts found")
    
    return montants, patterns_matched


def _detect_amount_method_b(lines: List[str]) -> float:
    """
    METHOD B: Detect amount by summing payment methods.
    
    Args:
        lines: Normalized OCR text lines
    
    Returns:
        Sum of payment amounts
    """
    logger.info("🔍 METHOD B: Looking for PAYMENT patterns (CB, CARTE, etc.)...")
    
    pattern_mgr = get_pattern_manager()
    paiement_patterns = pattern_mgr.get_payment_patterns()
    montant_regex = r"(\d{1,5}[.,]\d{1,2})"
    
    montants_found = []
    
    for line in lines:
        if any(re.search(p, line, re.IGNORECASE) for p in paiement_patterns):
            amounts = re.findall(montant_regex, line)
            for val in amounts:
                amount = safe_convert(val)
                montants_found.append(amount)
                logger.debug(f"  Payment line: {line} → {amount}€")
    
    total = round(sum(montants_found), 2) if montants_found else 0.0
    
    if total > 0:
        logger.info(f"✅ METHOD B: Sum of payments = {total}€")
    else:
        logger.warning("⚠️  METHOD B: No payment amounts found")
    
    return total


def _detect_amount_method_c(lines: List[str]) -> float:
    """
    METHOD C: Detect amount by summing HT + TVA.
    
    Args:
        lines: Normalized OCR text lines
    
    Returns:
        Sum of HT + TVA
    """
    logger.info("🔍 METHOD C: Looking for HT + TVA...")
    
    montant_regex = r"(\d{1,5}[.,]\d{1,2})"
    
    # Find HT (net) lines
    net_lines = [l for l in lines if re.search(r"HT|NET", l, re.IGNORECASE)]
    total_HT = 0.0
    for line in net_lines:
        vals = re.findall(montant_regex, line)
        for v in vals:
            total_HT += safe_convert(v)
    
    # Find TVA lines
    tva_lines = [l for l in lines if re.search(r"TVA|T\.V\.A", l, re.IGNORECASE)]
    total_TVA = 0.0
    for line in tva_lines:
        vals = re.findall(montant_regex, line)
        for v in vals:
            total_TVA += safe_convert(v)
    
    total = round(total_HT + total_TVA, 2) if total_HT > 0 else 0.0
    
    if total > 0:
        logger.info(f"✅ METHOD C: HT ({total_HT}€) + TVA ({total_TVA}€) = {total}€")
    else:
        logger.warning("⚠️  METHOD C: No HT/TVA found")
    
    return total


def _detect_amount_method_d(ocr_text: str) -> float:
    """
    METHOD D: DÉSACTIVÉ - Fallback désactivé pour forcer méthodes A, B, C.
    
    Args:
        ocr_text: Raw OCR text
    
    Returns:
        Always 0.0 (disabled)
    """
    logger.info("🔍 METHOD D: DÉSACTIVÉ (fallback forcé à 0)")
    return 0.0  # Désactivé pour améliorer méthodes A, B, C


def _cross_validate_amounts(
    montants_A: List[float],
    montant_B: float,
    montant_C: float,
    montant_D: float
) -> Tuple[float, str]:
    """
    Cross-validate amounts from different methods.
    
    Args:
        montants_A: Amounts from method A
        montant_B: Amount from method B
        montant_C: Amount from method C
        montant_D: Amount from method D (fallback)
    
    Returns:
        Tuple of (final amount, detection method)
    """
    logger.info("🔬 CROSS-VALIDATION: Comparing all methods...")
    
    # Gather all candidates
    candidats = [x for x in montants_A + [montant_B, montant_C, montant_D] if x > 0]
    
    if not candidats:
        logger.error("❌ No amounts found by ANY method!")
        return 0.0, "AUCUNE"
    
    # Count frequency of each amount
    freq = {}
    for amount in candidats:
        rounded = round(amount, 2)
        freq[rounded] = freq.get(rounded, 0) + 1
    
    logger.debug(f"  Amount frequency: {freq}")
    
    # Most frequent amount wins
    final_amount = max(freq, key=freq.get)
    
    # Determine which methods found this amount
    methods = []
    if final_amount in montants_A:
        methods.append("A-PATTERNS")
    if montant_B == final_amount:
        methods.append("B-PAIEMENT")
    if montant_C == final_amount:
        methods.append("C-HT+TVA")
    if montant_D == final_amount and not methods:
        methods.append("D-FALLBACK")
    
    method_str = "+".join(methods) if methods else "UNKNOWN"
    
    logger.info(f"✅ FINAL: {final_amount}€ (methods: {method_str}, confidence: {freq[final_amount]}/{len(candidats)})")
    
    return final_amount, method_str


def _detect_date(ocr_text: str) -> str:
    """
    Detect date from OCR text.
    
    Args:
        ocr_text: Raw OCR text
    
    Returns:
        Detected date in ISO format
    """
    logger.info("📅 Detecting date...")
    
    date_patterns = [
        r"\b\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}\b",
        r"\b\d{1,2}\s*(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)\.?\s*\d{2,4}\b"
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, ocr_text, re.IGNORECASE)
        if match:
            try:
                detected = date_parser.parse(match.group(0), dayfirst=True, fuzzy=True).date().isoformat()
                logger.info(f"✅ Date found: {detected}")
                return detected
            except:
                continue
    
    fallback = datetime.now().date().isoformat()
    logger.warning(f"⚠️  No date found, using today: {fallback}")
    return fallback


def parse_ticket_metadata_v2(ocr_text: str) -> Dict[str, Any]:
    """
    REFACTORED: Extract metadata from receipt OCR text.
    
    Cleaner, more debuggable version with detailed logging.
    
    Args:
        ocr_text: Raw OCR text
    
    Returns:
        Dictionary with extracted data
    """
    logger.info("=" * 60)
    logger.info("🎫 STARTING OCR PARSING")
    logger.info("=" * 60)
    
    # Step 1: Normalize text
    lines = _normalize_ocr_text(ocr_text)
    
    # Step 2: Try all detection methods
    montants_A, patterns_A = _detect_amount_method_a(lines)
    montant_B = _detect_amount_method_b(lines)
    montant_C = _detect_amount_method_c(lines)
    montant_D = _detect_amount_method_d(ocr_text)
    
    # Step 3: Cross-validate
    final_amount, method = _cross_validate_amounts(montants_A, montant_B, montant_C, montant_D)
    
    # Step 4: Detect date
    detected_date = _detect_date(ocr_text)
    
    # Step 5: Determine reliability
    is_reliable = method not in ["D-FALLBACK", "AUCUNE"]
    
    if is_reliable:
        logger.info("✅ RELIABLE detection")
    else:
        logger.warning("⚠️  UNRELIABLE detection (fallback used)")
    
    logger.info("=" * 60)
    
    # Return structured result
    all_candidates = [x for x in montants_A + [montant_B, montant_C, montant_D] if x > 0]
    
    return {
        "montant": final_amount,
        "montants_possibles": sorted(set(all_candidates), reverse=True),
        "date": detected_date,
        "methode_detection": method,
        "fiable": is_reliable,
        "debug_info": {
            "methode_A": montants_A,
            "methode_B": montant_B,
            "methode_C": montant_C,
            "methode_D": montant_D,
            "patterns_A": patterns_A
        }
    }
