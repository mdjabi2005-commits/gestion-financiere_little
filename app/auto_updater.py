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


# Source unique de vérité pour la version
VERSION_FILE = Path("version.txt")
VERSION_ACTUELLE = "v0.2.4"  # Valeur par défaut si le fichier n'existe pas


# ==============================
# 📝 GESTION DE LA CONFIGURATION
# ==============================
def get_current_version():
    """Lit la version actuelle depuis version.txt"""
    try:
        if VERSION_FILE.exists():
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        return VERSION_ACTUELLE
    except Exception:
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


# Variable globale pour mémoriser la dernière vérification pendant la session
_last_check_time = None

def should_check_updates():
    """
    Détermine s’il faut vérifier les mises à jour.
    ✅ Évite les vérifications trop fréquentes pendant une même session.
    """
    global _last_check_time
    now = datetime.now()

    # Si jamais aucune vérification n’a encore eu lieu
    if _last_check_time is None:
        _last_check_time = now
        return True

    # Vérifie qu’au moins 24h se sont écoulées
    if now - _last_check_time >= timedelta(hours=24):
        _last_check_time = now
        return True

    # Sinon, on ne revérifie pas
    return False

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
    """Relance l'application après mise à jour"""
    python_exe = sys.executable
    script_path = sys.argv[0]
    try:
        if getattr(sys, "frozen", False):
            # Si c'est un exécutable PyInstaller
            subprocess.Popen([sys.executable])
        else:
            subprocess.Popen([python_exe, script_path])
        sys.exit(0)
    except Exception as e:
        st.error(f"❌ Impossible de redémarrer automatiquement ({e})")


# ==============================
# 🎨 INTERFACE STREAMLIT
# ==============================
# Mémoire de session temporaire
if "ignored_version" not in st.session_state:
    st.session_state["ignored_version"] = None
if "remind_later_until" not in st.session_state:
    st.session_state["remind_later_until"] = None
if "last_check_time" not in st.session_state:
    st.session_state["last_check_time"] = None


def show_update_notification():
    """Affiche une notification de mise à jour dans Streamlit"""
    
    # Vérification simple (1x par session ou 1x par 24h)
    if st.session_state["last_check_time"]:
        delta = datetime.now() - st.session_state["last_check_time"]
        if delta < timedelta(hours=24):
            return
    st.session_state["last_check_time"] = datetime.now()
    
    # Vérifier les mises à jour sur GitHub
    update_info = check_for_updates()
    if not update_info.get("available"):
        return
    
    latest_version = update_info.get("version")
    current_version = get_current_version()
    
    # Si version ignorée
    if st.session_state["ignored_version"] == latest_version:
        return

    # Si "plus tard" actif
    remind_until = st.session_state["remind_later_until"]
    if remind_until and datetime.now() < remind_until:
        return

    # Si version pas plus récente, on ne montre rien
    if compare_versions(latest_version, current_version) <= 0:
        return

    # Affichage dans Streamlit
    st.toast(f"🎉 Nouvelle version disponible : {latest_version}", icon="🎉")

    with st.expander(f"🆕 Mise à jour disponible : {latest_version}", expanded=True):
        st.markdown(f"**Version actuelle :** {current_version}")
        st.markdown(f"**Nouvelle version :** {latest_version}")
        st.markdown(
            f"**Publiée le :** {datetime.fromisoformat(update_info['published_at'].replace('Z', '+00:00')).strftime('%d/%m/%Y')}"
        )

        if update_info.get("body"):
            st.markdown("**Notes de version :**")
            st.markdown(update_info["body"])

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📥 Installer maintenant", type="primary"):
                install_update(update_info)

        with col2:
            if st.button("⏰ Plus tard"):
                st.session_state["remind_later_until"] = datetime.now() + timedelta(days=1)
                st.rerun()

        with col3:
            if st.button("🚫 Ignorer cette version"):
                st.session_state["ignored_version"] = latest_version
                st.rerun()

        with col4:
            if st.button("📖 Voir sur GitHub"):
                st.markdown(f"[Ouvrir la release]({update_info['html_url']})")


def install_update(update_info):
    """Télécharge et installe proprement une mise à jour"""
    latest_version = update_info.get("version")
    assets = update_info.get("assets", [])

    asset = get_platform_asset(assets)
    if not asset:
        st.error("❌ Aucun fichier de mise à jour disponible pour votre système.")
        return

    st.info(f"📥 Téléchargement de {asset['name']} ({asset['size'] / 1024 / 1024:.1f} MB)...")

    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(percent):
        progress_bar.progress(percent)
        status_text.text(f"Téléchargement en cours... {percent}%")

    # Télécharger l’archive ZIP
    zip_path = download_update(asset, update_progress)
    if not zip_path:
        st.error("❌ Échec du téléchargement.")
        return

    status_text.text("📦 Installation de la mise à jour en cours...")

    # Dossier d'installation actuel
    if getattr(sys, 'frozen', False):
        install_dir = Path(sys.executable).parent
    else:
        install_dir = Path(__file__).parent.resolve()

    # Dossier temporaire pour extraire le ZIP
    temp_extract_dir = Path(tempfile.mkdtemp(prefix="update_extract_"))
    backup_dir = install_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        # Étape 1 → Créer un backup du dossier existant
        if not backup_dir.exists():
            shutil.copytree(install_dir, backup_dir, dirs_exist_ok=True)
        st.info(f"💾 Sauvegarde créée dans : `{backup_dir}`")

        # Étape 2 → Extraire l’archive ZIP téléchargée
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_extract_dir)

        # Étape 3 → Copier les fichiers extraits vers le dossier d’installation
        for item in temp_extract_dir.iterdir():
            dest = install_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

        # Étape 4 → Écrire la nouvelle version dans version.txt
        try:
            version_file = install_dir / "version.txt"
            with open(version_file, "w", encoding="utf-8") as f:
                f.write(latest_version)
        except Exception as e:
            st.warning(f"⚠️ Impossible d’écrire version.txt ({e})")

        # Étape 5 → Nettoyer le dossier temporaire
        shutil.rmtree(temp_extract_dir, ignore_errors=True)

        # ✅ Succès
        st.success(f"✅ Mise à jour vers {latest_version} installée avec succès !")
        st.info(f"💾 Backup : `{backup_dir}`")

        # Proposition de redémarrage
        if st.button("🔄 Redémarrer maintenant", type="primary"):
            st.info("🔄 Redémarrage de l’application...")
            restart_application()

    except Exception as e:
        st.error(f"❌ Erreur critique pendant l’installation : {e}")
        if backup_dir.exists():
            st.info(f"💾 Le backup reste disponible dans : {backup_dir}")

    finally:
        # Nettoyage si jamais le zip reste temporairement ouvert
        try:
            os.remove(zip_path)
        except Exception:
            pass

def update_settings_ui():
    """Interface des paramètres de mise à jour"""
    st.subheader("🔄 Paramètres de mise à jour")

    current_version = get_current_version()
    st.info(f"**Version actuelle :** {current_version}")

    # ✅ Option de vérification automatique (stockée en session)
    auto_check = st.checkbox(
        "Vérifier automatiquement les mises à jour",
        value=st.session_state.get("auto_check", True)
    )
    st.session_state["auto_check"] = auto_check

    st.markdown("---")

    # ✅ Vérification manuelle
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