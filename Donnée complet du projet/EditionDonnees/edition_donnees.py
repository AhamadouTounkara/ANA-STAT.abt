"""Opérations d'édition des données, façon Excel : variables, observations, filtres, tri, fusion, jointure, agrégation."""
import pandas as pd
from PyQt6.QtWidgets import (
    QInputDialog, QMessageBox, QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QFileDialog, QListWidget, QAbstractItemView, QDialogButtonBox
)


# ---------- VARIABLES ----------

def ajouter_variable(donnees, parent=None):
    """Ajoute une nouvelle variable (colonne) vide."""
    if donnees is None:
        QMessageBox.warning(parent, "Erreur", "Importe d'abord des données.")
        return donnees
    nom, ok = QInputDialog.getText(parent, "Ajouter une variable", "Nom de la nouvelle variable :")
    if not ok or not nom.strip():
        return donnees
    if nom in donnees.columns:
        QMessageBox.warning(parent, "Erreur", "Cette variable existe déjà.")
        return donnees
    donnees[nom] = None
    return donnees


def supprimer_variable(donnees, parent=None):
    """Supprime une variable (colonne) choisie par l'utilisateur."""
    if donnees is None:
        QMessageBox.warning(parent, "Erreur", "Importe d'abord des données.")
        return donnees
    colonne, ok = QInputDialog.getItem(parent, "Supprimer une variable", "Colonne à supprimer :",
                                        list(donnees.columns), 0, False)
    if not ok:
        return donnees
    return donnees.drop(columns=[colonne])


def renommer_variable(donnees, parent=None):
    """Renomme une variable (colonne)."""
    if donnees is None:
        QMessageBox.warning(parent, "Erreur", "Importe d'abord des données.")
        return donnees
    colonne, ok = QInputDialog.getItem(parent, "Renommer une variable", "Colonne à renommer :",
                                        list(donnees.columns), 0, False)
    if not ok:
        return donnees
    nouveau_nom, ok2 = QInputDialog.getText(parent, "Renommer une variable", f"Nouveau nom pour '{colonne}' :")
    if not ok2 or not nouveau_nom.strip():
        return donnees
    return donnees.rename(columns={colonne: nouveau_nom})


def convertir_type(donnees, parent=None):
    """Convertit une variable en nombre, texte ou date."""
    if donnees is None:
        QMessageBox.warning(parent, "Erreur", "Importe d'abord des données.")
        return donnees
    colonne, ok = QInputDialog.getItem(parent, "Convertir le type", "Colonne à convertir :",
                                        list(donnees.columns), 0, False)
    if not ok:
        return donnees
    type_cible, ok2 = QInputDialog.getItem(parent, "Convertir le type", "Nouveau type :",
                                            ["Nombre", "Texte", "Date"], 0, False)
    if not ok2:
        return donnees
    try:
        if type_cible == "Nombre":
            donnees[colonne] = pd.to_numeric(donnees[colonne], errors="coerce")
        elif type_cible == "Texte":
            donnees[colonne] = donnees[colonne].astype(str)
        elif type_cible == "Date":
            donnees[colonne] = pd.to_datetime(donnees[colonne], errors="coerce")
    except Exception as erreur:
        QMessageBox.critical(parent, "Erreur", f"Conversion impossible :\n{erreur}")
    return donnees


def recoder_variable(donnees, parent=None):
    """Recode les valeurs d'une variable selon une liste de correspondances ancienne=nouvelle."""
    if donnees is None:
        QMessageBox.warning(parent, "Erreur", "Importe d'abord des données.")
        return donnees
    colonne, ok = QInputDialog.getItem(parent, "Recoder une variable", "Colonne à recoder :",
                                        list(donnees.columns), 0, False)
    if not ok:
        return donnees
    texte, ok2 = QInputDialog.getMultiLineText(
        parent, "Recoder une variable",
        "Une correspondance par ligne, au format : ancienne_valeur=nouvelle_valeur\n"
        "Exemple :\nM=Masculin\nF=Féminin"
    )
    if not ok2 or not texte.strip():
        return donnees
    correspondances = {}
    for ligne in texte.strip().split("\n"):
        if "=" in ligne:
            ancienne, nouvelle = ligne.split("=", 1)
            correspondances[ancienne.strip()] = nouvelle.strip()
    donnees[colonne] = donnees[colonne].astype(str).replace(correspondances)
    return donnees


