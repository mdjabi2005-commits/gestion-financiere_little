"""
OCR Analysis Page Module

This module contains the complete OCR analysis interface for diagnostics and performance monitoring.
Copied from orc.py
"""

import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Optional

from config import OCR_PERFORMANCE_LOG, PATTERN_STATS_LOG, OCR_SCAN_LOG
from shared.ui import toast_success, toast_error, toast_warning
from domains.ocr.diagnostics import (
    get_ocr_performance_report,
    get_best_patterns,
    get_worst_patterns,
    get_scan_history,
    analyze_external_log,
    diagnose_ocr_patterns
)
from domains.ocr.export_logs import (
    get_logs_summary,
    prepare_logs_for_support,
    export_logs_to_desktop
)


def interface_ocr_analysis_complete() -> None:
    """
    Complete OCR analysis interface - Control Tower.

    Features:
    - Analyze your own scans
    - Analyze external logs
    - Compare multiple logs
    - Complete diagnostic with recommendations

    Returns:
        None
    """
    st.title("🔍 Analyse OCR Complète - Tour de Contrôle")
    st.markdown("Analysez vos propres scans ou diagnostiquez les logs de vos utilisateurs")

    # Choix du mode
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Mes propres scans",
        "🔬 Analyser logs externes",
        "📈 Comparaison",
        "🛠️ Diagnostic complet",
        "📦 Exporter pour Support"
    ])

    with tab1:
        # Interface existante pour vos propres logs
        interface_own_scans()

    with tab2:
        # Nouvelle interface pour analyser les logs des utilisateurs
        interface_external_logs()

    with tab3:
        # Comparaison entre différents logs
        interface_comparison()

    with tab4:
        # Diagnostic approfondi avec recommandations
        interface_diagnostic()

    with tab5:
        # Export des logs pour le support
        interface_export_logs()


