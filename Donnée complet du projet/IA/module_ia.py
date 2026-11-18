"""Module IA d'ANA-STAT.abt : assistant local, analyses automatiques et rapports.

Ce module fonctionne entièrement hors ligne. Il n'a besoin d'aucune clé API ni
connexion internet : l'assistant répond à partir d'une base de connaissances
locale et de calculs statistiques sur les données importées.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QGroupBox,
    QFileDialog, QMessageBox, QFrame, QScrollArea, QLineEdit,
    QTextEdit, QListWidget
)
import pandas as pd
import numpy as np
import unicodedata
import re
from datetime import datetime
from docx import Document

DOMAINES_LIES = ["Démographie", "Santé", "Éducation", "Économie", "Agriculture",
                  "Environnement", "Commerce", "Emploi et Social", "Sécurité", "SIG"]

# Base de connaissances locale pour l'assistant-guide (fonctionne sans internet).
BASE_CONNAISSANCES = {
    "taux de mortalité": "Le taux de mortalité se calcule ainsi : (Nombre de décès / Population totale) × 1000. "
                          "Il s'exprime en « décès pour 1000 habitants ». Tu le trouveras dans le module Démographie ou Santé.",
    "taux de natalité": "Le taux de natalité se calcule ainsi : (Nombre de naissances / Population totale) × 1000.",
    "taux de croissance": "Le taux de croissance se calcule ainsi : ((Population finale - Population initiale) "
                           "/ Population initiale) × 100. Disponible dans le module Démographie.",
    "rendement": "Le rendement agricole se calcule ainsi : Production / Superficie cultivée. "
                 "Disponible dans le module Agriculture.",
    "importer": "Pour importer des données : va dans l'onglet « Importation des données » ou clique sur "
                "« Excel / CSV » dans n'importe quel module sectoriel, puis choisis ton fichier.",
    "comment utiliser": "Chaque module sectoriel suit la même logique : 1) Importe tes données, "
                         "2) Coche les analyses qui t'intéressent dans le Menu d'analyse, "
                         "3) Clique sur « Lancer l'analyse », 4) Consulte les résultats et exporte-les si besoin.",
    "graphique": "Pour des comparaisons entre catégories (pays, régions...), utilise un histogramme (barres). "
                 "Pour une évolution dans le temps, utilise une courbe. Pour une répartition en pourcentage, "
                 "utilise un diagramme circulaire.",
    "moyenne": "La moyenne est la somme des valeurs divisée par leur nombre. Sensible aux valeurs extrêmes ; "
               "complète-la avec la médiane.",
    "médiane": "La médiane est la valeur centrale d'une série triée. Elle résiste mieux aux valeurs extrêmes que la moyenne.",
    "écart-type": "L'écart-type mesure la dispersion des valeurs autour de la moyenne. Plus il est grand, plus les "
                  "valeurs sont dispersées.",
    "variance": "La variance est le carré de l'écart-type ; elle mesure aussi la dispersion.",
    "corrélation": "La corrélation mesure le lien linéaire entre deux variables numériques (entre -1 et 1). "
                   "Au-dessus de 0,7 en valeur absolue, le lien est fort.",
    "outlier": "Une valeur atypique (outlier) s'écarte fortement du reste des données. L'assistant les détecte par la "
               "méthode IQR (écart interquartile).",
    "valeur manquante": "Une valeur manquante (NaN) est une donnée absente. L'assistant ne les invente pas ; il les "
                        "signale pour que tu décides (suppression, imputation, etc.).",
    "doublon": "Un doublon est une ligne identique à une autre. L'assistant peut les supprimer automatiquement.",
    "type de données": "Les colonnes peuvent être numériques, textuelles ou dates. L'assistant détecte ces types "
                       "automatiquement pour choisir les bonnes analyses.",
    "normalisation": "La normalisation ramène des variables sur une même échelle (ex. 0-1). Utile avant certaines "
                     "analyses comparatives.",
    "test de student": "Le test de Student compare les moyennes de deux groupes. Disponible dans les modules sectoriels "
                       "si les colonnes requises sont présentes.",
    "anova": "L'ANOVA compare les moyennes de plusieurs groupes. Disponible dans les modules sectoriels concernés.",
    "régression": "La régression linéaire modélise la relation entre une variable cible et une ou plusieurs variables "
                  "explicatives. Voir le module Analyse.",
    "courbe de lorenz": "La courbe de Lorenz visualise l'inégalité d'une distribution (revenus, population...). "
                        "Disponible dans le module Analyse.",
    "coefficient de gini": "Le coefficient de Gini mesure l'inégalité (0 = égalité parfaite, 1 = inégalité totale).",
    "population": "La population est l'ensemble complet des individus étudiés. Un échantillon en est un sous-ensemble.",
    "échantillon": "Un échantillon est un sous-ensemble de la population, utilisé pour estimer des caractéristiques "
                   "de la population.",
    "modalité": "Une modalité est une valeur possible d'une variable qualitative (ex. « masculin », « féminin »).",
    "fréquence": "La fréquence d'une modalité est le nombre (ou le pourcentage) d'observations qui la prennent.",
    "pourcentage": "Un pourcentage exprime une part sur 100. L'assistant calcule automatiquement les pourcentages dans "
                   "les tableaux de fréquences.",
    "tableau croisé": "Un tableau croisé (contingence) croise deux variables qualitatives pour voir leurs liens.",
    "pivot": "Un tableau pivot regroupe et agrège des données selon des lignes et des colonnes choisies.",
    "jointure": "Une jointure combine deux tables selon une clé commune (ex. code région). Disponible dans Édition des données.",
    "fusion": "La fusion (concaténation) empile plusieurs fichiers de même structure. Disponible dans Édition des données.",
    "export": "Pour exporter : utilise les boutons « Exporter » dans chaque module (CSV, Excel, Word, PDF).",
    "carte": "Pour afficher une carte : module SIG, avec des colonnes latitude/longitude ou un découpage administratif.",
    "prévision": "La prévision projette une valeur future à partir d'une tendance observée, avec une fourchette "
                 "d'incertitude. Utilise le bouton « Prévoir ».",
    "incertitude": "L'incertitude est la fourchette basse/haute autour d'une projection, basée sur la dispersion "
                   "observée.",
    "rapport word": "Le bouton « Générer un rapport » crée un document Word structuré (9 sections) à partir des données.",
    "thème": "Le thème (clair/sombre) se change via le bouton ⚙️ dans la barre supérieure.",
    "navigation": "Le menu latéral ouvre les modules. Les onglets se ferment comme dans un navigateur.",
    "sig": "Le module SIG affiche une carte choroplèthe du Mali (régions, cercles, communes) avec recherche et export.",
    "créateur": "Cette plateforme a été créée par ABT.",
    "créé par": "Cette plateforme a été créée par ABT.",
    "auteur": "Cette plateforme a été créée par ABT.",
    "développeur": "Cette plateforme a été créée par ABT.",
    "qui a créé": "Cette plateforme a été créée par ABT.",
    "qui a fait": "Cette plateforme a été créée par ABT.",
}


# ---------- OUTILS TEXTE ----------

def _normaliser_texte(texte):
    """Minuscule, sans accents ni ponctuation, pour une recherche tolérante."""
    if texte is None:
        return ""
    texte = unicodedata.normalize("NFKD", str(texte)).encode("ascii", "ignore").decode("ascii")
    texte = texte.lower()
    texte = re.sub(r"[^a-z0-9\s]", " ", texte)
    return re.sub(r"\s+", " ", texte).strip()


def _score_mot_cle(mot_cle_normalise, question_normalisee):
    """Score de pertinence d'un mot-clé par rapport à la question."""
    if mot_cle_normalise and mot_cle_normalise in question_normalisee:
        return 100 + len(mot_cle_normalise)
    mots_cle = set(mot_cle_normalise.split())
    mots_question = set(question_normalisee.split())
    communs = mots_cle & mots_question
    if not communs:
        return 0
    return len(communs) * 10 + int(10 * len(communs) / max(1, len(mots_cle)))


