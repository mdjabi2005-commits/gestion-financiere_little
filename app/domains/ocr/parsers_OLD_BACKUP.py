"""Document parsing functions for extracting structured data from OCR text."""

import os
import re
import shutil
import logging
from datetime import datetime, date
from calendar import monthrange
from typing import Dict, Tuple, List, Optional, Any
from dateutil import parser
from pdfminer.high_level import extract_text

from config import SORTED_DIR, PROBLEMATIC_DIR
from shared.utils import safe_convert
from .pattern_manager import get_pattern_manager

logger = logging.getLogger(__name__)


def get_montant_from_line(
    label_pattern: str,
    all_lines: List[str],
    allow_next_line: bool = True
) -> Tuple[float, bool]:
    """
    Extract amount from a line matching a pattern.

    Searches for a label pattern (e.g., 'TOTAL', 'MONTANT') and extracts
    the associated amount from the same line or the next line.

    Args:
        label_pattern: Regex pattern to find the label
        all_lines: List of all text lines
        allow_next_line: Whether to check the next line if no amount found on current line

    Returns:
        Tuple of (amount, found) where found indicates if pattern matched
    """
    montant_regex = r"(\d{1,5}[.,]?\d{0,2})\s*(?:€|eur|euros?)?"

    def clean_ocr_text(txt: str) -> str:
        """Correct common OCR reading errors (O/0, I/1, etc.)."""
        # Replace O with 0 ONLY in numeric context
        txt = re.sub(r'(\d)[Oo](\d)', r'\g<1>0\g<2>', txt)  # 1O5 → 105
        txt = re.sub(r'(\d)[Oo](?=\s|$|,|\.)', r'\g<1>0', txt)  # 1O → 10
        txt = re.sub(r'(^|[\s,\.])[Oo](\d)', r'\g<1>0\g<2>', txt)  # O5 at start/after delimiter → 05

        # Replace I/l with 1 ONLY in numeric context
        txt = re.sub(r'(\d)[Il](\d)', r'\g<1>1\g<2>', txt)  # 2I5 → 215
        txt = re.sub(r'(\d)[Il](?=\s|$|,|\.)', r'\g<1>1', txt)  # 2I → 21
        txt = re.sub(r'(^|[\s,\.])[Il](\d)', r'\g<1>1\g<2>', txt)  # I5 at start/after delimiter → 15

        # Clean spaces
        txt = re.sub(r"[\u200b\s]+", " ", txt)
        return txt.strip()

    for i, l in enumerate(all_lines):
        l_clean = clean_ocr_text(l)

        # Search for label (e.g., 'TOTAL', 'MONTANT', etc.)
        if re.search(label_pattern, l_clean, re.IGNORECASE):
            found_same = re.findall(montant_regex, l_clean, re.IGNORECASE)
            if found_same:
                # Take the largest amount on the line (often the TTC total)
                return (safe_convert(max(found_same, key=lambda x: safe_convert(x))), True)

            # Check next line if allowed
            if allow_next_line and i + 1 < len(all_lines):
                next_line = clean_ocr_text(all_lines[i + 1])
                found_next = re.findall(montant_regex, next_line, re.IGNORECASE)
                if found_next:
                    return (safe_convert(max(found_next, key=lambda x: safe_convert(x))), True)

    # Pattern not found
    return (0.0, False)


def detect_potential_patterns(ocr_text: str, known_patterns: List[str]) -> List[Dict[str, Any]]:
    """
    Detect potential new patterns in OCR text that might contain amounts.

    This function helps improve the OCR system by identifying amount labels
    that are not yet in our known patterns list.

    Args:
        ocr_text: Raw OCR text
        known_patterns: List of known pattern regexes

    Returns:
        List of potential patterns found, each containing:
        - pattern: The detected label/keyword
        - line: The complete line containing the pattern
        - amount: The associated amount
        - context: Surrounding text
    """
    lines = [l.strip() for l in ocr_text.split("\n") if l.strip()]
    montant_regex = r"(\d{1,5}[.,]\d{1,2})\s*(?:€|eur|EUR|euros?)?"
    potential_patterns = []

    for line in lines:
        # Find amounts in this line
        amounts = re.findall(montant_regex, line, re.IGNORECASE)
        if not amounts:
            continue

        # Extract the text before the amount (potential label)
        # Look for 1-4 words before the amount
        label_pattern = r"(\b[\w\-À-ÿ]+(?:\s+[\w\-À-ÿ]+){0,3})\s*[:=\-–]?\s*\d{1,5}[.,]\d{1,2}"
        label_matches = re.findall(label_pattern, line, re.IGNORECASE)

        for label in label_matches:
            label_clean = label.strip().upper()

            # Check if this label matches any known pattern
            is_known = False
            for known in known_patterns:
                if re.search(known, label_clean, re.IGNORECASE):
                    is_known = True
                    break

            # If not known, this is a potential new pattern
            if not is_known and len(label_clean) >= 2:
                potential_patterns.append({
                    "pattern": label_clean,
                    "line": line.strip(),
                    "amount": amounts[0] if amounts else None,
                    "raw_label": label.strip()
                })

    return potential_patterns


