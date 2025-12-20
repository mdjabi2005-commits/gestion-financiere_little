"""
OCR Learning Service

Analyzes user corrections to automatically improve OCR pattern detection.
When users correct an OCR error, the system learns from it.
"""

import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from shared.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CorrectionAnalysis:
    """Result of analyzing a user correction."""
    already_detected: bool = False
    found_in_text: bool = False
    scan_error: bool = False
    context_lines: List[str] = None
    suggested_pattern: Optional[str] = None
    amount_line_index: Optional[int] = None
    
    def __post_init__(self):
        if self.context_lines is None:
            self.context_lines = []


def analyze_user_correction(
    ocr_text: str,
    detected_amount: float,
    corrected_amount: float,
    detection_methods: List[str]
) -> CorrectionAnalysis:
    """
    Analyze a user correction to learn new patterns.
    
    Args:
        ocr_text: Raw OCR text from ticket
        detected_amount: Amount initially detected by OCR (may be 0)
        corrected_amount: Amount corrected by user
        detection_methods: Methods that were used (e.g., ['A', 'B'])
    
    Returns:
        CorrectionAnalysis with findings and suggestions
    
    Example:
        >>> analysis = analyze_user_correction(
...             "PRICE TOTAL: 25.80",
...             0.0,  # Not detected
...             25.80,  # User corrected
...             []
...         )
        >>> analysis.found_in_text
        True
        >>> analysis.suggested_pattern
        "PRICE\\s*TOTAL\\s*:"
    """
    logger.info(f"Analyzing correction: {detected_amount}€ → {corrected_amount}€")
    
    # Step 1: Check if we already had it right
    if abs(detected_amount - corrected_amount) < 0.01:
        logger.info("Amount was already correct, no learning needed")
        return CorrectionAnalysis(already_detected=True)
    
    # Step 2: Search for corrected amount in OCR text
    found, variant, line_idx = find_amount_in_text(ocr_text, corrected_amount)
    
    if not found:
        logger.warning(f"Amount {corrected_amount}€ not found in OCR text - likely scan error")
        return CorrectionAnalysis(scan_error=True)
    
    logger.info(f"Found amount in OCR text (variant: {variant}) at line {line_idx}")
    
    # Step 3: Extract context around the amount
    lines = ocr_text.split('\n')
    context = extract_context_around_line(lines, line_idx)
    
    # Step 4: Suggest a pattern
    pattern = suggest_pattern_from_context(context, variant)
    
    return CorrectionAnalysis(
        found_in_text=True,
        context_lines=context,
        suggested_pattern=pattern,
        amount_line_index=line_idx
    )