# ---------- FONCTIONS D'ANALYSE AUTOMATIQUE ----------

def analyser_donnees_automatiquement(donnees):
    """Vérifie les données, détecte les problèmes courants et résume l'état général."""
    if donnees is None or (hasattr(donnees, "empty") and donnees.empty):
        return "Aucune donnée importée pour le moment."

    lignes, colonnes = donnees.shape
    valeurs_manquantes = int(donnees.isnull().sum().sum())
    doublons = int(donnees.duplicated().sum())
    colonnes_numeriques = list(donnees.select_dtypes(include="number").columns)
    colonnes_texte = list(donnees.select_dtypes(include=["object", "category", "string"]).columns)
    colonnes_date = list(donnees.select_dtypes(include=["datetime", "datetimetz"]).columns)

    texte = "Analyse automatique :\n"
    texte += f"- {lignes} lignes, {colonnes} colonnes\n"
    texte += f"- {valeurs_manquantes} valeurs manquantes au total\n"
    texte += f"- {doublons} lignes en double\n"
    texte += f"- {len(colonnes_numeriques)} colonnes numériques, {len(colonnes_texte)} textuelles"
    if colonnes_date:
        texte += f", {len(colonnes_date)} de dates"
    texte += "\n"

    # Colonnes constantes
    constantes = [c for c in donnees.columns if donnees[c].nunique(dropna=False) <= 1]
    if constantes:
        texte += f"- Colonnes constantes (peu utiles) : {', '.join(constantes)}\n"

    # Colonnes textuelles à forte cardinalité
    haute_card = [c for c in colonnes_texte if donnees[c].nunique(dropna=True) > max(50, lignes * 0.5)]
    if haute_card:
        texte += f"- Colonnes textuelles à forte cardinalité : {', '.join(haute_card)}\n"

    # Valeurs manquantes par colonne (top 5)
    manquants_par_col = donnees.isnull().sum()
    manquants_par_col = manquants_par_col[manquants_par_col > 0].sort_values(ascending=False)
    if not manquants_par_col.empty:
        texte += "\nValeurs manquantes par colonne (top 5) :\n"
        for col, n in manquants_par_col.head(5).items():
            pct = round(100 * n / max(1, lignes), 1)
            texte += f"  - {col} : {int(n)} ({pct} %)\n"

    # Valeurs atypiques (IQR)
    outliers = {}
    for col in colonnes_numeriques:
        serie = donnees[col].dropna()
        if serie.empty:
            continue
        q1 = serie.quantile(0.25)
        q3 = serie.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        bas = q1 - 1.5 * iqr
        haut = q3 + 1.5 * iqr
        n_out = int(((donnees[col] < bas) | (donnees[col] > haut)).sum())
        if n_out:
            outliers[col] = n_out
    if outliers:
        texte += "\nValeurs atypiques (méthode IQR) :\n"
        for col, n in list(outliers.items())[:5]:
            texte += f"  - {col} : {n}\n"

    # Corrélations les plus fortes
    if len(colonnes_numeriques) >= 2:
        try:
            corr = donnees[colonnes_numeriques].corr().abs()
            paires = []
            for i in range(len(colonnes_numeriques)):
                for j in range(i + 1, len(colonnes_numeriques)):
                    paires.append((float(corr.iloc[i, j]), colonnes_numeriques[i], colonnes_numeriques[j]))
            paires.sort(reverse=True)
            fortes = [p for p in paires if p[0] >= 0.5][:3]
            if fortes:
                texte += "\nCorrélations les plus fortes :\n"
                for v, a, b in fortes:
                    texte += f"  - {a} ↔ {b} : {v:.2f}\n"
        except Exception:
            pass

    if colonnes_numeriques:
        texte += "\nAperçu statistique des colonnes numériques :\n"
        resume = donnees[colonnes_numeriques].describe().round(2)
        texte += resume.to_string()

    return texte