def interface_own_scans() -> None:
    """Analyse de vos propres scans (interface originale améliorée)."""

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Performance",
        "✅ Patterns fiables",
        "⚠️ Patterns à corriger",
        "📋 Historique",
        "📊 Statistiques détaillées"
    ])

    with tab1:
        st.subheader("📊 Performance Globale")

        # Charger les stats depuis vos fichiers locaux
        perf = get_ocr_performance_report()

        # DEBUG: Afficher ce qui a été chargé
        print(f"[DEBUG-ANALYSE] Fichier existe: {os.path.exists(OCR_PERFORMANCE_LOG)}")
        print(f"[DEBUG-ANALYSE] Contenu perf: {perf}")
        print(f"[DEBUG-ANALYSE] Type perf: {type(perf)}")
        print(f"[DEBUG-ANALYSE] Clés: {list(perf.keys()) if perf else 'None'}")

        # Vérifier si des données existent
        if not perf or (not perf.get('ticket') and not perf.get('revenu')):
            st.info("📊 **Aucune donnée OCR disponible pour le moment**")
            st.markdown(f"""
            ### 💡 Comment générer des statistiques ?

            Les statistiques OCR sont générées automatiquement lorsque vous :
            - 🧾 Scannez des tickets via l'interface OCR
            - 💼 Ajoutez des revenus avec OCR
            - 📸 Utilisez la fonction d'analyse de documents

            **Fichiers requis :**
            - `data/ocr_logs/performance_stats.json` - Statistiques de performance
            - `data/ocr_logs/pattern_stats.json` - Statistiques des patterns
            - `data/ocr_logs/scan_history.jsonl` - Historique des scans

            **📍 Localisation actuelle :**
            - Performance: `{"✅ Existe" if os.path.exists(OCR_PERFORMANCE_LOG) else "❌ Inexistant"}`
            - Patterns: `{"✅ Existe" if os.path.exists(PATTERN_STATS_LOG) else "❌ Inexistant"}`
            - Historique: `{"✅ Existe" if os.path.exists(OCR_SCAN_LOG) else "❌ Inexistant"}`

            🚀 **Commencez à scanner des documents pour voir les statistiques !**
            """)
        else:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("### 🧾 Tickets")
                if 'ticket' in perf:
                    ticket_stats = perf['ticket']
                    st.metric("Total scannés", ticket_stats.get('total', 0))
                    st.metric("Taux succès", f"{ticket_stats.get('success_rate', 0):.1f}%")
                    st.metric("Corrections", f"{ticket_stats.get('correction_rate', 0):.1f}%")
                else:
                    st.info("📭 Aucun ticket scanné")

            with col2:
                st.markdown("### 💼 Revenus")
                if 'revenu' in perf:
                    revenu_stats = perf['revenu']
                    st.metric("Total scannés", revenu_stats.get('total', 0))
                    st.metric("Taux succès", f"{revenu_stats.get('success_rate', 0):.1f}%")
                    st.metric("Corrections", f"{revenu_stats.get('correction_rate', 0):.1f}%")
                else:
                    st.info("📭 Aucun revenu scanné")

            with col3:
                st.markdown("### 📊 Global")
                total_scans = perf.get('ticket', {}).get('total', 0) + perf.get('revenu', {}).get('total', 0)

                if total_scans > 0:
                    avg_success = (
                        (perf.get('ticket', {}).get('success', 0) + perf.get('revenu', {}).get('success', 0))
                        / total_scans * 100
                    )
                    st.metric("Total documents", total_scans)
                    st.metric("Succès moyen", f"{avg_success:.1f}%")
                    st.metric("Dernière MAJ", perf.get('last_updated', 'N/A')[:10])
                else:
                    st.info("📭 Aucune donnée")

    with tab2:
        st.subheader("✅ Patterns les plus fiables")

        min_detections = st.slider("🔢 Détections minimum", 1, 20, 5, key="min_detections_slider")
        min_success = st.slider("📈 Taux succès minimum (%)", 50, 100, 70, key="min_success_slider")

        best = get_best_patterns(min_detections, min_success)

        if best:
            st.success(f"✨ **{len(best)} patterns fiables trouvés** avec au moins {min_detections} détections et {min_success}% de succès")

            df = pd.DataFrame(best)

            # Graphique
            fig = px.bar(
                df.head(20),
                x='pattern',
                y='reliability_score',
                color='success_rate',
                title='🏆 Top 20 Patterns Fiables',
                labels={'reliability_score': 'Score de fiabilité', 'pattern': 'Pattern'},
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Tableau
            st.dataframe(df, use_container_width=True)
        else:
            st.info("📊 **Aucun pattern fiable avec ces critères**")
            st.markdown(f"""
            ### 💡 Pourquoi aucun pattern n'est affiché ?

            **Raisons possibles :**
            - 📭 Aucun document n'a encore été scanné
            - 🔍 Les critères de filtrage sont trop stricts
            - 📉 Les patterns détectés n'atteignent pas les seuils minimum

            **Solutions :**
            1. 🔧 Réduisez les critères de filtrage ci-dessus
            2. 🧾 Scannez plus de documents pour générer des statistiques
            3. 📍 Vérifiez que le fichier `data/ocr_logs/pattern_stats.json` existe

            **État actuel :**
            - Fichier patterns: `{"✅ Existe" if os.path.exists(PATTERN_STATS_LOG) else "❌ Inexistant - Créez-le en scannant des documents"}`

            🚀 **Astuce :** Commencez par scanner quelques tickets pour alimenter les statistiques !
            """)

    with tab3:
        st.subheader("⚠️ Patterns problématiques")

        worst = get_worst_patterns(3, 50)

        if worst:
            df = pd.DataFrame(worst)

            # Alerte
            st.warning(f"🚨 **{len(worst)} patterns nécessitent une amélioration**")

            # Graphique des échecs
            fig = px.scatter(
                df,
                x='detections',
                y='success_rate',
                size='corrections',
                color='success_rate',
                hover_data=['pattern'],
                title='⚠️ Patterns Problématiques (taille = corrections)',
                labels={'success_rate': 'Taux de succès (%)', 'detections': 'Nombre de détections'},
                color_continuous_scale='RdYlGn'
            )
            fig.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="🚨 Seuil critique")
            st.plotly_chart(fig, use_container_width=True)

            # Recommandations
            st.markdown("### 💡 Recommandations d'Amélioration")
            for idx, row in df.iterrows():
                if row['success_rate'] < 30:
                    st.error(f"🔴 **{row['pattern']}** : Taux d'échec critique ({row['success_rate']:.1f}%) - {row['detections']} détections")
                elif row['success_rate'] < 40:
                    st.warning(f"🟠 **{row['pattern']}** : Nécessite attention urgente ({row['success_rate']:.1f}%) - {row['detections']} détections")
                else:
                    st.info(f"🟡 **{row['pattern']}** : À améliorer ({row['success_rate']:.1f}%) - {row['detections']} détections")
        else:
            toast_success("**Aucun pattern problématique détecté !**")
            st.markdown(f"""
            ### 🎉 Excellent travail !

            **Statut actuel :**
            - ✅ Tous les patterns détectés fonctionnent correctement
            - ✅ Aucun pattern n'a un taux d'échec supérieur à 50%
            - ✅ L'OCR fonctionne de manière optimale

            **Ou bien :**
            - 📭 Aucune donnée disponible (fichiers logs vides)
            - 🔍 Les patterns n'ont pas encore été testés suffisamment

            **Fichier patterns :**
            - État: `{"✅ Existe" if os.path.exists(PATTERN_STATS_LOG) else "❌ Inexistant - Commencez à scanner pour générer des stats"}`

            💡 **Conseil :** Continuez à scanner des documents pour maintenir ces bonnes performances !
            """)

    with tab4:
        st.subheader("📋 Historique des scans")

        col1, col2 = st.columns([2, 1])
        with col1:
            doc_type = st.selectbox("🗂️ Type de document", ["Tous", "ticket", "revenu"], key="doc_type_select")
        with col2:
            limit = st.number_input("📊 Nombre max", 10, 500, 50, step=10, key="limit_input")

        scans = get_scan_history(None if doc_type == "Tous" else doc_type, limit)

        if scans:
            # Conversion en DataFrame
            df_scans = pd.DataFrame(scans)

            st.success(f"**{len(df_scans)} scans trouvés** dans l'historique")

            # Graphique temporel
            if 'timestamp' in df_scans.columns:
                df_scans['timestamp'] = pd.to_datetime(df_scans['timestamp'])
                df_scans['success'] = df_scans['result'].apply(lambda x: x.get('success', False))

                # Évolution du taux de succès dans le temps
                daily_stats = df_scans.set_index('timestamp').resample('D')['success'].agg(['sum', 'count'])
                daily_stats['success_rate'] = daily_stats['sum'] / daily_stats['count'] * 100

                fig = px.line(
                    daily_stats.reset_index(),
                    x='timestamp',
                    y='success_rate',
                    title='📈 Évolution du Taux de Succès OCR',
                    labels={'success_rate': 'Taux de succès (%)', 'timestamp': 'Date'},
                    markers=True
                )
                fig.update_traces(line_color='#10b981', line_width=3)
                st.plotly_chart(fig, use_container_width=True)

            # Tableau détaillé
            st.markdown("### 📊 Derniers Scans")
            st.dataframe(df_scans[['timestamp', 'document_type', 'filename']].head(20), use_container_width=True)
        else:
            st.info("📭 **Aucun scan dans l'historique**")
            st.markdown(f"""
            ### 💡 Comment générer un historique ?

            **L'historique des scans se remplit automatiquement lorsque vous :**
            - 🧾 Scannez des tickets de caisse
            - 💼 Ajoutez des revenus avec reconnaissance OCR
            - 📸 Utilisez n'importe quelle fonction d'analyse de documents

            **Fichier d'historique :**
            - Chemin: `data/ocr_logs/scan_history.jsonl`
            - État: `{"✅ Existe" if os.path.exists(OCR_SCAN_LOG) else "❌ Inexistant - Sera créé au premier scan"}`

            **Structure attendue :**
            Chaque scan génère une entrée avec :
            - 📅 Timestamp (date et heure)
            - 📄 Type de document (ticket/revenu)
            - 📝 Nom du fichier
            - ✅ Résultat (succès/échec)

            🚀 **Commencez à scanner pour voir l'historique se remplir !**
            """)

    with tab5:
        st.subheader("📊 Statistiques détaillées")

        # Analyses avancées
        scans = get_scan_history(limit=1000)

        if scans:
            df = pd.DataFrame(scans)

            st.success(f"📈 **Analyse de {len(df)} scans** (limité à 1000 les plus récents)")

            col1, col2 = st.columns(2)

            with col1:
                # Distribution des montants
                st.markdown("### 💰 Distribution des montants")

                montants = []
                for scan in scans:
                    if 'extraction' in scan:
                        montant = scan['extraction'].get('montant_final', 0)
                        if montant > 0:
                            montants.append(montant)

                if montants:
                    fig = px.histogram(
                        montants,
                        nbins=30,
                        title="💵 Distribution des montants scannés",
                        labels={'value': 'Montant (€)', 'count': 'Fréquence'},
                        color_discrete_sequence=['#10b981']
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Statistiques
                    st.markdown(f"""
                    **📊 Statistiques des montants :**
                    - 💰 Total: {sum(montants):.2f} €
                    - 📊 Moyenne: {sum(montants)/len(montants):.2f} €
                    - 📈 Maximum: {max(montants):.2f} €
                    - 📉 Minimum: {min(montants):.2f} €
                    """)
                else:
                    st.info("💭 Aucun montant valide extrait des scans")

            with col2:
                # Catégories les plus fréquentes
                st.markdown("### 📂 Catégories détectées")

                categories = []
                for scan in scans:
                    if 'extraction' in scan:
                        cat = scan['extraction'].get('categorie_final', 'autres')
                        if cat:
                            categories.append(cat)

                if categories:
                    cat_counts = pd.Series(categories).value_counts().head(10)

                    fig = px.pie(
                        values=cat_counts.values,
                        names=cat_counts.index,
                        title="🏆 Top 10 Catégories",
                        color_discrete_sequence=px.colors.sequential.Greens_r
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    st.markdown(f"""
                    **📋 Répartition :**
                    - 🔢 Catégories uniques: {len(cat_counts)}
                    - 👑 Plus fréquente: {cat_counts.index[0]} ({cat_counts.values[0]} fois)
                    """)
                else:
                    st.info("💭 Aucune catégorie détectée dans les scans")

            # Graphique temporel additionnel
            st.markdown("### 📅 Activité de Scan")
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['date'] = df['timestamp'].dt.date

                daily_counts = df.groupby('date').size().reset_index(name='count')

                fig = px.bar(
                    daily_counts,
                    x='date',
                    y='count',
                    title='📊 Nombre de scans par jour',
                    labels={'date': 'Date', 'count': 'Nombre de scans'},
                    color='count',
                    color_continuous_scale='Greens'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 **Aucune statistique détaillée disponible**")
            st.markdown(f"""
            ### 💡 Génération des statistiques détaillées

            **Cette section affiche :**
            - 💰 Distribution des montants extraits par OCR
            - 📂 Répartition par catégories automatiques
            - 📅 Activité de scan journalière
            - 📈 Tendances et patterns d'utilisation

            **Pour générer ces statistiques :**
            1. 🧾 Scannez des tickets de caisse
            2. 💼 Ajoutez des revenus avec OCR
            3. 📸 Utilisez l'extraction automatique de données

            **Fichier requis :**
            - Chemin: `data/ocr_logs/scan_history.jsonl`
            - État: `{"✅ Existe" if os.path.exists(OCR_SCAN_LOG) else "❌ Inexistant - Créé automatiquement au premier scan"}`
            - Format: JSONL (une ligne JSON par scan)

            **Données extraites par scan :**
            - 📅 Timestamp
            - 💰 Montant (montant_final)
            - 📂 Catégorie (categorie_final)
            - ✅ Statut de réussite

            🚀 **Commencez à scanner pour voir des statistiques riches !**
            """)


def interface_external_logs() -> None:
    """Interface pour analyser des logs externes uploadés par les utilisateurs."""
    st.subheader("🔬 Analyse de Logs Externes")
    st.info("💡 **Feature to be implemented**")
    st.markdown("""
    This section will allow analyzing OCR logs from other users/instances.
    Upload functionality and detailed diagnostics coming soon.
    """)


def interface_comparison() -> None:
    """Interface de comparaison entre différents logs."""
    st.subheader("📈 Comparaison Multi-Sources")
    st.info("💡 **Feature to be implemented**")
    st.markdown("""
    This section will allow comparing performance across:
    - Different users
    - Time periods
    - Document types
    """)


def interface_diagnostic() -> None:
    """Interface de diagnostic complet."""
    st.subheader("🛠️ Diagnostic Complet OCR")
    st.info("💡 **Feature to be implemented**")
    st.markdown("""
    This section will provide comprehensive OCR diagnostics with:
    - Performance analysis
    - Pattern effectiveness
    - Improvement recommendations
    """)


def interface_export_logs() -> None:
    """Interface pour exporter les logs OCR pour le support."""
    st.subheader("📦 Export des Logs OCR pour Support")

    st.markdown("""
    ### 🎯 Objectif

    Cette fonctionnalité permet d'exporter tous vos logs OCR dans un fichier ZIP compressé
    que vous pouvez envoyer au support pour améliorer l'application.

    ### 📋 Contenu de l'export

    Le fichier ZIP contient :
    - 📊 **Historique des scans** : Tous les tickets/documents scannés
    - 🔍 **Patterns potentiels** : Nouveaux patterns détectés automatiquement
    - 📈 **Statistiques de performance** : Taux de réussite par type de document
    - 📉 **Patterns problématiques** : Patterns qui ont besoin d'amélioration
    - 📄 **Métadonnées des tickets problématiques** : Contexte des échecs de détection

    ### 🔒 Confidentialité

    - ✅ **Aucune image** de ticket n'est incluse
    - ✅ **Pas de données personnelles** sensibles
    - ✅ Uniquement des **métadonnées techniques** (montants, patterns, méthodes)
    - ✅ **100% sécurisé** pour l'envoi au support

    """)

    # Get logs summary
    summary = get_logs_summary()

    # Display current statistics
    st.markdown("### 📊 Statistiques actuelles")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de scans", summary.get('total_scans', 0))
    with col2:
        st.metric("Patterns potentiels", summary.get('potential_patterns_count', 0))
    with col3:
        st.metric("Fichiers de logs", len(summary.get('log_files', [])))

    # Performance by type
    if summary.get('performance_by_type'):
        st.markdown("### 📈 Performance par type de document")

        perf_data = []
        for doc_type, stats in summary['performance_by_type'].items():
            perf_data.append({
                "Type": doc_type,
                "Total scans": stats.get('total', 0),
                "Taux de réussite": f"{stats.get('success_rate', 0):.1f}%"
            })

        if perf_data:
            st.dataframe(perf_data, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Export options
    st.markdown("### 🚀 Exporter les logs")

    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        include_problematic = st.checkbox(
            "Inclure les métadonnées des tickets problématiques",
            value=True,
            help="Inclut les informations sur les tickets dont la détection a échoué (sans les images)"
        )

    with col_exp2:
        st.caption("📍 Le fichier sera créé sur votre Bureau")

    st.markdown("")

    if st.button("📦 Créer l'export pour le support", type="primary", use_container_width=True):
        try:
            with st.spinner("🔄 Préparation de l'export en cours..."):
                # Export to desktop
                zip_path = export_logs_to_desktop()

            st.success(f"✅ Export créé avec succès !")

            st.info(f"""
            📁 **Fichier créé :**
            `{os.path.basename(zip_path)}`

            📍 **Emplacement :**
            `{zip_path}`

            ### 📧 Prochaines étapes :

            1. Localisez le fichier sur votre Bureau
            2. Envoyez-le au support (voir instructions ci-dessous)
            3. Le support analysera vos logs pour améliorer la détection OCR

            **Le fichier sera automatiquement supprimé après 7 jours pour libérer de l'espace.**
            """)

            # Show file size
            if os.path.exists(zip_path):
                file_size = os.path.getsize(zip_path)
                size_mb = file_size / (1024 * 1024)
                st.caption(f"💾 Taille du fichier : {size_mb:.2f} MB")

        except Exception as e:
            st.error(f"❌ Erreur lors de la création de l'export : {e}")
            st.exception(e)

    st.markdown("---")

    # Instructions for sending to support
    st.markdown("""
    ### 📧 Comment envoyer les logs au support

    #### Option 1 : Email (recommandé)
    1. Ouvrez votre client email
    2. Créez un nouveau message à : **support@gestio.app** (à remplacer par votre email)
    3. Sujet : `Logs OCR pour amélioration - [Votre Nom]`
    4. Attachez le fichier ZIP créé
    5. Optionnel : Ajoutez des commentaires sur les types de tickets qui posent problème

    #### Option 2 : Cloud Storage
    1. Uploadez le fichier sur Google Drive / Dropbox / OneDrive
    2. Générez un lien de partage
    3. Envoyez le lien par email au support

    #### Option 3 : GitHub Issue (pour les développeurs)
    1. Créez une issue sur le repo GitHub
    2. Uploadez le fichier ZIP en pièce jointe
    3. Décrivez les problèmes rencontrés

    ---

    ### 🙏 Merci de contribuer à l'amélioration de Gestio !

    Vos logs sont précieux pour :
    - ✨ Améliorer les taux de détection
    - 🔍 Découvrir de nouveaux formats de tickets
    - 🎯 Optimiser les patterns existants
    - 🚀 Créer une meilleure expérience pour tous les utilisateurs
    """)

    # Show logs files location
    with st.expander("🔍 Emplacement des fichiers de logs"):
        st.code(f"""
Dossier des logs OCR :
{os.path.join(os.path.expanduser("~"), "gestion_financiere_data", "ocr_logs")}

Fichiers inclus :
- scan_history.jsonl : Historique complet
- potential_patterns.jsonl : Patterns découverts
- performance_stats.json : Statistiques globales
- pattern_stats.json : Fiabilité des patterns
- pattern_log.json : Occurrences
        """, language="text")
