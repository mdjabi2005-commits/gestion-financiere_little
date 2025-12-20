"""
Problematic Tickets Page Module

This module provides an interface to review and reprocess tickets
that had unreliable amount detection.
"""

import os
import json
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any

from config import PROBLEMATIC_DIR
from domains.ocr.scanner import full_ocr
from domains.ocr.parsers_OLD_BACKUP import (
    parse_ticket_metadata, test_patterns_on_ticket,
    move_ticket_to_sorted, extract_text_from_pdf
)
from shared.ui import insert_transaction_batch
from shared.ui import toast_success, toast_error, toast_warning
from shared.utils import safe_convert, safe_date_convert


def get_problematic_tickets() -> List[Dict[str, Any]]:
    """
    Get all problematic tickets with their metadata.

    Returns:
        List of dictionaries containing ticket info and metadata
    """
    tickets = []

    if not os.path.exists(PROBLEMATIC_DIR):
        return tickets

    for filename in os.listdir(PROBLEMATIC_DIR):
        if filename.endswith('_metadata.json'):
            continue  # Skip metadata files

        # Look for image/PDF files
        if not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.pdf']):
            continue

        ticket_path = os.path.join(PROBLEMATIC_DIR, filename)
        metadata_path = os.path.splitext(ticket_path)[0] + "_metadata.json"

        # Load metadata if exists
        metadata = {}
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception as e:
                st.warning(f"Failed to load metadata for {filename}: {e}")

        tickets.append({
            'filename': filename,
            'path': ticket_path,
            'metadata': metadata
        })

    # Sort by move date (newest first)
    tickets.sort(
        key=lambda t: t['metadata'].get('moved_at', ''),
        reverse=True
    )

    return tickets