def find_amount_in_text(
    text: str,
    amount: float
) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Find amount in OCR text with various format variants.
    
    Args:
        text: OCR text
        amount: Amount to find (e.g., 25.80)
    
    Returns:
        Tuple of (found, variant_matched, line_index)
        
    Example:
        >>> find_amount_in_text("TOTAL: 25.80€", 25.80)
        (True, "25.80", 0)
    """
    lines = text.split('\n')
    
    # Generate amount variants
    variants = generate_amount_variants(amount)
    
    for variant in variants:
        for idx, line in enumerate(lines):
            if variant in line:
                logger.debug(f"Found amount variant '{variant}' in line {idx}: {line[:50]}")
                return True, variant, idx
    
    return False, None, None


def generate_amount_variants(amount: float) -> List[str]:
    """
    Generate common OCR variants of an amount.
    
    Args:
        amount: Amount to generate variants for
    
    Returns:
        List of string variants
        
    Example:
        >>> generate_amount_variants(25.80)
        ['25.80', '25,80', '2580', ' 25.80', '25.80 ', '25.80€']
    """
    # Basic formats
    dot_format = f"{amount:.2f}"
    comma_format = dot_format.replace('.', ',')
    no_decimal = str(int(amount * 100))  # 25.80 → 2580
    
    variants = [
        dot_format,  # 25.80
        comma_format,  # 25,80
        no_decimal,  # 2580
        f" {dot_format}",  # Leading space
        f"{dot_format} ",  # Trailing space
        f"{dot_format}€",  # With euro
        f"{comma_format}€",
    ]
    
    # Also check variant with single decimal if .X0
    if amount % 1 == 0:  # Whole number (25.00)
        variants.append(str(int(amount)))  # 25
    
    return variants


def extract_context_around_line(
    lines: List[str],
    line_idx: int,
    context_size: int = 2
) -> List[str]:
    """
    Extract lines around a target line for context.
    
    Args:
        lines: All OCR lines
        line_idx: Index of target line
        context_size: Number of lines before/after to include
    
    Returns:
        List of context lines (before + target + after)
    """
    start = max(0, line_idx - context_size)
    end = min(len(lines), line_idx + context_size + 1)
    
    context = lines[start:end]
    logger.debug(f"Extracted {len(context)} context lines around line {line_idx}")
    
    return context


def suggest_pattern_from_context(
    context_lines: List[str],
    amount_variant: str
) -> str:
    """
    Generate a regex pattern from context lines.
    
    Args:
        context_lines: Lines containing and around the amount
        amount_variant: The specific amount string found (e.g., "25.80")
    
    Returns:
        Suggested regex pattern
        
    Example:
        >>> suggest_pattern_from_context(
...             ["PRICE TOTAL: 25.80€"],
...             "25.80"
...         )
        "PRICE\\s*TOTAL\\s*:"
    """
    # Find line containing amount
    amount_line =None
    for line in context_lines:
        if amount_variant in line:
            amount_line = line
            break
    
    if not amount_line:
        # Fallback
        amount_line = context_lines[len(context_lines) // 2]
    
    # Extract words BEFORE the amount
    amount_pos = amount_line.find(amount_variant)
    words_before = amount_line[:amount_pos].strip()
    
    if not words_before:
        logger.warning("No words found before amount, using full line")
        words_before = amount_line
    
    # Generate flexible regex pattern
    pattern = create_flexible_pattern(words_before)
    
    logger.info(f"Suggested pattern: {pattern}")
    return pattern


def create_flexible_pattern(text: str) -> str:
    """
    Create a flexible regex pattern from text.
    
    Handles:
    - Spaces → \\s*
    - Common separators → optional
    - Case insensitive
    
    Args:
        text: Text to convert to pattern
    
    Returns:
        Regex pattern string
        
    Example:
        >>> create_flexible_pattern("PRICE TOTAL:")
        "PRICE\\s*TOTAL\\s*:?"
    """
    # Split into words
    words = text.split()
    
    if not words:
        return ""
    
    # Join words with flexible spacing
    pattern_parts = []
    for word in words:
        # Remove special chars except letters/numbers
        cleaned = re.sub(r'[^A-Za-z0-9]', '', word)
        if cleaned:
            pattern_parts.append(cleaned)
    
    # Join with flexible whitespace
    pattern = "\\s*".join(pattern_parts)
    
    # Add optional separator at end (: or =)
    if text.strip().endswith((':' , '=')):
        pattern += "\\s*[=:]?"
    
    return pattern


def save_learned_pattern(
    pattern: str,
    source_ticket: str,
    user_confirmed: bool = False
) -> None:
    """
    Save a learned pattern to config.
    
    Args:
        pattern: Regex pattern to save
        source_ticket: Filename of ticket that generated this
        user_confirmed: If True, add to main config. If False, save to pending.
    """
    import yaml
    from datetime import datetime
    
    learned_config_path = Path("config/ocr_patterns_learned.yml")
    
    # Load existing or create new
    if learned_config_path.exists():
        with open(learned_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {'learned_patterns': []}
    
    # Add new pattern
    new_pattern = {
        'pattern': pattern,
        'source': source_ticket,
        'learned_date': datetime.now().strftime('%Y-%m-%d'),
        'user_confirmed': user_confirmed,
        'confidence': 0.8 if user_confirmed else 0.5
    }
    
    if 'learned_patterns' not in config:
        config['learned_patterns'] = []
    
    config['learned_patterns'].append(new_pattern)
    
    # Save
    learned_config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(learned_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    logger.info(f"Saved learned pattern: {pattern} (confirmed={user_confirmed})")
