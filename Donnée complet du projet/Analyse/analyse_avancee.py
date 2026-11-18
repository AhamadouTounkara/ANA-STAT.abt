from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QGroupBox,
    QMessageBox, QScrollArea, QTabWidget, QListWidget, QAbstractItemView, QSpinBox
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm


# ---------- FONCTIONS DE CALCUL : CORRÉLATION ----------

def calculer_matrice_correlation(donnees, colonnes):
    """Calcule la matrice de corrélation de Pearson entre les colonnes numériques choisies."""
    return donnees[colonnes].corr(method="pearson")


def interpreter_correlation(valeur):
    """Donne une interprétation textuelle simple d'un coefficient de corrélation."""
    valeur_absolue = abs(valeur)
    if valeur_absolue >= 0.7:
        force = "forte"
    elif valeur_absolue >= 0.4:
        force = "modérée"
    elif valeur_absolue >= 0.2:
        force = "faible"
    else:
        force = "quasi nulle"
    sens = "positive" if valeur > 0 else "négative" if valeur < 0 else "nulle"
    return f"Corrélation {force} et {sens} (r = {valeur:.3f})"


# ---------- FONCTIONS DE CALCUL : RÉGRESSION ----------

def calculer_regression_lineaire(donnees, colonne_x, colonne_y):
    """Calcule une régression linéaire simple y = a*x + b, avec le R² et le coefficient de corrélation."""
    sous_ensemble = donnees[[colonne_x, colonne_y]].dropna()
    x = sous_ensemble[colonne_x].values
    y = sous_ensemble[colonne_y].values

    pente, ordonnee, r_valeur, p_valeur, erreur_std = stats.linregress(x, y)

    resultat = {
        "pente": pente,
        "ordonnee_origine": ordonnee,
        "r_carre": r_valeur ** 2,
        "coefficient_correlation": r_valeur,
        "p_valeur": p_valeur,
        "x": x,
        "y": y,
    }
    return resultat


# ---------- FONCTIONS DE CALCUL : TESTS D'HYPOTHÈSES ----------

def test_t_deux_groupes(donnees, colonne_groupe, colonne_valeur, groupe_1, groupe_2):
    """Test t de Student pour comparer les moyennes de deux groupes indépendants."""
    valeurs_1 = donnees[donnees[colonne_groupe].astype(str) == str(groupe_1)][colonne_valeur].dropna()
    valeurs_2 = donnees[donnees[colonne_groupe].astype(str) == str(groupe_2)][colonne_valeur].dropna()

    statistique, p_valeur = stats.ttest_ind(valeurs_1, valeurs_2, equal_var=False)

    return {
        "statistique_t": statistique,
        "p_valeur": p_valeur,
        "moyenne_1": valeurs_1.mean(),
        "moyenne_2": valeurs_2.mean(),
        "n1": len(valeurs_1),
        "n2": len(valeurs_2),
        "significatif": p_valeur < 0.05,
    }


def test_chi_deux(donnees, colonne_1, colonne_2):
    """Test du chi-deux d'indépendance entre deux variables catégorielles."""
    table_contingence = pd.crosstab(donnees[colonne_1], donnees[colonne_2])
    statistique, p_valeur, degres_liberte, frequences_attendues = stats.chi2_contingency(table_contingence)

    return {
        "statistique_chi2": statistique,
        "p_valeur": p_valeur,
        "degres_liberte": degres_liberte,
        "table_contingence": table_contingence,
        "significatif": p_valeur < 0.05,
    }


# ---------- FONCTIONS DE CALCUL : SÉRIES TEMPORELLES ----------

def calculer_tendance_temporelle(donnees, colonnes_periodes):
    """Calcule la tendance linéaire (MCO) d'une série de colonnes représentant des périodes successives."""
    valeurs = donnees[colonnes_periodes].sum().values
    periodes = np.arange(1, len(colonnes_periodes) + 1)

    pente, ordonnee, r_valeur, p_valeur, erreur_std = stats.linregress(periodes, valeurs)
    tendance = pente * periodes + ordonnee

    return {
        "periodes": colonnes_periodes,
        "valeurs": valeurs,
        "tendance": tendance,
        "pente": pente,
        "r_carre": r_valeur ** 2,
    }


def remplir_tableau_dataframe(tableau, dataframe, inclure_index=True):
    """Affiche un DataFrame pandas (avec ou sans son index) dans un QTableWidget."""
    colonnes = ([dataframe.index.name or "Index"] + list(dataframe.columns)) if inclure_index else list(dataframe.columns)
    tableau.setColumnCount(len(colonnes))
    tableau.setHorizontalHeaderLabels([str(c) for c in colonnes])
    tableau.setRowCount(dataframe.shape[0])

    for ligne in range(dataframe.shape[0]):
        decalage = 0
        if inclure_index:
            tableau.setItem(ligne, 0, QTableWidgetItem(str(dataframe.index[ligne])))
            decalage = 1
        for colonne in range(dataframe.shape[1]):
            valeur = dataframe.iloc[ligne, colonne]
            texte = f"{valeur:.3f}" if isinstance(valeur, (float, np.floating)) else str(valeur)
            tableau.setItem(ligne, colonne + decalage, QTableWidgetItem(texte))


