from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QGroupBox
from donnees import SEUIL_GRANDES_DONNEES


def creer_petit_tableau_stats(nom_colonne, statistiques):
    """Crée un petit groupe avec un tableau de statistiques pour UNE colonne."""
    groupe = QGroupBox(nom_colonne)
    layout_groupe = QVBoxLayout()

    tableau = QTableWidget()
    tableau.setRowCount(len(statistiques))
    tableau.setColumnCount(1)
    tableau.setHorizontalHeaderLabels(["Valeur"])
    tableau.setVerticalHeaderLabels(list(statistiques.keys()))

    for i, valeur in enumerate(statistiques.values()):
        tableau.setItem(i, 0, QTableWidgetItem(f"{valeur:.2f}"))

    tableau.setMaximumHeight(180)
    layout_groupe.addWidget(tableau)
    groupe.setLayout(layout_groupe)
    return groupe


def calculer_statistiques(donnees, conteneur_stats):
    """Calcule les statistiques descriptives et les affiche selon la taille des données."""
    if donnees is None:
        return

    while conteneur_stats.layout().count():
        item = conteneur_stats.layout().takeAt(0)
        if item.widget():
            item.widget().deleteLater()

    colonnes_numeriques = donnees.select_dtypes(include="number")
    if colonnes_numeriques.empty:
        return

    if donnees.shape[0] < SEUIL_GRANDES_DONNEES:
        layout_grille = QHBoxLayout()
        colonne_actuelle = QVBoxLayout()
        compteur = 0

        for nom_colonne in colonnes_numeriques.columns:
            serie = colonnes_numeriques[nom_colonne]
            statistiques = {
                "Moyenne": serie.mean(),
                "Médiane": serie.median(),
                "Écart-type": serie.std(),
                "Min": serie.min(),
                "Max": serie.max(),
            }
            groupe = creer_petit_tableau_stats(nom_colonne, statistiques)
            colonne_actuelle.addWidget(groupe)
            compteur += 1

            if compteur % 3 == 0:
                layout_grille.addLayout(colonne_actuelle)
                colonne_actuelle = QVBoxLayout()

        layout_grille.addLayout(colonne_actuelle)
        conteneur_stats.layout().addLayout(layout_grille)

    else:
        resume = colonnes_numeriques.describe()
        tableau_resume = QTableWidget()
        tableau_resume.setRowCount(resume.shape[0])
        tableau_resume.setColumnCount(resume.shape[1])
        tableau_resume.setHorizontalHeaderLabels(resume.columns.astype(str))
        tableau_resume.setVerticalHeaderLabels(resume.index.astype(str))

        for ligne in range(resume.shape[0]):
            for colonne in range(resume.shape[1]):
                valeur = f"{resume.iloc[ligne, colonne]:.2f}"
                tableau_resume.setItem(ligne, colonne, QTableWidgetItem(valeur))

        conteneur_stats.layout().addWidget(tableau_resume)
