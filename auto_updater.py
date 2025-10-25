# -*- coding: utf-8 -*-
"""
Système de mise à jour automatique pour Gestion Financière Little
Vérifie les nouvelles versions sur GitHub et propose l'installation automatique
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
import requests
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta

# ==============================
# 📦 CONFIGURATION
# ==============================
GITHUB_REPO = "mdjabi2005-commits/gestion-financiere_little"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
VERSION_ACTUELLE = "v1.0.0"  # À mettre à jour à chaque release

# Fichiers de configuration
CONFIG_DIR = Path.home() / ".gestiolittle"
CONFIG_DIR.mkdir(exist_ok=True)
UPDATE_CONFIG_FILE = CONFIG_DIR / "update_config.json"
VERSION_FILE = CONFIG_DIR / "version.json"


# ==============================
# 📝 GESTION DE LA CONFIGURATION
# ==============================
def load_update_config():
    """Charge la configuration des mises à jour"""
    default_config = {
        "auto_check": True,
        "last_check": None,
        "remind_later_until": None,
        "installed_version": VERSION_ACTUELLE,
        "skip_version": None
    }
    
    if UPDATE_CONFIG_FILE.exists():
        try:
            with open(UPDATE_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**default_config, **config}
        except Exception as e:
            print(f"Erreur lecture config update: {e}")
    
    return default_config


def save_update_config(config):
    """Sauvegarde la configuration des mises à jour"""
    try:
        with open(UPDATE_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Erreur sauvegarde config update: {e}")


def get_current_version():
    """Récupère la version actuelle installée"""
    if VERSION_FILE.exists():
        try:
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("version", VERSION_ACTUELLE)
        except:
            pass
    return VERSION_ACTUELLE


def save_current_version(version):
    """Sauvegarde la version actuelle"""
    try:
        with open(VERSION_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "version": version,
                "installed_at": datetime.now().isoformat()
            }, f, indent=2)
    except Exception as e:
        print(f"Erreur sauvegarde version: {e}")


# ==============================
# 🔍 VÉRIFICATION DES MISES À JOUR
# ==============================
def check_for_updates():
    """Vérifie si une nouvelle version est disponible sur GitHub"""
    try:
        response = requests.get(GITHUB_API_URL, timeout=5)
        if response.status_code == 200:
            latest_release = response.json()
            return {
                "available": True,
                "version": latest_release.get("tag_name"),
                "name": latest_release.get("name"),
                "body": latest_release.get("body", ""),
                "published_at": latest_release.get("published_at"),
                "html_url": latest_release.get("html_url"),
                "assets": latest_release.get("assets", [])
            }
    except Exception as e:
        print(f"Erreur vérification update: {e}")
    
    return {"available": False}


def should_check_updates():
    """Détermine si on doit vérifier les mises à jour maintenant"""
    config = load_update_config()
    
    # Si l'utilisateur a désactivé les vérifications automatiques
    if not config.get("auto_check", True):
        return False
    
    # Si l'utilisateur a cliqué sur "Plus tard"
    remind_later = config.get("remind_later_until")
    if remind_later:
        remind_date = datetime.fromisoformat(remind_later)
        if datetime.now() < remind_date:
            return False
    
    # Vérifier maximum une fois par jour
    last_check = config.get("last_check")
    if last_check:
        last_check_date = datetime.fromisoformat(last_check)
        if datetime.now() - last_check_date < timedelta(days=1):
            return False
    
    return True


def compare_versions(v1, v2):
    """Compare deux versions (format: v1.2.3)
    Retourne: 1 si v1 > v2, -1 si v1 < v2, 0 si égales
    """
    try:
        # Enlever le 'v' initial et séparer
        v1_parts = [int(x) for x in v1.lstrip('v').split('.')]
        v2_parts = [int(x) for x in v2.lstrip('v').split('.')]
        
        # Comparer partie par partie
        for i in range(max(len(v1_parts), len(v2_parts))):
            val1 = v1_parts[i] if i < len(v1_parts) else 0
            val2 = v2_parts[i] if i < len(v2_parts) else 0
            
            if val1 > val2:
                return 1
            elif val1 < val2:
                return -1
        
        return 0
    except Exception as e:
        print(f"Erreur comparaison versions: {e}")
        return 0


# ==============================
# 📥 TÉLÉCHARGEMENT ET INSTALLATION
# ==============================
def get_platform_asset(assets):
    """Trouve l'asset correspondant à la plateforme actuelle"""
    import platform
    system = platform.system()
    
    for asset in assets:
        name = asset.get("name", "").lower()
        
        if system == "Windows" and "windows" in name and name.endswith(".zip"):
            return asset
        elif system == "Linux" and "linux" in name and name.endswith(".zip"):
            return asset
        elif system == "Darwin" and "macos" in name and name.endswith(".zip"):
            return asset
    
    return None