# ---------- ONGLET CORRÉLATION ----------

def creer_onglet_correlation(obtenir_donnees_actuelles):
    onglet = QWidget()
    layout = QVBoxLayout()

    layout_choix = QHBoxLayout()
    combo_x = QComboBox()
    combo_y = QComboBox()
    bouton_calculer = QPushButton("Calculer la corrélation")
    bouton_actualiser = QPushButton("Actualiser les colonnes")
    layout_choix.addWidget(QLabel("Variable 1 :"))
    layout_choix.addWidget(combo_x)
    layout_choix.addWidget(QLabel("Variable 2 :"))
    layout_choix.addWidget(combo_y)
    layout_choix.addWidget(bouton_calculer)
    layout_choix.addWidget(bouton_actualiser)

    label_resultat = QLabel("Choisis deux variables numériques et clique sur 'Calculer la corrélation'.")
    label_resultat.setWordWrap(True)

    figure = Figure(figsize=(5, 4))
    canvas = FigureCanvasQTAgg(figure)
    canvas.setMinimumHeight(300)

    label_matrice_titre = QLabel("Matrice de corrélation complète (toutes les colonnes numériques)")
    label_matrice_titre.setStyleSheet("font-weight: bold;")
    bouton_matrice = QPushButton("Afficher la matrice complète")
    tableau_matrice = QTableWidget()
    tableau_matrice.setMinimumHeight(200)

    def gerer_actualisation():
        donnees = obtenir_donnees_actuelles()
        colonnes_num = list(donnees.select_dtypes(include="number").columns) if donnees is not None else []
        combo_x.clear()
        combo_y.clear()
        combo_x.addItems(colonnes_num)
        combo_y.addItems(colonnes_num)

    def gerer_calcul():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            QMessageBox.warning(onglet, "Erreur", "Importe d'abord des données.")
            return
        colonne_x, colonne_y = combo_x.currentText(), combo_y.currentText()
        if not colonne_x or not colonne_y:
            return

        sous_ensemble = donnees[[colonne_x, colonne_y]].dropna()
        r = sous_ensemble[colonne_x].corr(sous_ensemble[colonne_y])
        label_resultat.setText(interpreter_correlation(r))

        figure.clear()
        ax = figure.add_subplot(111)
        ax.scatter(sous_ensemble[colonne_x], sous_ensemble[colonne_y], alpha=0.6)
        ax.set_xlabel(colonne_x)
        ax.set_ylabel(colonne_y)
        ax.set_title(f"Nuage de points : {colonne_x} vs {colonne_y}")
        figure.tight_layout()
        canvas.draw()

    def gerer_matrice():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            QMessageBox.warning(onglet, "Erreur", "Importe d'abord des données.")
            return
        colonnes_num = list(donnees.select_dtypes(include="number").columns)
        if len(colonnes_num) < 2:
            QMessageBox.information(onglet, "Info", "Il faut au moins 2 colonnes numériques.")
            return
        matrice = calculer_matrice_correlation(donnees, colonnes_num)
        remplir_tableau_dataframe(tableau_matrice, matrice, inclure_index=True)

    bouton_actualiser.clicked.connect(gerer_actualisation)
    bouton_calculer.clicked.connect(gerer_calcul)
    bouton_matrice.clicked.connect(gerer_matrice)

    layout.addLayout(layout_choix)
    layout.addWidget(label_resultat)
    layout.addWidget(canvas)
    layout.addWidget(label_matrice_titre)
    layout.addWidget(bouton_matrice)
    layout.addWidget(tableau_matrice)
    onglet.setLayout(layout)
    return onglet


# ---------- ONGLET RÉGRESSION ----------

