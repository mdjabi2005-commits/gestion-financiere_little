"""
Transactions Add Module - Interface d'ajout de transactions.

Ce module contient les fonctions pour ajouter des transactions :
- interface_transactions_simplifiee() : Menu principal d'ajout
- interface_ajouter_depenses_fusionnee() : Ajout manuel + Import CSV
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime, date
from config import TO_SCAN_DIR, REVENUS_A_TRAITER
from shared.ui import (
    load_transactions,
    insert_transaction_batch,
    refresh_and_rerun
)
from shared.ui import toast_success, toast_error
from shared.utils import safe_convert
from domains.revenues import is_uber_transaction, process_uber_revenue
from domains.transactions.service import normalize_category, normalize_subcategory


def interface_transactions_simplifiee() -> None:
    """
    Simplified transaction interface - main menu for adding transactions.

    Features:
    - Scanner un ticket (OCR)
    - Ajouter des dépenses (manuel + CSV)
    - Créer une transaction récurrente
    - Ajouter un revenu

    Returns:
        None
    """
    st.title("💸 Ajouter une Transaction")

    # Menu de sélection principal
    col1, col2 = st.columns([3, 1])

    with col1:
        type_action = st.selectbox(
            "Que voulez-vous faire ?",
            [
                "📸 Scanner un ticket (OCR)",
                "💰 Scanner un revenu (PDF)",
                "💸 Ajouter une Dépense ou un Revenu"
            ],
            key="type_action_transaction"
        )

    with col2:
        st.caption("")
        st.caption("")
        if st.button("🔄 Actualiser", key="refresh_transactions"):
            refresh_and_rerun()

    st.markdown("---")

    # === SCANNER UN TICKET ===
    if type_action == "📸 Scanner un ticket (OCR)":
        st.subheader("📸 Scanner les tickets automatiquement")
        st.info(f"**📂 Dossier de scan :** `{TO_SCAN_DIR}`")

        with st.expander("ℹ️ Comment ça marche ?", expanded=False):
            st.markdown(f"""
            ### Mode d'emploi :
            1. **Nommer votre ticket** avec le format : `nom.categorie.sous_categorie.extension`
               - Exemple : `carrefour.alimentation.courses.jpg`
               - Exemple : `shell.transport.essence.jpg`
            2. **Déposer le fichier** dans le dossier : `{TO_SCAN_DIR}`
            3. **Cliquer sur "Scanner"** ci-dessous
            4. **Vérifier et valider** les informations détectées

            **Formats acceptés :** JPG, PNG, PDF
            """)

        # Import scanning function here to avoid circular imports
        from domains.ocr.pages.scanning import process_all_tickets_in_folder
        process_all_tickets_in_folder()

    # === AJOUTER DES DÉPENSES (MANUEL + CSV) ===
    elif type_action == "💰 Scanner un revenu (PDF)":
        from domains.revenues.pages.revenues import interface_process_all_revenues_in_folder
        st.subheader("💰 Scanner un revenu (PDF)")
        st.info(f"**📂 Dossier de scan :** `{REVENUS_A_TRAITER}`")
        interface_process_all_revenues_in_folder()

    # === REVENU (NON-RÉCURRENT) ===
    elif type_action == "💸 Ajouter une Dépense ou un Revenu":
        
        # Import revenue function to avoid circular imports
        interface_ajouter_depenses_fusionnee() 


def interface_ajouter_depenses_fusionnee() -> None:
    """
    Unified interface for adding expenses (manual + CSV import).

    Features:
    - Manual entry form
    - CSV bulk import with template download
    - Duplicate detection
    - Uber revenue processing support

    Returns:
        None
    """
    st.subheader("💸 Ajouter une Dépense ou un Revenu")

    # Tabs pour séparer clairement les deux méthodes
    tab1, tab2 = st.tabs(["✍️ Ajout manuel", "📄 Import CSV"])

    # ===== TAB 1: AJOUT MANUEL =====
    with tab1:
        st.markdown("### ✍️ Ajouter une dépense manuellement")
        st.info("💡 Remplissez le formulaire ci-dessous pour ajouter une seule dépense")

        with st.form("add_manual_depense"):
            col1, col2, col3 = st.columns(3)

            with col1:
                date_tr = st.date_input("📅 Date", value=date.today())
                type_tr = st.selectbox("📊 Type", ["dépense", "revenu"])

            with col2:
                cat = st.text_input("🏷️ Catégorie principale", placeholder="Ex: Alimentation")
                sous_cat = st.text_input("📌 Sous-catégorie", placeholder="Ex: Courses")

            with col3:
                montant = st.number_input("💰 Montant (€)", min_value=0.0, step=0.01, format="%.2f")
                desc = st.text_input("📝 Description", placeholder="Ex: Carrefour")

            # Uber tax checkbox (shown inside form so user can see it before submitting)
            apply_uber_tax = st.checkbox(
                "🚗 Appliquer la taxe Uber (21%) pour ce revenu ?",
                value=False,
                key="apply_uber_tax_manual",
                help="Cochez cette case uniquement si c'est un revenu Uber. Le prélèvement de 21% sera appliqué automatiquement. ⚠️ Ne pas ajouter les dépenses URSSAF séparément dans ce cas."
            )

            valider = st.form_submit_button("✅ Ajouter la transaction", type="primary")

        if valider:
            if not cat or montant <= 0:
                toast_error("Veuillez entrer au moins une catégorie et un montant valide.")
            else:
                transaction_data = {
                    "type": type_tr,
                    "categorie": normalize_category(cat.strip()),
                    "sous_categorie": normalize_subcategory(sous_cat.strip()),
                    "description": desc.strip(),
                    "montant": float(montant),
                    "date": date_tr.isoformat(),
                    "source": "manuel"
                }

                # Process Uber revenue ONLY if user checked the box AND it's actually an Uber transaction
                if type_tr == "revenu" and apply_uber_tax:
                    if is_uber_transaction(cat, desc):
                        transaction_data, uber_msg = process_uber_revenue(transaction_data, apply_tax=True)
                        if uber_msg:
                            st.info(uber_msg)
                    else:
                        st.warning("⚠️ La taxe Uber n'a pas été appliquée car la transaction ne contient pas le mot 'Uber'.")

                insert_transaction_batch([transaction_data])
                toast_success(f"✅ Transaction ajoutée : {cat} — {transaction_data['montant']:.2f} €")
                st.balloons()
                st.info("💡 N'oubliez pas d'actualiser la page pour voir vos changements")

    # ===== TAB 2: IMPORT CSV =====
    with tab2:
        st.markdown("### 📄 Importer plusieurs dépenses depuis un fichier CSV")

        # Guide étape par étape
        st.markdown("#### 📋 Guide d'importation")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("##### 1️⃣ Télécharger le modèle")
            st.caption("Téléchargez le fichier modèle CSV avec les colonnes requises")

            # Créer un modèle CSV
            modele_csv = """type,date,categorie,sous_categorie,montant,description
