"""
Error Handler UI - Messages d'Erreur Conviviaux

Traduit les erreurs techniques en messages clairs pour l'utilisateur.
Affiche des conseils pratiques pour résoudre les problèmes.
"""

import streamlit as st
from typing import Optional
from shared.exceptions import (
    GestioException,
    DatabaseError,
    OCRError,
    ValidationError,
    ServiceError,
    FileOperationError,
    ConfigurationError
)
from shared.logging_config import get_logger

logger = get_logger(__name__)


def display_error(error: Exception, context: str = "") -> None:
    """
    Affiche une erreur de manière conviviale dans Streamlit.
    
    Traduit les erreurs techniques en messages simples avec des conseils.
    
    Args:
        error: L'exception levée
        context: Contexte optionnel (ex: "lors de l'ajout d'une transaction")
    
    Example:
        >>> try:
        ...     add_transaction(data)
        ... except DatabaseError as e:
        ...     display_error(e, "lors de l'ajout de la transaction")
    """
    logger.error(f"Displaying error to user: {error}", exc_info=True)
    
    # Déterminer le type d'erreur et afficher le message approprié
    if isinstance(error, DatabaseError):
        _display_database_error(error, context)
    
    elif isinstance(error, OCRError):
        _display_ocr_error(error, context)
    
    elif isinstance(error, ValidationError):
        _display_validation_error(error, context)
    
    elif isinstance(error, ServiceError):
        _display_service_error(error, context)
    
    elif isinstance(error, FileOperationError):
        _display_file_error(error, context)
    
    elif isinstance(error, ConfigurationError):
        _display_config_error(error, context)
    
    elif isinstance(error, GestioException):
        _display_generic_gestio_error(error, context)
    
    else:
        _display_unknown_error(error, context)


def _display_database_error(error: DatabaseError, context: str) -> None:
    """Affiche une erreur de base de données de manière conviviale."""
    error_msg = str(error).lower()
    
    # Analyser le message d'erreur pour donner des conseils spécifiques
    if "locked" in error_msg or "verrouillée" in error_msg:
        st.error("⏳ **Base de données temporairement occupée**")
        st.info("""
        💡 **Que faire ?**
        - Attendez quelques secondes et réessayez
        - Fermez les autres fenêtres de l'application si ouvertes
        - Si le problème persiste, redémarrez l'application
        """)
    
    elif "unique" in error_msg or "constraint" in error_msg:
        st.error("🚫 **Cette donnée existe déjà**")
        st.info("""
        💡 **Que faire ?**
        - Vérifiez que vous n'avez pas déjà ajouté cette transaction
        - Modifiez légèrement les informations pour la rendre unique
        """)
    
    elif "no such table" in error_msg or "no such column" in error_msg:
        st.error("🗄️ **Structure de base de données incorrecte**")
        st.warning("""
        ⚠️ **Action requise**
        - La base de données semble corrompue ou ancienne
        - Contactez le support technique
        - Sauvegardez vos données avant toute manipulation
        """)
    
    else:
        st.error(f"❌ **Erreur de base de données** {context}")
        st.info("""
        💡 **Que faire ?**
        - Vérifiez que vous avez les droits d'accès au fichier
        - Assurez-vous que le disque n'est pas plein
        - Redémarrez l'application si nécessaire
        """)
    
    # Détails techniques en expander (pour les utilisateurs avancés)
    with st.expander("🔧 Détails techniques (pour support)"):
        st.code(str(error))


def _display_ocr_error(error: OCRError, context: str) -> None:
    """Affiche une erreur OCR de manière conviviale."""
    error_msg = str(error).lower()
    
    if "tesseract" in error_msg:
        st.error("📸 **Logiciel de reconnaissance manquant**")
        st.info("""
        💡 **Installation requise**
        - Le logiciel Tesseract OCR n'est pas installé
        - Consultez le guide d'installation dans la documentation
        - Contactez votre administrateur si vous n'avez pas les droits
        """)
    
    elif "empty" in error_msg or "vide" in error_msg:
        st.error("📄 **Impossible de lire le ticket**")
        st.info("""
        💡 **Que faire ?**
        - Vérifiez que l'image est claire et bien éclairée
        - Prenez une nouvelle photo du ticket
        - Assurez-vous que le texte est lisible
        - Évitez les photos floues ou trop sombres
        """)
    
    elif "amount" in error_msg or "montant" in error_msg:
        st.warning("💰 **Montant non détecté automatiquement**")
        st.info("""
        💡 **Que faire ?**
        - Vous pouvez saisir le montant manuellement
        - Assurez-vous que le montant est bien visible sur la photo
        - Essayez de recadrer l'image sur le total
        """)
    
    else:
        st.error(f"📸 **Erreur de lecture du ticket** {context}")
        st.info("""
        💡 **Que faire ?**
        - Prenez une photo plus claire du ticket
        - Assurez-vous que le document est bien éclairé
        - Évitez les reflets et les ombres
        - Essayez avec un format PDF si possible
        """)
    
    with st.expander("🔧 Détails techniques"):
        st.code(str(error))


def _display_validation_error(error: ValidationError, context: str) -> None:
    """Affiche une erreur de validation de manière conviviale."""
    st.warning(f"⚠️ **Données invalides** {context}")
    st.error(f"**Problème** : {str(error)}")
    st.info("""
    💡 **Que faire ?**
    - Vérifiez que tous les champs obligatoires sont remplis
    - Assurez-vous que les montants sont positifs
    - Vérifiez le format des dates (JJ/MM/AAAA)
    - Contrôlez que la catégorie existe
    """)