def nettoyer_donnees(donnees):
    """Supprime les doublons et signale les valeurs manquantes, sans les inventer."""
    if donnees is None or (hasattr(donnees, "empty") and donnees.empty):
        return None, "Aucune donnée à nettoyer."

    nb_avant = donnees.shape[0]
    donnees_nettoyees = donnees.drop_duplicates().copy()
    nb_apres = donnees_nettoyees.shape[0]
    valeurs_manquantes = donnees_nettoyees.isnull().sum()
    colonnes_avec_manquants = valeurs_manquantes[valeurs_manquantes > 0]

    texte = f"Nettoyage effectué :\n- {nb_avant - nb_apres} doublons supprimés\n"
    if not colonnes_avec_manquants.empty:
        texte += "- Valeurs manquantes restantes (non inventées, à traiter manuellement) :\n"
        texte += colonnes_avec_manquants.to_string()
    else:
        texte += "- Aucune valeur manquante restante."

    return donnees_nettoyees, texte


def imputer_donnees(donnees, methode="mediane"):
    """Impute les valeurs manquantes (numériques par médiane/moyenne, textuelles par mode).

    Retourne (données imputées, rapport). Ne modifie pas les données d'origine.
    """
    if donnees is None or (hasattr(donnees, "empty") and donnees.empty):
        return None, "Aucune donnée à imputer."

    resultat = donnees.copy()
    rapport = []
    nb_total = 0

    for col in resultat.columns:
        manquants = int(resultat[col].isnull().sum())
        if manquants == 0:
            continue
        if pd.api.types.is_numeric_dtype(resultat[col]):
            if methode == "moyenne":
                valeur = resultat[col].mean()
            else:
                valeur = resultat[col].median()
            resultat[col] = resultat[col].fillna(valeur)
            rapport.append(f"- {col} : {manquants} valeur(s) remplacée(s) par {methode} ({valeur:.4g})")
        else:
            mode = resultat[col].mode()
            if not mode.empty:
                valeur = mode.iloc[0]
                resultat[col] = resultat[col].fillna(valeur)
                rapport.append(f"- {col} : {manquants} valeur(s) remplacée(s) par le mode ({valeur})")
            else:
                rapport.append(f"- {col} : {manquants} valeur(s) manquante(s), aucune imputation possible")
        nb_total += manquants

    if not rapport:
        rapport.append("- Aucune valeur manquante à imputer.")
    else:
        rapport.insert(0, f"Imputation ({methode}) : {nb_total} valeur(s) au total.")
    return resultat, "\n".join(rapport)