def creer_onglet_regression(obtenir_donnees_actuelles):
    onglet = QWidget()
    layout = QVBoxLayout()

    layout_choix = QHBoxLayout()
    combo_x = QComboBox()
    combo_y = QComboBox()
    bouton_calculer = QPushButton("Calculer la régression")
    bouton_actualiser = QPushButton("Actualiser les colonnes")
    layout_choix.addWidget(QLabel("Variable explicative (X) :"))
    layout_choix.addWidget(combo_x)
    layout_choix.addWidget(QLabel("Variable à expliquer (Y) :"))
    layout_choix.addWidget(combo_y)
    layout_choix.addWidget(bouton_calculer)
    layout_choix.addWidget(bouton_actualiser)

    label_equation = QLabel("Choisis X et Y, puis lance le calcul.")
    label_equation.setWordWrap(True)
    label_equation.setStyleSheet("font-weight: bold;")

    figure = Figure(figsize=(5, 4))
    canvas = FigureCanvasQTAgg(figure)
    canvas.setMinimumHeight(320)

    def gerer_actualisation():
        donnees = obtenir_donnees_actuelles()
        colonnes_num = list(donnees.select_dtypes(include="number").columns) if donnees is not None else []
        combo_x.clear()
        combo_y.clear()
        combo_x.addItems(colonnes_num)
        combo_y.addItems(colonnes_num)

    def gerer_calcul():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            QMessageBox.warning(onglet, "Erreur", "Importe d'abord des données.")
            return
        colonne_x, colonne_y = combo_x.currentText(), combo_y.currentText()
        if not colonne_x or not colonne_y:
            return

        resultat = calculer_regression_lineaire(donnees, colonne_x, colonne_y)

        signe = "+" if resultat["ordonnee_origine"] >= 0 else "-"
        label_equation.setText(
            f"Équation : {colonne_y} = {resultat['pente']:.4f} × {colonne_x} {signe} {abs(resultat['ordonnee_origine']):.4f}\n"
            f"R² = {resultat['r_carre']:.4f}  (le modèle explique {resultat['r_carre']*100:.1f}% de la variation)\n"
            f"p-valeur = {resultat['p_valeur']:.4f}  "
            f"({'relation statistiquement significative' if resultat['p_valeur'] < 0.05 else 'relation non significative au seuil de 5%'})"
        )

        figure.clear()
        ax = figure.add_subplot(111)
        ax.scatter(resultat["x"], resultat["y"], alpha=0.6, label="Données")
        x_trie = np.sort(resultat["x"])
        y_predit = resultat["pente"] * x_trie + resultat["ordonnee_origine"]
        ax.plot(x_trie, y_predit, color="red", label="Droite de régression")
        ax.set_xlabel(colonne_x)
        ax.set_ylabel(colonne_y)
        ax.legend()
        ax.set_title("Régression linéaire")
        figure.tight_layout()
        canvas.draw()

    bouton_actualiser.clicked.connect(gerer_actualisation)
    bouton_calculer.clicked.connect(gerer_calcul)

    layout.addLayout(layout_choix)
    layout.addWidget(label_equation)
    layout.addWidget(canvas)
    onglet.setLayout(layout)
    return onglet


# ---------- ONGLET TESTS D'HYPOTHÈSES ----------