def test_patterns_on_ticket(
    ocr_text: str,
    additional_patterns: List[str]
) -> Dict[str, Any]:
    """
    Test additional patterns on a ticket to see if detection improves.

    This function allows testing new patterns discovered in potential_patterns.jsonl
    to validate whether they improve detection accuracy before adding them permanently.

    Args:
        ocr_text: Raw OCR text from the ticket
        additional_patterns: List of additional regex patterns to test

    Returns:
        Dictionary containing:
        - original_result: Result with standard patterns only
        - test_result: Result with additional patterns included
        - improvement: Whether the new patterns improved detection
        - comparison: Detailed comparison of methods

    Example:
        >>> patterns = [r"PAYÉ", r"SOLDE"]
        >>> result = test_patterns_on_ticket(ocr_text, patterns)
        >>> if result['improvement']:
        ...     print(f"New patterns improved detection: {result['comparison']}")
    """
    # First, get original detection with standard patterns
    original_result = parse_ticket_metadata(ocr_text)

    # Now test with additional patterns by temporarily modifying the detection
    lines = [l.strip() for l in ocr_text.split("\n") if l.strip()]

    def normalize_line(l: str) -> str:
        return l.replace("O", "0").replace("o", "0").replace("I", "1").replace("l", "1").strip()

    lines = [normalize_line(l) for l in lines]
    montant_regex = r"(\d{1,5}[.,]\d{1,2})"

    # Test additional patterns
    montants_new = []
    patterns_new_matches = []
    for pattern in additional_patterns:
        montant, matched = get_montant_from_line(pattern, lines)
        if matched and montant > 0:
            montants_new.append(round(montant, 2))
            patterns_new_matches.append(pattern)

    # Create test result
    test_result = {
        "montants_from_new_patterns": montants_new,
        "patterns_matched": patterns_new_matches,
        "montant_original": original_result.get("montant", 0.0),
        "montant_with_new": montants_new[0] if montants_new else original_result.get("montant", 0.0),
        "methode_original": original_result.get("methode_detection", "UNKNOWN"),
        "methode_improved": "A-NEW-PATTERNS" if montants_new else original_result.get("methode_detection", "UNKNOWN")
    }

    # Determine if there's an improvement
    improvement = False
    improvement_reason = []

    # Improvement if we found amount with new patterns and original was fallback
    if montants_new and original_result.get("methode_detection") in ["D-FALLBACK", "AUCUNE"]:
        improvement = True
        improvement_reason.append("New patterns found amount where fallback was used")

    # Improvement if new patterns give consistent result
    if montants_new and len(set(montants_new)) == 1:
        improvement = True
        improvement_reason.append("New patterns give consistent amount")

    return {
        "original_result": original_result,
        "test_result": test_result,
        "improvement": improvement,
        "improvement_reason": improvement_reason,
        "comparison": {
            "original_montant": original_result.get("montant", 0.0),
            "original_method": original_result.get("methode_detection", "UNKNOWN"),
            "original_reliable": original_result.get("fiable", False),
            "new_montant": test_result["montant_with_new"],
            "new_patterns_found": len(montants_new),
            "new_reliable": len(montants_new) > 0
        }
    }


