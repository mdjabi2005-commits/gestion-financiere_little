def render_pipeline_debug_tab():
    """Tab for detailed OCR pipeline visualization."""
    st.subheader("🔬 Debug Pipeline OCR - Étape par Étape")
    
    st.markdown("""
    ### 💡 Visualisez exactement où le pipeline coince
    
    Upload un ticket et voyez chaque étape du processus :
    1. 📄 Extraction texte (OCR ou PDF)
    2. 🔡 Normalisation
    3. 🔍 Méthode A (Patterns)
    4. 💳 Méthode B (Paiement)
    5. 🧾 Méthode C (HT+TVA)
    6. ✅ Cross-validation
    """)
    
    # Upload
    uploaded_file = st.file_uploader(
        "📎 Upload ticket (JPG, PNG, PDF)",
        type=['jpg', 'jpeg', 'png', 'pdf'],
        key="pipeline_debug_upload"
    )
    
    if uploaded_file:
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        st.markdown("---")
        
        # ÉTAPE 1: Extraction
        st.markdown("### 📄 ÉTAPE 1: Extraction Texte")
        
        with st.spinner("Extraction en cours..."):
            if uploaded_file.name.lower().endswith('.pdf'):
                from domains.ocr.parsers_OLD_BACKUP import extract_text_from_pdf
                ocr_text = extract_text_from_pdf(tmp_path)
                method = "PDF (pdfminer)"
            else:
                from domains.ocr import full_ocr
                ocr_text = full_ocr(tmp_path)
                method = "Image (Tesseract OCR)"
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Méthode", method)
        with col2:
            st.metric("Caractères extraits", len(ocr_text))
        
        if len(ocr_text) < 10:
            st.error("❌ Texte trop court ! Problème d'extraction.")
            st.stop()
        else:
            st.success("✅ Texte extrait avec succès")
        
        with st.expander("📝 Voir texte brut"):
            st.code(ocr_text, language="text")
        
        st.markdown("---")
        
        # ÉTAPE 2: Normalisation
        st.markdown("### 🔡 ÉTAPE 2: Normalisation")
        
        from domains.ocr.parsers import _normalize_ocr_text
        
        lines = _normalize_ocr_text(ocr_text)
        
        st.metric("Lignes après normalisation", len(lines))
        
        with st.expander(f"📋 Voir lignes normalisées ({len(lines)} lignes)"):
            for i, line in enumerate(lines[:50], 1):  # Limit to 50
                st.text(f"{i:3d}. {line}")
            if len(lines) > 50:
                st.info(f"... et {len(lines) - 50} lignes supplémentaires")
        
        st.success("✅ Normalisation terminée")
        
        st.markdown("---")
        
        # ÉTAPE 3: Méthode A
        st.markdown("### 🔍 ÉTAPE 3: Méthode A - Pattern Matching")
        
        from domains.ocr.parsers import _detect_amount_method_a
        
        montants_a, patterns_matched = _detect_amount_method_a(lines)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Montants trouvés", len(montants_a))
        with col2:
            st.metric("Patterns matchés", len(patterns_matched))
        
        if montants_a:
            st.success(f"✅ Méthode A: {montants_a}")
            with st.expander("🔎 Patterns qui ont matché"):
                for pattern in patterns_matched:
                    st.code(pattern)
        else:
            st.warning("⚠️ Méthode A: Aucun montant trouvé")
        
        st.markdown("---")
        
        # ÉTAPE 4: Méthode B
        st.markdown("### 💳 ÉTAPE 4: Méthode B - Détection Paiement")
        
        from domains.ocr.parsers import _detect_amount_method_b
        
        montant_b = _detect_amount_method_b(lines)
        
        if montant_b > 0:
            st.success(f"✅ Méthode B: {montant_b}€")
        else:
            st.warning("⚠️ Méthode B: Aucun montant trouvé")
        
        st.markdown("---")
        
        # ÉTAPE 5: Méthode C
        st.markdown("### 🧾 ÉTAPE 5: Méthode C - HT+TVA")
        
        from domains.ocr.parsers import _detect_amount_method_c
        
        montant_c = _detect_amount_method_c(lines)
        
        if montant_c > 0:
            st.success(f"✅ Méthode C: {montant_c}€")
        else:
            st.info("ℹ️ Méthode C: Non applicable (pas de HT/TVA)")
        
        st.markdown("---")
        
        # ÉTAPE 6: Cross-validation
        st.markdown("### ✅ ÉTAPE 6: Cross-Validation & Résultat Final")
        
        from domains.ocr.parsers import parse_ticket_metadata_v2
        
        final_result = parse_ticket_metadata_v2(ocr_text)
        
        # Recap des méthodes
        st.markdown("#### 📊 Récapitulatif des méthodes")
        
        recap_data = {
            "Méthode A": montants_a if montants_a else ["Aucun"],
            "Méthode B": [f"{montant_b}€"] if montant_b > 0 else ["Aucun"],
            "Méthode C": [f"{montant_c}€"] if montant_c > 0 else ["Aucun"]
        }
        
        for method, values in recap_data.items():
            st.text(f"{method}: {', '.join(map(str, values))}")
        
        st.markdown("---")
        
        # Résultat final
        st.markdown("#### 🎯 Résultat Final")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💶 Montant", f"{final_result['montant']}€")
        with col2:
            reliability_icon = "✅" if final_result['fiable'] else "⚠️"
            st.metric("Fiabilité", reliability_icon)
        with col3:
            st.metric("Méthode gagnante", final_result['methode_detection'])
        
        if final_result['montant'] > 0:
            st.success("✅ Pipeline réussi ! Montant détecté.")
        else:
            st.error("❌ Pipeline échoué : Aucune méthode n'a trouvé de montant.")
            
            st.markdown("#### 💡 Diagnostic")
            
            if len(ocr_text) < 100:
                st.warning("⚠️ Texte trop court → Problème à l'étape 1 (Extraction)")
            elif not montants_a and montant_b == 0 and montant_c == 0:
                st.warning("⚠️ Aucune méthode n'a fonctionné → Patterns manquants ?")
                st.info("💡 Suggestion: Ajoutez de nouveaux patterns dans l'onglet 'Tester Patterns'")
            else:
                st.info("ℹ️ Certaines méthodes ont trouvé des montants mais la cross-validation a échoué")
        
        # Cleanup
        try:
            os.unlink(tmp_path)
        except:
            pass
