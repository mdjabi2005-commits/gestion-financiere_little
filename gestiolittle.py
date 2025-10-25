# -*- coding: utf-8 -*-
"""
Created on Sun Oct 12 19:43:10 2025

@author: djabi"""



from difflib import get_close_matches
import os
import shutil
import sqlite3
import pandas as pd
import pytesseract
import os
pytesseract.pytesseract.tesseract_cmd = os.path.join(os.path.dirname(__file__), "tesseract", "tesseract.exe")
from PIL import Image
import re
import streamlit as st
from datetime import datetime,date,timedelta
from dateutil import parser
import cv2
import numpy as np
from dateutil.relativedelta import relativedelta

# ==============================
# ⚙️ CONFIGURATION AUTOMATIQUE DE TESSERACT
# ==============================
import platform, subprocess, sys

def config_tesseract():
    system = platform.system()
    tesseract_path = None

    if system == "Windows":
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        tesseract_path = os.path.join(base_path, "tesseract", "tesseract.exe")

        if not os.path.exists(tesseract_path):
            st.error("⚠️ Tesseract n’a pas été trouvé dans le dossier 'tesseract/'.")
            return False

        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        return True

    tesseract_path = shutil.which("tesseract")

    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        return True

    st.warning("⚠️ Tesseract n'est pas installé sur ce système.")
    install_auto = st.button("🛠️ Installer automatiquement Tesseract")

    if install_auto:
        try:
            if system == "Linux":
                with st.spinner("Installation de Tesseract en cours..."):
                    subprocess.run(["sudo", "apt", "update"], check=True)
                    subprocess.run(["sudo", "apt", "install", "-y", "tesseract-ocr", "tesseract-ocr-fra"], check=True)
            elif system == "Darwin":
                if shutil.which("brew"):
                    with st.spinner("Installation de Tesseract via Homebrew..."):
                        subprocess.run(["brew", "install", "tesseract"], check=True)
                        subprocess.run(["brew", "install", "tesseract-lang"], check=True)
                else:
                    st.error("❌ Homebrew n'est pas installé. Installe-le d'abord depuis https://brew.sh")
                    return False
            else:
                st.error("⚠️ L’installation automatique n’est pas disponible pour ce système.")
                return False

            tesseract_path = shutil.which("tesseract")
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                st.success(f"✅ Tesseract a été installé avec succès ({tesseract_path}) !")
                return True
            else:
                st.error("❌ L’installation semble avoir échoué. Réessaie manuellement.")

        except subprocess.CalledProcessError as e:
            st.error(f"❌ Échec de l’installation : {e}")
        except Exception as e:
            st.error(f"❌ Erreur inattendue : {e}")

    st.info("""
    💡 Pour installer manuellement Tesseract :
    - Sur **Linux** : `sudo apt install tesseract-ocr tesseract-ocr-fra`
    - Sur **macOS** : `brew install tesseract`
    """)
    return False

# 🚀 Vérifie immédiatement
TESSERACT_OK = config_tesseract()

if not TESSERACT_OK:
    st.stop()  # ⛔ Stoppe le chargement si Tesseract n'est pas dispo



# ==============================
# 📄 Configuration Streamlit
# ==============================
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    div[data-testid="stDataFrame"] div[role="gridcell"] {
        font-size: 16px !important;
        padding: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)


# ==============================
# 📂 CONFIGURATION DES DOSSIERS
# ==============================
from configlittle import  DATA_DIR, DB_PATH, TO_SCAN_DIR, SORTED_DIR, REVENUS_A_TRAITER, REVENUS_TRAITES
def get_db_connection():
    """Retourne une connexion SQLite cohérente avec DB_PATH."""
    return sqlite3.connect(DB_PATH)

# ==============================
# 📁 Dictionnaire des mois
# ==============================
mois_dict = {
    "janvier": "01", "février": "02", "mars": "03", "avril": "04",
    "mai": "05", "juin": "06", "juillet": "07", "août": "08",
    "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12"
}

def numero_to_mois(num: str) -> str:
    for mois, numero in mois_dict.items():
        if numero == num:
            return mois
    return "inconnu"

# ==============================
# 🧠 OCR ET TRAITEMENT DE TICKET ET REVENU
# ==============================
def full_ocr(image_path: str, show_ticket: bool = False) -> str:
    """
    Effectue un OCR complet sur une image de ticket.
    Version robuste + option d’affichage du ticket dans Streamlit.
    """
    try:
        # --- Lecture robuste du fichier image ---
        image_data = np.fromfile(image_path, dtype=np.uint8)
        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

        if image is None:
            raise FileNotFoundError(f"Impossible de lire ou décoder l’image : {image_path}")

        # --- Prétraitement pour OCR ---
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        pil_img = Image.fromarray(thresh)

        # --- OCR ---
        text = pytesseract.image_to_string(pil_img, lang="fra")
        text = text.replace("\x0c", "").strip()

        # --- Option : affichage dans Streamlit ---
        if show_ticket:
            with st.expander(f"🧾 Aperçu du ticket : {os.path.basename(image_path)}", expanded=False):
                st.image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), caption=os.path.basename(image_path))
                if text:
                    st.text_area("Texte OCR détecté :", text, height=200)
                else:
                    st.warning("⚠️ Aucun texte détecté par l’OCR.")

        return text

    except Exception as e:
        st.error(f"❌ Erreur OCR sur {os.path.basename(image_path)} : {e}")
        return ""


def get_montant_from_line(label_pattern, all_lines, allow_next_line=True):
    """
    Recherche un montant à partir d'un label (ex: 'TOTAL', 'MONTANT RÉEL', etc.)
    Corrigée pour être plus robuste face aux erreurs d’OCR et aux formats de tickets variés.
    """
    montant_regex = r"(\d{1,5}[.,]?\d{0,2})\s*(?:€|eur|euros?)?"

    def clean_ocr_text(txt):
        """Corrige les erreurs courantes de lecture OCR (O/0, I/1, etc.)."""
        txt = txt.replace("O", "0").replace("o", "0")
        txt = txt.replace("I", "1").replace("l", "1")
        txt = re.sub(r"[\u200b\s]+", " ", txt)
        return txt.strip()

    for i, l in enumerate(all_lines):
        l_clean = clean_ocr_text(l)

        # Recherche du label (ex: 'TOTAL', 'MONTANT', etc.)
        if re.search(label_pattern, l_clean, re.IGNORECASE):
            found_same = re.findall(montant_regex, l_clean, re.IGNORECASE)
            if found_same:
                # Prend le montant le plus grand sur la ligne (souvent le total TTC)
                return float(max(found_same, key=lambda x: float(x.replace(",", "."))).replace(",", "."))

            # Ligne suivante possible
            if allow_next_line and i + 1 < len(all_lines):
                next_line = clean_ocr_text(all_lines[i + 1])
                found_next = re.findall(montant_regex, next_line, re.IGNORECASE)
                if found_next:
                    return float(max(found_next, key=lambda x: float(x.replace(",", "."))).replace(",", "."))

    # Si rien trouvé, essaie de repérer un montant seul sur une ligne typique de paiement
    for l in all_lines:
        l_clean = clean_ocr_text(l)
        match = re.search(r"(\d+[.,]\d{2})", l_clean)
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                continue


    return 0.0