def parse_ticket_metadata(ocr_text: str) -> Dict[str, Any]:
    """
    Extract metadata from receipt OCR text using multiple detection methods.

    Uses four detection methods:
    A. Direct total patterns (TOTAL TTC, MONTANT, NET A PAYER, etc.)
    B. Payment sum (CB, CARTE, ESPECES, etc.)
    C. Net + VAT sum (HT + TVA)
    D. Global fallback (largest amount)

    Cross-validates results and returns the most frequent amount.

    Args:
        ocr_text: Raw OCR text from receipt

    Returns:
        Dictionary containing:
        - montants_possibles: List of all possible amounts
        - montant: Final selected amount
        - date: Detected or current date
        - infos: Key lines from the receipt
        - methode_detection: Detection method used
        - debug_info: Detailed detection information
    """
    lines = [l.strip() for l in ocr_text.split("\n") if l.strip()]

    def normalize_line(l: str) -> str:
        return l.replace("O", "0").replace("o", "0").replace("I", "1").replace("l", "1").strip()

    lines = [normalize_line(l) for l in lines]

    montant_regex = r"(\d{1,5}[.,]\d{1,2})"

    # === METHOD A: Direct totals ===
    # Load patterns from YAML configuration
    pattern_mgr = get_pattern_manager()
    total_patterns = pattern_mgr.get_amount_patterns()
    
    montants_A = []
    patterns_A_matches = []
    for pattern in total_patterns:
        montant, matched = get_montant_from_line(pattern, lines)
        if matched and montant > 0:  # Only count if pattern REALLY matched
            montants_A.append(round(montant, 2))
            patterns_A_matches.append(pattern)

    # === METHOD B: Sum of payments ===
    paiement_patterns = pattern_mgr.get_payment_patterns()
    montants_B = []
    for l in lines:
        if any(re.search(p, l, re.IGNORECASE) for p in paiement_patterns):
            found = re.findall(montant_regex, l)
            for val in found:
                montants_B.append(safe_convert(val))
    somme_B = round(sum(montants_B), 2) if montants_B else 0.0

    # === METHOD C: Net + VAT ===
    net_lines = [l for l in lines if re.search(r"HT|NET", l, re.IGNORECASE)]
    tva_lines = [l for l in lines if re.search(r"TVA|T\.V\.A", l, re.IGNORECASE)]
    total_HT = 0.0
    total_TVA = 0.0
    for l in net_lines:
        vals = re.findall(montant_regex, l)
        for v in vals:
            total_HT += safe_convert(v)
    for l in tva_lines:
        vals = re.findall(montant_regex, l)
        for v in vals:
            total_TVA += safe_convert(v)
    somme_C = round(total_HT + total_TVA, 2) if total_HT > 0 else 0.0

    # === METHOD D: Global fallback ===
    all_amounts = [safe_convert(m) for m in re.findall(montant_regex, ocr_text)]
    montant_fallback = max(all_amounts) if all_amounts else 0.0

    # === CROSS-VALIDATION ===
    candidats = [x for x in montants_A + [somme_B, somme_C, montant_fallback] if x > 0]
    freq = {}
    for m in candidats:
        m_rond = round(m, 2)
        freq[m_rond] = freq.get(m_rond, 0) + 1

    if not freq:
        montant_final = 0.0
        methode_detection = "AUCUNE"
    else:
        montant_final = max(freq, key=freq.get)  # Take most frequent amount

        # Determine which method found this amount
        methode_detection = []
        if montant_final in montants_A:
            methode_detection.append("A-PATTERNS")
        if somme_B == montant_final:
            methode_detection.append("B-PAIEMENT")
        if somme_C == montant_final:
            methode_detection.append("C-HT+TVA")
        if montant_fallback == montant_final and not methode_detection:
            methode_detection.append("D-FALLBACK")
        methode_detection = "+".join(methode_detection) if methode_detection else "UNKNOWN"

    # === Date detection ===
    date_patterns = [
        r"\b\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}\b",
        r"\b\d{1,2}\s*(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)\.?\s*\d{2,4}\b"
    ]
    detected_date = None
    for p in date_patterns:
        match = re.search(p, ocr_text, re.IGNORECASE)
        if match:
            try:
                detected_date = parser.parse(match.group(0), dayfirst=True, fuzzy=True).date().isoformat()
                break
            except:
                continue
    if not detected_date:
        detected_date = datetime.now().date().isoformat()

    # === Key lines (for display in interface) ===
    key_lines = [
        l for l in lines if any(re.search(p, l, re.IGNORECASE) for p in total_patterns + paiement_patterns)
    ]

    # === DETECT POTENTIAL NEW PATTERNS ===
    # Combine all known patterns for detection
    all_known_patterns = total_patterns + paiement_patterns + [r"HT", r"NET", r"TVA", r"T\.V\.A"]
    potential_new_patterns = detect_potential_patterns(ocr_text, all_known_patterns)

    # === Determine reliability ===
    # Fallback method is unreliable - mark amounts detected ONLY by fallback as not reliable
    is_reliable = methode_detection != "D-FALLBACK" and methode_detection != "AUCUNE"

    # === Final result ===
    montants_possibles = sorted(set(candidats), reverse=True)
    return {
        "montants_possibles": montants_possibles if montants_possibles else [montant_final],
        "montant": montant_final,
        "date": detected_date,
        "infos": "\n".join(key_lines),
        "methode_detection": methode_detection,
        "fiable": is_reliable,  # NEW: Mark fallback-only detections as unreliable
        "patterns_potentiels": potential_new_patterns,  # NEW: Potential patterns for improvement
        "debug_info": {
            "methode_A": montants_A,
            "methode_B": somme_B,
            "methode_C": somme_C,
            "methode_D": montant_fallback,
            "patterns_A": patterns_A_matches
        }
    }