def download_update(asset, progress_callback=None):
    """Télécharge la mise à jour depuis GitHub"""
    try:
        url = asset.get("browser_download_url")
        if not url:
            return None
        
        # Télécharger dans un fichier temporaire
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, asset.get("name"))
        
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(temp_file, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        progress_callback(progress)
        
        return temp_file
    
    except Exception as e:
        print(f"Erreur téléchargement: {e}")
        return None


def extract_and_install(zip_path, install_dir):
    """Extrait et installe la mise à jour"""
    try:
        # Créer un backup de l'installation actuelle
        backup_dir = install_dir.parent / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if install_dir.exists():
            shutil.copytree(install_dir, backup_dir)
        
        # Extraire la nouvelle version
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(install_dir)
        
        return True, backup_dir
    
    except Exception as e:
        print(f"Erreur installation: {e}")
        return False, None


def restart_application():
    """Redémarre l'application après mise à jour"""
    try:
        if getattr(sys, 'frozen', False):
            # Si compilé avec PyInstaller
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            # Si lancé depuis Python
            python = sys.executable
            os.execl(python, python, *sys.argv)
    except Exception as e:
        print(f"Erreur redémarrage: {e}")
        st.error("⚠️ Redémarrage manuel nécessaire. Ferme et relance l'application.")


# ==============================
# 🎨 INTERFACE STREAMLIT
# ==============================
def show_update_notification():
    """Affiche une notification de mise à jour dans Streamlit"""
    
    if not should_check_updates():
        return
    
    # Vérifier les mises à jour
    update_info = check_for_updates()
    
    if not update_info.get("available"):
        return
    
    latest_version = update_info.get("version")
    current_version = get_current_version()
    
    # Sauvegarder la date de vérification
    config = load_update_config()
    config["last_check"] = datetime.now().isoformat()
    save_update_config(config)
    
    # Si version à ignorer
    if config.get("skip_version") == latest_version:
        return
    
    # Comparer les versions
    if compare_versions(latest_version, current_version) <= 0:
        return  # Pas de nouvelle version
    
    # Afficher la notification
    st.toast(f"🎉 Nouvelle version disponible : {latest_version}", icon="🎉")
    
    with st.expander(f"🆕 Mise à jour disponible : {latest_version}", expanded=True):
        st.markdown(f"**Version actuelle :** {current_version}")
        st.markdown(f"**Nouvelle version :** {latest_version}")
        st.markdown(f"**Publiée le :** {datetime.fromisoformat(update_info['published_at'].replace('Z', '+00:00')).strftime('%d/%m/%Y')}")
        
        if update_info.get("body"):
            st.markdown("**Notes de version :**")
            st.markdown(update_info["body"])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📥 Installer maintenant", type="primary"):
                install_update(update_info)
        
        with col2:
            if st.button("⏰ Plus tard"):
                config["remind_later_until"] = (datetime.now() + timedelta(days=1)).isoformat()
                save_update_config(config)
                st.rerun()
        
        with col3:
            if st.button("🚫 Ignorer cette version"):
                config["skip_version"] = latest_version
                save_update_config(config)
                st.rerun()
        
        with col4:
            if st.button("📖 Voir sur GitHub"):
                st.markdown(f"[Ouvrir la page de release]({update_info['html_url']})")


def install_update(update_info):
    """Interface d'installation de mise à jour"""
    latest_version = update_info.get("version")
    assets = update_info.get("assets", [])
    
    # Trouver l'asset pour la plateforme
    asset = get_platform_asset(assets)
    
    if not asset:
        st.error("❌ Aucun fichier de mise à jour disponible pour votre système.")
        return
    
    st.info(f"📥 Téléchargement de {asset['name']} ({asset['size'] / 1024 / 1024:.1f} MB)...")
    
    # Barre de progression
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_progress(percent):
        progress_bar.progress(percent)
        status_text.text(f"Téléchargement en cours... {percent}%")
    
    # Télécharger
    zip_path = download_update(asset, update_progress)
    
    if not zip_path:
        st.error("❌ Échec du téléchargement.")
        return
    
    status_text.text("📦 Installation en cours...")
    
    # Déterminer le dossier d'installation
    if getattr(sys, 'frozen', False):
        install_dir = Path(sys.executable).parent
    else:
        install_dir = Path(__file__).parent
    
    # Installer
    success, backup_dir = extract_and_install(zip_path, install_dir)
    
    if not success:
        st.error("❌ Échec de l'installation.")
        if backup_dir and backup_dir.exists():
            st.info(f"💾 Un backup a été créé : {backup_dir}")
        return
    
    # Sauvegarder la nouvelle version
    save_current_version(latest_version)
    
    # Mettre à jour la config
    config = load_update_config()
    config["installed_version"] = latest_version
    config["skip_version"] = None
    save_update_config(config)
    
    st.success(f"✅ Mise à jour vers {latest_version} installée avec succès !")
    st.info(f"💾 Backup créé : {backup_dir}")
    
    if st.button("🔄 Redémarrer maintenant", type="primary"):
        st.info("🔄 Redémarrage de l'application...")
        restart_application()


def update_settings_ui():
    """Interface des paramètres de mise à jour"""
    st.subheader("🔄 Paramètres de mise à jour")
    
    config = load_update_config()
    current_version = get_current_version()
    
    st.info(f"**Version actuelle :** {current_version}")
    
    # Vérification automatique
    auto_check = st.checkbox(
        "Vérifier automatiquement les mises à jour",
        value=config.get("auto_check", True)
    )
    
    if auto_check != config.get("auto_check"):
        config["auto_check"] = auto_check
        save_update_config(config)
        st.success("✅ Préférence sauvegardée")
    
    st.markdown("---")
    
    # Vérification manuelle
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Vérifier maintenant", type="primary"):
            with st.spinner("Vérification en cours..."):
                update_info = check_for_updates()
                
                if not update_info.get("available"):
                    st.error("❌ Impossible de vérifier les mises à jour.")
                    return
                
                latest_version = update_info.get("version")
                
                if compare_versions(latest_version, current_version) > 0:
                    st.success(f"🎉 Nouvelle version disponible : {latest_version}")
                    if st.button("📥 Installer"):
                        install_update(update_info)
                else:
                    st.success("✅ Vous avez la dernière version !")
    
    with col2:
        if st.button("📋 Voir les releases sur GitHub"):
            st.markdown(f"[Ouvrir GitHub Releases](https://github.com/{GITHUB_REPO}/releases)")
    
    # Historique
    if VERSION_FILE.exists():
        try:
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                installed_at = data.get("installed_at")
                if installed_at:
                    st.caption(f"📅 Installée le : {datetime.fromisoformat(installed_at).strftime('%d/%m/%Y %H:%M')}")
        except:
            pass