def detecter_problemes(donnees):
    """Renvoie une liste de problèmes détectés dans les données."""
    if donnees is None or (hasattr(donnees, "empty") and donnees.empty):
        return ["Aucune donnée importée."]

    problemes = []
    lignes, colonnes = donnees.shape
    if donnees.isnull().sum().sum() > 0:
        problemes.append(f"{int(donnees.isnull().sum().sum())} valeur(s) manquante(s) au total.")
    if donnees.duplicated().sum() > 0:
        problemes.append(f"{int(donnees.duplicated().sum())} ligne(s) en double.")
    constantes = [c for c in donnees.columns if donnees[c].nunique(dropna=False) <= 1]
    if constantes:
        problemes.append(f"Colonne(s) constante(s) : {', '.join(constantes)}.")
    if not list(donnees.select_dtypes(include="number").columns):
        problemes.append("Aucune colonne numérique : les analyses statistiques seront limitées.")
    if lignes < 5:
        problemes.append("Très peu de lignes : les résultats peuvent être peu fiables.")
    if not problemes:
        problemes.append("Aucun problème majeur détecté.")
    return problemes


def calculer_prevision_avec_incertitude(donnees, colonne_categorie, colonne_debut, colonne_fin,
                                          annees_ecart, annees_projection=1):
    """Projette une valeur future et calcule une fourchette d'incertitude basée sur la dispersion observée."""
    if donnees is None or (hasattr(donnees, "empty") and donnees.empty):
        return None

    colonnes_requises = [colonne_categorie, colonne_debut, colonne_fin]
    if not all(c in donnees.columns for c in colonnes_requises):
        return None

    sous_ensemble = donnees[colonnes_requises].copy().dropna()
    sous_ensemble = sous_ensemble[sous_ensemble[colonne_debut] > 0]
    if sous_ensemble.empty:
        return None

    taux_annuel = (sous_ensemble[colonne_fin] / sous_ensemble[colonne_debut]) ** (1 / max(1, annees_ecart)) - 1
    projection = sous_ensemble[colonne_fin] * (1 + taux_annuel) ** annees_projection

    ecart_type_taux = taux_annuel.std() if len(taux_annuel) > 1 else abs(taux_annuel.mean()) * 0.2
    projection_basse = sous_ensemble[colonne_fin] * (1 + taux_annuel - ecart_type_taux) ** annees_projection
    projection_haute = sous_ensemble[colonne_fin] * (1 + taux_annuel + ecart_type_taux) ** annees_projection

    resultat = pd.DataFrame({
        colonne_categorie: sous_ensemble[colonne_categorie].values,
        "Estimation basse": projection_basse.values,
        f"Projection (+{annees_projection})": projection.values,
        "Estimation haute": projection_haute.values,
    })
    return resultat.sort_values(by=f"Projection (+{annees_projection})", ascending=False).reset_index(drop=True)