def creer_onglet_tests(obtenir_donnees_actuelles):
    onglet = QWidget()
    layout = QVBoxLayout()

    # --- Test t ---
    groupe_t = QGroupBox("Test t de Student (comparaison de deux groupes)")
    layout_t = QVBoxLayout()
    layout_choix_t = QHBoxLayout()
    combo_groupe_t = QComboBox()
    combo_valeur_t = QComboBox()
    combo_g1 = QComboBox()
    combo_g2 = QComboBox()
    bouton_actualiser_t = QPushButton("Actualiser")
    bouton_calculer_t = QPushButton("Lancer le test t")
    layout_choix_t.addWidget(QLabel("Colonne groupe :"))
    layout_choix_t.addWidget(combo_groupe_t)
    layout_choix_t.addWidget(QLabel("Colonne valeur :"))
    layout_choix_t.addWidget(combo_valeur_t)
    layout_choix_t.addWidget(QLabel("Groupe 1 :"))
    layout_choix_t.addWidget(combo_g1)
    layout_choix_t.addWidget(QLabel("Groupe 2 :"))
    layout_choix_t.addWidget(combo_g2)
    label_resultat_t = QLabel("Choisis une colonne catégorielle (groupe) et une colonne numérique (valeur).")
    label_resultat_t.setWordWrap(True)

    def gerer_actualisation_t():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            return
        colonnes_texte = list(donnees.select_dtypes(include="object").columns)
        colonnes_num = list(donnees.select_dtypes(include="number").columns)
        combo_groupe_t.clear()
        combo_valeur_t.clear()
        combo_groupe_t.addItems(colonnes_texte)
        combo_valeur_t.addItems(colonnes_num)

    def gerer_maj_groupes():
        donnees = obtenir_donnees_actuelles()
        colonne_groupe = combo_groupe_t.currentText()
        if donnees is None or not colonne_groupe:
            return
        valeurs_uniques = sorted(donnees[colonne_groupe].dropna().astype(str).unique())
        combo_g1.clear()
        combo_g2.clear()
        combo_g1.addItems(valeurs_uniques)
        combo_g2.addItems(valeurs_uniques)

    def gerer_calcul_t():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            QMessageBox.warning(onglet, "Erreur", "Importe d'abord des données.")
            return
        colonne_groupe, colonne_valeur = combo_groupe_t.currentText(), combo_valeur_t.currentText()
        groupe_1, groupe_2 = combo_g1.currentText(), combo_g2.currentText()
        if not all([colonne_groupe, colonne_valeur, groupe_1, groupe_2]) or groupe_1 == groupe_2:
            QMessageBox.information(onglet, "Info", "Choisis deux groupes différents.")
            return

        resultat = test_t_deux_groupes(donnees, colonne_groupe, colonne_valeur, groupe_1, groupe_2)
        conclusion = ("différence statistiquement significative (p < 0.05)" if resultat["significatif"]
                      else "pas de différence statistiquement significative (p ≥ 0.05)")
        label_resultat_t.setText(
            f"Moyenne {groupe_1} (n={resultat['n1']}) = {resultat['moyenne_1']:.3f}   |   "
            f"Moyenne {groupe_2} (n={resultat['n2']}) = {resultat['moyenne_2']:.3f}\n"
            f"Statistique t = {resultat['statistique_t']:.3f}   |   p-valeur = {resultat['p_valeur']:.4f}\n"
            f"Conclusion : {conclusion}"
        )

    bouton_actualiser_t.clicked.connect(gerer_actualisation_t)
    combo_groupe_t.currentTextChanged.connect(gerer_maj_groupes)
    bouton_calculer_t.clicked.connect(gerer_calcul_t)

    layout_t.addLayout(layout_choix_t)
    layout_t.addWidget(bouton_actualiser_t)
    layout_t.addWidget(bouton_calculer_t)
    layout_t.addWidget(label_resultat_t)
    groupe_t.setLayout(layout_t)

    # --- Test chi-deux ---
    groupe_chi2 = QGroupBox("Test du chi-deux (indépendance entre deux variables catégorielles)")
    layout_chi2 = QVBoxLayout()
    layout_choix_chi2 = QHBoxLayout()
    combo_var1 = QComboBox()
    combo_var2 = QComboBox()
    bouton_actualiser_chi2 = QPushButton("Actualiser")
    bouton_calculer_chi2 = QPushButton("Lancer le test chi-deux")
    layout_choix_chi2.addWidget(QLabel("Variable 1 :"))
    layout_choix_chi2.addWidget(combo_var1)
    layout_choix_chi2.addWidget(QLabel("Variable 2 :"))
    layout_choix_chi2.addWidget(combo_var2)
    label_resultat_chi2 = QLabel("Choisis deux colonnes catégorielles.")
    label_resultat_chi2.setWordWrap(True)

    def gerer_actualisation_chi2():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            return
        colonnes_texte = list(donnees.select_dtypes(include="object").columns)
        combo_var1.clear()
        combo_var2.clear()
        combo_var1.addItems(colonnes_texte)
        combo_var2.addItems(colonnes_texte)

    def gerer_calcul_chi2():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            QMessageBox.warning(onglet, "Erreur", "Importe d'abord des données.")
            return
        colonne_1, colonne_2 = combo_var1.currentText(), combo_var2.currentText()
        if not colonne_1 or not colonne_2 or colonne_1 == colonne_2:
            QMessageBox.information(onglet, "Info", "Choisis deux colonnes différentes.")
            return

        resultat = test_chi_deux(donnees, colonne_1, colonne_2)
        conclusion = ("les deux variables semblent liées (p < 0.05)" if resultat["significatif"]
                      else "pas de lien statistiquement significatif détecté (p ≥ 0.05)")
        label_resultat_chi2.setText(
            f"Statistique chi² = {resultat['statistique_chi2']:.3f}   |   "
            f"degrés de liberté = {resultat['degres_liberte']}   |   p-valeur = {resultat['p_valeur']:.4f}\n"
            f"Conclusion : {conclusion}"
        )

    bouton_actualiser_chi2.clicked.connect(gerer_actualisation_chi2)
    bouton_calculer_chi2.clicked.connect(gerer_calcul_chi2)

    layout_chi2.addLayout(layout_choix_chi2)
    layout_chi2.addWidget(bouton_actualiser_chi2)
    layout_chi2.addWidget(bouton_calculer_chi2)
    layout_chi2.addWidget(label_resultat_chi2)
    groupe_chi2.setLayout(layout_chi2)

    layout.addWidget(groupe_t)
    layout.addWidget(groupe_chi2)
    onglet.setLayout(layout)
    return onglet


# ---------- ONGLET SÉRIES TEMPORELLES ----------

