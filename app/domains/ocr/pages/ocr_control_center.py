"""
OCR Control Center - Tour de Contrôle OCR

Interface de debug simplifiée pour diagnostiquer et réparer les problèmes OCR.
Fusionne ocr_page + problematic_tickets + pattern testing.
"""

import streamlit as st
import logging

# Configure detailed logging for debug
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

from domains.ocr.pages.ocr_page import (
    interface_own_scans,
    interface_export_logs
)
from domains.ocr.pages.problematic_tickets import (
    render_problematic_tickets_page as render_problematic_section
)
from domains.ocr.pages.pipeline_debug_tab import render_pipeline_debug_tab


def render_pattern_testing_tab():
    """Tab for testing new OCR patterns."""
    st.subheader("🧪 Tester Nouveaux Patterns OCR")
    
    st.markdown("""
    ### 💡 Comment ça marche ?
    
    1. **Uploadez un ticket** problématique
    2. **Test automatique** avec patterns actuels
    3. **Ajoutez un nouveau pattern** et testez
    4. **Sauvegardez** si ça améliore la détection
    """)
    
    # Upload ticket
    uploaded_file = st.file_uploader(
        "📎 Upload ticket (JPG, PNG, PDF)",
        type=['jpg', 'jpeg', 'png', 'pdf']
    )
    
    if uploaded_file:
        # Save temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        # Extract text
        st.info("📖 Extraction du texte OCR...")
        
        if uploaded_file.name.lower().endswith('.pdf'):
            from domains.ocr.parsers_OLD_BACKUP import extract_text_from_pdf
            ocr_text = extract_text_from_pdf(tmp_path)
        else:
            from domains.ocr import full_ocr
            ocr_text = full_ocr(tmp_path)
        
        # Show preview
        with st.expander("📄 Texte OCR extrait (preview)"):
            st.code(ocr_text[:500] + "..." if len(ocr_text) > 500 else ocr_text)
        
        st.markdown("---")
        
        # Parse with current patterns
        st.markdown("### 📊 Détection Actuelle")
        
        # Enable detailed logging
        logger = logging.getLogger('modules.ocr.parsers')
        logger.setLevel(logging.INFO)
        
        from domains.ocr.parsers import parse_ticket_metadata_v2
        
        # Capture logs in expander
        with st.expander("🔍 Logs de détection (détaillés)", expanded=False):
            result = parse_ticket_metadata_v2(ocr_text)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Montant détecté", f"{result['montant']:.2f} €")
        with col2:
            reliability_icon = "✅" if result['fiable'] else "⚠️"
            st.metric("Fiabilité", reliability_icon)
        with col3:
            st.metric("Méthode", result['methode_detection'])
        
        # Debug info
        with st.expander("🔬 Détails debug"):
            st.json(result['debug_info'])
        
        st.markdown("---")
        
        # Test new pattern
        st.markdown("### 🧪 Tester Nouveau Pattern")
        
        new_pattern = st.text_input(
            "Pattern regex à tester",
            placeholder="Ex: PAYÉ|SOLDE|RESTE",
            help="Entrez un pattern regex pour tester la détection"
        )
        
        if new_pattern and st.button("🔬 Tester ce pattern"):
            from domains.ocr.parsers_OLD_BACKUP import test_patterns_on_ticket
            
            test_result = test_patterns_on_ticket(ocr_text, [new_pattern])
            
            st.markdown("#### 📈 Résultats")
            
            comparison = test_result['comparison']
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric(
                    "Standard",
                    f"{comparison['original_montant']:.2f} €",
                    help=f"Méthode: {comparison['original_method']}"
                )
            with col_b:
                delta = comparison['new_montant'] - comparison['original_montant']
                st.metric(
                    "Avec nouveau pattern",
                    f"{comparison['new_montant']:.2f} €",
                    delta=f"{delta:+.2f} €" if delta != 0 else "Aucun changement"
                )
            
            if test_result['improvement']:
                st.success("✅ Ce pattern améliore la détection !")
                st.info(" | ".join(test_result['improvement_reason']))
                
                if st.button("💾 Sauvegarder ce pattern"):
                    from domains.ocr import get_pattern_manager
                    
                    pm = get_pattern_manager()
                    pm.add_amount_pattern(
                        pattern=new_pattern,
                        description=f"Pattern ajouté via UI le {st.session_state.get('today', 'unknown')}",
                        priority=50
                    )
                    st.success("✅ Pattern sauvegardé dans config/ocr_patterns.yml !")
                    st.info("💡 Rechargez l'application pour que le pattern soit actif")
            else:
                st.info("ℹ️ Pas d'amélioration avec ce pattern")
        
        # Cleanup temp file
        try:
            os.unlink(tmp_path)
        except:
            pass


def render_ocr_control_center():
    """Main OCR Control Center interface."""
    st.title("🔍 OCR - Tour de Contrôle")
    
    st.markdown("""
    Interface de debug pour diagnostiquer et réparer les problèmes OCR.
    """)
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Statistiques OCR",
        "🚨 Tickets Problématiques",
        "🔬 Pipeline Debug",
        "🧪 Tester Patterns",
        "📦 Export Logs"
    ])
    
    with tab1:
        # Stats from ocr_page
        interface_own_scans()
    
    with tab2:
        # Problematic tickets
        render_problematic_section()
    
    with tab3:
        # Pipeline step-by-step debug
        render_pipeline_debug_tab()
    
    with tab4:
        # Pattern testing
        render_pattern_testing_tab()
    
    with tab5:
        # Export logs
        interface_export_logs()


if __name__ == "__main__":
    render_ocr_control_center()