def repondre_assistant_guide(question, donnees=None):
    """Cherche une réponse dans la base de connaissances locale à partir de mots-clés.

    Si des données sont fournies et que la question le demande, ajoute un aperçu
    automatique des données.
    """
    question_norm = _normaliser_texte(question)

    # Score de chaque mot-clé
    scores = [(mot_cle, _score_mot_cle(_normaliser_texte(mot_cle), question_norm)) for mot_cle in BASE_CONNAISSANCES]
    scores.sort(key=lambda x: x[1], reverse=True)

    meilleur_mot, meilleur_score = scores[0] if scores else (None, 0)

    # Domaines liés
    domaine_trouve = None
    for domaine in DOMAINES_LIES:
        if _normaliser_texte(domaine) in question_norm:
            domaine_trouve = domaine
            break

    if meilleur_score >= 20:
        reponse = BASE_CONNAISSANCES[meilleur_mot]
    elif domaine_trouve is not None:
        reponse = (f"Pour analyser tes données de {domaine_trouve} : ouvre le module {domaine_trouve} dans le menu "
                   f"latéral, importe ton fichier, coche les analyses voulues dans le Menu d'analyse, "
                   f"puis clique sur « Lancer l'analyse ».")
        meilleur_score = 50
    else:
        suggestions = [m for m, s in scores[:3] if s > 0]
        if not suggestions:
            suggestions = list(BASE_CONNAISSANCES.keys())[:3]
        reponse = ("Je n'ai pas de réponse locale toute prête pour cette question. "
                   "Sans connexion à une IA en ligne, je peux seulement répondre à partir de ma base de "
                   "connaissances (formules statistiques, guide d'utilisation des modules). "
                   "Essaie de reformuler avec des mots-clés comme : " + ", ".join(suggestions) + ".")

    # Aperçu des données si pertinent
    demande_donnees = any(m in question_norm for m in ["mes donnees", "mon fichier", "analyse", "resume", "apercu", "donnees"])
    if donnees is not None and demande_donnees:
        try:
            reponse += "\n\n--- Aperçu de tes données ---\n" + analyser_donnees_automatiquement(donnees)
        except Exception:
            pass

    return reponse


def generer_rapport_word(donnees, domaine, chemin_fichier):
    """Génère un rapport Word structuré selon les 9 sections prévues, à partir des données actuelles."""
    document = Document()

    document.add_heading("Rapport d'analyse automatique", level=0)
    document.add_paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} par l'Assistant IA de ANA-STAT.abt.")

    document.add_heading("Introduction", level=1)
    document.add_paragraph(
        "Ce rapport présente une analyse automatique des données importées dans le logiciel ANA-STAT.abt. "
        "Il a été généré par l'Assistant IA local, sans connexion à un service en ligne."
    )

    document.add_heading("Source des données", level=1)
    if donnees is not None:
        document.add_paragraph(
            f"Le jeu de données contient {donnees.shape[0]} lignes et {donnees.shape[1]} colonnes. "
            f"Domaine détecté automatiquement : {domaine if domaine else 'non déterminé'}."
        )
    else:
        document.add_paragraph("Aucune donnée n'était disponible au moment de la génération de ce rapport.")

    document.add_heading("Méthodologie", level=1)
    document.add_paragraph(
        "Les statistiques descriptives ont été calculées directement sur l'ensemble des données importées "
        "(moyenne, médiane, écart-type, minimum, maximum pour les colonnes numériques). "
        "Les valeurs manquantes et les doublons ont été signalés sans être inventés."
    )

    document.add_heading("Résultats", level=1)
    if donnees is not None:
        colonnes_numeriques = list(donnees.select_dtypes(include="number").columns)
        if colonnes_numeriques:
            resume = donnees[colonnes_numeriques].describe().round(2)
            table = document.add_table(rows=1, cols=len(resume.columns) + 1)
            table.style = "Light Grid Accent 1"
            cellules_entete = table.rows[0].cells
            cellules_entete[0].text = "Statistique"
            for i, colonne in enumerate(resume.columns):
                cellules_entete[i + 1].text = str(colonne)
            for index_ligne in resume.index:
                ligne = table.add_row().cells
                ligne[0].text = str(index_ligne)
                for i, colonne in enumerate(resume.columns):
                    ligne[i + 1].text = str(resume.loc[index_ligne, colonne])
        else:
            document.add_paragraph("Aucune colonne numérique disponible pour générer un tableau de résultats.")
    else:
        document.add_paragraph("Aucun résultat disponible.")

    # Valeurs manquantes et doublons
    document.add_heading("Qualité des données", level=1)
    if donnees is not None:
        vm = int(donnees.isnull().sum().sum())
        dd = int(donnees.duplicated().sum())
        document.add_paragraph(f"- Valeurs manquantes : {vm}")
        document.add_paragraph(f"- Lignes en double : {dd}")
        manquants = donnees.isnull().sum()
        manquants = manquants[manquants > 0].sort_values(ascending=False)
        if not manquants.empty:
            document.add_paragraph("Colonnes avec valeurs manquantes :")
            for col, n in manquants.head(10).items():
                document.add_paragraph(f"  - {col} : {int(n)}", style="List Bullet")
    else:
        document.add_paragraph("Aucune donnée disponible.")

    # Corrélations
    document.add_heading("Corrélations", level=1)
    if donnees is not None:
        colonnes_numeriques = list(donnees.select_dtypes(include="number").columns)
        if len(colonnes_numeriques) >= 2:
            try:
                corr = donnees[colonnes_numeriques].corr().abs()
                paires = []
                for i in range(len(colonnes_numeriques)):
                    for j in range(i + 1, len(colonnes_numeriques)):
                        paires.append((float(corr.iloc[i, j]), colonnes_numeriques[i], colonnes_numeriques[j]))
                paires.sort(reverse=True)
                fortes = [p for p in paires if p[0] >= 0.5][:5]
                if fortes:
                    for v, a, b in fortes:
                        document.add_paragraph(f"- {a} ↔ {b} : {v:.2f}", style="List Bullet")
                else:
                    document.add_paragraph("Aucune corrélation forte détectée (seuil 0,5).")
            except Exception:
                document.add_paragraph("Calcul des corrélations impossible.")
        else:
            document.add_paragraph("Pas assez de colonnes numériques.")
    else:
        document.add_paragraph("Aucune donnée disponible.")

    document.add_heading("Graphiques", level=1)
    document.add_paragraph(
        "Les graphiques générés dans l'application ne sont pas encore intégrés automatiquement à ce rapport. "
        "Fonctionnalité à venir : capture et insertion automatique des graphiques."
    )

    document.add_heading("Analyse", level=1)
    document.add_paragraph(
        "Cette section nécessite une interprétation experte des résultats ci-dessus. "
        "L'Assistant IA local ne rédige pas encore d'analyse qualitative automatique ; "
        "cette fonctionnalité nécessite une connexion à une IA en ligne."
    )

    document.add_heading("Tendances", level=1)
    document.add_paragraph(
        "Pour une analyse de tendance détaillée, utilise la fonction « Prévoir » de l'Assistant IA, "
        "qui fournit une estimation avec une fourchette d'incertitude basée sur les données historiques."
    )

    document.add_heading("Limites", level=1)
    document.add_paragraph(
        "Ce rapport est généré automatiquement à partir des données brutes fournies. Il ne remplace pas "
        "une analyse experte. Les projections sont des estimations statistiques et non des certitudes. "
        "La qualité des résultats dépend entièrement de la qualité des données importées."
    )

    document.add_heading("Recommandations", level=1)
    if donnees is not None:
        problemes = detecter_problemes(donnees)
        for p in problemes:
            document.add_paragraph(f"- {p}", style="List Bullet")
    else:
        document.add_paragraph("- Importe des données pour obtenir des recommandations.")

    document.add_heading("Conclusion", level=1)
    document.add_paragraph(
        "Ce document a été généré automatiquement par le module IA local de ANA-STAT.abt. "
        "Pour une analyse plus poussée, utilise les modules sectoriels correspondants."
    )

    document.save(chemin_fichier)


