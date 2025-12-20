"""OCR scanning functionality for image-based document processing."""

import os
import logging
import cv2
import numpy as np
import pytesseract
from PIL import Image
from typing import Optional

from .logging import log_pattern_occurrence

logger = logging.getLogger(__name__)


def full_ocr(image_path: str, show_ticket: bool = False) -> str:
    """
    Perform full OCR on an image file with preprocessing.

    This function:
    1. Reads the image file robustly
    2. Applies preprocessing (grayscale, blur, threshold)
    3. Performs multi-language OCR (French + English)
    4. Returns extracted text

    Args:
        image_path: Path to the image file
        show_ticket: If True, display the ticket in Streamlit (requires streamlit context)

    Returns:
        Extracted text from the image, or empty string if OCR fails

    Example:
        >>> text = full_ocr("/path/to/receipt.jpg")
        >>> if text:
        ...     print(f"Extracted: {text[:100]}")
    """
    try:
        # --- Robust image file reading ---
        image_data = np.fromfile(image_path, dtype=np.uint8)
        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

        if image is None:
            raise FileNotFoundError(f"Unable to read or decode image: {image_path}")

        # --- Preprocessing for OCR ---
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        pil_img = Image.fromarray(thresh)

        # --- MULTI-LANGUAGE OCR (French + English) ---
        # Uses fra+eng to better recognize TOTAL, PAYMENT, AMOUNT, etc.
        text = pytesseract.image_to_string(pil_img, lang="fra+eng")
        text = text.replace("\x0c", "").strip()

        # Log detected languages for statistics
        if text:
            log_pattern_occurrence("ocr_success_fra+eng")

        # --- Optional: Display in Streamlit ---
        if show_ticket:
            try:
                import streamlit as st
                with st.expander(f"🧾 Receipt preview: {os.path.basename(image_path)}", expanded=False):
                    st.image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), caption=os.path.basename(image_path))
                    if text:
                        st.text_area("Detected OCR text:", text, height=200)
                    else:
                        st.warning("No text detected by OCR.")
            except ImportError:
                logger.warning("Streamlit not available for display")

        return text

    except Exception as e:
        logger.error(f"OCR error on {image_path}: {e}")
        return ""
