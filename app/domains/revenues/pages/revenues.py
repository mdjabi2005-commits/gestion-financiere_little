"""
Revenues Page - UI Layer

Clean Streamlit interface for revenue processing.
Business logic in revenues_service, DB in revenues_db.
"""

import streamlit as st
import logging
from typing import List

from domains.revenues.revenues_service import (
    scan_revenue_files,
    process_single_revenue,
    validate_revenue_data,
    prepare_revenue_for_db,
    RevenueData
)
from domains.revenues.revenues_db import (
    save_revenue_to_database,
    move_revenue_file,
    log_revenue_scan
)
from domains.revenues import is_uber_transaction
from shared.ui import toast_success, toast_warning, toast_error
from shared.utils import safe_convert

logger = logging.getLogger(__name__)


def render_revenue_card(revenue: RevenueData, index: int):
    """Render single revenue with edit form."""
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        st.write("💹")
        filename_short = revenue.filename[:20] + "..." if len(revenue.filename) > 20 else revenue.filename
        st.caption(f"📄 {filename_short}")
    
    with col2:
        cat = st.text_input(
            "Catégorie",
            revenue.categorie,
            key=f"cat_{index}",
            label_visibility="collapsed"
        )
        subcat = st.text_input(
            "Sous-catégorie",
            revenue.sous_categorie,
            key=f"subcat_{index}",
            label_visibility="collapsed"
        )
        
        col_date, col_desc = st.columns(2)
        with col_date:
            date = st.date_input(
                "Date", revenue.date,
                key=f"date_{index}",
                label_visibility="collapsed"
            )
        with col_desc:
            desc = st.text_input(
                "Description",
                revenue.description,
                key=f"desc_{index}",
                placeholder="Description...",
                label_visibility="collapsed"
            )
    
    with col3:
        amount = st.text_input(
            "Montant",
            f"{revenue.montant:.2f}",
            key=f"amount_{index}",
            label_visibility="collapsed"
        )
        amount_val = safe_convert(amount)
        st.markdown(
            f"<p style='color: #00D4AA; text-align: right; font-weight: bold; font-size: 18px;'>+{amount_val:.2f} €</p>",
            unsafe_allow_html=True
        )
    
    # Update revenue
    revenue.categorie = cat.strip()
    revenue.sous_categorie = subcat.strip()
    revenue.montant = amount_val
    revenue.date = date
    revenue.description = desc.strip()
    
    return revenue


def interface_process_all_revenues_in_folder():
    """
    Main revenues scanning interface - UI ONLY.
    """
    st.subheader("📥 Scanner les revenus")
    
    # Session state
    if "revenus_data" not in st.session_state:
        st.session_state["revenus_data"] = []
    
    # Scan button
    if st.button("🚀 Scanner tous les revenus") and not st.session_state["revenus_data"]:
        files = scan_revenue_files()
        
        if not files:
            toast_warning("Aucun PDF trouvé")
            return
        
        revenues = []
        with st.spinner(f"📄 Traitement de {len(files)} PDF..."):
            for f in files:
                rev = process_single_revenue(f)
                if rev:
                    revenues.append(rev)
        
        st.session_state["revenus_data"] = revenues
        toast_success(f"✅ {len(revenues)} revenu(s) scanné(s)")
    
    # Display revenues
    if st.session_state.get("revenus_data"):
        revenues: List[RevenueData] = st.session_state["revenus_data"]
        
        st.markdown(f"### 📋 {len(revenues)} revenu(s) à valider")
        st.markdown("---")
        
        updated_revenues = []
        for i, rev in enumerate(revenues):
            updated_rev = render_revenue_card(rev, i)
            updated_revenues.append(updated_rev)
            st.markdown("---")
        
        st.session_state["revenus_data"] = updated_revenues
        
        # Uber tax checkbox
        has_uber = any(is_uber_transaction(r.categorie, "") for r in updated_revenues)
        apply_uber_tax = False
        
        if has_uber:
            st.warning("🚗 Revenus Uber détectés")
            apply_uber_tax = st.checkbox(
                "✅ Appliquer taxe Uber (21%)",
                value=True,
                help="Prélèvement 21% sur revenus Uber"
            )
        
        # Confirm button
        if st.button("✅ Confirmer et enregistrer", type="primary"):
            success_count = 0
            
            for rev in updated_revenues:
                is_valid, errors = validate_revenue_data(rev)
                if not is_valid:
                    for err in errors:
                        toast_error(f"{rev.filename}: {err}")
                    continue
                
                try:
                    data = prepare_revenue_for_db(rev, apply_uber_tax)
                    tx_id = save_revenue_to_database(data)
                    move_revenue_file(rev.path, rev.categorie, rev.sous_categorie, tx_id)
                    log_revenue_scan(
                        rev.filename,
                        rev.montant_initial,
                        rev.montant,
                        rev.categorie,
                        rev.sous_categorie
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Save failed for {rev.filename}: {e}")
                    toast_error(f"Erreur: {rev.filename}")
            
            toast_success(f"✅ {success_count} revenu(s) enregistré(s)")
            st.session_state.pop("revenus_data")
            st.rerun()
