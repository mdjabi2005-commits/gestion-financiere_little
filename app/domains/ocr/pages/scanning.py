"""
Scanning Page - UI Layer

Clean Streamlit interface using scanning_service for business logic.
This file contains ONLY UI code - no business logic.
"""

import streamlit as st
import logging
from typing import List

from domains.ocr.scanning_service import (
    scan_ticket_files,
    process_single_ticket,
    validate_ticket_data,
    deduce_subcategory,
    prepare_ticket_for_db,
    TicketData
)
from domains.ocr.pages.scanning_db import save_ticket_to_database, move_ticket_file, log_ticket_scan
from shared.ui import toast_success, toast_warning, toast_error
from shared.utils import safe_convert, safe_date_convert

logger = logging.getLogger(__name__)


def render_ticket_card(ticket: TicketData, index: int):
    """Render single ticket with edit form."""
    st.markdown("---")
    st.markdown(f"### 🧾 {ticket.filename}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Montant", f"{ticket.montant}€")
    with col2:
        reliability = "✅" if ticket.fiable else "⚠️"
        st.caption(f"{reliability} {ticket.methode_detection}")
        
        st.markdown(f"""
        - **Montant :** {ticket.montant}€ {reliability}
        - **Date :** {ticket.date}
        - **Méthode :** {ticket.methode_detection}
        """)
        
    if ticket.sous_categorie == "Autre":
        ticket.sous_categorie = deduce_subcategory(ticket)
    
    st.caption(f"🧠 Suggéré: {ticket.categorie} → {ticket.sous_categorie}")
    
    if not ticket.fiable:
        st.warning("⚠️ Montant peu fiable - Vérifiez SVP")
        
        # Show learning suggestion
        from domains.ocr.learning_ui import show_learning_suggestion
        show_learning_suggestion(
            ocr_text=ticket.ocr_text,
            detected_amount=ticket.montant,
            is_reliable=ticket.fiable
        )
    
    with st.form(f"form_{index}"):
        col1, col2 = st.columns(2)
        with col1:
            cat = st.text_input("Catégorie", ticket.categorie)
            subcat = st.text_input("Sous-catégorie", ticket.sous_categorie)
        with col2:
            amount = st.number_input("Montant (€)", value=float(ticket.montant), min_value=0.0, step=0.01)
            date = st.date_input("Date", safe_date_convert(ticket.date))
        
        desc = st.text_input("Description", placeholder="Optionnel")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submit = st.form_submit_button("✅ Valider", type="primary")
        with col_btn2:
            mark = st.form_submit_button("⚠️ Problématique")
        
        if submit:
            ticket.categorie = cat.strip()
            ticket.sous_categorie = subcat.strip()
            ticket.montant = safe_convert(amount)
            ticket.date = date.isoformat()
            
            is_valid, errors = validate_ticket_data(ticket)
            if not is_valid:
                for err in errors:
                    toast_error(err)
                return False
            
            try:
                data = prepare_ticket_for_db(ticket)
                data['description'] = desc.strip()
                
                tx_id = save_ticket_to_database(data)
                move_ticket_file(ticket.path, ticket.categorie, ticket.sous_categorie, tx_id)
                log_ticket_scan(
                    ticket.filename,
                    [ticket.montant],
                    ticket.montant,
                    ticket.categorie,
                    ticket.sous_categorie,
                    ticket.methode_detection,
                    ticket.ocr_text
                )
                
                toast_success(f"✅ {ticket.montant}€ enregistré")
                return True
            except Exception as e:
                logger.error(f"Save failed: {e}")
                toast_error(f"Erreur: {e}")
                return False
        
        if mark:
            toast_warning(f"Marqué: {ticket.filename}")
            return True
    
    return False


def process_all_tickets_in_folder():
    """Main scanning interface."""
    st.subheader("🧾 Scanner les tickets")
    
    files = scan_ticket_files()
    if not files:
        st.info("📂 Aucun ticket à scanner")
        return
    
    st.success(f"🧮 {len(files)} ticket(s)")
    
    tickets = []
    with st.spinner("🔍 OCR..."):
        for f in files:
            tickets.append(process_single_ticket(f))
    
    st.markdown("### 📋 Tickets détectés")
    
    count = 0
    for i, t in enumerate(tickets):
        if render_ticket_card(t, i):
            count += 1
    
    if count > 0:
        st.success(f"✅ {count} traité(s)")
        if st.button("🔄 Actualiser"):
            st.rerun()