def creer_onglet_series_temporelles(obtenir_donnees_actuelles):
    onglet = QWidget()
    layout = QVBoxLayout()

    label_info = QLabel(
        "Sélectionne plusieurs colonnes numériques représentant des périodes successives "
        "(ex: Population 2000, Population 2010, Population 2020) pour calculer la tendance générale."
    )
    label_info.setWordWrap(True)
    label_info.setStyleSheet("color: gray;")

    liste_colonnes = QComboBox()
    liste_colonnes.setPlaceholderText("Sélectionne les colonnes de périodes, une par une")

    layout_boutons = QHBoxLayout()
    bouton_actualiser = QPushButton("Actualiser les colonnes")
    bouton_ajouter = QPushButton("Ajouter cette période")
    bouton_calculer = QPushButton("Calculer la tendance")
    bouton_reinitialiser = QPushButton("Réinitialiser la sélection")
    layout_boutons.addWidget(bouton_actualiser)
    layout_boutons.addWidget(bouton_ajouter)
    layout_boutons.addWidget(bouton_calculer)
    layout_boutons.addWidget(bouton_reinitialiser)

    label_periodes_choisies = QLabel("Périodes sélectionnées : aucune")
    label_periodes_choisies.setWordWrap(True)

    label_resultat = QLabel("")
    label_resultat.setWordWrap(True)
    label_resultat.setStyleSheet("font-weight: bold;")

    figure = Figure(figsize=(6, 4))
    canvas = FigureCanvasQTAgg(figure)
    canvas.setMinimumHeight(320)

    periodes_selectionnees = {"liste": []}

    def gerer_actualisation():
        donnees = obtenir_donnees_actuelles()
        colonnes_num = list(donnees.select_dtypes(include="number").columns) if donnees is not None else []
        liste_colonnes.clear()
        liste_colonnes.addItems(colonnes_num)

    def gerer_ajout():
        colonne = liste_colonnes.currentText()
        if colonne and colonne not in periodes_selectionnees["liste"]:
            periodes_selectionnees["liste"].append(colonne)
            label_periodes_choisies.setText("Périodes sélectionnées : " + ", ".join(periodes_selectionnees["liste"]))

    def gerer_reinitialisation():
        periodes_selectionnees["liste"] = []
        label_periodes_choisies.setText("Périodes sélectionnées : aucune")

    def gerer_calcul():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            QMessageBox.warning(onglet, "Erreur", "Importe d'abord des données.")
            return
        if len(periodes_selectionnees["liste"]) < 3:
            QMessageBox.information(onglet, "Info", "Ajoute au moins 3 périodes pour calculer une tendance fiable.")
            return

        resultat = calculer_tendance_temporelle(donnees, periodes_selectionnees["liste"])

        sens = "croissante" if resultat["pente"] > 0 else "décroissante"
        label_resultat.setText(
            f"Tendance {sens} : {resultat['pente']:.2f} par période   |   "
            f"R² = {resultat['r_carre']:.4f} (qualité de l'ajustement)"
        )

        figure.clear()
        ax = figure.add_subplot(111)
        ax.plot(resultat["periodes"], resultat["valeurs"], marker="o", label="Valeurs observées")
        ax.plot(resultat["periodes"], resultat["tendance"], linestyle="--", color="red", label="Tendance (MCO)")
        ax.set_title("Évolution et tendance")
        ax.legend()
        ax.tick_params(axis="x", rotation=30)
        figure.tight_layout()
        canvas.draw()

    bouton_actualiser.clicked.connect(gerer_actualisation)
    bouton_ajouter.clicked.connect(gerer_ajout)
    bouton_reinitialiser.clicked.connect(gerer_reinitialisation)
    bouton_calculer.clicked.connect(gerer_calcul)

    layout.addWidget(label_info)
    layout.addWidget(liste_colonnes)
    layout.addLayout(layout_boutons)
    layout.addWidget(label_periodes_choisies)
    layout.addWidget(label_resultat)
    layout.addWidget(canvas)
    onglet.setLayout(layout)
    return onglet


# ---------- PAGE COMPLÈTE ----------

# ---------- ANOVA ----------

