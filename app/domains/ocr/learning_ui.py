"""
OCR Learning UI Integration

Integrates learning system into OCR workflow when detection fails.
"""

import streamlit as st
from domains.ocr.learning_service import analyze_user_correction


def show_learning_suggestion(ocr_text: str, detected_amount: float, is_reliable: bool):
    """
    Display learning suggestion when OCR fails or is unreliable.
    
    Args:
        ocr_text: Raw OCR text
        detected_amount: Amount detected (may be 0 or unreliable)
        is_reliable: Whether detection was reliable
    """
    if is_reliable:
        return  # No learning needed
    
    st.warning("⚠️ Détection OCR non fiable - Le système peut apprendre !")
    
    with st.expander("🧠 Aide le système à apprendre", expanded=True):
        st.markdown("""
        L'OCR n'a pas trouvé le montant avec les patterns existants.
        **Vous pouvez aider le système à s'améliorer !**
        """)
        
        # User correction input
        corrected_amount = st.number_input(
            "Quel est le montant correct ? (€)",
            min_value=0.0,
            step=0.01,
            key="learning_correction"
        )
        
        if st.button("✅ Analyser et suggérer pattern", key="analyze_correction"):
            if corrected_amount > 0:
                # Analyze correction
                analysis = analyze_user_correction(
                    ocr_text=ocr_text,
                    detected_amount=detected_amount,
                    corrected_amount=corrected_amount,
                    detection_methods=[]
                )
                
                # Display results
                if analysis.scan_error:
                    st.error("❌ Montant non trouvé dans le texte OCR")
                    st.info("💡 Possible erreur de scan. Vérifiez l'image du ticket.")
                
                elif analysis.found_in_text:
                    st.success(f"✅ Montant '{corrected_amount}€' trouvé dans OCR !")
                    
                    # Show suggested pattern
                    if analysis.suggested_pattern:
                        st.subheader("🎯 Pattern suggéré")
                        st.code(analysis.suggested_pattern, language='regex')
                        
                        # Show context
                        st.subheader("📝 Contexte")
                        for line in analysis.context_lines:
                            st.text(line)
                        
                        # Option to save
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Ajouter ce pattern", key="save_pattern"):
                                from domains.ocr.learning_service import save_learned_pattern
                                save_learned_pattern(
                                    analysis.suggested_pattern,
                                    "manual_correction",
                                    user_confirmed=True
                                )
                                st.success("🎉 Pattern ajouté ! OCR amélioré.")
                                st.balloons()
                        
                        with col2:
                            if st.button("❌ Ignorer", key="ignore_pattern"):
                                st.info("Pattern ignoré")
                
                elif analysis.already_detected:
                    st.info("ℹ️ Le montant était déjà correct")
            else:
                st.warning("Veuillez entrer un montant valide")
