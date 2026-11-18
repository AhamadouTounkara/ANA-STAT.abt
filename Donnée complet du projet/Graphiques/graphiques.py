"""Laboratoire graphique : crée librement histogrammes, barres, secteurs, courbes, nuages de points,
boxplots, pyramide des âges et courbe de Lorenz à partir des données actuellement importées."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QGroupBox, QListWidget, QAbstractItemView, QCheckBox, QFileDialog, QMessageBox
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np

TYPES_GRAPHIQUES = [
    "Histogramme", "Barres", "Barres empilées", "Secteurs", "Courbes",
    "Nuage de points", "Boxplot", "Pyramide des âges", "Courbe de Lorenz",
]

# Pour chaque type, quels sélecteurs de colonnes sont utiles.
BESOINS_PAR_TYPE = {
    "Histogramme": {"x": "Colonne (numérique)"},
    "Barres": {"x": "Colonne catégorielle (X)", "y": "Colonne numérique (Y)"},
    "Barres empilées": {"x": "Colonne catégorielle (X)", "multi": "Colonnes numériques à empiler"},
    "Secteurs": {"x": "Colonne catégorielle", "y": "Colonne numérique"},
    "Courbes": {"x": "Colonne X", "multi": "Colonne(s) Y"},
    "Nuage de points": {"x": "Colonne X (numérique)", "y": "Colonne Y (numérique)"},
    "Boxplot": {"multi": "Colonne(s) numérique(s)"},
    "Pyramide des âges": {"x": "Colonne âge", "y": "Colonne sexe", "z": "Colonne effectif"},
    "Courbe de Lorenz": {"x": "Colonne (numérique)"},
}


def calculer_courbe_lorenz(valeurs):
    """Calcule les coordonnées de la courbe de Lorenz à partir d'une série de valeurs numériques."""
    valeurs_triees = np.sort(valeurs)
    cumul = np.cumsum(valeurs_triees)
    cumul_pourcentage = np.insert(cumul / cumul[-1], 0, 0)
    population_pourcentage = np.linspace(0, 1, len(cumul_pourcentage))
    return population_pourcentage, cumul_pourcentage