def creer_variable_calculee(donnees, parent=None):
    """Crée une nouvelle variable à partir d'une formule utilisant les colonnes existantes."""
    if donnees is None:
        QMessageBox.warning(parent, "Erreur", "Importe d'abord des données.")
        return donnees
    nom, ok = QInputDialog.getText(parent, "Créer une variable calculée", "Nom de la nouvelle variable :")
    if not ok or not nom.strip():
        return donnees
    formule, ok2 = QInputDialog.getText(
        parent, "Créer une variable calculée",
        "Formule (utilise les noms de colonnes existantes), ex : Revenu / Taille_menage"
    )
    if not ok2 or not formule.strip():
        return donnees
    try:
        donnees[nom] = donnees.eval(formule)
    except Exception as erreur:
        QMessageBox.critical(parent, "Erreur", f"Formule invalide :\n{erreur}")
    return donnees


# ---------- OBSERVATIONS ----------

def ajouter_observation(donnees, parent=None):
    """Ajoute une ligne vide à la fin du tableau."""
    if donnees is None:
        QMessageBox.warning(parent, "Erreur", "Importe d'abord des données.")
        return donnees
    nouvelle_ligne = pd.DataFrame([[None] * donnees.shape[1]], columns=donnees.columns)
    return pd.concat([donnees, nouvelle_ligne], ignore_index=True)


def supprimer_observations(donnees, indices_lignes, parent=None):
    """Supprime les lignes dont les indices sont donnés (typiquement la sélection dans le tableau)."""
    if donnees is None or not indices_lignes:
        return donnees
    return donnees.drop(index=indices_lignes).reset_index(drop=True)


# ---------- ORGANISATION ----------

def filtrer_donnees(donnees, parent=None):
    """Filtre les lignes selon une condition choisie par l'utilisateur (colonne, opérateur, valeur)."""
    if donnees is None:
        QMessageBox.warning(parent, "Erreur", "Importe d'abord des données.")
        return donnees

    dialogue = QDialog(parent)
    dialogue.setWindowTitle("Filtrer les données")
    layout = QFormLayout()
    combo_colonne = QComboBox()
    combo_colonne.addItems(list(donnees.columns))
    combo_operateur = QComboBox()
    combo_operateur.addItems(["=", "≠", ">", "<", ">=", "<=", "contient"])
    champ_valeur = QLineEdit()
    layout.addRow("Colonne :", combo_colonne)
    layout.addRow("Condition :", combo_operateur)
    layout.addRow("Valeur :", champ_valeur)
    boutons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    boutons.accepted.connect(dialogue.accept)
    boutons.rejected.connect(dialogue.reject)
    layout.addWidget(boutons)
    dialogue.setLayout(layout)

    if dialogue.exec() != QDialog.DialogCode.Accepted:
        return donnees

    colonne = combo_colonne.currentText()
    operateur = combo_operateur.currentText()
    valeur_texte = champ_valeur.text()

    try:
        serie = donnees[colonne]
        if operateur == "contient":
            masque = serie.astype(str).str.contains(valeur_texte, case=False, na=False)
        else:
            try:
                valeur = float(valeur_texte)
                serie_comparaison = pd.to_numeric(serie, errors="coerce")
            except ValueError:
                valeur = valeur_texte
                serie_comparaison = serie.astype(str)

            if operateur == "=":
                masque = serie_comparaison == valeur
            elif operateur == "≠":
                masque = serie_comparaison != valeur
            elif operateur == ">":
                masque = serie_comparaison > valeur
            elif operateur == "<":
                masque = serie_comparaison < valeur
            elif operateur == ">=":
                masque = serie_comparaison >= valeur
            else:
                masque = serie_comparaison <= valeur
        donnees = donnees[masque].reset_index(drop=True)
    except Exception as erreur:
        QMessageBox.critical(parent, "Erreur", f"Filtre invalide :\n{erreur}")

    return donnees