def parse_ticket_metadata(ocr_text: str):
    """
    Analyse un texte OCR de ticket pour extraire les montants (total, paiements, TVA),
    et choisit le montant final par validation croisée.
    """
    lines = [l.strip() for l in ocr_text.split("\n") if l.strip()]

    def normalize_line(l):
        return l.replace("O", "0").replace("o", "0").replace("I", "1").replace("l", "1").strip()

    lines = [normalize_line(l) for l in lines]

    montant_regex = r"(\d{1,5}[.,]\d{1,2})"

    # === MÉTHODE A : Totaux directs (comme avant)
    total_patterns = [
        r"TOTAL\s*TTC", r"TOTAL\s*(A\s*PAYER)?", r"MONTANT\s*(R[EÉ]EL|TTC)?",
        r"NET\s*A\s*PAYER", r"À\s*PAYER", r"TOTAL$", r"TTC"
    ]
    montants_A = []
    for pattern in total_patterns:
        m = get_montant_from_line(pattern, lines)
        if m > 0:
            montants_A.append(round(m, 2))

    # === MÉTHODE B : Somme des paiements (CB, espèces, web, etc.)
    paiement_patterns = [r"CB", r"CARTE", r"ESPECES", r"WEB", r"PAYPAL", r"CHEQUE"]
    montants_B = []
    for l in lines:
        if any(re.search(p, l, re.IGNORECASE) for p in paiement_patterns):
            found = re.findall(montant_regex, l)
            for val in found:
                try:
                    montants_B.append(float(val.replace(",", ".")))
                except:
                    pass
    somme_B = round(sum(montants_B), 2) if montants_B else 0.0

    # === MÉTHODE C : Net + TVA
    net_lines = [l for l in lines if re.search(r"HT|NET", l, re.IGNORECASE)]
    tva_lines = [l for l in lines if re.search(r"TVA|T\.V\.A", l, re.IGNORECASE)]
    total_HT = 0.0
    total_TVA = 0.0
    for l in net_lines:
        vals = re.findall(montant_regex, l)
        for v in vals:
            total_HT += float(v.replace(",", "."))
    for l in tva_lines:
        vals = re.findall(montant_regex, l)
        for v in vals:
            total_TVA += float(v.replace(",", "."))
    somme_C = round(total_HT + total_TVA, 2) if total_HT > 0 else 0.0

    # === MÉTHODE D : fallback global (si rien trouvé)
    all_amounts = [float(m.replace(",", ".")) for m in re.findall(montant_regex, ocr_text)]
    montant_fallback = max(all_amounts) if all_amounts else 0.0

    # === VALIDATION CROISÉE
    candidats = [x for x in montants_A + [somme_B, somme_C, montant_fallback] if x > 0]
    freq = {}
    for m in candidats:
        m_rond = round(m, 2)
        freq[m_rond] = freq.get(m_rond, 0) + 1
    if not freq:
        montant_final = 0.0
    else:
        montant_final = max(freq, key=freq.get)  # prend le montant le plus récurrent

    # === Détection de la date (inchangée)
    date_patterns = [
        r"\b\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}\b",
        r"\b\d{1,2}\s*(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)\.?\s*\d{2,4}\b"
    ]
    detected_date = None
    for p in date_patterns:
        match = re.search(p, ocr_text, re.IGNORECASE)
        if match:
            try:
                detected_date = parser.parse(match.group(0), dayfirst=True, fuzzy=True).date().isoformat()
                break
            except:
                continue
    if not detected_date:
        detected_date = datetime.now().date().isoformat()

    # === Lignes clés (pour affichage dans interface)
    key_lines = [
        l for l in lines if any(re.search(p, l, re.IGNORECASE) for p in total_patterns + paiement_patterns)
    ]

    # === Résultat final
    montants_possibles = sorted(set(candidats), reverse=True)
    return {
        "montants_possibles": montants_possibles if montants_possibles else [montant_final],
        "montant": montant_final,
        "date": detected_date,
        "infos": "\n".join(key_lines)
    }



def move_ticket_to_sorted(ticket_path, categorie, sous_categorie):
    """Déplace un ticket traité vers le dossier 'tickets_scannes' classé par catégorie/sous-catégorie.
       Gère automatiquement les doublons en renommant les fichiers si nécessaire."""
    cat_dir = os.path.join(SORTED_DIR, categorie.strip())
    souscat_dir = os.path.join(cat_dir, sous_categorie.strip())
    os.makedirs(souscat_dir, exist_ok=True)

    base_name = os.path.basename(ticket_path)
    dest_path = os.path.join(souscat_dir, base_name)

    # 🔁 Si un fichier du même nom existe déjà, on crée un nom unique
    if os.path.exists(dest_path):
        name, ext = os.path.splitext(base_name)
        counter = 1
        while os.path.exists(dest_path):
            new_name = f"{name}_{counter}{ext}"
            dest_path = os.path.join(souscat_dir, new_name)
            counter += 1

    shutil.move(ticket_path, dest_path)
    st.success(f"✅ Ticket déplacé vers : {dest_path}")
    
    