def move_ticket_to_sorted(ticket_path: str, categorie: str, sous_categorie: str, transaction_id: Optional[int] = None) -> None:
    """
    Move a ticket to the sorted directory with category/subcategory structure.

    If transaction_id is provided, renames the file to {transaction_id}.{extension}.
    Otherwise, keeps the original filename (legacy behavior).

    Args:
        ticket_path: Path to the ticket file
        categorie: Category name
        sous_categorie: Subcategory name
        transaction_id: Optional transaction ID for renaming the file
    """
    cat_dir = os.path.join(SORTED_DIR, categorie.strip())
    souscat_dir = os.path.join(cat_dir, sous_categorie.strip())
    os.makedirs(souscat_dir, exist_ok=True)

    # Determine the destination filename
    if transaction_id is not None:
        # Use transaction ID as filename
        _, ext = os.path.splitext(ticket_path)
        new_name = f"{transaction_id}{ext}"
        dest_path = os.path.join(souscat_dir, new_name)
    else:
        # Legacy behavior: keep original name with counter if needed
        base_name = os.path.basename(ticket_path)
        dest_path = os.path.join(souscat_dir, base_name)
        
        # If a file with the same name exists, create a unique name
        if os.path.exists(dest_path):
            name, ext = os.path.splitext(base_name)
            counter = 1
            while os.path.exists(dest_path):
                new_name = f"{name}_{counter}{ext}"
                dest_path = os.path.join(souscat_dir, new_name)
                counter += 1

    shutil.move(ticket_path, dest_path)
    logger.info(f"Ticket moved to: {dest_path}")


