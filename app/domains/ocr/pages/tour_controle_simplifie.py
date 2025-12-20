"""
Tour de Contrôle OCR - Version Simplifiée

Page légère centrée sur workflow de support :
1. Analyser tickets problématiques
2. Visualiser logs OCR
3. Gérer patterns
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from config import OCR_LOGS_DIR, OCR_SCAN_LOG, OCR_PERFORMANCE_LOG, PATTERN_STATS_LOG
from domains.ocr.parsers import parse_ticket_metadata_v2
from domains.ocr.scanner import full_ocr
from domains.ocr.learning_ui import show_learning_suggestion
from domains.ocr.export_logs import get_logs_summary, export_logs_to_desktop
from shared.logging_config import get_logger

logger = get_logger(__name__)


def load_scan_history(limit: int = 10) -> List[Dict]:
    """Load recent scans from scan_history.jsonl."""
    scans = []
    try:
        if os.path.exists(OCR_SCAN_LOG):
            with open(OCR_SCAN_LOG, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Get last N lines
                for line in lines[-limit:]:
                    try:
                        scans.append(json.loads(line))
                    except:
                        pass
            scans.reverse()  # Most recent first
    except Exception as e:
        logger.error(f"Error loading scan history: {e}")
    return scans


def load_performance_stats() -> Dict:
    """Load performance statistics."""
    try:
        if os.path.exists(OCR_PERFORMANCE_LOG):
            with open(OCR_PERFORMANCE_LOG, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}


def load_pattern_stats() -> Dict:
    """Load pattern reliability statistics."""
    try:
        if os.path.exists(PATTERN_STATS_LOG):
            with open(PATTERN_STATS_LOG, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}


def render_analyze_ticket_tab():
    """Tab 1: Analyze problematic tickets."""
    st.subheader("🎫 Analyser Ticket Problématique")
    
    st.markdown("""
    Uploadez un ticket qui pose problème pour voir les résultats de détection.
    Si l'OCR échoue, le système d'apprentissage vous aidera à créer un nouveau pattern.
    """)
    
    # Upload ticket
    uploaded_file = st.file_uploader(
        "📎 Upload ticket (JPG, PNG, PDF)",
        type=['jpg', 'jpeg', 'png', 'pdf'],
        key="analyze_ticket_upload"
    )
    
    if uploaded_file:
        # Save temp
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        
        try:
            # Extract OCR
            with st.spinner("🔍 Extraction OCR..."):
                if uploaded_file.name.lower().endswith('.pdf'):
                    from domains.ocr.parsers_OLD_BACKUP import extract_text_from_pdf
                    ocr_text = extract_text_from_pdf(tmp_path)
                else:
                    ocr_text = full_ocr(tmp_path)
            
            # Show OCR text
            with st.expander("📄 Texte OCR brut", expanded=False):
                st.text_area("", ocr_text, height=200, key="ocr_text_display")
            
            # Parse
            with st.spinner("🔍 Analyse..."):
                result = parse_ticket_metadata_v2(ocr_text)
            
            # Show results
            st.markdown("### 📊 Résultats Détection")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Montant Détecté", f"{result.get('montant', 0):.2f} €")
            with col2:
                fiable = result.get('fiable', False)
                st.metric("Fiabilité", "✅ Fiable" if fiable else "⚠️ Peu fiable")
            with col3:
                st.metric("Méthode", result.get('methode_detection', 'NONE'))
            
            # Method details
            with st.expander("🔍 Détails Méthodes Testées"):
                st.markdown(f"""
                **Méthode utilisée** : {result.get('methode_detection', 'NONE')}
                
                **Cross-validation** : {'✅ Oui' if result.get('fiable') else '❌ Non'}
                
                Les 4 méthodes (A, B, C, D) ont été testées en parallèle.
                """)
            
            # Learning system if unreliable
            if not result.get('fiable', False):
                st.warning("⚠️ Détection peu fiable - Le système peut apprendre !")
                show_learning_suggestion(
                    ocr_text=ocr_text,
                    detected_amount=result.get('montant', 0),
                    is_reliable=False
                )
        
        finally:
            # Cleanup
            try:
                os.unlink(tmp_path)
            except:
                pass


def render_logs_overview_tab():
    """Tab 2: OCR logs overview."""
    st.subheader("📊 Logs OCR - Vue d'ensemble")
    
    # Get summary
    summary = get_logs_summary()
    
    # Stats rapides
    st.markdown("### 📈 Statistiques Globales")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Scans", summary.get('total_scans', 0))
    
    # Calculate stats from performance data
    perf = summary.get('performance_by_type', {})
    total_success = sum(p.get('success_rate', 0) * p.get('total', 0) for p in perf.values())
    total_scans = sum(p.get('total', 0) for p in perf.values())
    avg_success = (total_success / total_scans) if total_scans > 0 else 0
    
    with col2:
        st.metric("Taux Succès", f"{avg_success:.1f}%")
    
    with col3:
        st.metric("Patterns Trouvés", summary.get('potential_patterns_count', 0))
    
    with col4:
        st.metric("Fichiers Logs", len(summary.get('log_files', [])))
    
    st.markdown("---")
    
    # Performance by type
    if perf:
        st.markdown("### 📋 Performance par Type Document")
        
        for doc_type, stats in perf.items():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{doc_type.title()}**")
            with col2:
                st.write(f"{stats.get('total', 0)} scans")
            with col3:
                success_rate = stats.get('success_rate', 0)
                color = "🟢" if success_rate >= 90 else "🟡" if success_rate >= 70 else "🔴"
                st.write(f"{color} {success_rate:.1f}%")
        
        st.markdown("---")
    
    # Recent scans
    st.markdown("### 🕒 Derniers Scans")
    scans = load_scan_history(limit=10)
    
    if scans:
        for scan in scans:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.write(f"**{scan.get('filename', 'N/A')}**")
                
                with col2:
                    dt = datetime.fromisoformat(scan.get('timestamp', ''))
                    st.caption(dt.strftime('%d/%m %H:%M'))
                
                with col3:
                    success = scan.get('success_level', 'failed')
                    icon = "✅" if success == "exact" else "⚠️" if success == "partial" else "❌"
                    st.write(f"{icon} {success}")
                
                with col4:
                    st.write(f"{scan.get('montant_choisi', 0):.2f}€")
                
                st.markdown("---")
    else:
        st.info("Aucun scan enregistré")
    
    # Export buttons
    st.markdown("### 📥 Export")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Exporter pour Support", key="export_support"):
            try:
                zip_path = export_logs_to_desktop()
                st.success(f"✅ Logs exportés : {os.path.basename(zip_path)}")
                st.info(f"📂 Fichier créé sur le Bureau")
            except Exception as e:
                st.error(f"Erreur : {e}")


def render_patterns_list_tab():
    """Tab 3: Current patterns list with performance."""
    st.subheader("📋 Patterns Actuels")
    
    # Load all patterns from config
    import yaml
    patterns_config_path = Path("config/ocr_patterns.yml")
    all_patterns = {}
    
    if patterns_config_path.exists():
        with open(patterns_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
            # Extract all patterns
            for method_key in ['amount_patterns', 'payment_patterns', 'ht_tva_patterns']:
                patterns_list = config.get(method_key, [])
                for pattern_item in patterns_list:
                    if isinstance(pattern_item, dict):
                        pattern_name = pattern_item.get('label', pattern_item.get('pattern', 'Unknown'))
                    else:
                        pattern_name = str(pattern_item)
                    
                    all_patterns[pattern_name] = {
                        'method': method_key.replace('_patterns', '').upper(),
                        'pattern': pattern_item
                    }
    
    # Load stats
    pattern_stats = load_pattern_stats()
    
    # Create 2 sections
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### ✅ Patterns Actifs")
        st.caption(f"**{len(all_patterns)} patterns** disponibles dans la config")
        
        # Group by method
        methods = {}
        for name, info in all_patterns.items():
            method = info['method']
            if method not in methods:
                methods[method] = []
            
            # Get stats if available
            stats = pattern_stats.get(name, {})
            methods[method].append({
                'name': name,
                'detections': stats.get('total_detections', 0),
                'success_rate': stats.get('success_rate', 0),
                'used': name in pattern_stats
            })
        
        # Display by method
        for method_name, patterns in methods.items():
            with st.expander(f"**Méthode {method_name}** ({len(patterns)} patterns)", expanded=True):
                for p in patterns:
                    col_a, col_b = st.columns([3, 1])
                    
                    with col_a:
                        # Color based on usage
                        if p['used']:
                            st.write(f"✅ **{p['name']}**")
                        else:
                            st.write(f"⚪ {p['name']}")
                    
                    with col_b:
                        if p['used']:
                            st.caption(f"{p['detections']} uses")
                
                st.markdown("---")
    
    with col2:
        st.markdown("### ⭐ Performance")
        
        if pattern_stats:
            st.caption(f"**{len(pattern_stats)} patterns** utilisés avec stats")
            
            # Sort by success rate
            sorted_patterns = sorted(
                pattern_stats.items(),
                key=lambda x: (x[1].get('success_rate', 0), x[1].get('total_detections', 0)),
                reverse=True
            )
            
            # Top performers
            st.markdown("**🏆 Top Performers**")
            for pattern_name, stats in sorted_patterns[:10]:
                success_rate = stats.get('success_rate', 0)
                detections = stats.get('total_detections', 0)
                
                # Color by performance
                if success_rate >= 90:
                    icon = "🟢"
                elif success_rate >= 70:
                    icon = "🟡"
                else:
                    icon = "🔴"
                
                col_a, col_b, col_c = st.columns([2, 1, 1])
                with col_a:
                    st.write(f"{icon} **{pattern_name}**")
                with col_b:
                    st.caption(f"{detections}×")
                with col_c:
                    st.caption(f"{success_rate:.0f}%")
            
            st.markdown("---")
            
            # Low performers
            low_performers = [p for p in sorted_patterns if p[1].get('success_rate', 0) < 70]
            if low_performers:
                st.markdown("**⚠️ À Améliorer**")
                for pattern_name, stats in low_performers[:5]:
                    success_rate = stats.get('success_rate', 0)
                    detections = stats.get('total_detections', 0)
                    
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.write(f"🔴 **{pattern_name}**")
                    with col_b:
                        st.caption(f"{success_rate:.0f}% ({detections}×)")
        else:
            st.info("Aucune statistique disponible")
    
    st.markdown("---")
    
    # Learned patterns section
    st.markdown("### 🧠 Patterns Appris (Système d'Apprentissage)")
    
    learned_path = Path("config/ocr_patterns_learned.yml")
    if learned_path.exists():
        with open(learned_path, 'r', encoding='utf-8') as f:
            learned_config = yaml.safe_load(f)
        
        learned_patterns = learned_config.get('learned_patterns', [])
        
        if learned_patterns:
            col1, col2 = st.columns(2)
            
            for idx, pattern in enumerate(learned_patterns):
                with col1 if idx % 2 == 0 else col2:
                    with st.container():
                        col_a, col_b = st.columns([3, 1])
                        
                        with col_a:
                            st.write(f"**{pattern.get('pattern', 'N/A')}**")
                            st.caption(f"Source: {pattern.get('source', 'N/A')}")
                        
                        with col_b:
                            confirmed = pattern.get('user_confirmed', False)
                            confidence = pattern.get('confidence', 0)
                            st.write("✅" if confirmed else "⏳")
                            st.caption(f"{confidence*100:.0f}%")
                        
                        st.markdown("---")
        else:
            st.info("Aucun pattern appris pour le moment")
    else:
        st.info("Fichier de patterns appris non trouvé")


def render_tour_controle_simple():
    """Main function: Simplified OCR Control Center."""
    st.title("🔍 Tour de Contrôle OCR")
    
    st.markdown("""
    Interface simplifiée pour analyser les tickets problématiques et améliorer la détection OCR.
    """)
    
    # 3 tabs
    tabs = st.tabs(["🎫 Analyser Ticket", "📊 Logs OCR", "📋 Patterns"])
    
    with tabs[0]:
        render_analyze_ticket_tab()
    
    with tabs[1]:
        render_logs_overview_tab()
    
    with tabs[2]:
        render_patterns_list_tab()