def insert_transaction_batch(transactions):
    """
    Insère plusieurs transactions dans la base SQLite.
    Évite les doublons basés sur (type, catégorie, sous_catégorie, montant, date).
    """
    if not transactions:
        return
    conn = get_db_connection()
    cur = conn.cursor()

    inserted, skipped = 0, 0

    for t in transactions:
        try:
            cur.execute("""
                SELECT COUNT(*) FROM transactions
                WHERE type = ? AND categorie = ? AND sous_categorie = ?
                      AND montant = ? AND date = ?
            """, (
                t["type"],
                t.get("categorie", ""),
                t.get("sous_categorie", ""),
                float(t["montant"]),
                t["date"]
            ))

            if cur.fetchone()[0] > 0:
                skipped += 1
                continue

            cur.execute("""
                INSERT INTO transactions
                (type, categorie, sous_categorie, description, montant, date, source, recurrence, date_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t["type"],
                t.get("categorie", ""),
                t.get("sous_categorie", ""),
                t.get("description", ""),
                float(t["montant"]),
                t["date"],
                t.get("source", "manuel"),
                t.get("recurrence", "ponctuelle"),
                t.get("date_fin")
            ))
            inserted += 1

        except Exception as e:
            print(f"Erreur lors de l’insertion de {t}: {e}")

    conn.commit()
    conn.close()
    st.success(f"✅ {inserted} transaction(s) insérée(s).")
    if skipped > 0:
        st.info(f"ℹ️ {skipped} doublon(s) détecté(s) et ignoré(s).")



def extract_text_from_pdf(pdf_path):
    """Lit un PDF et renvoie le texte brut."""
    from pdfminer.high_level import extract_text
    try:
        return extract_text(pdf_path)
    except Exception as e:
        st.warning(f"⚠️ Impossible de lire le PDF {pdf_path} ({e})")
        return ""
    
    
def parse_uber_pdf(pdf_path: str) -> dict:
    """
    Parseur spécifique pour les PDF Uber.
    Objectif : extraire le montant net (net earnings) et la date de fin de période de facturation.
    Renvoie dict avec clés : montant (float), date (datetime.date), categorie, sous_categorie, source.
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return {
            "montant": 0.0,
            "date": datetime.now().date(),
            "categorie": "Revenu",
            "sous_categorie": "Uber",
            "source": "PDF Uber"
        }

    # Cherche une période de facturation sous forme "Période de facturation : 01/07/2025 - 31/07/2025"
    date_fin = None
    periode_match = re.search(
        r"P[eé]riode de facturation\s*[:\-]?\s*([0-3]?\d[\/\-\.][01]?\d[\/\-\.]\d{2,4})\s*[\-–]\s*([0-3]?\d[\/\-\.][01]?\d[\/\-\.]\d{2,4})",
        text,
        re.IGNORECASE
    )
    if periode_match:
        debut_str, fin_str = periode_match.groups()
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
            try:
                date_fin = datetime.strptime(fin_str, fmt).date()
                break
            except Exception:
                continue

    # Si non trouvé par pattern, on tente de trouver une date "Période terminée le : 31/07/2025" ou "Period ending 31/07/2025"
    if not date_fin:
        m2 = re.search(
            r"(period ending|p[eé]riode termin[eé]e le|Date de fin)\s*[:\-]?\s*([0-3]?\d[\/\-\.][01]?\d[\/\-\.]\d{2,4})",
            text,
            re.IGNORECASE
        )
        if m2:
            date_str = m2.group(2)
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
                try:
                    date_fin = datetime.strptime(date_str, fmt).date()
                    break
                except Exception:
                    continue

    if not date_fin:
        date_fin = datetime.now().date()

    # Montant net : varie selon le PDF Uber (Net earnings, Total to be paid, etc.)
    # On cherche d'abord des expressions anglaises ou françaises communes
    montant = 0.0
    montant_patterns = [
        r"(?:Net earnings|Net to driver|Total net|Montant net|Net earnings \(driver\))\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})\s*€?",
        r"([\d]{1,3}(?:[ .,]\d{3})*[.,]\d{2})\s*€\s*(?:net|netto|net earnings|to driver)?"
    ]
    for p in montant_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            s = m.group(1).replace(" ", "").replace(".", "").replace(",", ".") if "," in m.group(1) and "." in m.group(1) else m.group(1).replace(",", ".").replace(" ", "")
            try:
                montant = float(s)
                break
            except Exception:
                continue

    # fallback: chercher le dernier montant présent dans le texte (souvent utile si formats variés)
    if montant == 0.0:
        all_amounts = re.findall(r"(\d+[.,]\d{2})\s*€?", text)
        if all_amounts:
            # souvent le montant net est parmi les derniers montants, on prend le dernier non nul
            for a in reversed(all_amounts):
                try:
                    candidate = float(a.replace(",", "."))
                    if candidate > 0:
                        montant = candidate
                        break
                except:
                    continue

    return {
        "montant": round(montant, 2),
        "date": date_fin,
        "categorie": "Revenu",
        "sous_categorie": "Uber Eats",
        "source": "PDF Uber"
    }

    
def parse_fiche_paie(pdf_path: str) -> dict:
    """
    Parseur spécifique pour fiche de paie.
    Objectif : trouver la période (ou la date concernée) et le net à payer.
    Renvoie dict similaire à parse_uber_pdf.
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return {"montant": 0.0, "date": datetime.now().date(), "categorie": "Revenu", "sous_categorie": "Salaire", "source": "PDF Fiche de paie"}

    # 1) Trouver le net à payer (patterns : NET A PAYER, Net à payer, Net pay, Net salary)
    montant = 0.0
    net_patterns = [
        r"NET\s*A\s*PAYER\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})",
        r"Net à payer\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})",
        r"Net à payer \(à vous\)\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})",
        r"Net\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})"  # fallback
    ]
    for p in net_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                montant = float(m.group(1).replace(",", "."))
                break
            except:
                continue

    # fallback : prendre le dernier montant trouvé, mais prudence
    if montant == 0.0:
        amounts = re.findall(r"(\d+[.,]\d{2})\s*€?", text)
        if amounts:
            # on peut prioriser montants > 100 (supposés être net), sinon prendre le dernier
            candidates = [float(a.replace(",", ".")) for a in amounts]
            bigs = [c for c in candidates if c > 100]  # heuristique : salaire > 100€
            montant = bigs[-1] if bigs else candidates[-1]

    # 2) Trouver la période ou la date : recherche de "période" ou intervalle "01/07/2025 - 31/07/2025"
    date_found = None
    periode_match = re.search(r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s*[\-–]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", text)
    if periode_match:
        # on prend la date de fin comme date du revenu
        fin_str = periode_match.groups()[1]
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
            try:
                date_found = datetime.strptime(fin_str, fmt).date()
                break
            except:
                pass

    # autre pattern : "Période du : 01/07/2025 au 31/07/2025" ou "Pour le mois de juillet 2025"
    if not date_found:
        m2 = re.search(r"Pour le mois de\s+([A-Za-zéûà]+)\s+(\d{4})", text, re.IGNORECASE)
        if m2:
            mois_str, annee_str = m2.groups()
            # mapping simple des mois FR (on peut étendre si besoin)
            mois_map = {
                "janvier":1,"février":2,"fevrier":2,"mars":3,"avril":4,"mai":5,"juin":6,
                "juillet":7,"août":8,"aout":8,"septembre":9,"octobre":10,"novembre":11,"décembre":12,"decembre":12
            }
            mois_key = mois_str.lower()
            mois_num = mois_map.get(mois_key)
            if mois_num:
                # on choisit la fin du mois comme date
                from calendar import monthrange
                last_day = monthrange(int(annee_str), mois_num)[1]
                date_found = date(int(annee_str), mois_num, last_day)

    if not date_found:
        # fallback : date d'aujourd'hui
        date_found = datetime.now().date()

    return {
        "montant": round(float(montant), 2),
        "date": date_found,
        "categorie": "Revenu",
        "sous_categorie": "Salaire",
        "source": "PDF Fiche de paie"
    }


def parse_pdf_dispatcher(pdf_path: str, source_type: str) -> dict:
    """
    Dispatcher simple pour choisir le parseur adapté.
    source_type attendu : 'uber', 'fiche_paie', 'ticket' (ou 'auto' pour tentative heuristique).
    """
    stype = source_type.lower().strip()
    if stype in ("uber", "uber_pdf", "uber eats"):
        return parse_uber_pdf(pdf_path)
    elif stype in ("fiche_paie", "fiche de paie", "paye", "salaire"):
        return parse_fiche_paie(pdf_path)
    elif stype in ("ticket", "receipt", "ticket_ocr"):
        # si tu veux parser un PDF ticket (rare), tu peux appeler parse_ticket_metadata en lui passant le texte
        text = extract_text_from_pdf(pdf_path)
        # parse_ticket_metadata attend du texte OCR ; si elle attend un path, adapte
        return parse_ticket_metadata(text)
    elif stype == "auto":
        # heuristique : essaye d'identifier le type en recherchant des mots-clés dans le PDF
        text = extract_text_from_pdf(pdf_path).lower()
        if "uber" in text or "net to driver" in text or "period" in text:
            return parse_uber_pdf(pdf_path)
        if "net a payer" in text or "fiche de paie" in text or "bulletin" in text:
            return parse_fiche_paie(pdf_path)
        # fallback : on renvoie quelque chose générique
        return {"montant": 0.0, "date": datetime.now().date(), "categorie": "Revenu", "sous_categorie": "Inconnu", "source": "PDF Auto"}
    else:
        raise ValueError(f"Source_type inconnu pour parse_pdf_dispatcher: {source_type}")


def ajouter_transaction(
    categorie,
    sous_categorie,
    montant,
    date_transaction,
    type_transac="dépense",
    source="manuel",
    recurrence=None,
    date_fin=None
):
    """Ajoute une transaction dans la base de données."""
    if not categorie or montant <= 0:
        raise ValueError("Catégorie ou montant invalide.")

    # ✅ Connexion à la base configurée
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO transactions (type, categorie, sous_categorie, montant, date, source, recurrence, date_fin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        type_transac,
        categorie.strip(),
        sous_categorie.strip() if sous_categorie else "",
        float(montant),
        date_transaction.isoformat(),
        source,
        recurrence,
        date_fin.isoformat() if date_fin else None
    ))

    conn.commit()
    conn.close()


def _inc(d, recurrence):
    if recurrence == "hebdomadaire":
        return d + relativedelta(weeks=1)
    if recurrence == "mensuelle":
        return d + relativedelta(months=1)
    if recurrence == "annuelle":
        return d + relativedelta(years=1)
    return d  # fallback


def backfill_recurrences_to_today(db_path):
    """
    Pour chaque modèle 'récurrente', génère toutes les occurrences manquantes
    (source='récurrente_auto') jusqu'à aujourd'hui (ou date_fin si elle existe).
    """
    today = date.today()

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1) Récupère tous les modèles
    cur.execute("""
        SELECT id, type, categorie, sous_categorie,description, montant, date, source, recurrence, date_fin
        FROM transactions
        WHERE source='récurrente_auto'
    """)
    models = cur.fetchall()

    for m in models:
        cat = (m["categorie"] or "").strip()
        sous = (m["sous_categorie"] or "").strip()
        rec = (m["recurrence"] or "").strip()
        if not rec:
            continue

        # bornes
        try:
            start = date.fromisoformat(m["date"])
        except Exception:
            continue
        end_limit = None
        if m["date_fin"]:
            try:
                end_limit = date.fromisoformat(m["date_fin"])
            except Exception:
                end_limit = None
        limit = min(today, end_limit) if end_limit else today

        if start > limit:
            continue  # rien à générer encore

        # 2) Dernière occurrence déjà existante
        cur.execute("""
            SELECT MAX(date) as last_date
            FROM transactions
            WHERE source='récurrente_auto'
              AND categorie=? AND sous_categorie=?
              AND recurrence=?
              AND type=?
        """, (cat, sous, rec, m["type"]))
        row = cur.fetchone()
        last = date.fromisoformat(row["last_date"]) if row and row["last_date"] else None

        # 3) Calcule la prochaine date à générer
        if last:
            next_d = _inc(last, rec)
        else:
            # première occurrence = start (et on l’ajoute si <= limit)
            next_d = start

        # 4) Génère tout ce qui manque jusqu’à 'limit'
        to_insert = []
        while next_d <= limit:
            to_insert.append((
                m["type"], cat, sous, float(m["montant"]), next_d.isoformat(),
                "récurrente_auto", rec, m["date_fin"]
            ))
            next_d = _inc(next_d, rec)

        if to_insert:
            cur.executemany("""
                INSERT INTO transactions (type, categorie, sous_categorie, montant, date, source, recurrence, date_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, to_insert)

    conn.commit()
    conn.close()


# ==============================
# ⚙️ CONFIGURATION DES CHEMINS
# ==============================
def interface_configuration_chemins():
    """Interface pour modifier les chemins des dossiers internes"""
    st.header("⚙️ Configuration des dossiers")
    
    st.info("""
    **📁 Organisation actuelle :**
    - 🎯 **Tickets à scanner** : `{}` (sur le Bureau)
    - 🎯 **Revenus à traiter** : `{}` (sur le Bureau)
    - 🔧 **Dossiers modifiables** : Tickets scannés et Revenus traités
    """.format(TO_SCAN_DIR, REVENUS_A_TRAITER))
    
    st.markdown("---")
    
    # Modification des dossiers internes
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📂 Tickets scannés")
        st.write(f"Chemin actuel : `{SORTED_DIR}`")
        nouveau_sorted = st.text_input(
            "Nouveau chemin pour Tickets scannés :",
            value=SORTED_DIR,
            help="Dossier où seront rangés les tickets après traitement"
        )
        
        if st.button("💾 Sauvegarder Tickets scannés"):
            if nouveau_sorted and nouveau_sorted != SORTED_DIR:
                try:
                    os.makedirs(nouveau_sorted, exist_ok=True)
                    config = load_config()
                    config["sorted_dir"] = nouveau_sorted
                    save_config(config)
                    st.success(f"✅ Chemin Tickets scannés mis à jour : {nouveau_sorted}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")
    
    with col2:
        st.subheader("📂 Revenus traités")
        st.write(f"Chemin actuel : `{REVENUS_TRAITES}`")
        nouveau_revenus = st.text_input(
            "Nouveau chemin pour Revenus traités :",
            value=REVENUS_TRAITES,
            help="Dossier où seront rangés les revenus après traitement"
        )
        
        if st.button("💾 Sauvegarder Revenus traités"):
            if nouveau_revenus and nouveau_revenus != REVENUS_TRAITES:
                try:
                    os.makedirs(nouveau_revenus, exist_ok=True)
                    config = load_config()
                    config["revenus_traites_dir"] = nouveau_revenus
                    save_config(config)
                    st.success(f"✅ Chemin Revenus traités mis à jour : {nouveau_revenus}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")
    
    st.markdown("---")
    
    # Réinitialisation
    if st.button("🔄 Réinitialiser les chemins par défaut"):
        config = {"sorted_dir": None, "revenus_traites_dir": None}
        save_config(config)
        st.success("✅ Chemins réinitialisés aux valeurs par défaut")
        st.rerun()

# ==============================
# 📤 UPLOAD DE SECOURS
# ==============================
def interface_upload_secours_tickets():
    """Upload de secours pour les tickets"""
    st.markdown("---")
    st.subheader("📤 Uploader des tickets directement")
    
    uploaded_files = st.file_uploader(
        "Si vous ne trouvez pas le dossier, uploader ici :",
        type=["jpg", "jpeg", "png", "pdf"],
        accept_multiple_files=True,
        key="upload_secours_tickets"
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_path = os.path.join(TO_SCAN_DIR, uploaded_file.name)
            
            # Gestion des doublons
            counter = 1
            name, ext = os.path.splitext(uploaded_file.name)
            while os.path.exists(file_path):
                new_name = f"{name}_{counter}{ext}"
                file_path = os.path.join(TO_SCAN_DIR, new_name)
                counter += 1
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        st.success(f"✅ {len(uploaded_files)} ticket(s) ajouté(s) !")
        st.info("🔄 Actualisez la page pour voir les nouveaux tickets")
        st.rerun()

def interface_upload_secours_revenus():
    """Upload de secours pour les revenus"""
    st.markdown("---")
    st.subheader("📤 Uploader des revenus directement")
    
    uploaded_files = st.file_uploader(
        "Si vous ne trouvez pas le dossier, uploader ici :",
        type=["pdf"],
        accept_multiple_files=True,
        key="upload_secours_revenus"
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_path = os.path.join(REVENUS_A_TRAITER, uploaded_file.name)
            
            # Gestion des doublons
            counter = 1
            name, ext = os.path.splitext(uploaded_file.name)
            while os.path.exists(file_path):
                new_name = f"{name}_{counter}{ext}"
                file_path = os.path.join(REVENUS_A_TRAITER, new_name)
                counter += 1
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        st.success(f"✅ {len(uploaded_files)} revenu(s) ajouté(s) !")
        st.info("🔄 Actualisez la page pour voir les nouveaux revenus")
        st.rerun()


# ==============================
# ⚙️ TRAITEMENT DES TICKETS ET REVENUS
# ==============================
def process_all_tickets_in_folder():
    """
    Traite tous les tickets du dossier TO_SCAN_DIR :
    - OCR
    - extraction montants / date / infos clés
    - confirmation utilisateur
    - insertion en base + déplacement
    """
    st.subheader("🧾 Traitement des tickets à scanner")

    tickets = [f for f in os.listdir(TO_SCAN_DIR) if f.lower().endswith((".jpg", ".png", ".jpeg", ".pdf"))]
    if not tickets:
        st.info("📂 Aucun ticket à scanner pour le moment.")
        return

     # Information des chemins
    st.info(f"""
    **📁 Dossier des tickets à scanner :**
    `{TO_SCAN_DIR}`
    
    **💡 Méthode recommandée :** Glissez-déposez vos tickets directement dans ce dossier sur le Bureau
    """)
    
    tickets = [f for f in os.listdir(TO_SCAN_DIR) if f.lower().endswith((".jpg", ".png", ".jpeg", ".pdf"))]
    
    if not tickets:
        st.warning("📂 Aucun ticket trouvé dans le dossier.")
        # Afficher l'upload de secours si pas de tickets
        interface_upload_secours_tickets()
        return
    
    st.success(f"🧮 {len(tickets)} ticket(s) détecté(s) - Prêts à être traités !")

    st.write(f"🧮 {len(tickets)} ticket(s) détecté(s) dans le dossier à scanner.")

    for ticket_file in tickets:
        ticket_path = os.path.join(TO_SCAN_DIR, ticket_file)
        st.markdown("---")
        st.markdown(f"### 🧾 {ticket_file}")

        # --- OCR selon format ---
        try:
            if ticket_file.lower().endswith(".pdf"):
                text = extract_text_from_pdf(ticket_path)
                # 👉 Affichage PDF : on montre juste le texte OCR
                with st.expander(f"📄 Texte OCR extrait du PDF : {ticket_file}", expanded=False):
                    st.text_area("Contenu OCR :", text, height=200)
            else:
                # 👉 Affichage image : on montre l'image + texte OCR
                text = full_ocr(ticket_path, show_ticket=True)
        except Exception as e:
            st.error(f"❌ Erreur OCR sur {ticket_file} : {e}")
            continue

        # --- Analyse du texte OCR ---
        data = parse_ticket_metadata(text)



        montant_final = data.get("montant", 0.0)
        montants_possibles = data.get("montants_possibles", [montant_final])
        detected_date = data.get("date", datetime.now().date().isoformat())
        key_info = data.get("infos", "")
        
        # --- Déduction de la catégorie et sous-catégorie à partir du nom de fichier ---
        name = os.path.splitext(ticket_file)[0]
        parts = name.split(".")[1:]  # Ignore la première partie (ex: le2)

        if len(parts) >= 2:
            categorie_auto = parts[1].capitalize()
            sous_categorie_auto = parts[0].capitalize()
        elif len(parts) == 1:
            categorie_auto = parts[0].capitalize()
            sous_categorie_auto = "Autre"
        else:
            categorie_auto = "Divers"
            sous_categorie_auto = "Autre"

        # --- Affichage automatique ---
        st.markdown(f"🧠 **Catégorie auto-détectée :** {categorie_auto} → {sous_categorie_auto}")

        # --- Affichage des infos clés OCR ---
        with st.expander("📜 Aperçu OCR (lignes clés)"):
            st.text(key_info)

        # --- Interface de validation du ticket ---
        with st.form(f"form_{ticket_file}"):
            col1, col2 = st.columns(2)
            with col1:
                categorie = st.text_input("Catégorie principale", categorie_auto)
                sous_categorie = st.text_input("Sous-catégorie (ex: supermarché, restaurant...)", sous_categorie_auto)
            with col2:
                montant_select = st.selectbox(
                    "Montant détecté",
                    options=[round(m, 2) for m in montants_possibles],
                    index=0 if montants_possibles else 0
                )
                montant_corrige = st.number_input(
                    "💶 Corriger le montant si besoin (€)",
                    value=float(montant_select) if montant_select else 0.0,
                    min_value=0.0,
                    step=0.01
                )
                date_ticket = st.date_input("📅 Date du ticket", datetime.fromisoformat(detected_date))

            valider = st.form_submit_button("✅ Valider et enregistrer ce ticket")


        # --- Validation / sauvegarde ---
        if valider:
            if not categorie or montant_corrige <= 0:
                st.error("⚠️ Catégorie ou montant invalide.")
                continue

            # Ajout à la base de données
            insert_transaction_batch([{
                "type": "dépense",
                "categorie": categorie.strip(),
                "sous_categorie": sous_categorie.strip(),
                "montant": montant_corrige,
                "date": date_ticket.isoformat(),
                "source": "OCR"
            }])

            # Déplacement du ticket classé
            move_ticket_to_sorted(ticket_path, categorie, sous_categorie)

            st.success(f"💾 Ticket {ticket_file} enregistré avec succès ({montant_corrige:.2f} €).")


def interface_process_all_revenues_in_folder():
    st.subheader("📥 Scanner et enregistrer tous les revenus depuis le dossier")

     # Information des chemins
    st.info(f"""
    **📁 Dossier des revenus à traiter :**
    `{REVENUS_A_TRAITER}`
    
    **💡 Méthode recommandée :** Glissez-déposez vos PDF directement dans ce dossier sur le Bureau
    """)
    
    # [RESTE DU CODE EXISTANT INCHANGÉ jusqu'à la vérification des fichiers...]
    
    src_folder = REVENUS_A_TRAITER 
    pdfs = [os.path.join(root, f)
            for root, _, files in os.walk(src_folder)
            for f in files if f.lower().endswith(".pdf")]
    
    if not pdfs:
        st.warning("📂 Aucun PDF de revenu trouvé dans le dossier.")
        # Afficher l'upload de secours si pas de revenus
        interface_upload_secours_revenus()
        return
    
    st.success(f"🧮 {len(pdfs)} revenu(s) détecté(s) - Prêts à être traités !")

    # --- Étape 1 : scanner les fichiers une seule fois ---
    if "revenus_data" not in st.session_state:
        st.session_state["revenus_data"] = []

    if st.button("🚀 Scanner tous les revenus") and not st.session_state["revenus_data"]:
        pdfs = [os.path.join(root, f)
                for root, _, files in os.walk(src_folder)
                for f in files if f.lower().endswith(".pdf")]

        if not pdfs:
            st.warning("📂 Aucun PDF de revenu trouvé dans le dossier.")
            return

        data_list = []
        for pdf_path in pdfs:
            # Identifier le sous-dossier utile
            parent_folder = os.path.basename(os.path.dirname(pdf_path))

            # Si le parent est "revenus_a_traiter", on ignore
            if parent_folder.lower() in ["revenus_a_traiter", "revenus_traité", "revenus_traités"]:
                sous_dossier = "Revenus"
            else:
                sous_dossier = parent_folder


            # Parsing selon type
            try:
                if sous_dossier.lower() == "uber":
                    parsed = parse_uber_pdf(pdf_path)
                else:
                    parsed = parse_fiche_paie(pdf_path)
            except Exception:
                parsed = {"montant": 0.0, "date": datetime.today().date(), "source": "PDF Auto"}

            # Calcul du mois en français
            date_val = parsed.get("date", datetime.today().date())
            if isinstance(date_val, str):
                date_val = datetime.fromisoformat(date_val).date()
            mois_nom = numero_to_mois(f"{date_val.month:02d}")

            data_list.append({
                "file": os.path.basename(pdf_path),
                "path": pdf_path,
                "categorie": sous_dossier,
                "sous_categorie": mois_nom,
                "montant": parsed.get("montant", 0.0),
                "date": date_val,
                "source": parsed.get("source", "PDF Auto")
            })

        st.session_state["revenus_data"] = data_list
        st.success("✅ Revenus scannés avec succès. Tu peux maintenant les modifier avant validation.")

    # --- Étape 2 : affichage et édition persistante ---
    if st.session_state.get("revenus_data"):
        updated_list = []
        for idx, data in enumerate(st.session_state["revenus_data"]):
            st.markdown("---")
            st.write(f"📄 {data['file']}")
            col1, col2 = st.columns(2)
            with col1:
                cat = st.text_input(f"Catégorie ({data['file']})", value=data["categorie"], key=f"rev_cat_{idx}")
                souscat = st.text_input(f"Sous-catégorie ({data['file']})", value=data["sous_categorie"], key=f"rev_souscat_{idx}")
            with col2:
                montant_str = f"{data['montant']:.2f}" if data["montant"] else ""
                montant_edit = st.text_input(f"Montant (€) ({data['file']})", value=montant_str, key=f"rev_montant_{idx}")
                date_edit = st.date_input(f"Date ({data['file']})", value=data["date"], key=f"rev_date_{idx}")

            try:
                montant_val = float(montant_edit.replace(",", "."))
            except ValueError:
                montant_val = 0.0

            updated_list.append({
                "file": data["file"],
                "path": data["path"],
                "categorie": cat.strip(),
                "sous_categorie": souscat.strip(),
                "montant": montant_val,
                "date": date_edit,
                "source": data["source"]
            })

        st.session_state["revenus_data"] = updated_list

        st.markdown("---")
        st.warning("⚠️ Vérifie bien les informations avant de confirmer l’enregistrement.")

        # --- Étape 3 : validation et insertion ---
        if st.button("✅ Confirmer et enregistrer tous les revenus"):
            conn = get_db_connection()
            cursor = conn.cursor()

            for data in st.session_state["revenus_data"]:
                cursor.execute("""
                    INSERT INTO transactions (type, categorie, sous_categorie, montant, date, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "revenu",
                    data["categorie"],
                    data["sous_categorie"],
                    data["montant"],
                    data["date"].isoformat(),
                    data["source"]
                ))

                # Déplacement du fichier — tout reste centralisé dans /data
                target_dir = os.path.join(REVENUS_TRAITES, data["categorie"], data["sous_categorie"])
                os.makedirs(target_dir, exist_ok=True)

                # On déplace depuis /data/revenus_a_traiter → /data/revenus_traités/...
                shutil.move(data["path"], os.path.join(target_dir, data["file"]))


            conn.commit()
            conn.close()
            st.success("🎉 Tous les revenus ont été enregistrés et rangés avec succès !")
            st.session_state.pop("revenus_data")


# =============================
#   TRANSACTION MANUELLE
# ✍️ AJOUTER UNE TRANSACTION MANUELLE
# =============================
def interface_transaction_manuelle():
    st.subheader("✍️ Ajouter une dépense manuelle")

    mode = st.radio(
        "Choisir le mode d’ajout :",
        ["➕ Ajouter une dépense unique", "📥 Importer plusieurs transactions (CSV)"]
    )

    if mode == "➕ Ajouter une dépense unique":
        with st.form("ajouter_transaction_manuelle", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                categorie = st.text_input("Catégorie principale (ex: essence, courses, santé)")
                sous_categorie = st.text_input("Sous-catégorie (ex: Auchan, médecin, pharmacie)")
                description = st.text_area("Description (facultatif)")
            with col2:
                montant = st.number_input("Montant (€)", min_value=0.0, format="%.2f", step=0.01)
                date_transaction = st.date_input("Date de la transaction", date.today())
            submit_btn = st.form_submit_button("💾 Enregistrer la transaction")

        if submit_btn:
            if not categorie or montant <= 0:
                st.error("⚠️ Veuillez entrer au moins une catégorie et un montant valide.")
                return

            transaction = {
                "type": "dépense",
                "categorie": categorie,
                "sous_categorie": sous_categorie,
                "description": description,
                "montant": montant,
                "date": date_transaction.isoformat(),
                "source": "manuel"
            }
            insert_transaction_batch([transaction])
            st.success(f"✅ Transaction enregistrée : {categorie} → {sous_categorie or '(aucune sous-catégorie)'} — {montant:.2f} €")

    elif mode == "📥 Importer plusieurs transactions (CSV)":
        st.info("💡 Le fichier CSV doit contenir : `Date`, `Categorie`, `Sous_categorie`, `Montant`, `Type` (revenu ou dépense).")
        uploaded_csv = st.file_uploader("Importer un fichier CSV de transactions", type=["csv"])
        if uploaded_csv:
            save_path = os.path.join("data", uploaded_csv.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_csv.getbuffer())

            try:
                df = pd.read_csv(save_path, sep=",", encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(save_path, sep=",", encoding="ISO-8859-1")
            except Exception:
                df = pd.read_csv(save_path, sep=",", encoding="ISO-8859-1")

            st.dataframe(df.head(), use_container_width=True)
            st.success("✅ Fichier CSV lu avec succès. Vérifie ci-dessus les 5 premières lignes.")

            if st.button("📤 Importer dans la base de données"):
                required_cols = {"Date", "Categorie", "Sous_categorie", "Montant", "Type"}
                if not required_cols.issubset(df.columns):
                    st.error("⚠️ Le fichier CSV doit contenir : Date, Categorie, Sous_categorie, Montant, Type.")
                    return

                transactions = []
                for _, row in df.iterrows():
                    try:
                        date_str = str(row["Date"])
                        if "-" in date_str:
                            date_iso = datetime.strptime(date_str, "%Y-%m-%d").date().isoformat()
                        else:
                            try:
                                date_iso = datetime.strptime(date_str, "%d/%m/%Y").date().isoformat()
                            except ValueError:
                                date_iso = datetime.strptime(date_str, "%d/%m/%y").date().isoformat()

                        transactions.append({
                            "type": str(row["Type"]).strip().lower(),
                            "categorie": str(row["Categorie"]).strip(),
                            "sous_categorie": str(row["Sous_categorie"]).strip(),
                            "montant": float(str(row["Montant"]).replace(",", ".")),
                            "date": date_iso,
                            "source": "import_csv"
                        })
                    except Exception as e:
                        st.warning(f"⚠️ Ligne ignorée à cause d'une erreur : {e}")

                insert_transaction_batch(transactions)
                st.success(f"🎉 Import terminé : {len(transactions)} transaction(s) traitée(s).")
        else:
            st.info("📂 Importez un fichier CSV avant de lancer l’import.")


# =============================
# 🔁 AJOUTER UNE TRANSACTION RÉCURRENTE
# =============================
def interface_transaction_recurrente():
    st.subheader("🔁 Ajouter une dépense récurrente")

    with st.form("ajouter_transaction_recurrente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            categorie = st.text_input("Catégorie principale (ex: logement, assurance, abonnement)")
            sous_categorie = st.text_input("Sous-catégorie (ex: EDF, Netflix, Loyer)")
            montant = st.number_input("Montant (€)", min_value=0.0, format="%.2f", step=0.01)
        with col2:
            recurrence = st.selectbox("Fréquence", ["hebdomadaire", "mensuelle", "annuelle"])
            date_debut = st.date_input("Date de début", date.today())
            date_fin = st.date_input("Date de fin (facultatif)", None)
        submit_btn = st.form_submit_button("💾 Enregistrer la récurrence")

    if submit_btn:
        if not categorie or montant <= 0:
            st.error("⚠️ Veuillez entrer une catégorie et un montant valide.")
            return

        safe_categorie = re.sub(r'[<>:"/\\|?*]', "_", categorie.strip())
        safe_sous_categorie = re.sub(r'[<>:"/\\|?*]', "_", sous_categorie.strip()) if sous_categorie else ""

        # Enregistrement modèle + occurrences
        today = date.today()
        occurrences = []
        current_date = date_debut
        while current_date <= today:
            occurrences.append(current_date)
            if recurrence == "hebdomadaire":
                current_date += timedelta(weeks=1)
            elif recurrence == "mensuelle":
                current_date += relativedelta(months=1)
            elif recurrence == "annuelle":
                current_date += relativedelta(years=1)
            if date_fin and current_date > date_fin:
                break

        transactions = [
            # modèle
            {
                "type": "dépense",
                "categorie": safe_categorie,
                "sous_categorie": safe_sous_categorie,
                "montant": montant,
                "date": date_debut.isoformat(),
                "source": "récurrente",
                "recurrence": recurrence,
                "date_fin": date_fin.isoformat() if date_fin else None
            }
        ] + [
            # occurrences passées
            {
                "type": "dépense",
                "categorie": safe_categorie,
                "sous_categorie": safe_sous_categorie,
                "montant": montant,
                "date": d.isoformat(),
                "source": "récurrente_auto",
                "recurrence": recurrence
            } for d in occurrences
        ]

        insert_transaction_batch(transactions)
        st.success(f"✅ Transaction récurrente ({recurrence}) enregistrée.")
        st.info(f"{len(occurrences)} occurrence(s) passée(s) ajoutée(s).")


# ==============================
# 💼 INTERFACE AJOUTER UN REVENU
# ==============================
def interface_ajouter_revenu():
    st.subheader("💼 Ajouter un revenu")

    mode = st.selectbox(
        "Choisir le mode d’ajout du revenu :",
        ["Sélectionner...", "Scanner depuis le dossier", "Ajouter manuellement", "Revenu récurrent"]
    )

    # =============================
    # 1️⃣ Scanner depuis le dossier
    # =============================
    if mode == "Scanner depuis le dossier":
        interface_process_all_revenues_in_folder()

    # =============================
    # 2️⃣ Ajouter un revenu manuel
    # =============================
    elif mode == "Ajouter manuellement":
        with st.form("ajouter_revenu_manuel", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                categorie = st.text_input("Catégorie principale (ex: Uber, Animation, Salaire)")
                sous_categorie = st.text_input("Sous-catégorie (ex: septembre, octobre, etc.)")
            with col2:
                montant = st.number_input("Montant (€)", min_value=0.0, format="%.2f", step=0.01)
                date_revenu = st.date_input("Date du revenu", date.today())

            submit_btn = st.form_submit_button("💾 Enregistrer le revenu")

        if submit_btn:
            if not categorie or montant <= 0:
                st.error("⚠️ Veuillez entrer une catégorie et un montant valide.")
                return

            insert_transaction_batch([{
                "type": "revenu",
                "categorie": categorie.strip(),
                "sous_categorie": sous_categorie.strip(),
                "montant": montant,
                "date": date_revenu.isoformat(),
                "source": "manuel"
            }])
            st.success("✅ Revenu manuel ajouté avec succès !")

    # =============================
    # 3️⃣ Revenu récurrent
    # =============================
    elif mode == "Revenu récurrent":
        with st.form("ajouter_revenu_recurrent", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                categorie = st.text_input("Catégorie principale (ex: Salaire, Bourse, CAF)")
                sous_categorie = st.text_input("Sous-catégorie (ex: septembre, octobre, etc.)")
                montant = st.number_input("Montant du revenu (€)", min_value=0.0, format="%.2f", step=0.01)
            with col2:
                recurrence = st.selectbox("Fréquence", ["mensuelle", "hebdomadaire", "annuelle"])
                date_debut = st.date_input("Date de début", date.today())
                date_fin = st.date_input("Date de fin (facultatif)", None)

            submit_btn = st.form_submit_button("💾 Enregistrer la récurrence")

        if submit_btn:
            if not categorie or montant <= 0:
                st.error("⚠️ Veuillez entrer une catégorie et un montant valide.")
                return

            safe_categorie = re.sub(r'[<>:"/\\|?*]', "_", categorie.strip())
            safe_sous_categorie = re.sub(r'[<>:"/\\|?*]', "_", sous_categorie.strip()) if sous_categorie else ""

            today = date.today()
            occurrences = []
            current_date = date_debut
            while current_date <= today:
                occurrences.append(current_date)
                if recurrence == "hebdomadaire":
                    current_date += timedelta(weeks=1)
                elif recurrence == "mensuelle":
                    current_date += relativedelta(months=1)
                elif recurrence == "annuelle":
                    current_date += relativedelta(years=1)
                if date_fin and current_date > date_fin:
                    break

            transactions = [
                {"type": "revenu", "categorie": safe_categorie, "sous_categorie": safe_sous_categorie,
                 "montant": montant, "date": date_debut.isoformat(), "source": "récurrente", "recurrence": recurrence,
                 "date_fin": date_fin.isoformat() if date_fin else None}
            ] + [
                {"type": "revenu", "categorie": safe_categorie, "sous_categorie": safe_sous_categorie,
                 "montant": montant, "date": d.isoformat(), "source": "récurrente_auto", "recurrence": recurrence}
                for d in occurrences
            ]
            insert_transaction_batch(transactions)
            st.success(f"✅ Revenu récurrent ({recurrence}) ajouté avec succès.")
            st.info(f"{len(occurrences)} versement(s) passé(s) ajouté(s).")


#==============================
# 🔁 GERER LES RECURRENCES
# =============================
def interface_gerer_recurrences():
    st.subheader("🔁 Gérer les transactions récurrentes")
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions WHERE source='récurrente_auto' ORDER BY date DESC", conn)
    conn.close()

    if df.empty:
        st.info("Aucune transaction récurrente trouvée.")
        return

    st.dataframe(df, use_container_width=True)
    selected_id = st.selectbox("Sélectionner une récurrence à modifier :", df["id"].tolist())

    if selected_id:
        selected = df[df["id"] == selected_id].iloc[0]
        st.markdown(f"### 🧾 {selected['categorie']} → {selected['sous_categorie']}")
        new_montant = st.number_input("Montant", value=float(selected["montant"]), step=0.01)
        new_recurrence = st.selectbox("Récurrence", ["hebdomadaire", "mensuelle", "annuelle"], index=["hebdomadaire","mensuelle","annuelle"].index(selected["recurrence"]))
        new_date_fin = st.date_input("Date de fin", value=date.today() if not selected["date_fin"] else datetime.fromisoformat(selected["date_fin"]).date())
        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Enregistrer les modifications"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE transactions SET montant=?, recurrence=?, date_fin=? WHERE id=?", (new_montant, new_recurrence, new_date_fin.isoformat(), selected_id))
                conn.commit()
                conn.close()
                st.success("✅ Récurrence mise à jour avec succès.")

        with col2:
            if st.button("🗑️ Supprimer cette récurrence et toutes ses occurrences"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transactions WHERE (source LIKE 'récurrente%' AND categorie=? AND sous_categorie=?)", (selected["categorie"], selected["sous_categorie"]))
                conn.commit()
                conn.close()
                st.success("🗑️ Récurrence supprimée entièrement.")


# =============================
# 🛠️ GERER LES TRANSACTIONS
# =============================
def interface_gerer_transactions():
    st.subheader("🛠️ Gérer les transactions (modifier ou supprimer)")

    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()

    if df.empty:
        st.info("Aucune transaction à gérer pour le moment.")
        return

    type_filter = st.selectbox("Type", ["Toutes", "revenu", "dépense"], key="type_filtre_gerer")
    cat_filter = st.selectbox("Catégorie", ["Toutes"] + sorted(df["categorie"].dropna().unique().tolist()), key="cat_filtre_gerer")
    souscat_filter = st.selectbox("Sous-catégorie", ["Toutes"] + sorted(df["sous_categorie"].dropna().unique().tolist()), key="souscat_filtre_gerer")

    if type_filter != "Toutes": df = df[df["type"] == type_filter]
    if cat_filter != "Toutes": df = df[df["categorie"] == cat_filter]
    if souscat_filter != "Toutes": df = df[df["sous_categorie"] == souscat_filter]

    if df.empty:
        st.warning("Aucune transaction trouvée avec ces filtres.")
        return

    df["🗑️ Supprimer"] = False
    st.info("💡 Modifie les valeurs directement ou coche les lignes à supprimer.")
    df_edit = st.data_editor(df, use_container_width=True, num_rows="fixed", key="editor_transactions", hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Enregistrer les modifications dans la base"):
            conn = sqlite3.connect(os.path.join(DATA_DIR, "finances.db"))
            cursor = conn.cursor()
            for _, row in df_edit.iterrows():
                cursor.execute("UPDATE transactions SET categorie=?, sous_categorie=?, montant=?, date=? WHERE id=?", (row["categorie"], row["sous_categorie"], float(row["montant"]), row["date"], row["id"]))
            conn.commit()
            conn.close()
            st.success(f"✅ {len(df_edit)} transaction(s) mise(s) à jour avec succès.")

    with col2:
        if st.button("🚮 Supprimer les transactions sélectionnées"):
            to_delete = df_edit[df_edit.get("🗑️ Supprimer", False)]
            if not to_delete.empty:
                conn = get_db_connection()
                cursor = conn.cursor()
                for _, row in to_delete.iterrows():
                    cursor.execute("DELETE FROM transactions WHERE id=?", (row["id"],))
                conn.commit()
                conn.close()
                st.success(f"🗑️ {len(to_delete)} transaction(s) supprimée(s) avec succès.")
            else:
                st.warning("⚠️ Coche au moins une transaction avant de supprimer.")


# =============================
# 📊 VOIR TOUTES LES TRANSACTIONS
# =============================
def interface_voir_transactions():
    st.subheader("📊 Voir toutes les transactions")
    
    # ✅ Backfill automatique avant de charger le tableau
    backfill_recurrences_to_today(DB_PATH)

    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()

    if df.empty:
        st.info("Aucune transaction enregistrée pour le moment.")
        return

    afficher_recurrentes = st.checkbox("👁️ Afficher aussi les modèles de récurrence (source = 'récurrente')", value=False)
    if not afficher_recurrentes: df = df[df["source"] != "récurrente"]

    type_filter = st.selectbox("Type de transaction", ["Toutes", "revenu", "dépense"])
    categories = ["Toutes"] + sorted(df["categorie"].dropna().unique().tolist())
    cat_filter = st.selectbox("Catégorie", categories)

    souscats = ["Toutes"]
    if cat_filter != "Toutes": souscats += sorted(df[df["categorie"] == cat_filter]["sous_categorie"].dropna().unique().tolist())
    souscat_filter = st.selectbox("Sous-catégorie", souscats)

    col1, col2 = st.columns(2)
    date_debut = col1.date_input("Date début", value=date(2025,1,1))
    date_fin = col2.date_input("Date fin", value=date.today())

    if type_filter != "Toutes": df = df[df["type"] == type_filter]
    if cat_filter != "Toutes": df = df[df["categorie"] == cat_filter]
    if souscat_filter != "Toutes": df = df[df["sous_categorie"] == souscat_filter]
    df = df[(df["date"] >= date_debut.isoformat()) & (df["date"] <= date_fin.isoformat())]

    if df.empty:
        st.warning("Aucune transaction trouvée avec ces filtres.")
        return

    st.markdown("---")
    st.markdown("### ✏️ Sélectionne les transactions à analyser ou laisse tout vide pour tout inclure")
    df_edit = st.data_editor(df, use_container_width=True, height=600, num_rows="fixed", key="data_view_editor",
                             column_config={"id":"ID","type":"Type","categorie":"Catégorie","sous_categorie":"Sous-catégorie","montant":"Montant (€)","date":"Date","source":"Source","recurrence":"Récurrence"}, hide_index=True)

    selected_rows = df_edit[df_edit.get("selected", False)] if "selected" in df_edit.columns else df_edit
    total_revenus = selected_rows[selected_rows["type"]=="revenu"]["montant"].sum()
    total_depenses = selected_rows[selected_rows["type"]=="dépense"]["montant"].sum()
    solde = total_revenus - total_depenses
    couleur_solde = "green" if solde>=0 else "red"

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("💸 Total revenus", f"{total_revenus:.2f} €")
    col2.metric("💳 Total dépenses", f"{total_depenses:.2f} €")
    col3.markdown(f"<h4 style='color:{couleur_solde}; text-align:center;'>💰 Solde : {solde:.2f} €</h4>", unsafe_allow_html=True)
    st.caption(f"📊 Calcul basé sur {len(selected_rows)} transaction(s) affichée(s).")




# Liste de catégories valides connues (tu peux l’étendre à volonté)
KNOWN_CATEGORIES = [
    "essence", "alimentation", "supermarché", "carrefour", "auchan",
    "restaurant", "boulangerie", "loisirs", "santé", "logement", "transport"
]

def correct_category_name(name):
    """Corrige les fautes simples dans les noms de catégorie/sous-catégorie."""
    if not name:
        return name
    name = name.lower().strip()
    matches = get_close_matches(name, KNOWN_CATEGORIES, n=1, cutoff=0.8)
    return matches[0] if matches else name


# ==============================
# 📋 MENU LATÉRAL
# ==============================
with st.sidebar:
    st.title("📂 Menu principal")
    page = st.radio(
        "Navigation",
        ["💸 Transactions", "📊 Voir Transactions"]
    )

# ==============================
# 💸 PAGE TRANSACTIONS
# ==============================
if page == "💸 Transactions":
    st.header("💸 Transactions")

    # Onglets pour les sous-parties
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧾 Ajouter un ticket",
        "✍️ Ajouter une dépense manuelle",
        "🔁 Dépense récurrente",
        "💰 Ajouter un revenu"
    ])

    with tab1:
        st.header("📸 Scanner les tickets automatiquement")
        st.info(f"Dépose tes tickets à scanner dans : `{TO_SCAN_DIR}`")
        process_all_tickets_in_folder()
    
    with tab2:
        interface_transaction_manuelle()

    with tab3:
        interface_transaction_recurrente()
    
    with tab4:
        interface_ajouter_revenu()

# ==============================
# 📊 PAGE VOIR / GÉRER TRANSACTIONS
# ==============================
elif page == "📊 Voir Transactions":
    st.header("📊 Voir Transactions")

    # --- Onglets pour les sous-parties ---
    tab1, tab2, tab3 = st.tabs([
        "📋 Transactions",
        "🗑️ Gérer les transactions",
        "🔁 Gérer les récurrences"
    ])

    # === Onglet 1 : Visualisation ===
    with tab1:
        interface_voir_transactions()

    # === Onglet 2 : Suppression et gestion ===
    with tab2:
        interface_gerer_transactions()

    # === Onglet 3 : Gestion des récurrences ===
    with tab3:
        interface_gerer_recurrences()
        
      