def move_ticket_to_problematic(
    ticket_path: str,
    montant_detecte: float,
    methode_detection: str,
    potential_patterns: List[Dict[str, Any]]
) -> str:
    """
    Move a ticket to the problematic directory for manual review.

    Tickets are moved here when:
    - Amount detected by fallback method only (unreliable)
    - No amount detected at all
    - User needs to verify the detection

    The filename is enriched with detection metadata for easier review.

    Args:
        ticket_path: Path to the ticket file
        montant_detecte: Detected amount (may be 0 or unreliable)
        methode_detection: Detection method used
        potential_patterns: List of potential patterns found

    Returns:
        Path to the moved file

    Example:
        Original: "ticket_123.jpg"
        Moved to: "tickets_problematiques/FALLBACK_0.00_ticket_123.jpg"
    """
    base_name = os.path.basename(ticket_path)
    name, ext = os.path.splitext(base_name)

    # Create enriched filename with detection info
    # Format: METHOD_AMOUNT_originalname.ext
    enriched_name = f"{methode_detection}_{montant_detecte:.2f}_{name}{ext}"
    dest_path = os.path.join(PROBLEMATIC_DIR, enriched_name)

    # Handle duplicate filenames
    if os.path.exists(dest_path):
        counter = 1
        while os.path.exists(dest_path):
            enriched_name = f"{methode_detection}_{montant_detecte:.2f}_{name}_{counter}{ext}"
            dest_path = os.path.join(PROBLEMATIC_DIR, enriched_name)
            counter += 1

    # Move the file
    shutil.move(ticket_path, dest_path)
    logger.info(f"Problematic ticket moved to: {dest_path}")

    # Also save a JSON metadata file alongside the ticket
    metadata_path = os.path.splitext(dest_path)[0] + "_metadata.json"
    metadata = {
        "original_filename": base_name,
        "montant_detecte": montant_detecte,
        "methode_detection": methode_detection,
        "potential_patterns": potential_patterns,
        "moved_at": datetime.now().isoformat()
    }

    try:
        import json
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.debug(f"Metadata saved to: {metadata_path}")
    except Exception as e:
        logger.warning(f"Failed to save metadata: {e}")

    return dest_path


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Read a PDF and return raw text.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text or empty string on error
    """
    try:
        return extract_text(pdf_path)
    except Exception as e:
        logger.warning(f"Unable to read PDF {pdf_path} ({e})")
        return ""


def parse_uber_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Parse an Uber Eats PDF invoice to extract revenue information.

    Extracts:
    - Billing period end date
    - Net earnings amount
    - Applies automatic 79% net calculation (21% tax)

    Args:
        pdf_path: Path to Uber PDF file

    Returns:
        Dictionary with montant (net), date, categorie, sous_categorie, source,
        montant_brut, and tax_amount
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return {
            "montant": 0.0,
            "date": datetime.now().date(),
            "categorie": "Revenu",
            "sous_categorie": "Uber",
            "source": "PDF Uber"
        }

    # Look for billing period: "Période de facturation : 01/07/2025 - 31/07/2025"
    date_fin = None
    periode_match = re.search(
        r"P[eé]riode de facturation\s*[:\-]?\s*([0-3]?\d[\/\-\.][ ]?[01]?\d[\/\-\.]\d{2,4})\s*[\-–]\s*([0-3]?\d[\/\-\.][ ]?[01]?\d[\/\-\.]\d{2,4})",
        text,
        re.IGNORECASE
    )
    if periode_match:
        debut_str, fin_str = periode_match.groups()
        fin_str = fin_str.replace(" ", "")  # Remove spaces
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
            try:
                date_fin = datetime.strptime(fin_str, fmt).date()
                break
            except Exception:
                continue

    # If not found, try "Période terminée le : 31/07/2025" or "Period ending 31/07/2025"
    if not date_fin:
        m2 = re.search(
            r"(period ending|p[eé]riode termin[eé]e le|Date de fin)\s*[:\-]?\s*([0-3]?\d[\/\-\.][01]?\d[\/\-\.]\d{2,4})",
            text,
            re.IGNORECASE
        )
        if m2:
            date_str = m2.group(2)
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
                try:
                    date_fin = datetime.strptime(date_str, fmt).date()
                    break
                except Exception:
                    continue

    # NEW: Try "Date de facturation : 16 sept. 2025" (French month abbreviations)
    if not date_fin:
        month_pattern = r"Date de facturation\s*[:\-]?\s*(\d{1,2})\s+(janv|f[eé]vr|mars|avr|mai|juin|juil|ao[uû]t|sept|oct|nov|d[eé]c)\.?\s+(\d{4})"
        m3 = re.search(month_pattern, text, re.IGNORECASE)
        if m3:
            day_str, month_str, year_str = m3.groups()
            month_map = {
                "janv": 1, "févr": 2, "fevr": 2, "mars": 3, "avr": 4,
                "mai": 5, "juin": 6, "juil": 7, "août": 8, "aout": 8,
                "sept": 9, "oct": 10, "nov": 11, "déc": 12, "dec": 12
            }
            month_num = month_map.get(month_str.lower())
            if month_num:
                try:
                    date_fin = date(int(year_str), month_num, int(day_str))
                except Exception:
                    pass

    if not date_fin:
        date_fin = datetime.now().date()

    # Net amount: varies by Uber PDF (Net earnings, Total to be paid, etc.)
    montant = 0.0
    montant_patterns = [
        r"Montant total [aà] payer\s*[:\-–]?\s*([0-9]+[., ][0-9]{2})\s*€?",
        r"(?:Net earnings|Net to driver|Total net|Montant net|Net earnings \(driver\))\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})\s*€?",
        r"([\d]{1,3}(?:[ .,]\d{3})*[.,]\d{2})\s*€\s*(?:net|netto|net earnings|to driver)?"
    ]
    for p in montant_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            s = m.group(1).replace(" ", "").replace(".", "").replace(",", ".") if "," in m.group(1) and "." in m.group(1) else m.group(1).replace(",", ".").replace(" ", "")
            try:
                montant = safe_convert(s)
                if montant > 0:
                    break
            except Exception:
                continue

    # Fallback: find last amount in text
    if montant == 0.0:
        all_amounts = re.findall(r"(\d+[., ]\d{2})\s*€?", text)
        if all_amounts:
            for a in reversed(all_amounts):
                try:
                    candidate = safe_convert(a.replace(" ", "").replace(",", "."))
                    if candidate > 0:
                        montant = candidate
                        break
                except:
                    continue

    # Apply automatic 79% for Uber
    montant_net = round(montant * 0.79, 2) if montant > 0 else 0.0
    tax_amount = round(montant - montant_net, 2) if montant > 0 else 0.0

    if montant > 0:
        logger.info(f"Uber PDF processed: {montant}€ → {montant_net}€ net (after 21% tax)")

    # Create preview text (first 500 chars)
    preview_text = text[:500] + "..." if len(text) > 500 else text

    return {
        "montant": montant_net,  # Return NET amount after taxes
        "date": date_fin,
        "categorie": "Uber Eats",  # Standardized category
        "sous_categorie": "Uber",
        "source": "PDF Uber",
        "montant_brut": montant,  # Additional information
        "tax_amount": tax_amount,
        "preview_text": preview_text  # NEW: Preview for verification
    }


def parse_fiche_paie(pdf_path: str) -> Dict[str, Any]:
    """
    Parse a salary slip (fiche de paie) PDF.

    Extracts:
    - Net pay amount
    - Pay period or month

    Args:
        pdf_path: Path to salary slip PDF

    Returns:
        Dictionary with montant, date, categorie, sous_categorie, and source
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return {
            "montant": 0.0,
            "date": datetime.now().date(),
            "categorie": "Revenu",
            "sous_categorie": "Salaire",
            "source": "PDF Fiche de paie"
        }

    # 1) Find net pay (patterns: NET A PAYER, Net à payer, Net pay, Net salary)
    montant = 0.0
    net_patterns = [
        r"NET\s*A\s*PAYER\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})",
        r"Net à payer\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})",
        r"Net à payer \(à vous\)\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})",
        r"Net\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})"  # fallback
    ]
    for p in net_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                montant = safe_convert(m.group(1))
                break
            except:
                continue

    # Fallback: take last amount found, but be careful
    if montant == 0.0:
        amounts = re.findall(r"(\d+[.,]\d{2})\s*€?", text)
        if amounts:
            candidates = [safe_convert(a) for a in amounts]
            bigs = [c for c in candidates if c > 100]
            montant = bigs[-1] if bigs else candidates[-1]

    # 2) Find period or date: search for "période" or interval "01/07/2025 - 31/07/2025"
    date_found = None
    periode_match = re.search(
        r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s*[\-–]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        text
    )
    if periode_match:
        fin_str = periode_match.groups()[1]
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
            try:
                date_found = datetime.strptime(fin_str, fmt).date()
                break
            except:
                pass

    if not date_found:
        m2 = re.search(r"Pour le mois de\s+([A-Za-zéûà]+)\s+(\d{4})", text, re.IGNORECASE)
        if m2:
            mois_str, annee_str = m2.groups()
            mois_map = {
                "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
                "juillet": 7, "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
                "décembre": 12, "decembre": 12
            }
            mois_key = mois_str.lower()
            mois_num = mois_map.get(mois_key)
            if mois_num:
                last_day = monthrange(int(annee_str), mois_num)[1]
                date_found = date(int(annee_str), mois_num, last_day)

    if not date_found:
        date_found = datetime.now().date()

    # Create preview text (first 500 chars)
    preview_text = text[:500] + "..." if len(text) > 500 else text

    return {
        "montant": round(float(montant), 2),
        "date": date_found,
        "categorie": "Revenu",
        "sous_categorie": "Salaire",
        "source": "PDF Fiche de paie",
        "preview_text": preview_text  # NEW: Preview for verification
    }


def parse_pdf_dispatcher(pdf_path: str, source_type: str) -> Dict[str, Any]:
    """
    Dispatch PDF parsing to the appropriate parser based on source type.

    Args:
        pdf_path: Path to PDF file
        source_type: Type of PDF ("uber", "fiche_paie", "ticket", etc.)

    Returns:
        Parsed document metadata
    """
    stype = source_type.lower().strip()

    if stype in ("uber", "uber_pdf", "uber eats"):
        return parse_uber_pdf(pdf_path)
    elif stype in ("fiche_paie", "fiche de paie", "paye", "salaire"):
        return parse_fiche_paie(pdf_path)
    elif stype in ("ticket", "receipt", "ticket_ocr"):
        text = extract_text_from_pdf(pdf_path)
        return parse_ticket_metadata(text)
    else:
        # Default: try ticket parsing
        text = extract_text_from_pdf(pdf_path)
        return parse_ticket_metadata(text)