def creer_page_graphiques(obtenir_donnees_actuelles):
    """Assemble la page du laboratoire graphique."""
    page = QWidget()
    layout_principal = QHBoxLayout()

    # ---- Panneau de gauche : réglages ----
    panneau_gauche = QWidget()
    layout_gauche = QVBoxLayout()

    groupe_type = QGroupBox("Type de graphique")
    layout_type = QVBoxLayout()
    combo_type = QComboBox()
    combo_type.addItems(TYPES_GRAPHIQUES)
    layout_type.addWidget(combo_type)
    groupe_type.setLayout(layout_type)

    groupe_colonnes = QGroupBox("Colonnes")
    layout_colonnes = QGridLayout()
    label_x = QLabel("Colonne X")
    combo_x = QComboBox()
    label_y = QLabel("Colonne Y")
    combo_y = QComboBox()
    label_z = QLabel("Colonne effectif")
    combo_z = QComboBox()
    label_multi = QLabel("Colonnes multiples")
    liste_multi = QListWidget()
    liste_multi.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
    liste_multi.setMaximumHeight(100)
    bouton_actualiser_colonnes = QPushButton("Actualiser les colonnes")

    layout_colonnes.addWidget(label_x, 0, 0)
    layout_colonnes.addWidget(combo_x, 0, 1)
    layout_colonnes.addWidget(label_y, 1, 0)
    layout_colonnes.addWidget(combo_y, 1, 1)
    layout_colonnes.addWidget(label_z, 2, 0)
    layout_colonnes.addWidget(combo_z, 2, 1)
    layout_colonnes.addWidget(label_multi, 3, 0)
    layout_colonnes.addWidget(liste_multi, 3, 1)
    layout_colonnes.addWidget(bouton_actualiser_colonnes, 4, 0, 1, 2)
    groupe_colonnes.setLayout(layout_colonnes)

    groupe_personnalisation = QGroupBox("Personnalisation")
    layout_perso = QGridLayout()
    champ_titre = QLineEdit()
    champ_sous_titre = QLineEdit()
    champ_label_x = QLineEdit()
    champ_label_y = QLineEdit()
    champ_source = QLineEdit()
    case_legende = QCheckBox("Afficher la légende")
    case_legende.setChecked(True)

    layout_perso.addWidget(QLabel("Titre :"), 0, 0)
    layout_perso.addWidget(champ_titre, 0, 1)
    layout_perso.addWidget(QLabel("Sous-titre :"), 1, 0)
    layout_perso.addWidget(champ_sous_titre, 1, 1)
    layout_perso.addWidget(QLabel("Étiquette axe X :"), 2, 0)
    layout_perso.addWidget(champ_label_x, 2, 1)
    layout_perso.addWidget(QLabel("Étiquette axe Y :"), 3, 0)
    layout_perso.addWidget(champ_label_y, 3, 1)
    layout_perso.addWidget(QLabel("Source :"), 4, 0)
    layout_perso.addWidget(champ_source, 4, 1)
    layout_perso.addWidget(case_legende, 5, 0, 1, 2)
    groupe_personnalisation.setLayout(layout_perso)

    bouton_generer = QPushButton("Générer le graphique")

    groupe_export = QGroupBox("Exportation")
    layout_export = QHBoxLayout()
    boutons_export = {}
    for format_export in ["PNG", "JPG", "SVG", "PDF"]:
        bouton = QPushButton(format_export)
        layout_export.addWidget(bouton)
        boutons_export[format_export] = bouton
    groupe_export.setLayout(layout_export)

    layout_gauche.addWidget(groupe_type)
    layout_gauche.addWidget(groupe_colonnes)
    layout_gauche.addWidget(groupe_personnalisation)
    layout_gauche.addWidget(bouton_generer)
    layout_gauche.addWidget(groupe_export)
    layout_gauche.addStretch()
    panneau_gauche.setLayout(layout_gauche)
    panneau_gauche.setMaximumWidth(360)

    # ---- Panneau de droite : le graphique ----
    figure = Figure(figsize=(7, 5.5))
    canvas = FigureCanvasQTAgg(figure)

    layout_principal.addWidget(panneau_gauche)
    layout_principal.addWidget(canvas, stretch=1)
    page.setLayout(layout_principal)

    # ---- Logique ----

    def gerer_actualisation_colonnes():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            return
        toutes_colonnes = list(donnees.columns)
        colonnes_num = list(donnees.select_dtypes(include="number").columns)

        combo_x.clear()
        combo_x.addItems(toutes_colonnes)
        combo_y.clear()
        combo_y.addItems(toutes_colonnes)
        combo_z.clear()
        combo_z.addItems(colonnes_num)
        liste_multi.clear()
        liste_multi.addItems(colonnes_num)

    def gerer_changement_type():
        type_choisi = combo_type.currentText()
        besoins = BESOINS_PAR_TYPE[type_choisi]

        label_x.setVisible("x" in besoins)
        combo_x.setVisible("x" in besoins)
        if "x" in besoins:
            label_x.setText(besoins["x"])

        label_y.setVisible("y" in besoins)
        combo_y.setVisible("y" in besoins)
        if "y" in besoins:
            label_y.setText(besoins["y"])

        label_z.setVisible("z" in besoins)
        combo_z.setVisible("z" in besoins)
        if "z" in besoins:
            label_z.setText(besoins["z"])

        label_multi.setVisible("multi" in besoins)
        liste_multi.setVisible("multi" in besoins)
        if "multi" in besoins:
            label_multi.setText(besoins["multi"])

    combo_type.currentTextChanged.connect(gerer_changement_type)
    bouton_actualiser_colonnes.clicked.connect(gerer_actualisation_colonnes)
    gerer_changement_type()

    def appliquer_habillage(ax):
        titre = champ_titre.text()
        sous_titre = champ_sous_titre.text()
        if titre and sous_titre:
            ax.set_title(f"{titre}\n{sous_titre}", fontsize=12)
        elif titre:
            ax.set_title(titre, fontsize=12)
        if champ_label_x.text():
            ax.set_xlabel(champ_label_x.text())
        if champ_label_y.text():
            ax.set_ylabel(champ_label_y.text())
        if champ_source.text():
            figure.text(0.01, 0.01, f"Source : {champ_source.text()}", fontsize=8, color="gray")

    def gerer_generation():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            QMessageBox.warning(page, "Erreur", "Importe d'abord des données.")
            return

        type_choisi = combo_type.currentText()
        figure.clear()
        ax = figure.add_subplot(111)

        try:
            if type_choisi == "Histogramme":
                colonne = combo_x.currentText()
                donnees[colonne].dropna().plot(kind="hist", ax=ax, bins=15, color="#2563EB")

            elif type_choisi == "Barres":
                colonne_x, colonne_y = combo_x.currentText(), combo_y.currentText()
                sous_ensemble = donnees[[colonne_x, colonne_y]].dropna().sort_values(by=colonne_y, ascending=False).head(15)
                ax.bar(sous_ensemble[colonne_x].astype(str), sous_ensemble[colonne_y], color="#2563EB")
                ax.tick_params(axis="x", rotation=45)

            elif type_choisi == "Barres empilées":
                colonne_x = combo_x.currentText()
                colonnes_y = [item.text() for item in liste_multi.selectedItems()]
                if not colonnes_y:
                    QMessageBox.information(page, "Info", "Sélectionne au moins une colonne numérique.")
                    return
                sous_ensemble = donnees[[colonne_x] + colonnes_y].dropna().head(15)
                bas = None
                for colonne in colonnes_y:
                    ax.bar(sous_ensemble[colonne_x].astype(str), sous_ensemble[colonne], bottom=bas, label=colonne)
                    bas = sous_ensemble[colonne] if bas is None else bas + sous_ensemble[colonne]
                ax.tick_params(axis="x", rotation=45)
                if case_legende.isChecked():
                    ax.legend()

            elif type_choisi == "Secteurs":
                colonne_x, colonne_y = combo_x.currentText(), combo_y.currentText()
                sous_ensemble = donnees[[colonne_x, colonne_y]].dropna().sort_values(by=colonne_y, ascending=False).head(10)
                ax.pie(sous_ensemble[colonne_y], labels=sous_ensemble[colonne_x].astype(str), autopct="%1.1f%%")

            elif type_choisi == "Courbes":
                colonne_x = combo_x.currentText()
                colonnes_y = [item.text() for item in liste_multi.selectedItems()]
                if not colonnes_y:
                    QMessageBox.information(page, "Info", "Sélectionne au moins une colonne Y.")
                    return
                sous_ensemble = donnees[[colonne_x] + colonnes_y].dropna()
                for colonne in colonnes_y:
                    ax.plot(sous_ensemble[colonne_x], sous_ensemble[colonne], marker="o", label=colonne)
                if case_legende.isChecked() and len(colonnes_y) > 1:
                    ax.legend()

            elif type_choisi == "Nuage de points":
                colonne_x, colonne_y = combo_x.currentText(), combo_y.currentText()
                sous_ensemble = donnees[[colonne_x, colonne_y]].dropna()
                ax.scatter(sous_ensemble[colonne_x], sous_ensemble[colonne_y], alpha=0.6, color="#2563EB")

            elif type_choisi == "Boxplot":
                colonnes = [item.text() for item in liste_multi.selectedItems()]
                if not colonnes:
                    QMessageBox.information(page, "Info", "Sélectionne au moins une colonne numérique.")
                    return
                ax.boxplot([donnees[colonne].dropna() for colonne in colonnes], labels=colonnes)

            elif type_choisi == "Pyramide des âges":
                colonne_age, colonne_sexe, colonne_effectif = combo_x.currentText(), combo_y.currentText(), combo_z.currentText()
                sous_ensemble = donnees[[colonne_age, colonne_sexe, colonne_effectif]].dropna()
                for sexe, groupe in sous_ensemble.groupby(colonne_sexe):
                    ax.barh(groupe[colonne_age].astype(str), groupe[colonne_effectif], label=str(sexe))
                if case_legende.isChecked():
                    ax.legend()

            elif type_choisi == "Courbe de Lorenz":
                colonne = combo_x.currentText()
                valeurs = donnees[colonne].dropna().values
                if len(valeurs) == 0:
                    QMessageBox.warning(page, "Erreur", "Aucune valeur numérique disponible.")
                    return
                pop_pct, cumul_pct = calculer_courbe_lorenz(valeurs)
                ax.plot(pop_pct, cumul_pct, color="#2563EB", label="Courbe de Lorenz")
                ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Égalité parfaite")
                if case_legende.isChecked():
                    ax.legend()

            appliquer_habillage(ax)
            figure.tight_layout()
            canvas.draw()

        except Exception as erreur:
            QMessageBox.critical(page, "Erreur", f"Impossible de générer ce graphique :\n{erreur}")

    bouton_generer.clicked.connect(gerer_generation)

    def creer_gestionnaire_export(extension, filtre):
        def gerer_export():
            chemin, _ = QFileDialog.getSaveFileName(page, f"Exporter en {extension.upper()}", "", filtre)
            if chemin:
                figure.savefig(chemin, dpi=150, bbox_inches="tight")
                QMessageBox.information(page, "Export réussi", f"Graphique exporté vers {chemin}")
        return gerer_export

    boutons_export["PNG"].clicked.connect(creer_gestionnaire_export("png", "Images PNG (*.png)"))
    boutons_export["JPG"].clicked.connect(creer_gestionnaire_export("jpg", "Images JPG (*.jpg)"))
    boutons_export["SVG"].clicked.connect(creer_gestionnaire_export("svg", "Images vectorielles SVG (*.svg)"))
    boutons_export["PDF"].clicked.connect(creer_gestionnaire_export("pdf", "Fichiers PDF (*.pdf)"))

    return page