def render_problematic_tickets_page() -> None:
    """Render the problematic tickets review interface."""
    st.markdown("## 🔧 Tickets Problématiques")
    st.info(
        "Cette page affiche les tickets dont la détection du montant a échoué ou était peu fiable. "
        "Vous pouvez les retraiter manuellement ou tester de nouveaux patterns pour améliorer la détection."
    )

    tickets = get_problematic_tickets()

    if not tickets:
        st.success("✅ Aucun ticket problématique ! Tous vos tickets ont été traités avec succès.")
        return

    st.markdown(f"### 📋 {len(tickets)} ticket(s) en attente de traitement")

    # Display each ticket
    for idx, ticket_info in enumerate(tickets):
        filename = ticket_info['filename']
        ticket_path = ticket_info['path']
        metadata = ticket_info['metadata']

        with st.expander(f"🎫 {filename}", expanded=(idx == 0)):
            # Display metadata
            col_meta1, col_meta2 = st.columns(2)
            with col_meta1:
                st.metric("Montant détecté", f"{metadata.get('montant_detecte', 0):.2f} €")
                st.caption(f"Méthode: {metadata.get('methode_detection', 'UNKNOWN')}")
            with col_meta2:
                moved_at = metadata.get('moved_at', 'Unknown')
                if moved_at != 'Unknown':
                    try:
                        moved_dt = datetime.fromisoformat(moved_at)
                        st.caption(f"Déplacé le: {moved_dt.strftime('%d/%m/%Y %H:%M')}")
                    except:
                        st.caption(f"Déplacé le: {moved_at}")

            # Display potential patterns from metadata
            potential_patterns = metadata.get('potential_patterns', [])
            if potential_patterns:
                st.markdown("**🔍 Patterns potentiels détectés:**")
                for p in potential_patterns[:3]:
                    st.code(f"{p.get('pattern')} : {p.get('amount')}")

            # Display the ticket image/pdf
            if ticket_path.lower().endswith('.pdf'):
                st.caption("📄 Fichier PDF - Extraction de texte...")
                ocr_text = extract_text_from_pdf(ticket_path)
            else:
                st.image(ticket_path, caption=filename, use_container_width=True)
                ocr_text = full_ocr(ticket_path)

            # Parse with standard patterns
            data = parse_ticket_metadata(ocr_text)
            montant_auto = data.get('montant', 0.0)
            methode = data.get('methode_detection', 'UNKNOWN')
            fiable = data.get('fiable', False)

            st.markdown("**📊 Détection actuelle:**")
            col_det1, col_det2 = st.columns(2)
            with col_det1:
                st.metric("Montant", f"{montant_auto:.2f} €")
            with col_det2:
                reliability_color = "🟢" if fiable else "🔴"
                st.caption(f"{reliability_color} Méthode: {methode}")

            # Test new patterns section
            with st.form(f"test_patterns_{idx}"):
                st.markdown("**🧪 Tester de nouveaux patterns:**")
                test_patterns_input = st.text_area(
                    "Patterns à tester (un par ligne)",
                    help="Exemples: PAYÉ, SOLDE, RESTE À PAYER",
                    placeholder="PAYÉ\nSOLDE\nRESTE"
                )
                test_btn = st.form_submit_button("🔬 Tester ces patterns")

            if test_btn and test_patterns_input:
                # Parse patterns
                test_patterns = [p.strip() for p in test_patterns_input.split('\n') if p.strip()]

                # Test patterns
                result = test_patterns_on_ticket(ocr_text, test_patterns)

                st.markdown("**📈 Résultats du test:**")
                comparison = result['comparison']

                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.metric(
                        "Détection standard",
                        f"{comparison['original_montant']:.2f} €",
                        help=f"Méthode: {comparison['original_method']}"
                    )
                with col_r2:
                    delta = comparison['new_montant'] - comparison['original_montant']
                    st.metric(
                        "Avec nouveaux patterns",
                        f"{comparison['new_montant']:.2f} €",
                        delta=f"{delta:+.2f} €" if delta != 0 else None
                    )

                if result['improvement']:
                    st.success("✅ " + " | ".join(result['improvement_reason']))
                    st.info("💡 Ces patterns améliorent la détection. Pensez à les ajouter au système!")
                else:
                    st.info("ℹ️ Pas d'amélioration détectée avec ces patterns.")

            # Manual validation form
            with st.form(f"validate_{idx}"):
                st.markdown("**✅ Validation manuelle:**")

                col_v1, col_v2 = st.columns(2)
                with col_v1:
                    categorie = st.text_input("Catégorie", "Divers")
                    sous_categorie = st.text_input("Sous-catégorie", "Autre")
                with col_v2:
                    montant_final = st.number_input(
                        "Montant final (€)",
                        value=float(montant_auto),
                        min_value=0.0,
                        step=0.01
                    )
                    date_ticket = st.date_input("Date", datetime.now())

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    validate_btn = st.form_submit_button("✅ Valider et enregistrer", type="primary")
                with col_btn2:
                    delete_btn = st.form_submit_button("🗑️ Supprimer ce ticket")

            if validate_btn:
                if not categorie or montant_final <= 0:
                    toast_error("Catégorie et montant valides requis")
                else:
                    # Insert transaction
                    insert_transaction_batch([{
                        "type": "dépense",
                        "categorie": categorie.strip(),
                        "sous_categorie": sous_categorie.strip(),
                        "montant": montant_final,
                        "date": date_ticket.isoformat(),
                        "source": "OCR-Retraité"
                    }])

                    # Move to sorted
                    move_ticket_to_sorted(ticket_path, categorie, sous_categorie)

                    # Delete metadata file
                    metadata_path = os.path.splitext(ticket_path)[0] + "_metadata.json"
                    if os.path.exists(metadata_path):
                        try:
                            os.remove(metadata_path)
                        except Exception as e:
                            st.warning(f"Impossible de supprimer le métadata: {e}")

                    toast_success(f"✅ Ticket validé et enregistré : {montant_final:.2f} €")
                    st.rerun()

            if delete_btn:
                # Delete ticket and metadata
                try:
                    os.remove(ticket_path)
                    metadata_path = os.path.splitext(ticket_path)[0] + "_metadata.json"
                    if os.path.exists(metadata_path):
                        os.remove(metadata_path)
                    toast_success("🗑️ Ticket supprimé")
                    st.rerun()
                except Exception as e:
                    toast_error(f"Erreur lors de la suppression: {e}")


if __name__ == "__main__":
    render_problematic_tickets_page()
