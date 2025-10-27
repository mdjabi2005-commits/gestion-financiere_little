# -*- coding: utf-8 -*-
"""
Interface pour afficher l'historique des versions et le changelog
"""

import os
import json
import streamlit as st
from pathlib import Path
from datetime import datetime


def load_releases_history():
    """Charge l'historique des releases depuis releases.json"""
    releases_file = Path(".app_data/releases.json")
    
    if releases_file.exists():
        try:
            with open(releases_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('releases', [])
        except Exception as e:
            print(f"Erreur lecture releases.json: {e}")
    
    return []


def load_changelog():
    """Charge le contenu du CHANGELOG.md"""
    changelog_file = Path("CHANGELOG.md")
    
    if changelog_file.exists():
        try:
            with open(changelog_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Erreur lecture CHANGELOG.md: {e}")
    
    return None


def parse_release_body(body):
    """Parse le contenu d'une release pour extraire les sections"""
    sections = {
        'nouveautes': [],
        'corrections': [],
        'ameliorations': [],
        'autres': []
    }
    
    current_section = 'autres'
    lines = body.split('\n')
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Détecter les sections
        if any(word in line_lower for word in ['nouveauté', 'nouveautés', '🎉', 'feature', 'feat']):
            current_section = 'nouveautes'
            continue
        elif any(word in line_lower for word in ['correction', 'bug', '🐛', 'fix']):
            current_section = 'corrections'
            continue
        elif any(word in line_lower for word in ['amélioration', 'improvement', '⚡', 'perf']):
            current_section = 'ameliorations'
            continue
        
        # Extraire les items (lignes commençant par - ou *)
        if line.strip().startswith(('-', '*', '•')):
            item = line.strip().lstrip('-*• ').strip()
            if item:
                sections[current_section].append(item)
    
    return sections


def display_release_card(release):
    """Affiche une carte pour une release"""
    version = release.get('version', 'Unknown')
    date = release.get('date', 'Unknown')
    name = release.get('name', '')
    body = release.get('body', '')
    url = release.get('url', '')
    
    # Parser le contenu
    sections = parse_release_body(body)
    
    # Déterminer le type de release
    is_major = '.0.0' in version
    is_minor = '.0' in version and not is_major
    
    if is_major:
        badge_color = "🔴"
        badge_text = "MAJOR"
    elif is_minor:
        badge_color = "🟡"
        badge_text = "MINOR"
    else:
        badge_color = "🟢"
        badge_text = "PATCH"
    
    with st.container():
        st.markdown(f"""
        <div style="
            border: 2px solid #667eea;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        ">
            <h3 style="margin: 0 0 10px 0;">{badge_color} {version} <span style="font-size: 0.7em; background: #667eea; color: white; padding: 3px 8px; border-radius: 5px;">{badge_text}</span></h3>
            <p style="color: #666; margin: 0 0 15px 0;">📅 {date} {f"• {name}" if name and version not in name else ""}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Afficher les sections
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if sections['nouveautes']:
                st.markdown("### 🎉 Nouveautés")
                for item in sections['nouveautes']:
                    st.markdown(f"- {item}")
        
        with col2:
            if sections['corrections']:
                st.markdown("### 🐛 Corrections")
                for item in sections['corrections']:
                    st.markdown(f"- {item}")
        
        with col3:
            if sections['ameliorations']:
                st.markdown("### ⚡ Améliorations")
                for item in sections['ameliorations']:
                    st.markdown(f"- {item}")
        
        # Autres items
        if sections['autres']:
            st.markdown("### 📝 Autres changements")
            for item in sections['autres']:
                st.markdown(f"- {item}")
        
        # Lien vers GitHub
        if url:
            st.markdown(f"[📋 Voir la release complète sur GitHub]({url})")
        
        st.markdown("---")


def display_changelog_page():
    """Page principale affichant l'historique des versions"""
    st.header("📜 Historique des versions")
    
    # Charger les releases
    releases = load_releases_history()
    
    if not releases:
        st.info("""
        📭 Aucun historique de version disponible pour le moment.
        
        **L'historique sera créé automatiquement** lorsque vous publierez votre première release sur GitHub.
        
        💡 **Comment ça marche ?**
        1. Vous créez une draft release sur GitHub
        2. Vous la testez localement
        3. Vous la publiez
        4. → L'historique s'affiche automatiquement ici !
        """)
        return
    
    # Statistiques globales
    st.markdown("### 📊 Statistiques")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏷️ Versions", len(releases))
    
    with col2:
        # Compter les nouveautés totales
        total_nouveautes = sum(
            len(parse_release_body(r.get('body', '')).get('nouveautes', []))
            for r in releases
        )
        st.metric("✨ Nouveautés", total_nouveautes)
    
    with col3:
        # Compter les corrections totales
        total_corrections = sum(
            len(parse_release_body(r.get('body', '')).get('corrections', []))
            for r in releases
        )
        st.metric("🐛 Corrections", total_corrections)
    
    with col4:
        # Date de la dernière release
        if releases:
            last_date = releases[0].get('date', 'Unknown')
            try:
                date_obj = datetime.fromisoformat(last_date)
                days_ago = (datetime.now() - date_obj).days
                st.metric("📅 Dernière MAJ", f"Il y a {days_ago}j")
            except:
                st.metric("📅 Dernière MAJ", last_date)
    
    st.markdown("---")
    
    # Filtres
    col1, col2 = st.columns([3, 1])
    
    with col1:
        filter_type = st.selectbox(
            "Filtrer par type",
            ["Toutes", "MAJOR", "MINOR", "PATCH"]
        )
    
    with col2:
        limit = st.number_input("Afficher", min_value=1, max_value=len(releases), value=min(5, len(releases)))
    
    # Filtrer les releases
    filtered_releases = releases
    
    if filter_type == "MAJOR":
        filtered_releases = [r for r in releases if '.0.0' in r.get('version', '')]
    elif filter_type == "MINOR":
        filtered_releases = [r for r in releases if '.0' in r.get('version', '') and '.0.0' not in r.get('version', '')]
    elif filter_type == "PATCH":
        filtered_releases = [r for r in releases if '.0' not in r.get('version', '').rsplit('.', 1)[1]]
    
    # Limiter le nombre
    filtered_releases = filtered_releases[:limit]
    
    st.markdown("---")
    
    # Afficher les releases
    if not filtered_releases:
        st.warning("Aucune version ne correspond aux filtres sélectionnés.")
    else:
        for release in filtered_releases:
            display_release_card(release)
    
    # Lien vers le changelog complet
    st.markdown("---")
    
    with st.expander("📄 Voir le CHANGELOG.md complet"):
        changelog = load_changelog()
        if changelog:
            st.markdown(changelog)
        else:
            st.info("Le fichier CHANGELOG.md sera créé automatiquement lors de la première publication de release.")


def display_whats_new():
    """Affiche les nouveautés de la dernière version (widget compact)"""
    releases = load_releases_history()
    
    if not releases:
        return
    
    latest = releases[0]
    version = latest.get('version', 'Unknown')
    
    sections = parse_release_body(latest.get('body', ''))
    
    # Compter les changements
    total_changes = (
        len(sections.get('nouveautes', [])) +
        len(sections.get('corrections', [])) +
        len(sections.get('ameliorations', []))
    )
    
    if total_changes == 0:
        return
    
    with st.expander(f"✨ Nouveautés de la version {version}", expanded=False):
        if sections.get('nouveautes'):
            st.markdown("**🎉 Nouveautés**")
            for item in sections['nouveautes'][:3]:  # Maximum 3 items
                st.markdown(f"- {item}")
        
        if sections.get('corrections'):
            st.markdown("**🐛 Corrections**")
            for item in sections['corrections'][:3]:
                st.markdown(f"- {item}")
        
        if sections.get('ameliorations'):
            st.markdown("**⚡ Améliorations**")
            for item in sections['ameliorations'][:3]:
                st.markdown(f"- {item}")
        
        if total_changes > 9:
            st.info("... et plus encore ! Voir l'onglet 'Mises à jour' pour tous les détails.")
