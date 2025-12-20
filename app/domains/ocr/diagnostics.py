"""OCR performance analysis and diagnostics functions."""

import json
import os
import logging
from typing import Dict, List, Optional, Any

from config import OCR_PERFORMANCE_LOG, PATTERN_STATS_LOG, OCR_SCAN_LOG

logger = logging.getLogger(__name__)


def get_ocr_performance_report() -> Dict[str, Any]:
    """
    Retrieve performance report from local files.

    Returns:
        Dictionary containing performance statistics by document type,
        or empty dict if no data available
    """
    try:
        logger.debug(f"get_ocr_performance_report() - Path: {OCR_PERFORMANCE_LOG}")
        if os.path.exists(OCR_PERFORMANCE_LOG):
            logger.debug("File exists, reading...")
            with open(OCR_PERFORMANCE_LOG, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Data loaded: {data}")
                return data
        else:
            logger.debug("File does not exist")
    except Exception as e:
        logger.error(f"Error reading performance report: {e}", exc_info=True)
    return {}


def get_best_patterns(min_detections: int, min_success_rate: float) -> List[Dict[str, Any]]:
    """
    Retrieve the best performing patterns.

    Args:
        min_detections: Minimum number of detections required
        min_success_rate: Minimum success rate required (0-100)

    Returns:
        List of pattern dictionaries with success metrics
    """
    try:
        if os.path.exists(PATTERN_STATS_LOG):
            with open(PATTERN_STATS_LOG, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                return [
                    {
                        'pattern': k,
                        'success_rate': v.get('success_rate', 0),
                        'reliability_score': v.get('reliability_score', 0),
                        'detections': v.get('total_detections', 0),
                        'corrections': v.get('correction_count', 0)
                    }
                    for k, v in stats.items()
                    if v.get('total_detections', 0) >= min_detections
                    and v.get('success_rate', 0) >= min_success_rate
                ]
    except Exception as e:
        logger.error(f"Error retrieving best patterns: {e}")
    return []


def get_worst_patterns(min_detections: int, max_success_rate: float) -> List[Dict[str, Any]]:
    """
    Retrieve problematic patterns with low success rates.

    Args:
        min_detections: Minimum number of detections required
        max_success_rate: Maximum success rate to be considered problematic (0-100)

    Returns:
        List of problematic pattern dictionaries
    """
    try:
        if os.path.exists(PATTERN_STATS_LOG):
            with open(PATTERN_STATS_LOG, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                return [
                    {
                        'pattern': k,
                        'success_rate': v.get('success_rate', 0),
                        'detections': v.get('total_detections', 0),
                        'corrections': v.get('correction_count', 0)
                    }
                    for k, v in stats.items()
                    if v.get('total_detections', 0) >= min_detections
                    and v.get('success_rate', 0) <= max_success_rate
                ]
    except Exception as e:
        logger.error(f"Error retrieving worst patterns: {e}")
    return []


def get_scan_history(document_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieve scan history from JSONL log file.

    Args:
        document_type: Optional filter by document type
        limit: Maximum number of scans to return

    Returns:
        List of scan records
    """
    try:
        if os.path.exists(OCR_SCAN_LOG):
            scans = []
            with open(OCR_SCAN_LOG, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        scan = json.loads(line)
                        if document_type is None or scan.get('document_type') == document_type:
                            scans.append(scan)
                    except json.JSONDecodeError:
                        continue
            return scans[:limit]
    except Exception as e:
        logger.error(f"Error retrieving scan history: {e}")
    return []


def analyze_external_log(uploaded_file) -> Optional[Any]:
    """
    Analyze an uploaded OCR log file.

    Supports:
    - JSONL format (one JSON per line)
    - JSON format (single object or array)
    - Plain text (pattern extraction)

    Args:
        uploaded_file: Streamlit uploaded file object

    Returns:
        Parsed data structure or None on error
    """
    try:
        content = uploaded_file.read()

        if uploaded_file.name.endswith('.jsonl'):
            # JSONL format (one JSON line per scan)
            lines = content.decode('utf-8').split('\n')
            scans = []
            for line in lines:
                if line.strip():
                    try:
                        scans.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return scans

        elif uploaded_file.name.endswith('.json'):
            # Standard JSON format
            data = json.loads(content)

            # If it's a pattern_log.json (simple counter)
            if isinstance(data, dict) and all(isinstance(v, (int, float)) for v in data.values()):
                return {"type": "pattern_counts", "data": data}

            # If it's a scan_history or performance log
            return data if isinstance(data, list) else [data]

        else:
            # Text format, try to parse
            text = content.decode('utf-8')
            patterns = extract_patterns_from_text(text)
            return {"type": "raw_text", "patterns": patterns, "content": text}

    except Exception as e:
        logger.error(f"Error analyzing uploaded file: {e}")
        return None


def extract_patterns_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract recognized patterns from raw text.

    Args:
        text: Raw text to analyze

    Returns:
        List of pattern dictionaries with counts and types
    """
    patterns = []

    # Receipt patterns
    ticket_patterns = [
        'total', 'montant', 'ttc', 'cb', 'carte', 'espèces', 'esp',
        'carrefour', 'auchan', 'leclerc', 'lidl', 'intermarché',
        'restaurant', 'boulangerie', 'pharmacie'
    ]

    # Revenue patterns
    revenu_patterns = [
        'salaire', 'net', 'brut', 'paie', 'bulletin', 'mensuel',
        'cotisations', 'sécurité sociale', 'retraite', 'prélèvement'
    ]

    text_lower = text.lower()

    for pattern in ticket_patterns + revenu_patterns:
        if pattern in text_lower:
            count = text_lower.count(pattern)
            patterns.append({
                'pattern': pattern,
                'count': count,
                'type': 'ticket' if pattern in ticket_patterns else 'revenu'
            })

    return patterns


def calculate_pattern_reliability(pattern_data: Dict[str, Any]) -> float:
    """
    Calculate reliability score for a pattern based on its statistics.

    Reliability = success_rate * weight * 100
    Weight = min(total_detections / 10, 1.0)

    Args:
        pattern_data: Pattern statistics dictionary

    Returns:
        Reliability score (0-100)
    """
    if isinstance(pattern_data, dict):
        total = pattern_data.get('total_detections', 0)
        success = pattern_data.get('success_count', 0)

        if total == 0:
            return 0

        success_rate = success / total
        # Weight by detection count (max at 10)
        weight = min(total / 10, 1.0)

        return success_rate * weight * 100
    return 0


def diagnose_ocr_patterns(scans_data: Any) -> Dict[str, Any]:
    """
    Complete diagnostic of OCR patterns with improvement recommendations.

    Args:
        scans_data: Scan data (can be dict with pattern counts or list of scans)

    Returns:
        Dictionary containing:
        - total_scans: Total number of scans
        - success_rate: Overall success rate
        - problematic_patterns: List of patterns with low success
        - reliable_patterns: List of patterns with high success
        - recommendations: List of improvement suggestions
    """
    diagnostics = {
        'total_scans': 0,
        'success_rate': 0,
        'problematic_patterns': [],
        'reliable_patterns': [],
        'recommendations': []
    }

    if not scans_data:
        return diagnostics

    # Analyze by data type
    if isinstance(scans_data, dict) and scans_data.get('type') == 'pattern_counts':
        # Simple counter analysis
        patterns = scans_data['data']
        diagnostics['total_patterns'] = len(patterns)
        diagnostics['most_common'] = sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:10]

        # Basic recommendations
        if len(patterns) < 10:
            diagnostics['recommendations'].append(
                "⚠️ Few patterns detected. Enrich the pattern base."
            )

    elif isinstance(scans_data, list):
        # Complete scan analysis
        diagnostics['total_scans'] = len(scans_data)

        pattern_stats = {}
        for scan in scans_data:
            if 'patterns_detected' in scan:
                for pattern in scan['patterns_detected']:
                    if pattern not in pattern_stats:
                        pattern_stats[pattern] = {
                            'detections': 0,
                            'successes': 0,
                            'failures': 0
                        }

                    pattern_stats[pattern]['detections'] += 1

                    if scan.get('result', {}).get('success'):
                        pattern_stats[pattern]['successes'] += 1
                    else:
                        pattern_stats[pattern]['failures'] += 1

        # Identify problematic and reliable patterns
        for pattern, stats in pattern_stats.items():
            success_rate = stats['successes'] / stats['detections'] if stats['detections'] > 0 else 0

            if success_rate < 0.5 and stats['detections'] >= 3:
                diagnostics['problematic_patterns'].append({
                    'pattern': pattern,
                    'success_rate': success_rate * 100,
                    'detections': stats['detections']
                })

            if success_rate > 0.7 and stats['detections'] >= 5:
                diagnostics['reliable_patterns'].append({
                    'pattern': pattern,
                    'success_rate': success_rate * 100,
                    'detections': stats['detections']
                })

        # Calculate overall success rate
        total_success = sum(1 for scan in scans_data if scan.get('result', {}).get('success'))
        diagnostics['success_rate'] = (total_success / len(scans_data) * 100) if scans_data else 0

        # Specific recommendations
        if diagnostics['success_rate'] < 50:
            diagnostics['recommendations'].append(
                "❌ Low success rate. Review extraction logic."
            )

        if diagnostics['problematic_patterns']:
            diagnostics['recommendations'].append(
                f"⚠️ {len(diagnostics['problematic_patterns'])} problematic patterns to fix"
            )

        if not diagnostics['reliable_patterns']:
            diagnostics['recommendations'].append(
                "💡 No reliable patterns identified. Improve detection."
            )

    return diagnostics