# ---------- SECTIONS DE L'INTERFACE ----------

def creer_entete():
    entete = QLabel("Accueil > Intelligence Artificielle")
    entete.setStyleSheet("color: gray; font-size: 11px;")
    return entete


def creer_section_connexion():
    groupe = QGroupBox("Connexion")
    layout = QVBoxLayout()

    layout.addWidget(QLabel("🔴 Hors ligne — mode local uniquement"))
    layout.addWidget(QLabel("🤖 IA locale disponible (base de connaissances, formules, guide)"))
    layout.addWidget(QLabel("📚 Aucune synchronisation en ligne configurée"))

    note = QLabel("L'IA en ligne (compréhension du langage libre, analyses expertes) nécessite une clé API "
                  "et une connexion internet. Non configurée pour l'instant.")
    note.setStyleSheet("color: gray; font-size: 10px;")
    note.setWordWrap(True)
    layout.addWidget(note)

    groupe.setLayout(layout)
    return groupe


def creer_zone_assistant(obtenir_donnees_actuelles, obtenir_domaine_actuel, ajouter_historique):
    groupe = QGroupBox("🤖 Assistant IA")
    layout = QVBoxLayout()

    zone_conversation = QTextEdit()
    zone_conversation.setReadOnly(True)
    zone_conversation.setMinimumHeight(220)
    zone_conversation.append("Assistant : Bonjour ! Comment puis-je vous aider ?")

    layout_saisie = QHBoxLayout()
    champ_question = QLineEdit()
    champ_question.setPlaceholderText("Écrivez votre question ici...")
    bouton_envoyer = QPushButton("Envoyer")
    bouton_copier = QPushButton("Copier")
    bouton_effacer = QPushButton("Effacer")
    layout_saisie.addWidget(champ_question)
    layout_saisie.addWidget(bouton_envoyer)
    layout_saisie.addWidget(bouton_copier)
    layout_saisie.addWidget(bouton_effacer)

    def gerer_envoi():
        question = champ_question.text().strip()
        if not question:
            return
        zone_conversation.append(f"\nVous : {question}")
        try:
            reponse = repondre_assistant_guide(question, obtenir_donnees_actuelles())
        except Exception as erreur:
            reponse = f"Une erreur est survenue : {erreur}"
        zone_conversation.append(f"Assistant : {reponse}")
        ajouter_historique(f"Question : {question[:50]}")
        champ_question.clear()

    def gerer_copie():
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(zone_conversation.toPlainText())

    def gerer_effacer():
        zone_conversation.clear()
        zone_conversation.append("Assistant : Conversation effacée.")

    bouton_envoyer.clicked.connect(gerer_envoi)
    bouton_copier.clicked.connect(gerer_copie)
    bouton_effacer.clicked.connect(gerer_effacer)
    champ_question.returnPressed.connect(gerer_envoi)

    layout.addWidget(zone_conversation)
    layout.addLayout(layout_saisie)

    label_exemples = QLabel(
        "Exemples : « Comment calculer le taux de mortalité ? » • « Analyse mes données d'éducation. » • "
        "« Quel graphique dois-je utiliser ? » • « Détecte les problèmes de mes données. »"
    )
    label_exemples.setStyleSheet("color: gray; font-size: 10px;")
    label_exemples.setWordWrap(True)
    layout.addWidget(label_exemples)

    groupe.setLayout(layout)
    return groupe, zone_conversation