def trier_donnees(donnees, parent=None):
    """Trie les données selon une colonne, croissant ou décroissant."""
    if donnees is None:
        QMessageBox.warning(parent, "Erreur", "Importe d'abord des données.")
        return donnees
    colonne, ok = QInputDialog.getItem(parent, "Trier", "Colonne :", list(donnees.columns), 0, False)
    if not ok:
        return donnees
    ordre, ok2 = QInputDialog.getItem(parent, "Trier", "Ordre :", ["Croissant", "Décroissant"], 0, False)
    if not ok2:
        return donnees
    return donnees.sort_values(by=colonne, ascending=(ordre == "Croissant")).reset_index(drop=True)


# ---------- QUALITÉ DES DONNÉES ----------

def detecter_valeurs_manquantes(donnees, parent=None):
    """Affiche un résumé des valeurs manquantes par colonne."""
    if donnees is None:
        QMessageBox.warning(parent, "Erreur", "Importe d'abord des données.")
        return
    manquants = donnees.isnull().sum()
    manquants = manquants[manquants > 0]
    if manquants.empty:
        QMessageBox.information(parent, "Valeurs manquantes", "Aucune valeur manquante détectée.")
    else:
        texte = "\n".join(f"{col} : {n} valeur(s) manquante(s)" for col, n in manquants.items())
        QMessageBox.information(parent, "Valeurs manquantes", texte)


def detecter_doublons(donnees, parent=None):
    """Affiche le nombre de lignes en double."""
    if donnees is None:
        QMessageBox.warning(parent, "Erreur", "Importe d'abord des données.")
        return
    nb_doublons = donnees.duplicated().sum()
    if nb_doublons == 0:
        QMessageBox.information(parent, "Doublons", "Aucune ligne en double détectée.")
    else:
        QMessageBox.information(parent, "Doublons", f"{nb_doublons} ligne(s) en double détectée(s).")


# ---------- COMBINAISON ----------

def fusionner_fichiers(donnees, parent=None):
    """Empile un second fichier sous les données actuelles (mêmes colonnes attendues)."""
    if donnees is None:
        QMessageBox.warning(parent, "Erreur", "Importe d'abord des données.")
        return donnees
    chemin, _ = QFileDialog.getOpenFileName(parent, "Choisir le fichier à empiler", "",
                                             "Fichiers CSV (*.csv);;Fichiers Excel (*.xlsx *.xls)")
    if not chemin:
        return donnees
    try:
        if chemin.endswith(".csv"):
            autre = pd.read_csv(chemin, sep=None, engine="python")
        else:
            autre = pd.read_excel(chemin)
        donnees = pd.concat([donnees, autre], ignore_index=True)
    except Exception as erreur:
        QMessageBox.critical(parent, "Erreur", f"Impossible de fusionner :\n{erreur}")
    return donnees