def creer_onglet_anova(obtenir_donnees_actuelles):
    onglet = QWidget()
    layout = QVBoxLayout()

    layout_choix = QHBoxLayout()
    combo_groupe = QComboBox()
    combo_valeur = QComboBox()
    bouton_actualiser = QPushButton("Actualiser les colonnes")
    bouton_calculer = QPushButton("Lancer l'ANOVA")
    layout_choix.addWidget(QLabel("Colonne groupe (catégorielle) :"))
    layout_choix.addWidget(combo_groupe)
    layout_choix.addWidget(QLabel("Colonne valeur (numérique) :"))
    layout_choix.addWidget(combo_valeur)
    layout_choix.addWidget(bouton_actualiser)
    layout_choix.addWidget(bouton_calculer)

    label_resultat = QLabel(
        "L'ANOVA compare les moyennes de plusieurs groupes (3 ou plus) pour voir si au moins "
        "un groupe se distingue significativement des autres."
    )
    label_resultat.setWordWrap(True)

    tableau_resultat = QTableWidget()
    tableau_resultat.setMinimumHeight(150)

    def gerer_actualisation():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            return
        combo_groupe.clear()
        combo_groupe.addItems(list(donnees.select_dtypes(include="object").columns))
        combo_valeur.clear()
        combo_valeur.addItems(list(donnees.select_dtypes(include="number").columns))

    def gerer_calcul():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            QMessageBox.warning(onglet, "Erreur", "Importe d'abord des données.")
            return
        colonne_groupe, colonne_valeur = combo_groupe.currentText(), combo_valeur.currentText()
        if not colonne_groupe or not colonne_valeur:
            return

        sous_ensemble = donnees[[colonne_groupe, colonne_valeur]].dropna().copy()
        sous_ensemble.columns = ["groupe", "valeur"]
        nb_groupes = sous_ensemble["groupe"].nunique()
        if nb_groupes < 2:
            QMessageBox.information(onglet, "Info", "Il faut au moins 2 groupes distincts.")
            return

        try:
            modele = ols("valeur ~ C(groupe)", data=sous_ensemble).fit()
            table_anova = anova_lm(modele, typ=2)
        except Exception as erreur:
            QMessageBox.critical(onglet, "Erreur", f"Impossible de calculer l'ANOVA :\n{erreur}")
            return

        f_valeur = table_anova["F"].iloc[0]
        p_valeur = table_anova["PR(>F)"].iloc[0]
        conclusion = ("différence significative entre les groupes (p < 0.05)" if p_valeur < 0.05
                      else "pas de différence significative détectée (p ≥ 0.05)")
        label_resultat.setText(
            f"Statistique F = {f_valeur:.3f}   |   p-valeur = {p_valeur:.4f}\nConclusion : {conclusion}"
        )
        remplir_tableau_dataframe(tableau_resultat, table_anova.round(4), inclure_index=True)

    bouton_actualiser.clicked.connect(gerer_actualisation)
    bouton_calculer.clicked.connect(gerer_calcul)

    layout.addLayout(layout_choix)
    layout.addWidget(label_resultat)
    layout.addWidget(tableau_resultat)
    onglet.setLayout(layout)
    return onglet


# ---------- RÉGRESSION LOGISTIQUE ----------

def creer_onglet_regression_logistique(obtenir_donnees_actuelles):
    onglet = QWidget()
    layout = QVBoxLayout()

    layout_choix = QHBoxLayout()
    combo_y = QComboBox()
    liste_x = QListWidget()
    liste_x.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
    liste_x.setMaximumHeight(100)
    bouton_actualiser = QPushButton("Actualiser les colonnes")
    bouton_calculer = QPushButton("Lancer la régression logistique")

    layout_y = QVBoxLayout()
    layout_y.addWidget(QLabel("Variable à expliquer (0/1 ou deux catégories) :"))
    layout_y.addWidget(combo_y)
    layout_x = QVBoxLayout()
    layout_x.addWidget(QLabel("Variables explicatives (numériques, sélection multiple) :"))
    layout_x.addWidget(liste_x)

    layout_choix.addLayout(layout_y)
    layout_choix.addLayout(layout_x)

    label_resultat = QLabel(
        "La régression logistique explique une variable à 2 catégories (ex : Oui/Non) "
        "à partir d'une ou plusieurs variables numériques."
    )
    label_resultat.setWordWrap(True)

    tableau_resultat = QTableWidget()
    tableau_resultat.setMinimumHeight(150)

    def gerer_actualisation():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            return
        combo_y.clear()
        combo_y.addItems(list(donnees.columns))
        liste_x.clear()
        liste_x.addItems(list(donnees.select_dtypes(include="number").columns))

    def gerer_calcul():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            QMessageBox.warning(onglet, "Erreur", "Importe d'abord des données.")
            return
        colonne_y = combo_y.currentText()
        colonnes_x = [item.text() for item in liste_x.selectedItems()]
        if not colonne_y or not colonnes_x:
            QMessageBox.information(onglet, "Info", "Choisis Y et au moins une variable explicative.")
            return

        sous_ensemble = donnees[[colonne_y] + colonnes_x].dropna()
        valeurs_uniques = sous_ensemble[colonne_y].unique()
        if len(valeurs_uniques) != 2:
            QMessageBox.information(onglet, "Info",
                                     "La variable à expliquer doit avoir exactement 2 catégories.")
            return

        y = (sous_ensemble[colonne_y] == valeurs_uniques[0]).astype(int)
        X = sous_ensemble[colonnes_x]

        try:
            modele = LogisticRegression(max_iter=1000)
            modele.fit(X, y)
            score = modele.score(X, y)
        except Exception as erreur:
            QMessageBox.critical(onglet, "Erreur", f"Impossible de calculer la régression :\n{erreur}")
            return

        label_resultat.setText(
            f"Précision du modèle sur les données : {score * 100:.1f}%   "
            f"(prédit '{valeurs_uniques[0]}' vs '{valeurs_uniques[1]}')\n"
            f"Un coefficient positif augmente la probabilité de '{valeurs_uniques[0]}'."
        )

        resultat = pd.DataFrame({
            "Variable": colonnes_x,
            "Coefficient": modele.coef_[0].round(4),
        })
        remplir_tableau_dataframe(tableau_resultat, resultat.set_index("Variable"), inclure_index=True)

    bouton_actualiser.clicked.connect(gerer_actualisation)
    bouton_calculer.clicked.connect(gerer_calcul)

    layout.addLayout(layout_choix)
    layout.addWidget(bouton_actualiser)
    layout.addWidget(bouton_calculer)
    layout.addWidget(label_resultat)
    layout.addWidget(tableau_resultat)
    onglet.setLayout(layout)
    return onglet


