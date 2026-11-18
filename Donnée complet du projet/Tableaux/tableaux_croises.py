"""Générateur de tableaux croisés : Variable → Indicateur → Désagrégation → Tableau."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog
)
import pandas as pd
from Export.export_avance import exporter_excel, exporter_pdf, exporter_word, exporter_image

INDICATEURS_DISPONIBLES = ["Effectif (nombres)", "Moyenne", "Médiane", "%", "% en ligne", "% en colonne", "Total"]


def generer_tableau_croise(donnees, variable_valeur, variable_ligne, variable_colonne, indicateur):
    """Construit le tableau croisé demandé et renvoie un DataFrame prêt à afficher."""
    fonctions_agregation = {
        "Effectif (nombres)": "count", "Moyenne": "mean", "Médiane": "median",
        "%": "sum", "% en ligne": "sum", "% en colonne": "sum", "Total": "sum",
    }
    fonction_agg = fonctions_agregation[indicateur]

    if variable_colonne:
        table = pd.pivot_table(
            donnees, values=variable_valeur, index=variable_ligne, columns=variable_colonne,
            aggfunc=fonction_agg, fill_value=0
        )
    else:
        table = donnees.groupby(variable_ligne)[variable_valeur].agg(fonction_agg).to_frame(name=variable_valeur)

    if indicateur == "%":
        table = (table / table.values.sum() * 100).round(2)
    elif indicateur == "% en ligne":
        table = table.div(table.sum(axis=1), axis=0).mul(100).round(2)
    elif indicateur == "% en colonne":
        table = table.div(table.sum(axis=0), axis=1).mul(100).round(2)
    elif indicateur == "Total":
        table["Total ligne"] = table.sum(axis=1)
        ligne_total = table.sum(axis=0)
        ligne_total.name = "Total colonne"
        table = pd.concat([table, ligne_total.to_frame().T])

    return table.reset_index()


def remplir_tableau_qt(tableau_qt, dataframe):
    """Affiche un DataFrame (avec son index déjà en colonne) dans un QTableWidget."""
    tableau_qt.setRowCount(dataframe.shape[0])
    tableau_qt.setColumnCount(dataframe.shape[1])
    tableau_qt.setHorizontalHeaderLabels([str(c) for c in dataframe.columns])
    tableau_qt.verticalHeader().setVisible(False)
    for ligne in range(dataframe.shape[0]):
        for colonne in range(dataframe.shape[1]):
            valeur = dataframe.iloc[ligne, colonne]
            texte = f"{valeur:.2f}" if isinstance(valeur, float) else str(valeur)
            tableau_qt.setItem(ligne, colonne, QTableWidgetItem(texte))


def creer_page_tableaux_croises(obtenir_donnees_actuelles):
    """Assemble la page du générateur de tableaux croisés."""
    page = QWidget()
    layout = QVBoxLayout()

    champ_titre = QLineEdit()
    champ_titre.setPlaceholderText("Titre du tableau, ex : Tableau 2.4 : Population par région et sexe")

    groupe_reglages = QGroupBox("Construction du tableau")
    layout_reglages = QGridLayout()

    combo_variable = QComboBox()
    combo_indicateur = QComboBox()
    combo_indicateur.addItems(INDICATEURS_DISPONIBLES)
    combo_ligne = QComboBox()
    combo_colonne = QComboBox()
    combo_colonne.addItem("(aucune — tableau simple)")
    bouton_actualiser = QPushButton("Actualiser les colonnes")
    bouton_generer = QPushButton("Générer le tableau")

    layout_reglages.addWidget(QLabel("Variable (valeur à résumer) :"), 0, 0)
    layout_reglages.addWidget(combo_variable, 0, 1)
    layout_reglages.addWidget(QLabel("Indicateur :"), 1, 0)
    layout_reglages.addWidget(combo_indicateur, 1, 1)
    layout_reglages.addWidget(QLabel("Désagrégation — lignes :"), 2, 0)
    layout_reglages.addWidget(combo_ligne, 2, 1)
    layout_reglages.addWidget(QLabel("Désagrégation — colonnes (optionnel) :"), 3, 0)
    layout_reglages.addWidget(combo_colonne, 3, 1)
    layout_reglages.addWidget(bouton_actualiser, 4, 0)
    layout_reglages.addWidget(bouton_generer, 4, 1)
    groupe_reglages.setLayout(layout_reglages)

    label_titre_affiche = QLabel("")
    label_titre_affiche.setStyleSheet("font-weight: bold; font-size: 13px;")
    tableau_resultat = QTableWidget()
    tableau_resultat.setMinimumHeight(300)

    groupe_export = QGroupBox("Exportation")
    layout_export = QHBoxLayout()
    bouton_excel = QPushButton("Excel")
    bouton_pdf = QPushButton("PDF")
    bouton_word = QPushButton("Word")
    bouton_image = QPushButton("Image")
    for bouton in (bouton_excel, bouton_pdf, bouton_word, bouton_image):
        layout_export.addWidget(bouton)
    groupe_export.setLayout(layout_export)

    layout.addWidget(champ_titre)
    layout.addWidget(groupe_reglages)
    layout.addWidget(label_titre_affiche)
    layout.addWidget(tableau_resultat)
    layout.addWidget(groupe_export)
    page.setLayout(layout)

    dernier_tableau = {"dataframe": None}

    def gerer_actualisation():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            return
        toutes_colonnes = list(donnees.columns)
        colonnes_num = list(donnees.select_dtypes(include="number").columns)
        combo_variable.clear()
        combo_variable.addItems(colonnes_num)
        combo_ligne.clear()
        combo_ligne.addItems(toutes_colonnes)
        combo_colonne.clear()
        combo_colonne.addItem("(aucune — tableau simple)")
        combo_colonne.addItems(toutes_colonnes)

    def gerer_generation():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            QMessageBox.warning(page, "Erreur", "Importe d'abord des données.")
            return

        variable_valeur = combo_variable.currentText()
        variable_ligne = combo_ligne.currentText()
        variable_colonne = combo_colonne.currentText()
        if variable_colonne == "(aucune — tableau simple)":
            variable_colonne = None
        indicateur = combo_indicateur.currentText()

        if not variable_valeur or not variable_ligne:
            QMessageBox.information(page, "Info", "Choisis au moins une variable et une désagrégation par ligne.")
            return

        try:
            resultat = generer_tableau_croise(donnees, variable_valeur, variable_ligne, variable_colonne, indicateur)
        except Exception as erreur:
            QMessageBox.critical(page, "Erreur", f"Impossible de générer ce tableau :\n{erreur}")
            return

        titre = champ_titre.text() or f"Tableau : {variable_valeur} par {variable_ligne}"
        label_titre_affiche.setText(titre)
        remplir_tableau_qt(tableau_resultat, resultat)
        dernier_tableau["dataframe"] = resultat

    bouton_actualiser.clicked.connect(gerer_actualisation)
    bouton_generer.clicked.connect(gerer_generation)

    def verifier():
        if dernier_tableau["dataframe"] is None:
            QMessageBox.warning(page, "Erreur", "Génère d'abord un tableau.")
            return None
        return dernier_tableau["dataframe"]

    def gerer_export_excel():
        resultat = verifier()
        if resultat is None:
            return
        chemin, _ = QFileDialog.getSaveFileName(page, "Exporter en Excel", "", "Fichiers Excel (*.xlsx)")
        if chemin:
            exporter_excel(resultat, chemin)
            QMessageBox.information(page, "Export réussi", f"Tableau exporté vers {chemin}")

    def gerer_export_pdf():
        resultat = verifier()
        if resultat is None:
            return
        chemin, _ = QFileDialog.getSaveFileName(page, "Exporter en PDF", "", "Fichiers PDF (*.pdf)")
        if chemin:
            exporter_pdf(resultat, label_titre_affiche.text() or "Tableau croisé", chemin)
            QMessageBox.information(page, "Export réussi", f"Tableau exporté vers {chemin}")

    def gerer_export_word():
        resultat = verifier()
        if resultat is None:
            return
        chemin, _ = QFileDialog.getSaveFileName(page, "Exporter en Word", "", "Documents Word (*.docx)")
        if chemin:
            exporter_word(resultat, label_titre_affiche.text() or "Tableau croisé", chemin)
            QMessageBox.information(page, "Export réussi", f"Tableau exporté vers {chemin}")

    def gerer_export_image():
        QMessageBox.information(
            page, "Info",
            "L'export direct du tableau en image n'est pas encore disponible ici. "
            "Utilise l'export PDF ou Excel en attendant."
        )

    bouton_excel.clicked.connect(gerer_export_excel)
    bouton_pdf.clicked.connect(gerer_export_pdf)
    bouton_word.clicked.connect(gerer_export_word)
    bouton_image.clicked.connect(gerer_export_image)

    return page
