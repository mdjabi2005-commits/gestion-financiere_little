# 🧪 Guide d'Installation pour Testeurs Beta
## Gestion Financière Little

---

## 📥 Téléchargement

**Lien de téléchargement :** [GitHub Releases](https://github.com/mdjabi2005-commits/gestion-financiere_little/releases/latest)

Téléchargez selon votre système :
- 🪟 **Windows** : `GestionFinanciereLittle-Windows.zip`
- 🐧 **Linux** : `GestionFinanciereLittle-Linux.zip`
- 🍎 **macOS** : `GestionFinanciereLittle-macOS.zip`

---

## 🚀 Installation Rapide

### 🪟 Windows (Exécutable Standalone)

1. **Extraire** le ZIP
2. **Double-cliquer** sur `GestionFinanciereLittle.exe`
3. ✅ L'application s'ouvre dans votre navigateur !

⚠️ **Gardez tous les fichiers ensemble dans le même dossier**

---

### 🐧 Linux (Installation Automatique)

#### Méthode Recommandée : Script Automatique
```bash
# 1. Extraire le ZIP
unzip GestionFinanciereLittle-Linux.zip
cd GestionFinanciereLittle-Linux

# 2. Lancer le script (gère tout automatiquement)
chmod +x run.sh
./run.sh
```

Le script va :
- ✅ Vérifier si Python est installé
- ✅ **Proposer d'installer Python automatiquement si manquant**
- ✅ Installer Streamlit automatiquement
- ✅ Lancer l'application

💡 **Rien à faire manuellement !** Le script vous guide pas à pas.

#### Installation Manuelle (si le script échoue)
```bash
# Installer Python 3.11+ (si pas déjà installé)
sudo apt update
sudo apt install python3 python3-pip

# Installer Tesseract OCR (optionnel)
sudo apt install tesseract-ocr tesseract-ocr-fra

# Lancer
./run.sh
```

✅ **L'application s'ouvre dans votre navigateur !**

---

### 🍎 macOS (Installation Automatique)

#### Méthode Recommandée : Script Automatique
```bash
# 1. Extraire le ZIP
unzip GestionFinanciereLittle-macOS.zip
cd GestionFinanciereLittle-macOS

# 2. Lancer le script
chmod +x run.sh
./run.sh
```

Le script va :
- ✅ Vérifier si Python est installé
- ✅ **Proposer d'installer Python via Homebrew si manquant**
- ✅ Installer Streamlit automatiquement
- ✅ Lancer l'application

💡 **Si Homebrew n'est pas installé**, le script vous dira comment l'installer.

#### Installation Manuelle (si le script échoue)
```bash
# Installer Homebrew (si pas déjà installé)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Installer Python 3.11+
brew install python@3.11

# Installer Tesseract OCR (optionnel)
brew install tesseract tesseract-lang

# Lancer
./run.sh
```

✅ **L'application s'ouvre dans votre navigateur !**

---

## ⚠️ IMPORTANT : Antivirus et Alertes Windows

### Pourquoi mon antivirus réagit ?

Cette application est **100% sûre** mais compilée avec PyInstaller, un outil aussi utilisé par des malwares. 
C'est un **faux positif** très courant pour les applications Python.

**Preuves de sécurité :**
- ✅ Code source ouvert et vérifiable sur GitHub
- ✅ Compilé automatiquement par GitHub Actions (processus transparent)
- ✅ Aucun code suspect dans le projet
- ✅ Application de gestion financière personnelle (vos données restent locales)

---

## 🛡️ Instructions par Antivirus

### 🟠 **Avast / AVG**

#### Si le fichier est mis en quarantaine :
1. Ouvrir **Avast** → **Protection** → **Quarantaine antivirus**
2. Trouver `lancer_gestiolittle.exe`
3. **Clic droit** → **Restaurer et ajouter une exception**
4. ✅ Terminé !

#### OU ajouter une exception AVANT le téléchargement :
1. **Avast** → **Paramètres** ⚙️ → **Protection** → **Agents principaux**
2. Cliquer sur **Exceptions**
3. **Ajouter une exception** → Sélectionner le dossier `Téléchargements`
4. Télécharger et lancer normalement

---

### 🟦 **Windows Defender**

#### Si Windows SmartScreen bloque :
1. Cliquer sur **"Informations complémentaires"**
2. Cliquer sur **"Exécuter quand même"**
3. ✅ L'application se lance !

#### OU ajouter une exception :
1. **Paramètres Windows** → **Mise à jour et sécurité** → **Sécurité Windows**
2. **Protection contre les virus et menaces** → **Gérer les paramètres**
3. Descendre à **Exclusions** → **Ajouter ou supprimer des exclusions**
4. **Ajouter une exclusion** → **Fichier** → Sélectionner `lancer_gestiolittle.exe`

---

### 🟩 **Kaspersky**

1. **Kaspersky** → **Paramètres** → **Menaces et exclusions**
2. **Gérer les exclusions** → **Ajouter**
3. Sélectionner le fichier `lancer_gestiolittle.exe`
4. ✅ Enregistrer

---

### 🟪 **Bitdefender**

1. **Bitdefender** → **Protection** → **Exclusions**
2. **Ajouter une exclusion**
3. Parcourir et sélectionner `lancer_gestiolittle.exe`
4. ✅ Appliquer

---

### 🟥 **Norton**

1. **Norton** → **Paramètres** → **Antivirus**
2. **Analyses et risques** → **Exclusions/Risques faibles**
3. **Configurer** → **Ajouter** → Sélectionner le fichier
4. ✅ OK

---

### 🔵 **McAfee**

1. **McAfee** → **Navigation PC** (ou **My Protection**)
2. **Analyse antivirus en temps réel** → **Fichiers exclus**
3. **Ajouter un fichier** → Sélectionner `lancer_gestiolittle.exe`
4. ✅ Enregistrer

---

## 🚀 Installation Simple

### Méthode Rapide (pour tous)

1. **Télécharger** le fichier `.exe`
2. **Double-cliquer** dessus
3. Si votre antivirus alerte :
   - C'est **normal** (faux positif)
   - Suivez les instructions ci-dessus pour votre antivirus
4. ✅ **L'application se lance !**

### Emplacement Recommandé

Créez un dossier dédié :
```
C:\Users\VotreNom\GestionFinanciere\
└── lancer_gestiolittle.exe
```

---

## 🐛 Tests et Retours

### Ce que j'aimerais que vous testiez :

#### ✅ Fonctionnalités
- [ ] L'application se lance correctement
- [ ] Toutes les fonctionnalités sont accessibles
- [ ] Les calculs sont corrects
- [ ] L'interface est intuitive

#### ✅ Ergonomie
- [ ] La navigation est fluide
- [ ] Les boutons sont clairs
- [ ] Le design est agréable
- [ ] Les couleurs sont lisibles

#### ✅ Bugs potentiels
- [ ] Plantages ou erreurs
- [ ] Comportements étranges
- [ ] Messages d'erreur incompréhensibles

### Comment me faire un retour ?

**Option 1 : Message direct**
- Envoyez-moi un message avec vos remarques

**Option 2 : Formulaire détaillé**
Remplissez ce petit questionnaire :

```
📋 RETOUR TEST - Gestion Financière Little

Nom/Pseudo : _______________
Date du test : _______________

1. Installation
   - Antivirus utilisé : _______________
   - Problème rencontré ? □ Oui □ Non
   - Si oui, lequel : _______________

2. Première impression (sur 5)
   - Interface : ⭐⭐⭐⭐⭐
   - Facilité d'utilisation : ⭐⭐⭐⭐⭐

3. Points positifs
   - ___________________________________
   - ___________________________________
   - ___________________________________

4. Points à améliorer
   - ___________________________________
   - ___________________________________
   - ___________________________________

5. Bugs rencontrés
   - ___________________________________
   - ___________________________________

6. Fonctionnalités manquantes
   - ___________________________________
   - ___________________________________

7. Note globale : ___ / 10

8. Commentaires libres :
   _______________________________________
   _______________________________________
```

---

## 🆘 Besoin d'Aide ?

### Problèmes d'installation
Contactez-moi avec :
- Capture d'écran de l'erreur
- Votre antivirus
- Version de Windows

### L'application ne se lance pas
Vérifiez :
- Windows 10/11 à jour
- Antivirus a bien l'exception
- Fichier téléchargé complètement

---

## 🙏 Merci !

Votre aide est précieuse pour améliorer cette application.

**Version testée :** v[NUMERO_VERSION]
**Date :** [DATE]

---

## 🔒 Vie Privée

Cette application :
- ✅ **NE collecte AUCUNE donnée**
- ✅ **Ne se connecte PAS à Internet**
- ✅ **Stocke tout localement sur votre PC**
- ✅ **Ne contient aucun tracking**

Vos données financières restent **100% privées** sur votre ordinateur.