def creer_section_domaines(gerer_navigation):
    groupe = QGroupBox("Domaines disponibles")
    layout = QHBoxLayout()

    for domaine in DOMAINES_LIES:
        bouton = QPushButton(domaine)
        bouton.clicked.connect(lambda checked, d=domaine: gerer_navigation(d))
        layout.addWidget(bouton)

    groupe.setLayout(layout)
    return groupe


def creer_section_fonctions_ia(obtenir_donnees_actuelles, obtenir_domaine_actuel,
                                 zone_conversation, ajouter_historique):
    groupe = QGroupBox("Fonctions IA")
    layout = QGridLayout()

    def gerer_analyser():
        donnees = obtenir_donnees_actuelles()
        try:
            resultat = analyser_donnees_automatiquement(donnees)
        except Exception as erreur:
            resultat = f"Erreur lors de l'analyse : {erreur}"
        zone_conversation.append(f"\nAssistant : {resultat}")
        ajouter_historique("Analyse automatique des données")

    def gerer_nettoyer():
        donnees = obtenir_donnees_actuelles()
        try:
            _, resultat = nettoyer_donnees(donnees)
        except Exception as erreur:
            resultat = f"Erreur lors du nettoyage : {erreur}"
        zone_conversation.append(f"\nAssistant : {resultat}")
        ajouter_historique("Nettoyage des données")

    def gerer_imputer():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            zone_conversation.append("\nAssistant : Importe d'abord des données.")
            return
        try:
            _, resultat = imputer_donnees(donnees, methode="mediane")
        except Exception as erreur:
            resultat = f"Erreur lors de l'imputation : {erreur}"
        zone_conversation.append(f"\nAssistant : {resultat}")
        ajouter_historique("Imputation des valeurs manquantes")

    def gerer_detecter():
        donnees = obtenir_donnees_actuelles()
        try:
            problemes = detecter_problemes(donnees)
        except Exception as erreur:
            problemes = [f"Erreur : {erreur}"]
        zone_conversation.append("\nAssistant : Problèmes détectés :\n" + "\n".join(f"- {p}" for p in problemes))
        ajouter_historique("Détection de problèmes")

    def gerer_prevoir():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            QMessageBox.warning(None, "Erreur", "Importe d'abord des données.")
            return
        colonnes_num = list(donnees.select_dtypes(include="number").columns)
        colonnes_texte = list(donnees.select_dtypes(include=["object", "category", "string"]).columns)
        if len(colonnes_num) < 2 or not colonnes_texte:
            zone_conversation.append(
                "\nAssistant : Impossible de faire une prévision — il faut au moins 2 colonnes numériques "
                "(par exemple 2 années différentes) et une colonne catégorielle (ex. pays, région)."
            )
            return
        try:
            resultat = calculer_prevision_avec_incertitude(
                donnees, colonnes_texte[0], colonnes_num[-1], colonnes_num[0], annees_ecart=1
            )
        except Exception as erreur:
            zone_conversation.append(f"\nAssistant : Erreur lors de la prévision : {erreur}")
            return
        if resultat is None or resultat.empty:
            zone_conversation.append("\nAssistant : Impossible de calculer une prévision avec ces données.")
            return
        zone_conversation.append(
            "\nAssistant : Voici une estimation basée sur la tendance observée. "
            "⚠️ Ceci est une projection statistique, pas une certitude — regarde la fourchette basse/haute.\n"
            + resultat.head(10).to_string(index=False)
        )
        ajouter_historique("Prévision avec incertitude")

    def gerer_rapport():
        donnees = obtenir_donnees_actuelles()
        domaine = obtenir_domaine_actuel()
        chemin, _ = QFileDialog.getSaveFileName(None, "Enregistrer le rapport", "rapport.docx",
                                                  "Documents Word (*.docx)")
        if chemin:
            try:
                generer_rapport_word(donnees, domaine, chemin)
                QMessageBox.information(None, "Rapport généré", f"Rapport enregistré : {chemin}")
                ajouter_historique(f"Rapport généré : {chemin.split('/')[-1]}")
            except Exception as erreur:
                QMessageBox.critical(None, "Erreur", f"Impossible de générer le rapport :\n{erreur}")

    def gerer_expliquer():
        zone_conversation.append(
            "\nAssistant : Sans connexion à une IA en ligne, je ne peux pas interpréter un résultat "
            "en langage libre. Utilise plutôt la base de connaissances (tape une formule ou un mot-clé) "
            "ou consulte les info-bulles dans chaque module."
        )
        ajouter_historique("Demande d'explication")

    def gerer_analyser_carte():
        zone_conversation.append(
            "\nAssistant : Pour analyser une carte, va dans le module SIG. La carte fonctionne si ton fichier "
            "contient des colonnes latitude/longitude."
        )
        ajouter_historique("Demande d'analyse de carte")

    boutons = [
        ("📊 Analyser les données", gerer_analyser),
        ("📈 Prévoir", gerer_prevoir),
        ("🧹 Nettoyer les données", gerer_nettoyer),
        ("🩹 Imputer les manquants", gerer_imputer),
        ("🔍 Détecter les problèmes", gerer_detecter),
        ("📄 Générer un rapport", gerer_rapport),
        ("💡 Expliquer", gerer_expliquer),
        ("🗺️ Analyser une carte", gerer_analyser_carte),
    ]

    for i, (texte, fonction) in enumerate(boutons):
        bouton = QPushButton(texte)
        bouton.clicked.connect(fonction)
        layout.addWidget(bouton, i // 2, i % 2)

    groupe.setLayout(layout)
    return groupe


def creer_section_historique():
    groupe = QGroupBox("Historique")
    layout = QVBoxLayout()

    liste = QListWidget()
    liste.addItem("Aucune action pour le moment dans cette session.")
    layout.addWidget(liste)

    bouton_effacer = QPushButton("Effacer l'historique")
    bouton_effacer.clicked.connect(lambda: (liste.clear(), liste.addItem("Historique effacé.")))
    layout.addWidget(bouton_effacer)

    groupe.setLayout(layout)
    return groupe, liste


# ---------- PAGE COMPLÈTE ----------

def creer_page_module_ia(obtenir_donnees_actuelles, obtenir_domaine_actuel, gerer_navigation):
    """Assemble la page Module IA selon le schéma professionnel, en mode local (hors ligne)."""
    page = QWidget()
    layout_principal = QVBoxLayout()
    layout_principal.setSpacing(15)
    layout_principal.setContentsMargins(15, 15, 15, 15)

    section_historique, liste_historique = creer_section_historique()
    premier_element_historique = {"deja_efface": False}

    def ajouter_historique(texte):
        if not premier_element_historique["deja_efface"]:
            liste_historique.clear()
            premier_element_historique["deja_efface"] = True
        horodatage = datetime.now().strftime("%H:%M")
        liste_historique.insertItem(0, f"[{horodatage}] {texte}")

    section_connexion = creer_section_connexion()
    zone_assistant, zone_conversation = creer_zone_assistant(
        obtenir_donnees_actuelles, obtenir_domaine_actuel, ajouter_historique)
    section_domaines = creer_section_domaines(gerer_navigation)
    section_fonctions = creer_section_fonctions_ia(
        obtenir_donnees_actuelles, obtenir_domaine_actuel, zone_conversation, ajouter_historique)

    layout_principal.addWidget(creer_entete())
    layout_principal.addWidget(section_connexion)
    layout_principal.addWidget(zone_assistant)
    layout_principal.addWidget(section_domaines)
    layout_principal.addWidget(section_fonctions)
    layout_principal.addWidget(section_historique)

    page.setLayout(layout_principal)

    zone_defilement = QScrollArea()
    zone_defilement.setWidgetResizable(True)
    zone_defilement.setWidget(page)
    return zone_defilement