# ---------- ACP (ANALYSE EN COMPOSANTES PRINCIPALES) ----------

def creer_onglet_acp(obtenir_donnees_actuelles):
    onglet = QWidget()
    layout = QVBoxLayout()

    liste_variables = QListWidget()
    liste_variables.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
    liste_variables.setMaximumHeight(120)
    bouton_actualiser = QPushButton("Actualiser les colonnes")
    bouton_calculer = QPushButton("Lancer l'ACP")

    label_resultat = QLabel(
        "L'ACP résume plusieurs variables numériques en 2 axes principaux, pour visualiser "
        "la structure globale des données."
    )
    label_resultat.setWordWrap(True)

    figure = Figure(figsize=(5, 4))
    canvas = FigureCanvasQTAgg(figure)
    canvas.setMinimumHeight(320)

    def gerer_actualisation():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            return
        liste_variables.clear()
        liste_variables.addItems(list(donnees.select_dtypes(include="number").columns))

    def gerer_calcul():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            QMessageBox.warning(onglet, "Erreur", "Importe d'abord des données.")
            return
        colonnes = [item.text() for item in liste_variables.selectedItems()]
        if len(colonnes) < 2:
            QMessageBox.information(onglet, "Info", "Choisis au moins 2 variables numériques.")
            return

        sous_ensemble = donnees[colonnes].dropna()
        if sous_ensemble.shape[0] < 3:
            QMessageBox.information(onglet, "Info", "Pas assez de lignes complètes pour calculer une ACP.")
            return

        try:
            donnees_normalisees = StandardScaler().fit_transform(sous_ensemble)
            acp = PCA(n_components=2)
            composantes = acp.fit_transform(donnees_normalisees)
            variance_expliquee = acp.explained_variance_ratio_
        except Exception as erreur:
            QMessageBox.critical(onglet, "Erreur", f"Impossible de calculer l'ACP :\n{erreur}")
            return

        label_resultat.setText(
            f"Axe 1 explique {variance_expliquee[0]*100:.1f}% de la variance, "
            f"Axe 2 explique {variance_expliquee[1]*100:.1f}% "
            f"(ensemble : {(variance_expliquee[0]+variance_expliquee[1])*100:.1f}%)."
        )

        figure.clear()
        ax = figure.add_subplot(111)
        ax.scatter(composantes[:, 0], composantes[:, 1], alpha=0.6, color="#2563EB")
        ax.set_xlabel("Axe 1")
        ax.set_ylabel("Axe 2")
        ax.set_title("Projection ACP")
        ax.axhline(0, color="gray", linewidth=0.5)
        ax.axvline(0, color="gray", linewidth=0.5)
        figure.tight_layout()
        canvas.draw()

    bouton_actualiser.clicked.connect(gerer_actualisation)
    bouton_calculer.clicked.connect(gerer_calcul)

    layout.addWidget(QLabel("Variables numériques à inclure (sélection multiple) :"))
    layout.addWidget(liste_variables)
    layout.addWidget(bouton_actualiser)
    layout.addWidget(bouton_calculer)
    layout.addWidget(label_resultat)
    layout.addWidget(canvas)
    onglet.setLayout(layout)
    return onglet


# ---------- CLASSIFICATION (K-MEANS) ----------