dépense,2024-01-15,alimentation,courses,45.50,Carrefour
dépense,2024-01-16,transport,essence,60.00,Shell Station
revenu,2024-01-01,salaire,mensuel,2500.00,Salaire janvier
dépense,2024-01-20,loisirs,restaurant,35.80,Pizza
revenu,2024-01-15,freelance,mission,450.00,Projet X"""

            st.download_button(
                label="⬇️ Télécharger le modèle",
                data=modele_csv,
                file_name="modele_transactions.csv",
                mime="text/csv",
                help="Modèle avec exemples de transactions"
            )

        with col2:
            st.markdown("##### 2️⃣ Compléter le fichier")
            st.caption("Ouvrez le fichier dans Excel/LibreOffice et ajoutez vos transactions")
            st.markdown("""
            **Colonnes requises :**
            - `type` : dépense ou revenu
            - `date` : AAAA-MM-JJ
            - `categorie` : Catégorie principale
            - `sous_categorie` : Sous-catégorie
            - `montant` : Montant (avec . ou ,)
            - `description` : Description
            """)

        with col3:
            st.markdown("##### 3️⃣ Importer le fichier")
            st.caption("Uploadez votre fichier CSV complété ci-dessous")

        st.markdown("---")

        # Zone d'upload
        uploaded_file = st.file_uploader(
            "📤 Sélectionner votre fichier CSV",
            type=['csv'],
            help="Sélectionnez le fichier CSV avec vos transactions",
            key="csv_uploader_depenses"
        )

        if uploaded_file is not None:
            st.success(f"✅ Fichier '{uploaded_file.name}' chargé !")

            try:
                # Lire le CSV
                df_import = pd.read_csv(io.StringIO(uploaded_file.getvalue().decode('utf-8')))

                st.markdown("#### 📊 Aperçu des données")
                st.dataframe(df_import.head(10), use_container_width=True)

                st.info(f"📈 **{len(df_import)}** transactions détectées dans le fichier")

                # Options d'import
                col1, col2 = st.columns(2)

                with col1:
                    ignorer_doublons = st.checkbox(
                        "🔒 Ignorer les doublons",
                        value=True,
                        help="Évite d'importer plusieurs fois la même transaction"
                    )

                with col2:
                    st.caption("")

                # Bouton d'import
                if st.button("✅ Importer les transactions", type="primary", key="import_csv_depenses_btn"):
                    with st.spinner("Import en cours..."):
                        # Préparer les transactions
                        transactions_a_importer = []

                        for idx, row in df_import.iterrows():
                            # Conversion sécurisée
                            transaction = {
                                "type": str(row.get('type', 'dépense')).strip().lower(),
                                "date": str(row.get('date', datetime.now().date())),
                                "categorie": str(row.get('categorie', 'Divers')).strip(),
                                "sous_categorie": str(row.get('sous_categorie', 'Autre')).strip(),
                                "montant": safe_convert(row.get('montant', 0)),
                                "description": str(row.get('description', '')).strip() if pd.notna(row.get('description')) else "",
                                "source": "CSV Import"
                            }

                            # Validation basique
                            if transaction["montant"] > 0:
                                transactions_a_importer.append(transaction)

                        if transactions_a_importer:
                            # Insertion
                            if ignorer_doublons:
                                # Charger transactions existantes pour vérifier doublons
                                df_existant = load_transactions()
                                nouvelles = []
                                doublons = 0

                                for trans in transactions_a_importer:
                                    # Vérification doublon simple (même date, montant, catégorie)
                                    est_doublon = False
                                    if not df_existant.empty:
                                        est_doublon = (
                                            (df_existant['date'] == pd.Timestamp(trans['date'])) &
                                            (df_existant['montant'] == trans['montant']) &
                                            (df_existant['categorie'] == trans['categorie'])
                                        ).any()

                                    if not est_doublon:
                                        nouvelles.append(trans)
                                    else:
                                        doublons += 1

                                if nouvelles:
                                    insert_transaction_batch(nouvelles)
                                    toast_success(f"✅ {len(nouvelles)} transaction(s) importée(s) avec succès !")
                                    if doublons > 0:
                                        st.warning(f"⚠️ {doublons} doublon(s) ignoré(s)")
                                else:
                                    st.warning("⚠️ Toutes les transactions sont des doublons")
                            else:
                                insert_transaction_batch(transactions_a_importer)
                                toast_success(f"✅ {len(transactions_a_importer)} transaction(s) importée(s) !")

                            st.balloons()
                            st.info("💡 N'oubliez pas d'actualiser la page pour voir vos changements")
                        else:
                            toast_error("Aucune transaction valide trouvée dans le fichier")

            except Exception as e:
                st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
                st.caption("Vérifiez que le fichier respecte bien le format du modèle")