def joindre_fichiers(donnees, parent=None):
    """Joint un second fichier aux données actuelles, sur une colonne commune (comme une jointure SQL)."""
    if donnees is None:
        QMessageBox.warning(parent, "Erreur", "Importe d'abord des données.")
        return donnees
    chemin, _ = QFileDialog.getOpenFileName(parent, "Choisir le fichier à joindre", "",
                                             "Fichiers CSV (*.csv);;Fichiers Excel (*.xlsx *.xls)")
    if not chemin:
        return donnees
    try:
        if chemin.endswith(".csv"):
            autre = pd.read_csv(chemin, sep=None, engine="python")
        else:
            autre = pd.read_excel(chemin)
    except Exception as erreur:
        QMessageBox.critical(parent, "Erreur", f"Impossible de lire ce fichier :\n{erreur}")
        return donnees

    dialogue = QDialog(parent)
    dialogue.setWindowTitle("Joindre les données")
    layout = QFormLayout()
    combo_colonne_gauche = QComboBox()
    combo_colonne_gauche.addItems(list(donnees.columns))
    combo_colonne_droite = QComboBox()
    combo_colonne_droite.addItems(list(autre.columns))
    combo_type = QComboBox()
    combo_type.addItems(["inner (correspondances uniquement)", "left (garder tout à gauche)",
                          "right (garder tout à droite)", "outer (tout garder)"])
    layout.addRow("Colonne commune (fichier actuel) :", combo_colonne_gauche)
    layout.addRow("Colonne commune (nouveau fichier) :", combo_colonne_droite)
    layout.addRow("Type de jointure :", combo_type)
    boutons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    boutons.accepted.connect(dialogue.accept)
    boutons.rejected.connect(dialogue.reject)
    layout.addWidget(boutons)
    dialogue.setLayout(layout)

    if dialogue.exec() != QDialog.DialogCode.Accepted:
        return donnees

    type_jointure = combo_type.currentText().split(" ")[0]
    try:
        donnees = donnees.merge(
            autre, left_on=combo_colonne_gauche.currentText(), right_on=combo_colonne_droite.currentText(),
            how=type_jointure
        )
    except Exception as erreur:
        QMessageBox.critical(parent, "Erreur", f"Jointure impossible :\n{erreur}")

    return donnees


def agreger_donnees(donnees, parent=None):
    """Regroupe les données par une ou plusieurs colonnes et résume une colonne numérique."""
    if donnees is None:
        QMessageBox.warning(parent, "Erreur", "Importe d'abord des données.")
        return donnees

    dialogue = QDialog(parent)
    dialogue.setWindowTitle("Agréger les données")
    layout = QFormLayout()
    liste_groupement = QListWidget()
    liste_groupement.addItems(list(donnees.columns))
    liste_groupement.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
    combo_valeur = QComboBox()
    colonnes_num = list(donnees.select_dtypes(include="number").columns)
    combo_valeur.addItems(colonnes_num)
    combo_fonction = QComboBox()
    combo_fonction.addItems(["Somme", "Moyenne", "Compte", "Minimum", "Maximum"])
    layout.addRow("Regrouper par (sélection multiple) :", liste_groupement)
    layout.addRow("Colonne à résumer :", combo_valeur)
    layout.addRow("Fonction :", combo_fonction)
    boutons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    boutons.accepted.connect(dialogue.accept)
    boutons.rejected.connect(dialogue.reject)
    layout.addWidget(boutons)
    dialogue.setLayout(layout)

    if dialogue.exec() != QDialog.DialogCode.Accepted:
        return donnees

    colonnes_groupement = [item.text() for item in liste_groupement.selectedItems()]
    colonne_valeur = combo_valeur.currentText()
    fonction_choisie = combo_fonction.currentText()
    correspondance_fonctions = {"Somme": "sum", "Moyenne": "mean", "Compte": "count",
                                 "Minimum": "min", "Maximum": "max"}

    if not colonnes_groupement or not colonne_valeur:
        QMessageBox.warning(parent, "Erreur",
                             "Choisis au moins une colonne de regroupement et une colonne à résumer.")
        return donnees

    try:
        return donnees.groupby(colonnes_groupement)[colonne_valeur].agg(
            correspondance_fonctions[fonction_choisie]
        ).reset_index()
    except Exception as erreur:
        QMessageBox.critical(parent, "Erreur", f"Agrégation impossible :\n{erreur}")
        return donnees