def creer_onglet_classification(obtenir_donnees_actuelles):
    onglet = QWidget()
    layout = QVBoxLayout()

    liste_variables = QListWidget()
    liste_variables.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
    liste_variables.setMaximumHeight(120)

    layout_choix = QHBoxLayout()
    label_nb_groupes = QLabel("Nombre de groupes :")
    spin_nb_groupes = QSpinBox()
    spin_nb_groupes.setRange(2, 10)
    spin_nb_groupes.setValue(3)
    bouton_actualiser = QPushButton("Actualiser les colonnes")
    bouton_calculer = QPushButton("Lancer la classification")
    layout_choix.addWidget(label_nb_groupes)
    layout_choix.addWidget(spin_nb_groupes)
    layout_choix.addWidget(bouton_actualiser)
    layout_choix.addWidget(bouton_calculer)

    label_resultat = QLabel(
        "La classification (K-means) regroupe automatiquement les lignes qui se ressemblent "
        "en un nombre choisi de groupes."
    )
    label_resultat.setWordWrap(True)

    figure = Figure(figsize=(5, 4))
    canvas = FigureCanvasQTAgg(figure)
    canvas.setMinimumHeight(320)

    def gerer_actualisation():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            return
        liste_variables.clear()
        liste_variables.addItems(list(donnees.select_dtypes(include="number").columns))

    def gerer_calcul():
        donnees = obtenir_donnees_actuelles()
        if donnees is None:
            QMessageBox.warning(onglet, "Erreur", "Importe d'abord des données.")
            return
        colonnes = [item.text() for item in liste_variables.selectedItems()]
        if len(colonnes) < 2:
            QMessageBox.information(onglet, "Info", "Choisis au moins 2 variables numériques.")
            return

        sous_ensemble = donnees[colonnes].dropna()
        nb_groupes = spin_nb_groupes.value()
        if sous_ensemble.shape[0] < nb_groupes:
            QMessageBox.information(onglet, "Info", "Pas assez de lignes pour ce nombre de groupes.")
            return

        try:
            donnees_normalisees = StandardScaler().fit_transform(sous_ensemble)
            modele = KMeans(n_clusters=nb_groupes, n_init=10, random_state=0)
            groupes = modele.fit_predict(donnees_normalisees)
        except Exception as erreur:
            QMessageBox.critical(onglet, "Erreur", f"Impossible de calculer la classification :\n{erreur}")
            return

        tailles = pd.Series(groupes).value_counts().sort_index()
        label_resultat.setText(
            "Taille de chaque groupe : " + ", ".join(f"Groupe {i} : {n}" for i, n in tailles.items())
        )

        figure.clear()
        ax = figure.add_subplot(111)
        nuage = ax.scatter(sous_ensemble.iloc[:, 0], sous_ensemble.iloc[:, 1], c=groupes, cmap="tab10", alpha=0.7)
        ax.set_xlabel(colonnes[0])
        ax.set_ylabel(colonnes[1])
        ax.set_title(f"Classification en {nb_groupes} groupes")
        figure.tight_layout()
        canvas.draw()

    bouton_actualiser.clicked.connect(gerer_actualisation)
    bouton_calculer.clicked.connect(gerer_calcul)

    layout.addWidget(QLabel("Variables numériques à inclure (sélection multiple) :"))
    layout.addWidget(liste_variables)
    layout.addLayout(layout_choix)
    layout.addWidget(label_resultat)
    layout.addWidget(canvas)
    onglet.setLayout(layout)
    return onglet


def creer_page_analyse_avancee(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import,
                                 onglet_descriptif=None):
    """Assemble la page Analyse statistique avancée avec ses onglets."""
    page = QWidget()
    layout_principal = QVBoxLayout()
    layout_principal.setContentsMargins(15, 15, 15, 15)

    entete = QLabel("Accueil > Analyse statistique avancée")
    entete.setStyleSheet("color: gray; font-size: 11px;")

    onglets = QTabWidget()
    if onglet_descriptif is not None:
        onglets.addTab(onglet_descriptif, "Statistiques descriptives")
    onglets.addTab(creer_onglet_correlation(obtenir_donnees_actuelles), "Corrélation")
    onglets.addTab(creer_onglet_regression(obtenir_donnees_actuelles), "Régression")
    onglets.addTab(creer_onglet_tests(obtenir_donnees_actuelles), "Tests d'hypothèses")
    onglets.addTab(creer_onglet_series_temporelles(obtenir_donnees_actuelles), "Séries temporelles")
    onglets.addTab(creer_onglet_anova(obtenir_donnees_actuelles), "ANOVA")
    onglets.addTab(creer_onglet_regression_logistique(obtenir_donnees_actuelles), "Régression logistique")
    onglets.addTab(creer_onglet_acp(obtenir_donnees_actuelles), "ACP")
    onglets.addTab(creer_onglet_classification(obtenir_donnees_actuelles), "Classification")
    onglets.addTab(creer_onglet_anova(obtenir_donnees_actuelles), "ANOVA")
    onglets.addTab(creer_onglet_regression_logistique(obtenir_donnees_actuelles), "Régression logistique")
    onglets.addTab(creer_onglet_acp(obtenir_donnees_actuelles), "ACP")
    onglets.addTab(creer_onglet_classification(obtenir_donnees_actuelles), "Classification")

    layout_principal.addWidget(entete)
    layout_principal.addWidget(onglets)
    page.setLayout(layout_principal)

    zone_defilement = QScrollArea()
    zone_defilement.setWidgetResizable(True)
    zone_defilement.setWidget(page)
    return zone_defilement