def _display_service_error(error: ServiceError, context: str) -> None:
    """Affiche une erreur de service de manière conviviale."""
    error_msg = str(error).lower()
    
    if "export" in error_msg:
        st.error("📊 **Erreur lors de l'export**")
        st.info("""
        💡 **Que faire ?**
        - Vérifiez qu'il y a bien des données à exporter
        - Assurez-vous d'avoir les droits d'écriture dans le dossier
        - Fermez le fichier Excel s'il est ouvert
        - Essayez un autre emplacement de sauvegarde
        """)
    
    elif "recurrence" in error_msg or "récurrence" in error_msg:
        st.error("🔄 **Erreur de génération automatique**")
        st.info("""
        💡 **Que faire ?**
        - Vérifiez les paramètres de la récurrence
        - Assurez-vous que les dates sont cohérentes
        - Contrôlez que la fréquence est valide
        """)
    
    else:
        st.error(f"⚙️ **Erreur de traitement** {context}")
        st.info("""
        💡 **Que faire ?**
        - Réessayez l'opération
        - Vérifiez vos données
        - Contactez le support si le problème persiste
        """)
    
    with st.expander("🔧 Détails techniques"):
        st.code(str(error))


def _display_file_error(error: FileOperationError, context: str) -> None:
    """Affiche une erreur de fichier de manière conviviale."""
    error_msg = str(error).lower()
    
    if "not found" in error_msg or "introuvable" in error_msg:
        st.error("📁 **Fichier introuvable**")
        st.info("""
        💡 **Que faire ?**
        - Vérifiez que le fichier n'a pas été déplacé ou supprimé
        - Assurez-vous que le chemin d'accès est correct
        - Vérifiez vos dossiers de sauvegarde
        """)
    
    elif "permission" in error_msg or "denied" in error_msg:
        st.error("🔒 **Accès refusé au fichier**")
        st.warning("""
        ⚠️ **Action requise**
        - Vous n'avez pas les droits sur ce fichier
        - Demandez les permissions à votre administrateur
        - Essayez dans un autre dossier
        """)
    
    elif "disk" in error_msg or "space" in error_msg:
        st.error("💾 **Espace disque insuffisant**")
        st.warning("""
        ⚠️ **Action requise**
        - Libérez de l'espace sur votre disque
        - Supprimez des fichiers inutiles
        - Déplacez des fichiers vers un disque externe
        """)
    
    else:
        st.error(f"📁 **Erreur de fichier** {context}")
        st.info("""
        💡 **Que faire ?**
        - Vérifiez que le fichier existe
        - Assurez-vous d'avoir les droits nécessaires
        - Essayez avec un autre fichier
        """)
    
    with st.expander("🔧 Détails techniques"):
        st.code(str(error))


def _display_config_error(error: ConfigurationError, context: str) -> None:
    """Affiche une erreur de configuration de manière conviviale."""
    st.error("⚙️ **Erreur de configuration de l'application**")
    st.warning("""
    ⚠️ **Contactez le support technique**
    
    L'application n'est pas correctement configurée.
    Ce problème nécessite l'intervention d'un administrateur.
    
    **Ne tentez pas de résoudre ce problème vous-même.**
    """)
    
    with st.expander("🔧 Détails pour le support"):
        st.code(str(error))


def _display_generic_gestio_error(error: GestioException, context: str) -> None:
    """Affiche une erreur Gestio générique."""
    st.error(f"❌ **Une erreur s'est produite** {context}")
    st.info("""
    💡 **Que faire ?**
    - Réessayez l'opération
    - Redémarrez l'application si nécessaire
    - Contactez le support si le problème persiste
    """)
    
    with st.expander("🔧 Détails techniques"):
        st.code(str(error))


def _display_unknown_error(error: Exception, context: str) -> None:
    """Affiche une erreur inconnue de manière conviviale."""
    st.error(f"⚠️ **Erreur inattendue** {context}")
    st.warning("""
    Une erreur inattendue s'est produite.
    
    **Recommandations** :
    - Notez ce que vous faisiez au moment de l'erreur
    - Sauvegardez vos données en cours
    - Redémarrez l'application
    - Contactez le support avec les détails ci-dessous
    """)
    
    with st.expander("🔧 Détails complets pour le support"):
        st.code(str(error))
        st.code(f"Type: {type(error).__name__}")


def success_message(message: str, details: Optional[str] = None) -> None:
    """
    Affiche un message de succès convivial.
    
    Args:
        message: Message principal de succès
        details: Détails optionnels
    
    Example:
        >>> success_message("Transaction ajoutée", "ID: 142, Montant: 45.50€")
    """
    st.success(f"✅ {message}")
    if details:
        st.info(details)


def warning_message(message: str, advice: Optional[str] = None) -> None:
    """
    Affiche un avertissement convivial.
    
    Args:
        message: Message d'avertissement
        advice: Conseil optionnel
    
    Example:
        >>> warning_message("Aucune transaction trouvée", "Essayez d'élargir la période")
    """
    st.warning(f"⚠️ {message}")
    if advice:
        st.info(f"💡 **Conseil** : {advice}")
