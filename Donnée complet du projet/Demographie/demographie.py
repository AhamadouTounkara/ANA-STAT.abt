from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QGroupBox,
    QFileDialog, QMessageBox, QFrame, QScrollArea, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QSplitter, QStackedWidget
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import pandas as pd
from Export.export_avance import exporter_pdf, exporter_powerpoint, exporter_word, exporter_image, imprimer_widget, exporter_excel

# Noms de colonnes qu'on cherche à détecter automatiquement dans le fichier importé.
# Si une colonne dont le nom contient un de ces mots existe, le filtre devient actif.
CORRESPONDANCES_FILTRES = {
    "Région": ["region", "région"],
    "Cercle": ["cercle"],
    "Commune": ["commune"],
    "Village": ["village"],
    "Sexe": ["sexe", "sex"],
    "Âge": ["age", "âge"],
    "Année": ["annee", "année", "year"],
    "Période": ["periode", "période"],
}

ANALYSES_DISPONIBLES = [
    "Population totale",
    "Structure par âge",
    "Répartition par sexe",
    "Natalité",
    "Mortalité",
    "Fécondité",
    "Espérance de vie",
    "Migration",
    "Densité de population",
    "Croissance démographique",
    "Projection de population",
    "Pyramide des âges",
]


# ---------- FONCTIONS DE CALCUL ----------

def trouver_colonne_correspondante(donnees, mots_cles):
    """Cherche une colonne dont le nom contient un des mots-clés donnés."""
    if donnees is None:
        return None
    for colonne in donnees.columns:
        for mot in mots_cles:
            if mot.lower() in colonne.lower():
                return colonne
    return None


def calculer_population_totale(donnees, colonne_population):
    """Calcule la population totale (somme) sur la colonne choisie."""
    return donnees[colonne_population].sum()


def calculer_taux_croissance_global(donnees, colonne_debut, colonne_fin):
    """Calcule le taux de croissance global entre deux colonnes d'années."""
    total_debut = donnees[colonne_debut].sum()
    total_fin = donnees[colonne_fin].sum()
    if total_debut == 0:
        return 0
    return (total_fin - total_debut) / total_debut * 100


def calculer_indicateurs_cles(donnees):
    """Calcule les 5 indicateurs clés affichés en haut de page, quand c'est possible."""
    indicateurs = {
        "Population": "N/D",
        "Naissances": "N/D",
        "Décès": "N/D",
        "Migration": "N/D",
        "Croissance": "N/D",
    }

    if donnees is None:
        return indicateurs

    colonnes_numeriques = list(donnees.select_dtypes(include="number").columns)
    colonnes_population = [c for c in colonnes_numeriques if "population" in c.lower()]

    if colonnes_population:
        colonne_recente = colonnes_population[0]
        total = calculer_population_totale(donnees, colonne_recente)
        indicateurs["Population"] = f"{total:,.0f}".replace(",", " ")

        if len(colonnes_population) >= 2:
            taux = calculer_taux_croissance_global(donnees, colonnes_population[-1], colonnes_population[0])
            indicateurs["Croissance"] = f"{taux:.2f} %"

    colonne_naissances = trouver_colonne_correspondante(donnees, ["naissance", "birth"])
    if colonne_naissances:
        indicateurs["Naissances"] = f"{donnees[colonne_naissances].sum():,.0f}".replace(",", " ")

    colonne_deces = trouver_colonne_correspondante(donnees, ["deces", "décès", "death"])
    if colonne_deces:
        indicateurs["Décès"] = f"{donnees[colonne_deces].sum():,.0f}".replace(",", " ")

    colonne_migration = trouver_colonne_correspondante(donnees, ["migration"])
    if colonne_migration:
        indicateurs["Migration"] = f"{donnees[colonne_migration].sum():,.0f}".replace(",", " ")

    return indicateurs


def remplir_tableau_resultat(tableau, dataframe_resultat):
    """Affiche un DataFrame pandas dans un QTableWidget."""
    tableau.setRowCount(dataframe_resultat.shape[0])
    tableau.setColumnCount(dataframe_resultat.shape[1])
    tableau.setHorizontalHeaderLabels(dataframe_resultat.columns.astype(str))
    tableau.verticalHeader().setVisible(False)

    for ligne in range(dataframe_resultat.shape[0]):
        for colonne in range(dataframe_resultat.shape[1]):
            valeur = dataframe_resultat.iloc[ligne, colonne]
            texte = f"{valeur:.2f}" if isinstance(valeur, float) else str(valeur)
            tableau.setItem(ligne, colonne, QTableWidgetItem(texte))


def calculer_densite_population(donnees, colonne_pays, colonne_population, colonne_superficie):
    """Calcule la densité de population (habitants par km²) pour chaque pays."""
    resultat = donnees[[colonne_pays, colonne_population, colonne_superficie]].copy().dropna()
    resultat = resultat[resultat[colonne_superficie] > 0]
    resultat["Densité (hab/km²)"] = resultat[colonne_population] / resultat[colonne_superficie]
    return resultat.sort_values(by="Densité (hab/km²)", ascending=False)


def calculer_taux_natalite(donnees, colonne_pays, colonne_population, colonne_naissances):
    """Calcule le taux de natalité (naissances pour 1000 habitants) pour chaque pays."""
    resultat = donnees[[colonne_pays, colonne_population, colonne_naissances]].copy().dropna()
    resultat = resultat[resultat[colonne_population] > 0]
    resultat["Taux de natalité (‰)"] = resultat[colonne_naissances] / resultat[colonne_population] * 1000
    return resultat.sort_values(by="Taux de natalité (‰)", ascending=False)


def calculer_taux_mortalite(donnees, colonne_pays, colonne_population, colonne_deces):
    """Calcule le taux de mortalité (décès pour 1000 habitants) pour chaque pays."""
    resultat = donnees[[colonne_pays, colonne_population, colonne_deces]].copy().dropna()
    resultat = resultat[resultat[colonne_population] > 0]
    resultat["Taux de mortalité (‰)"] = resultat[colonne_deces] / resultat[colonne_population] * 1000
    return resultat.sort_values(by="Taux de mortalité (‰)", ascending=False)


def calculer_taux_migration(donnees, colonne_pays, colonne_population, colonne_migration):
    """Calcule le taux de migration nette (pour 1000 habitants) pour chaque pays."""
    resultat = donnees[[colonne_pays, colonne_population, colonne_migration]].copy().dropna()
    resultat = resultat[resultat[colonne_population] > 0]
    resultat["Taux de migration (‰)"] = resultat[colonne_migration] / resultat[colonne_population] * 1000
    return resultat.sort_values(by="Taux de migration (‰)", ascending=False)


def calculer_esperance_vie(donnees, colonne_pays, colonne_esperance_vie):
    """Classe les pays selon leur espérance de vie."""
    resultat = donnees[[colonne_pays, colonne_esperance_vie]].copy().dropna()
    return resultat.sort_values(by=colonne_esperance_vie, ascending=False)


def calculer_structure_age(donnees, colonne_age, colonne_effectif):
    """Regroupe l'effectif de population par tranche d'âge."""
    resultat = donnees.groupby(colonne_age)[colonne_effectif].sum().reset_index()
    return resultat.sort_values(by=colonne_age)


def calculer_repartition_sexe(donnees, colonne_sexe, colonne_effectif):
    """Regroupe l'effectif de population par sexe."""
    resultat = donnees.groupby(colonne_sexe)[colonne_effectif].sum().reset_index()
    return resultat


def calculer_pyramide_ages(donnees, colonne_age, colonne_sexe, colonne_effectif):
    """Prépare les données pour une pyramide des âges (effectif par âge et par sexe)."""
    resultat = donnees.groupby([colonne_age, colonne_sexe])[colonne_effectif].sum().reset_index()
    return resultat


def calculer_projection_population(donnees, colonne_pays, colonne_debut, colonne_fin, annees_ecart, annees_projection=5):
    """Projette la population future en appliquant le taux de croissance observé."""
    resultat = donnees[[colonne_pays, colonne_debut, colonne_fin]].copy().dropna()
    resultat = resultat[resultat[colonne_debut] > 0]
    taux_annuel = (resultat[colonne_fin] / resultat[colonne_debut]) ** (1 / annees_ecart) - 1
    resultat[f"Population projetée (+{annees_projection} ans)"] = (
        resultat[colonne_fin] * (1 + taux_annuel) ** annees_projection
    )
    return resultat.sort_values(by=f"Population projetée (+{annees_projection} ans)", ascending=False)



# ---------- ARBORESCENCE DES ANALYSES (structure fournie) ----------

CATEGORIES_ANALYSES = {
    "Population": ["Population totale", "Population moyenne", "Densité", "Répartition par sexe",
                   "Répartition par âge", "Population urbaine", "Population rurale"],
    "Natalité": ["Taux brut de natalité", "Taux spécifique de natalité", "Taux général de fécondité",
                 "Nombre de naissances", "Analyse des naissances"],
    "Mortalité": ["Taux brut de mortalité", "Mortalité infantile", "Mortalité maternelle",
                  "Mortalité par âge", "Mortalité par sexe", "Espérance de vie"],
    "Fécondité": ["ISF", "Taux de fécondité", "Fécondité par âge", "Descendance finale", "Analyse comparative"],
    "Migration": ["Immigration", "Émigration", "Solde migratoire", "Migration interne", "Migration internationale"],
    "Nuptialité": ["Mariages", "Divorces", "Célibataires", "Veuvage", "Situation matrimoniale"],
    "Structure": ["Pyramide des âges", "Structure par sexe", "Groupes d'âge",
                  "Rapport de masculinité", "Rapport de dépendance"],
    "Projections": ["Projection de population", "Projection des ménages", "Projection des naissances",
                     "Projection des décès", "Projection migratoire"],
    "Indicateurs démographiques": ["Accroissement naturel", "Accroissement total", "Taux d'accroissement",
                                    "Âge moyen", "Âge médian", "Temps de doublement", "Tous les indicateurs"],
}


# ---------- FONCTIONS DE CALCUL GÉNÉRIQUES SUPPLÉMENTAIRES ----------

def calculer_taux(donnees, colonne_categorie, colonne_numerateur, colonne_denominateur, facteur, nom_resultat):
    """Calcule un taux générique : (numérateur / dénominateur) × facteur, pour chaque ligne."""
    resultat = donnees[[colonne_categorie, colonne_numerateur, colonne_denominateur]].copy().dropna()
    resultat = resultat[resultat[colonne_denominateur] > 0]
    resultat[nom_resultat] = resultat[colonne_numerateur] / resultat[colonne_denominateur] * facteur
    return resultat.sort_values(by=nom_resultat, ascending=False)


def calculer_classement_direct(donnees, colonne_categorie, colonne_valeur):
    """Classe simplement les lignes selon une colonne, sans calcul de taux."""
    resultat = donnees[[colonne_categorie, colonne_valeur]].copy().dropna()
    return resultat.sort_values(by=colonne_valeur, ascending=False)


def calculer_solde(donnees, colonne_categorie, colonne_entrees, colonne_sorties, nom_resultat):
    """Calcule un solde : entrées moins sorties (utilisé pour le solde migratoire notamment)."""
    resultat = donnees[[colonne_categorie, colonne_entrees, colonne_sorties]].copy().dropna()
    resultat[nom_resultat] = resultat[colonne_entrees] - resultat[colonne_sorties]
    return resultat.sort_values(by=nom_resultat, ascending=False)


def calculer_repartition_par_categorie(donnees, colonne_categorie, colonne_effectif):
    """Regroupe et somme un effectif par catégorie (sexe, statut matrimonial, groupe d'âge...)."""
    resultat = donnees.groupby(colonne_categorie)[colonne_effectif].sum().reset_index()
    return resultat.sort_values(by=colonne_effectif, ascending=False)


def calculer_rapport_masculinite(donnees, colonne_sexe, colonne_effectif):
    """Calcule le rapport de masculinité : (hommes / femmes) × 100."""
    repartition = donnees.groupby(colonne_sexe)[colonne_effectif].sum()
    cle_hommes = next((c for c in repartition.index if str(c).lower().startswith(("h", "m"))), None)
    cle_femmes = next((c for c in repartition.index if str(c).lower().startswith("f")), None)
    if cle_hommes is None or cle_femmes is None or repartition[cle_femmes] == 0:
        return None
    rapport = repartition[cle_hommes] / repartition[cle_femmes] * 100
    return pd.DataFrame({"Indicateur": ["Rapport de masculinité (hommes pour 100 femmes)"], "Valeur": [rapport]})


def calculer_age_moyen(donnees, colonne_age, colonne_effectif):
    """Calcule l'âge moyen pondéré par l'effectif de chaque tranche d'âge."""
    sous_ensemble = donnees[[colonne_age, colonne_effectif]].copy().dropna()
    sous_ensemble[colonne_age] = pd.to_numeric(sous_ensemble[colonne_age], errors="coerce")
    sous_ensemble = sous_ensemble.dropna()
    if sous_ensemble[colonne_effectif].sum() == 0 or sous_ensemble.empty:
        return None
    age_moyen = (sous_ensemble[colonne_age] * sous_ensemble[colonne_effectif]).sum() / sous_ensemble[colonne_effectif].sum()
    return pd.DataFrame({"Indicateur": ["Âge moyen"], "Valeur": [round(age_moyen, 2)]})


def calculer_age_median(donnees, colonne_age, colonne_effectif):
    """Calcule l'âge médian à partir d'une répartition par âge et effectif."""
    sous_ensemble = donnees[[colonne_age, colonne_effectif]].copy().dropna()
    sous_ensemble[colonne_age] = pd.to_numeric(sous_ensemble[colonne_age], errors="coerce")
    sous_ensemble = sous_ensemble.dropna().sort_values(by=colonne_age)
    if sous_ensemble.empty:
        return None
    effectifs_cumules = sous_ensemble[colonne_effectif].cumsum()
    moitie = sous_ensemble[colonne_effectif].sum() / 2
    ligne_mediane = sous_ensemble[effectifs_cumules >= moitie].iloc[0]
    return pd.DataFrame({"Indicateur": ["Âge médian"], "Valeur": [ligne_mediane[colonne_age]]})


def calculer_accroissement_naturel(donnees, colonne_naissances, colonne_deces, colonne_population):
    """Calcule le taux d'accroissement naturel : (naissances - décès) / population × 100."""
    total_naissances = donnees[colonne_naissances].sum()
    total_deces = donnees[colonne_deces].sum()
    total_population = donnees[colonne_population].sum()
    if total_population == 0:
        return None
    taux = (total_naissances - total_deces) / total_population * 100
    return pd.DataFrame({"Indicateur": ["Taux d'accroissement naturel (%)"], "Valeur": [round(taux, 3)]})


def calculer_temps_doublement(taux_accroissement_pourcentage):
    """Calcule le temps de doublement de la population selon la règle logarithmique : ln(2) / taux."""
    import math
    if taux_accroissement_pourcentage is None or taux_accroissement_pourcentage <= 0:
        return None
    annees = math.log(2) / (taux_accroissement_pourcentage / 100)
    return pd.DataFrame({"Indicateur": ["Temps de doublement estimé (années)"], "Valeur": [round(annees, 1)]})


# ---------- CONFIGURATION DES ~50 INDICATEURS (colonnes attendues + formule) ----------
# Chaque indicateur définit : ses colonnes de saisie, sa "famille" de calcul, et les mots-clés
# utilisés pour le bouton optionnel "Remplir depuis mes données importées".

INDICATEURS_CONFIG = {
    # ---- Population ----
    "Population totale": {"colonnes": ["Catégorie", "Population"], "famille": "classement",
                           "mots_cles": {"Population": ["population"]}},
    "Population moyenne": {"colonnes": ["Population"], "famille": "moyenne_simple",
                            "mots_cles": {"Population": ["population"]}},
    "Densité": {"colonnes": ["Catégorie", "Population", "Superficie"], "famille": "densite",
                "mots_cles": {"Population": ["population"], "Superficie": ["superficie", "area", "km2"]}},
    "Répartition par sexe": {"colonnes": ["Sexe", "Population"], "famille": "classement",
                              "mots_cles": {"Population": ["population"]}},
    "Répartition par âge": {"colonnes": ["Tranche d'âge", "Population"], "famille": "classement",
                             "mots_cles": {"Population": ["population"]}},
    "Population urbaine": {"colonnes": ["Zone", "Population"], "famille": "classement",
                            "mots_cles": {"Population": ["population"]}},
    "Population rurale": {"colonnes": ["Zone", "Population"], "famille": "classement",
                           "mots_cles": {"Population": ["population"]}},

    # ---- Natalité ----
    "Taux brut de natalité": {"colonnes": ["Catégorie", "Naissances", "Population"], "famille": "taux",
                               "facteur": 1000, "nom_taux": "Taux (‰)",
                               "mots_cles": {"Naissances": ["naissance", "birth"], "Population": ["population"]}},
    "Taux spécifique de natalité": {"colonnes": ["Tranche d'âge", "Naissances", "Population"], "famille": "taux",
                                     "facteur": 1000, "nom_taux": "Taux (‰)",
                                     "mots_cles": {"Naissances": ["naissance"], "Population": ["population"]}},
    "Taux général de fécondité": {"colonnes": ["Catégorie", "Naissances", "Population féminine 15-49 ans"],
                                   "famille": "taux", "facteur": 1000, "nom_taux": "Taux (‰)",
                                   "mots_cles": {"Naissances": ["naissance"], "Population féminine 15-49 ans": ["femme"]}},
    "Nombre de naissances": {"colonnes": ["Catégorie", "Naissances"], "famille": "classement",
                              "mots_cles": {"Naissances": ["naissance"]}},
    "Analyse des naissances": {"colonnes": ["Période", "Naissances"], "famille": "classement",
                                "mots_cles": {"Naissances": ["naissance"]}},

    # ---- Mortalité ----
    "Taux brut de mortalité": {"colonnes": ["Catégorie", "Décès", "Population"], "famille": "taux",
                                "facteur": 1000, "nom_taux": "Taux (‰)",
                                "mots_cles": {"Décès": ["deces", "décès", "death"], "Population": ["population"]}},
    "Mortalité infantile": {"colonnes": ["Catégorie", "Décès d'enfants -1 an", "Naissances vivantes"],
                             "famille": "taux", "facteur": 1000, "nom_taux": "Taux (‰)",
                             "mots_cles": {"Naissances vivantes": ["naissance"]}},
    "Mortalité maternelle": {"colonnes": ["Catégorie", "Décès maternels", "Naissances vivantes"],
                              "famille": "taux", "facteur": 100000, "nom_taux": "Taux (pour 100 000)",
                              "mots_cles": {"Naissances vivantes": ["naissance"]}},
    "Mortalité par âge": {"colonnes": ["Tranche d'âge", "Décès"], "famille": "classement",
                           "mots_cles": {"Décès": ["deces", "décès"]}},
    "Mortalité par sexe": {"colonnes": ["Sexe", "Décès"], "famille": "classement",
                            "mots_cles": {"Décès": ["deces", "décès"]}},
    "Espérance de vie": {"colonnes": ["Catégorie", "Espérance de vie (ans)"], "famille": "classement",
                          "mots_cles": {"Espérance de vie (ans)": ["esperance", "espérance"]}},

    # ---- Fécondité ----
    "ISF": {"colonnes": ["Catégorie", "ISF"], "famille": "classement",
            "mots_cles": {"ISF": ["isf", "fecondite", "fécondité"]}},
    "Taux de fécondité": {"colonnes": ["Catégorie", "Naissances", "Population féminine 15-49 ans"],
                           "famille": "taux", "facteur": 1000, "nom_taux": "Taux (‰)",
                           "mots_cles": {"Naissances": ["naissance"], "Population féminine 15-49 ans": ["femme"]}},
    "Fécondité par âge": {"colonnes": ["Tranche d'âge", "ISF"], "famille": "classement",
                           "mots_cles": {"ISF": ["isf", "fecondite"]}},
    "Descendance finale": {"colonnes": ["Catégorie", "Descendance finale"], "famille": "classement",
                            "mots_cles": {"Descendance finale": ["descendance"]}},
    "Analyse comparative": {"colonnes": ["Catégorie", "ISF"], "famille": "classement",
                             "mots_cles": {"ISF": ["isf", "fecondite"]}},

    # ---- Migration ----
    "Immigration": {"colonnes": ["Catégorie", "Immigrants"], "famille": "classement",
                     "mots_cles": {"Immigrants": ["immigration"]}},
    "Émigration": {"colonnes": ["Catégorie", "Émigrants"], "famille": "classement",
                    "mots_cles": {"Émigrants": ["emigration", "émigration"]}},
    "Solde migratoire": {"colonnes": ["Catégorie", "Immigrants", "Émigrants"], "famille": "solde",
                          "nom_resultat": "Solde migratoire",
                          "mots_cles": {"Immigrants": ["immigration"], "Émigrants": ["emigration", "émigration"]}},
    "Migration interne": {"colonnes": ["Catégorie", "Migrants internes"], "famille": "classement",
                           "mots_cles": {"Migrants internes": ["migration interne"]}},
    "Migration internationale": {"colonnes": ["Catégorie", "Migrants internationaux"], "famille": "classement",
                                  "mots_cles": {"Migrants internationaux": ["migration internationale"]}},

    # ---- Nuptialité ----
    "Mariages": {"colonnes": ["Catégorie", "Mariages"], "famille": "classement",
                 "mots_cles": {"Mariages": ["mariage"]}},
    "Divorces": {"colonnes": ["Catégorie", "Divorces"], "famille": "classement",
                 "mots_cles": {"Divorces": ["divorce"]}},
    "Célibataires": {"colonnes": ["Catégorie", "Célibataires"], "famille": "classement",
                      "mots_cles": {"Célibataires": ["celibataire", "célibataire"]}},
    "Veuvage": {"colonnes": ["Catégorie", "Veufs / veuves"], "famille": "classement",
                "mots_cles": {"Veufs / veuves": ["veuvage", "veuf"]}},
    "Situation matrimoniale": {"colonnes": ["Statut matrimonial", "Population"], "famille": "classement",
                                "mots_cles": {"Population": ["population"]}},

    # ---- Structure ----
    "Pyramide des âges": {"colonnes": ["Tranche d'âge", "Sexe", "Population"], "famille": "pyramide",
                           "mots_cles": {"Population": ["population"]}},
    "Structure par sexe": {"colonnes": ["Sexe", "Population"], "famille": "classement",
                            "mots_cles": {"Population": ["population"]}},
    "Groupes d'âge": {"colonnes": ["Tranche d'âge", "Population"], "famille": "classement",
                       "mots_cles": {"Population": ["population"]}},
    "Rapport de masculinité": {"colonnes": ["Sexe", "Population"], "famille": "masculinite",
                                "mots_cles": {"Population": ["population"]}},
    "Rapport de dépendance": {"colonnes": ["Tranche d'âge (0-14, 15-64, 65+)", "Population"], "famille": "dependance",
                               "mots_cles": {"Population": ["population"]}},

    # ---- Projections ----
    "Projection de population": {"colonnes": ["Catégorie", "Population passée", "Population récente",
                                               "Écart (années)", "Projection (+ années)"], "famille": "projection",
                                  "mots_cles": {"Population récente": ["population"]}},
    "Projection des ménages": {"colonnes": ["Catégorie", "Ménages passés", "Ménages récents",
                                             "Écart (années)", "Projection (+ années)"], "famille": "projection",
                                "mots_cles": {"Ménages récents": ["menage", "ménage"]}},
    "Projection des naissances": {"colonnes": ["Catégorie", "Naissances passées", "Naissances récentes",
                                                "Écart (années)", "Projection (+ années)"], "famille": "projection",
                                   "mots_cles": {"Naissances récentes": ["naissance"]}},
    "Projection des décès": {"colonnes": ["Catégorie", "Décès passés", "Décès récents",
                                           "Écart (années)", "Projection (+ années)"], "famille": "projection",
                              "mots_cles": {"Décès récents": ["deces", "décès"]}},
    "Projection migratoire": {"colonnes": ["Catégorie", "Migration passée", "Migration récente",
                                            "Écart (années)", "Projection (+ années)"], "famille": "projection",
                               "mots_cles": {"Migration récente": ["migration"]}},

    # ---- Indicateurs démographiques ----
    "Accroissement naturel": {"colonnes": ["Naissances", "Décès", "Population"], "famille": "accroissement_naturel",
                               "mots_cles": {"Naissances": ["naissance"], "Décès": ["deces", "décès"],
                                             "Population": ["population"]}},
    "Accroissement total": {"colonnes": ["Catégorie", "Population début", "Population fin"], "famille": "taux_evolution",
                             "nom_taux": "Accroissement total (%)",
                             "mots_cles": {"Population fin": ["population"]}},
    "Taux d'accroissement": {"colonnes": ["Catégorie", "Population début", "Population fin"], "famille": "taux_evolution",
                              "nom_taux": "Taux d'accroissement (%)",
                              "mots_cles": {"Population fin": ["population"]}},
    "Âge moyen": {"colonnes": ["Âge", "Effectif"], "famille": "moyenne_ponderee",
                  "mots_cles": {"Effectif": ["population"]}},
    "Âge médian": {"colonnes": ["Âge", "Effectif"], "famille": "mediane_ponderee",
                   "mots_cles": {"Effectif": ["population"]}},
    "Temps de doublement": {"colonnes": ["Catégorie", "Population début", "Population fin"], "famille": "temps_doublement",
                             "mots_cles": {"Population fin": ["population"]}},
    "Tous les indicateurs": {"colonnes": ["Population", "Naissances", "Décès"], "famille": "tous_indicateurs",
                              "mots_cles": {"Population": ["population"], "Naissances": ["naissance"],
                                            "Décès": ["deces", "décès"]}},
}


# ---------- FONCTIONS DE CALCUL PAR FAMILLE (appliquées au tableau saisi par l'utilisateur) ----------

def lire_tableau_en_donnees(tableau, colonnes):
    """Lit le contenu actuel d'un QTableWidget et le transforme en DataFrame, en ignorant les lignes vides."""
    lignes = []
    for r in range(tableau.rowCount()):
        ligne = []
        vide = True
        for c in range(len(colonnes)):
            item = tableau.item(r, c)
            valeur = item.text().strip() if item else ""
            if valeur != "":
                vide = False
            ligne.append(valeur)
        if not vide:
            lignes.append(ligne)
    if not lignes:
        return None
    dataframe = pd.DataFrame(lignes, columns=colonnes)
    for colonne in colonnes:
        # On enlève les espaces (normaux et insécables) et les virgules, qui sont ici
        # traités comme des séparateurs de milliers — seul le point reste comme séparateur décimal.
        valeurs_nettoyees = (
            dataframe[colonne]
            .str.replace("\u202f", "", regex=False)  # espace insécable fine (courant en copié-collé Excel)
            .str.replace("\u00a0", "", regex=False)   # espace insécable classique
            .str.replace(" ", "", regex=False)
            .str.replace(",", "", regex=False)
        )
        dataframe[colonne + "__num"] = pd.to_numeric(valeurs_nettoyees, errors="coerce")
    return dataframe


def calculer_selon_famille(nom_indicateur, config, dataframe_saisi):
    """Applique la formule de la bonne famille sur les données saisies. Renvoie (resultat_df, message_erreur)."""
    famille = config["famille"]
    colonnes = config["colonnes"]

    try:
        if famille == "classement":
            colonne_valeur = colonnes[-1]
            df = dataframe_saisi.copy()
            df["Résultat"] = df[colonne_valeur + "__num"]
            if df["Résultat"].isna().all():
                return None, f"La colonne '{colonne_valeur}' doit contenir des nombres."
            resultat = df[[colonnes[0], "Résultat"]].sort_values(by="Résultat", ascending=False)
            return resultat, None

        elif famille == "taux":
            colonne_categorie, colonne_num, colonne_denom = colonnes[0], colonnes[1], colonnes[2]
            df = dataframe_saisi.copy()
            df = df[df[colonne_denom + "__num"] > 0]
            if df.empty:
                return None, f"Aucune ligne valide (vérifie que '{colonne_denom}' contient des nombres > 0)."
            nom_taux = config["nom_taux"]
            df[nom_taux] = df[colonne_num + "__num"] / df[colonne_denom + "__num"] * config["facteur"]
            resultat = df[[colonne_categorie, nom_taux]].sort_values(by=nom_taux, ascending=False)
            return resultat, None

        elif famille == "solde":
            colonne_categorie, colonne_entrees, colonne_sorties = colonnes[0], colonnes[1], colonnes[2]
            df = dataframe_saisi.copy()
            nom_resultat = config["nom_resultat"]
            df[nom_resultat] = df[colonne_entrees + "__num"] - df[colonne_sorties + "__num"]
            resultat = df[[colonne_categorie, nom_resultat]].sort_values(by=nom_resultat, ascending=False)
            return resultat, None

        elif famille == "densite":
            colonne_categorie, colonne_pop, colonne_superficie = colonnes[0], colonnes[1], colonnes[2]
            df = dataframe_saisi.copy()
            df = df[df[colonne_superficie + "__num"] > 0]
            if df.empty:
                return None, "Aucune ligne valide (superficie doit être > 0)."
            df["Densité (hab/km²)"] = df[colonne_pop + "__num"] / df[colonne_superficie + "__num"]
            resultat = df[[colonne_categorie, "Densité (hab/km²)"]].sort_values(by="Densité (hab/km²)", ascending=False)
            return resultat, None

        elif famille == "moyenne_simple":
            colonne = colonnes[0]
            valeurs = dataframe_saisi[colonne + "__num"].dropna()
            if valeurs.empty:
                return None, "Aucune valeur numérique saisie."
            resultat = pd.DataFrame({"Indicateur": [f"{nom_indicateur}"], "Valeur": [round(valeurs.mean(), 2)]})
            return resultat, None

        elif famille == "moyenne_ponderee":
            colonne_x, colonne_poids = colonnes[0], colonnes[1]
            df = dataframe_saisi.dropna(subset=[colonne_x + "__num", colonne_poids + "__num"])
            total_poids = df[colonne_poids + "__num"].sum()
            if total_poids == 0 or df.empty:
                return None, "Impossible de calculer (effectifs vides ou nuls)."
            moyenne = (df[colonne_x + "__num"] * df[colonne_poids + "__num"]).sum() / total_poids
            resultat = pd.DataFrame({"Indicateur": [nom_indicateur], "Valeur": [round(moyenne, 2)]})
            return resultat, None

        elif famille == "mediane_ponderee":
            colonne_x, colonne_poids = colonnes[0], colonnes[1]
            df = dataframe_saisi.dropna(subset=[colonne_x + "__num", colonne_poids + "__num"]).sort_values(by=colonne_x + "__num")
            if df.empty:
                return None, "Aucune donnée valide saisie."
            cumul = df[colonne_poids + "__num"].cumsum()
            moitie = df[colonne_poids + "__num"].sum() / 2
            lignes_depassant = df[cumul >= moitie]
            if lignes_depassant.empty:
                return None, "Impossible de déterminer la médiane avec ces données."
            valeur_mediane = lignes_depassant.iloc[0][colonne_x + "__num"]
            resultat = pd.DataFrame({"Indicateur": [nom_indicateur], "Valeur": [valeur_mediane]})
            return resultat, None

        elif famille == "masculinite":
            colonne_sexe, colonne_effectif = colonnes[0], colonnes[1]
            df = dataframe_saisi.copy()
            ligne_hommes = df[df[colonne_sexe].str.lower().str.startswith(("h", "m"), na=False)]
            ligne_femmes = df[df[colonne_sexe].str.lower().str.startswith("f", na=False)]
            if ligne_hommes.empty or ligne_femmes.empty:
                return None, "Il faut une ligne commençant par 'H' (Hommes) et une ligne commençant par 'F' (Femmes)."
            hommes = ligne_hommes[colonne_effectif + "__num"].sum()
            femmes = ligne_femmes[colonne_effectif + "__num"].sum()
            if femmes == 0:
                return None, "L'effectif des femmes ne peut pas être 0."
            resultat = pd.DataFrame({"Indicateur": ["Rapport de masculinité (hommes pour 100 femmes)"],
                                      "Valeur": [round(hommes / femmes * 100, 2)]})
            return resultat, None

        elif famille == "dependance":
            colonne_tranche, colonne_pop = colonnes[0], colonnes[1]
            df = dataframe_saisi.copy()
            df["tranche_normalisee"] = df[colonne_tranche].str.replace(" ", "").str.lower()
            jeunes = df[df["tranche_normalisee"].str.contains("0-14", na=False)][colonne_pop + "__num"].sum()
            actifs = df[df["tranche_normalisee"].str.contains("15-64", na=False)][colonne_pop + "__num"].sum()
            ages = df[df["tranche_normalisee"].str.contains("65", na=False)][colonne_pop + "__num"].sum()
            if actifs == 0:
                return None, "Il faut une ligne '15-64' avec un effectif > 0. Utilise exactement ces libellés : 0-14, 15-64, 65+."
            rapport = (jeunes + ages) / actifs * 100
            resultat = pd.DataFrame({"Indicateur": ["Rapport de dépendance (%)"], "Valeur": [round(rapport, 2)]})
            return resultat, None

        elif famille == "accroissement_naturel":
            colonne_naiss, colonne_deces, colonne_pop = colonnes[0], colonnes[1], colonnes[2]
            total_naiss = dataframe_saisi[colonne_naiss + "__num"].sum()
            total_deces = dataframe_saisi[colonne_deces + "__num"].sum()
            total_pop = dataframe_saisi[colonne_pop + "__num"].sum()
            if total_pop == 0:
                return None, "La population totale saisie ne peut pas être 0."
            taux = (total_naiss - total_deces) / total_pop * 100
            resultat = pd.DataFrame({"Indicateur": ["Taux d'accroissement naturel (%)"], "Valeur": [round(taux, 3)]})
            return resultat, None

        elif famille == "taux_evolution":
            colonne_categorie, colonne_debut, colonne_fin = colonnes[0], colonnes[1], colonnes[2]
            df = dataframe_saisi.copy()
            df = df[df[colonne_debut + "__num"] > 0]
            if df.empty:
                return None, f"'{colonne_debut}' doit contenir des valeurs > 0."
            nom_taux = config["nom_taux"]
            df[nom_taux] = (df[colonne_fin + "__num"] - df[colonne_debut + "__num"]) / df[colonne_debut + "__num"] * 100
            resultat = df[[colonne_categorie, nom_taux]].sort_values(by=nom_taux, ascending=False)
            return resultat, None

        elif famille == "temps_doublement":
            import math
            colonne_categorie, colonne_debut, colonne_fin = colonnes[0], colonnes[1], colonnes[2]
            df = dataframe_saisi.copy()
            df = df[df[colonne_debut + "__num"] > 0]
            if df.empty:
                return None, f"'{colonne_debut}' doit contenir des valeurs > 0."
            taux = (df[colonne_fin + "__num"] - df[colonne_debut + "__num"]) / df[colonne_debut + "__num"]
            df = df[taux > 0]
            if df.empty:
                return None, "Le taux de croissance doit être positif pour calculer un temps de doublement."
            taux_positif = (df[colonne_fin + "__num"] - df[colonne_debut + "__num"]) / df[colonne_debut + "__num"]
            df["Temps de doublement (années)"] = taux_positif.apply(lambda t: round(math.log(2) / t, 1))
            resultat = df[[colonne_categorie, "Temps de doublement (années)"]].sort_values(
                by="Temps de doublement (années)")
            return resultat, None

        elif famille == "projection":
            colonne_categorie, colonne_passe, colonne_recent, colonne_ecart, colonne_projection = colonnes
            df = dataframe_saisi.copy()
            df = df[(df[colonne_passe + "__num"] > 0) & (df[colonne_ecart + "__num"] > 0)]
            if df.empty:
                return None, f"'{colonne_passe}' et '{colonne_ecart}' doivent contenir des valeurs > 0."
            taux_annuel = (df[colonne_recent + "__num"] / df[colonne_passe + "__num"]) ** (1 / df[colonne_ecart + "__num"]) - 1
            nom_resultat = "Valeur projetée"
            df[nom_resultat] = df[colonne_recent + "__num"] * (1 + taux_annuel) ** df[colonne_projection + "__num"]
            resultat = df[[colonne_categorie, nom_resultat]].sort_values(by=nom_resultat, ascending=False)
            return resultat, None

        elif famille == "pyramide":
            colonne_tranche, colonne_sexe, colonne_pop = colonnes
            df = dataframe_saisi.copy()
            resultat = df.groupby([colonne_tranche, colonne_sexe])[colonne_pop + "__num"].sum().reset_index()
            resultat = resultat.rename(columns={colonne_pop + "__num": colonne_pop})
            return resultat, None

        elif famille == "tous_indicateurs":
            colonne_pop, colonne_naiss, colonne_deces = colonnes
            lignes = []
            if dataframe_saisi[colonne_pop + "__num"].notna().any():
                lignes.append(("Population totale", dataframe_saisi[colonne_pop + "__num"].sum()))
                lignes.append(("Population moyenne", round(dataframe_saisi[colonne_pop + "__num"].mean(), 2)))
            if dataframe_saisi[colonne_naiss + "__num"].notna().any():
                lignes.append(("Naissances totales", dataframe_saisi[colonne_naiss + "__num"].sum()))
            if dataframe_saisi[colonne_deces + "__num"].notna().any():
                lignes.append(("Décès totaux", dataframe_saisi[colonne_deces + "__num"].sum()))
            if not lignes:
                return None, "Aucune donnée numérique saisie."
            resultat = pd.DataFrame(lignes, columns=["Indicateur", "Valeur"])
            return resultat, None

        else:
            return None, "Famille de calcul inconnue."

    except Exception as erreur:
        return None, f"Erreur de calcul : {erreur}"



# ---------- DICTIONNAIRE DES INDICATEURS : FORMULES PAR FAMILLE ----------

def obtenir_categorie_indicateur(nom_indicateur):
    """Retrouve la catégorie (Population, Mortalité...) à laquelle appartient un indicateur."""
    for categorie, sous_items in CATEGORIES_ANALYSES.items():
        if nom_indicateur in sous_items:
            return categorie
    return "Non classé"


def obtenir_formule_texte(config):
    """Renvoie une description textuelle de la formule utilisée, selon la famille de l'indicateur."""
    famille = config["famille"]
    colonnes = config["colonnes"]

    if famille == "classement":
        return f"Classement des valeurs de la colonne « {colonnes[-1]} », de la plus grande à la plus petite."
    elif famille == "taux":
        return f"{config.get('nom_taux', 'Taux')} = ({colonnes[1]} ÷ {colonnes[2]}) × {config.get('facteur', '')}"
    elif famille == "solde":
        return f"{config.get('nom_resultat', 'Solde')} = {colonnes[1]} − {colonnes[2]}"
    elif famille == "densite":
        return f"Densité = {colonnes[1]} ÷ {colonnes[2]}"
    elif famille == "moyenne_simple":
        return f"Moyenne = somme des valeurs de « {colonnes[0]} » ÷ nombre de valeurs saisies."
    elif famille == "moyenne_ponderee":
        return f"Moyenne pondérée = Σ({colonnes[0]} × {colonnes[1]}) ÷ Σ({colonnes[1]})"
    elif famille == "mediane_ponderee":
        return (f"Médiane pondérée : valeur de « {colonnes[0]} » où la moitié de l'effectif "
                f"cumulé de « {colonnes[1]} » est atteint.")
    elif famille == "masculinite":
        return "Rapport de masculinité = (effectif Hommes ÷ effectif Femmes) × 100"
    elif famille == "dependance":
        return "Rapport de dépendance = (Population 0-14 + Population 65+) ÷ Population 15-64 × 100"
    elif famille == "accroissement_naturel":
        return f"Taux d'accroissement naturel = ({colonnes[0]} − {colonnes[1]}) ÷ {colonnes[2]} × 100"
    elif famille == "taux_evolution":
        return f"{config.get('nom_taux', 'Taux')} = ({colonnes[2]} − {colonnes[1]}) ÷ {colonnes[1]} × 100"
    elif famille == "temps_doublement":
        return "Temps de doublement = ln(2) ÷ taux de croissance annuel"
    elif famille == "projection":
        return ("Valeur projetée = Valeur récente × (1 + taux annuel) ^ nombre d'années à projeter, "
                "avec taux annuel = (Valeur récente ÷ Valeur passée) ^ (1 ÷ écart en années) − 1")
    elif famille == "pyramide":
        return f"Répartition croisée de « {colonnes[2]} » par « {colonnes[0]} » et « {colonnes[1]} »."
    elif famille == "tous_indicateurs":
        return ("Compilation de plusieurs indicateurs de base (population totale, moyenne, "
                "naissances totales, décès totaux) à partir des colonnes saisies.")
    else:
        return "Formule non documentée."


def obtenir_definition_texte(nom_indicateur, categorie):
    """Renvoie une courte définition générique de l'indicateur, basée sur sa catégorie et son nom."""
    return (f"« {nom_indicateur} » est un indicateur du domaine {categorie.lower()}, "
            f"calculé à partir des données saisies dans le tableau ci-dessus.")


def generer_interpretation(nom_indicateur, resultat):
    """Génère un texte d'interprétation simple à partir du résultat calculé."""
    if resultat is None or resultat.empty:
        return "Aucun résultat à interpréter."

    if resultat.shape[0] == 1:
        colonne_valeur = resultat.columns[-1]
        valeur = resultat.iloc[0][colonne_valeur]
        return f"La valeur calculée pour « {nom_indicateur} » est de {valeur}."

    colonne_categorie = resultat.columns[0]
    colonne_valeur = resultat.columns[-1]
    ligne_max = resultat.iloc[0]
    ligne_min = resultat.iloc[-1]
    return (
        f"Sur les {resultat.shape[0]} lignes calculées pour « {nom_indicateur} », "
        f"la valeur la plus élevée est observée pour « {ligne_max[colonne_categorie]} » "
        f"({ligne_max[colonne_valeur]:.2f} si numérique), et la plus basse pour « {ligne_min[colonne_categorie]} » "
        f"({ligne_min[colonne_valeur]:.2f} si numérique)."
    ) if pd.api.types.is_numeric_dtype(resultat[colonne_valeur]) else (
        f"{resultat.shape[0]} lignes ont été calculées pour « {nom_indicateur} »."
    )


def calculer_fiche_globale(config, dataframe_saisi):
    """Calcule un résumé global (totaux des colonnes saisies) pour l'afficher dans la fiche résultat."""
    resume = {}
    for colonne in config["colonnes"]:
        colonne_num = colonne + "__num"
        if colonne_num in dataframe_saisi.columns and dataframe_saisi[colonne_num].notna().any():
            resume[colonne] = round(dataframe_saisi[colonne_num].sum(), 2)
    return resume


# ---------- SECTIONS DE L'INTERFACE ----------

def creer_tableau_saisie(colonnes, nb_lignes_initial=12):
    """Crée un QTableWidget qui accepte le copier-coller depuis Excel (Ctrl+V)."""
    from PyQt6.QtGui import QShortcut, QKeySequence
    from PyQt6.QtWidgets import QApplication

    tableau = QTableWidget(nb_lignes_initial, len(colonnes))
    tableau.setHorizontalHeaderLabels(colonnes)

    def gerer_collage():
        presse_papier = QApplication.clipboard().text()
        if not presse_papier:
            return
        lignes_collees = presse_papier.strip("\n").split("\n")
        ligne_depart = tableau.currentRow() if tableau.currentRow() >= 0 else 0
        colonne_depart = tableau.currentColumn() if tableau.currentColumn() >= 0 else 0

        for i, ligne_texte in enumerate(lignes_collees):
            valeurs = ligne_texte.split("\t")
            ligne_cible = ligne_depart + i
            if ligne_cible >= tableau.rowCount():
                tableau.insertRow(tableau.rowCount())
            for j, valeur in enumerate(valeurs):
                colonne_cible = colonne_depart + j
                if colonne_cible < tableau.columnCount():
                    tableau.setItem(ligne_cible, colonne_cible, QTableWidgetItem(valeur.strip()))

    raccourci = QShortcut(QKeySequence.StandardKey.Paste, tableau)
    raccourci.activated.connect(gerer_collage)

    return tableau


def remplir_depuis_donnees_importees(tableau, colonnes, mots_cles, donnees):
    """Remplit le tableau de saisie avec les vraies colonnes du fichier importé, si elles sont trouvées."""
    if donnees is None:
        QMessageBox.warning(None, "Erreur", "Aucune donnée importée. Va d'abord dans l'onglet 'Données'.")
        return

    colonnes_texte = list(donnees.select_dtypes(include="object").columns)
    colonne_categorie_source = colonnes_texte[0] if colonnes_texte else None

    colonnes_sources = {}
    colonnes_manquantes = []
    for colonne_config in colonnes:
        if colonne_config in mots_cles:
            colonne_trouvee = trouver_colonne_correspondante(donnees, mots_cles[colonne_config])
            if colonne_trouvee:
                colonnes_sources[colonne_config] = colonne_trouvee
            else:
                colonnes_manquantes.append(colonne_config)
        elif colonne_categorie_source:
            colonnes_sources[colonne_config] = colonne_categorie_source
        else:
            colonnes_manquantes.append(colonne_config)

    if not colonnes_sources:
        QMessageBox.information(None, "Info", "Aucune colonne correspondante trouvée dans le fichier importé.")
        return

    nb_lignes = min(len(donnees), 500)
    tableau.setRowCount(nb_lignes)
    for i in range(nb_lignes):
        for j, colonne_config in enumerate(colonnes):
            if colonne_config in colonnes_sources:
                valeur = donnees.iloc[i][colonnes_sources[colonne_config]]
                tableau.setItem(i, j, QTableWidgetItem(str(valeur)))

    if colonnes_manquantes:
        QMessageBox.information(
            None, "Remplissage partiel",
            "Colonnes non trouvées dans le fichier importé (à compléter à la main) :\n"
            + ", ".join(colonnes_manquantes)
        )


def creer_onglet_donnees(fonction_import, fonction_import_sql):
    """Onglet Données : source et filtres."""
    contenu = QWidget()
    layout = QVBoxLayout()

    groupe_source = QGroupBox("Sélection de la source de données")
    layout_source = QHBoxLayout()
    bouton_excel = QPushButton("Importer Excel / CSV")
    bouton_excel.clicked.connect(fonction_import)
    layout_source.addWidget(bouton_excel)

    bouton_sql = QPushButton("Base SQL")
    bouton_sql.clicked.connect(fonction_import_sql)
    layout_source.addWidget(bouton_sql)

    for nom in ["Recensement", "Enquête"]:
        bouton = QPushButton(nom)
        bouton.setEnabled(False)
        bouton.setToolTip("À venir")
        layout_source.addWidget(bouton)
    groupe_source.setLayout(layout_source)

    groupe_filtres = QGroupBox("Filtres")
    layout_filtres = QGridLayout()
    colonne_index = 0
    for nom_filtre in CORRESPONDANCES_FILTRES:
        label = QLabel(nom_filtre)
        combo = QComboBox()
        combo.setMinimumWidth(120)
        combo.setEnabled(False)
        combo.addItem("Non disponible")
        layout_filtres.addWidget(label, 0, colonne_index)
        layout_filtres.addWidget(combo, 1, colonne_index)
        colonne_index += 1
    groupe_filtres.setLayout(layout_filtres)

    layout.addWidget(groupe_source)
    layout.addWidget(groupe_filtres)
    layout.addStretch()
    contenu.setLayout(layout)

    zone_defilement = QScrollArea()
    zone_defilement.setWidgetResizable(True)
    zone_defilement.setWidget(contenu)
    return zone_defilement


def creer_onglet_visualisations():
    """Onglet Visualisations : le graphique du dernier calcul est visible directement dans Analyses."""
    onglet = QWidget()
    layout = QVBoxLayout()
    label_info = QLabel(
        "Le graphique du dernier indicateur calculé est visible directement dans l'onglet Analyses "
        "(bouton 'Graphique')."
    )
    label_info.setStyleSheet("color: gray;")
    label_info.setWordWrap(True)
    layout.addWidget(label_info)
    layout.addStretch()
    onglet.setLayout(layout)
    return onglet


def creer_onglet_rapports(obtenir_dernier_resultat):
    """Onglet Rapports : export du dernier résultat calculé dans Analyses."""
    onglet = QWidget()
    layout = QVBoxLayout()

    label_info = QLabel("Exporte le dernier résultat calculé dans l'onglet Analyses.")
    label_info.setWordWrap(True)
    label_info.setStyleSheet("color: gray;")
    layout.addWidget(label_info)

    layout_boutons = QHBoxLayout()

    def verifier_et_obtenir():
        resultat = obtenir_dernier_resultat()
        if resultat is None:
            QMessageBox.warning(None, "Erreur", "Calcule d'abord un résultat dans l'onglet Analyses.")
        return resultat

    def gerer_export_excel():
        resultat = verifier_et_obtenir()
        if resultat is None:
            return
        chemin, _ = QFileDialog.getSaveFileName(None, "Exporter en Excel", "", "Fichiers Excel (*.xlsx)")
        if chemin:
            exporter_excel(resultat, chemin)
            QMessageBox.information(None, "Export réussi", f"Résultat exporté vers {chemin}")

    def gerer_export_pdf():
        resultat = verifier_et_obtenir()
        if resultat is None:
            return
        chemin, _ = QFileDialog.getSaveFileName(None, "Exporter en PDF", "", "Fichiers PDF (*.pdf)")
        if chemin:
            exporter_pdf(resultat, "Résultat d'analyse - Démographie", chemin)
            QMessageBox.information(None, "Export réussi", f"Résultat exporté vers {chemin}")

    def gerer_export_word():
        resultat = verifier_et_obtenir()
        if resultat is None:
            return
        chemin, _ = QFileDialog.getSaveFileName(None, "Exporter en Word", "", "Documents Word (*.docx)")
        if chemin:
            exporter_word(resultat, "Résultat d'analyse - Démographie", chemin)
            QMessageBox.information(None, "Export réussi", f"Résultat exporté vers {chemin}")

    def gerer_export_powerpoint():
        resultat = verifier_et_obtenir()
        if resultat is None:
            return
        chemin, _ = QFileDialog.getSaveFileName(None, "Exporter en PowerPoint", "", "Fichiers PowerPoint (*.pptx)")
        if chemin:
            exporter_powerpoint(resultat, "Résultat d'analyse - Démographie", chemin)
            QMessageBox.information(None, "Export réussi", f"Résultat exporté vers {chemin}")

    for nom, fonction in [("Excel", gerer_export_excel), ("PDF", gerer_export_pdf),
                           ("Word", gerer_export_word), ("PowerPoint", gerer_export_powerpoint)]:
        bouton = QPushButton(nom)
        bouton.clicked.connect(fonction)
        layout_boutons.addWidget(bouton)

    layout.addLayout(layout_boutons)
    layout.addStretch()
    onglet.setLayout(layout)
    return onglet


def creer_onglet_accueil(gerer_ouverture_categorie):
    """Onglet Accueil : cartes cliquables par catégorie, qui ouvrent Analyses sur la bonne catégorie."""
    onglet = QWidget()
    layout = QVBoxLayout()

    titre = QLabel("ANALYSE DÉMOGRAPHIQUE")
    titre.setStyleSheet("font-size: 16px; font-weight: bold;")
    titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(titre)

    grille = QGridLayout()
    grille.setSpacing(15)
    noms_categories = list(CATEGORIES_ANALYSES.keys())
    for i, categorie in enumerate(noms_categories):
        carte = QPushButton(categorie.upper())
        carte.setMinimumHeight(70)
        carte.setStyleSheet("font-weight: bold;")
        carte.clicked.connect(lambda checked, c=categorie: gerer_ouverture_categorie(c))
        grille.addWidget(carte, i // 3, i % 3)

    conteneur_grille = QWidget()
    conteneur_grille.setLayout(grille)
    layout.addWidget(conteneur_grille)
    layout.addStretch()
    onglet.setLayout(layout)
    return onglet


def creer_widget_fiche_resultat():
    """Crée le petit encadré 'fiche professionnelle' qui résume les données saisies et le résultat."""
    cadre = QFrame()
    cadre.setFrameShape(QFrame.Shape.Box)
    cadre.setStyleSheet("background-color: #f7f7f7;")
    layout = QVBoxLayout()
    label_titre = QLabel("")
    label_titre.setStyleSheet("font-weight: bold; font-size: 13px;")
    label_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label_contenu = QLabel("")
    label_contenu.setWordWrap(True)
    layout.addWidget(label_titre)
    layout.addWidget(label_contenu)
    cadre.setLayout(layout)
    return cadre, label_titre, label_contenu


def creer_onglet_analyses(obtenir_donnees_actuelles, enregistrer_dernier_resultat):
    """Onglet Analyses : arborescence à gauche, fiche + saisie + résultat (Tableau/Graphique/Formule/Interprétation) à droite."""
    onglet = QWidget()
    layout = QHBoxLayout()

    arbre = QTreeWidget()
    arbre.setHeaderLabel("Indicateurs")
    arbre.setMinimumWidth(260)
    elements_categorie = {}
    for categorie, sous_items in CATEGORIES_ANALYSES.items():
        item_categorie = QTreeWidgetItem([categorie])
        for sous_item in sous_items:
            item_categorie.addChild(QTreeWidgetItem([sous_item]))
        arbre.addTopLevelItem(item_categorie)
        elements_categorie[categorie] = item_categorie

    panneau_droit = QWidget()
    layout_droit = QVBoxLayout()
    label_titre = QLabel("Sélectionne un indicateur dans la liste à gauche.")
    label_titre.setStyleSheet("font-weight: bold; font-size: 13px;")

    label_instructions = QLabel("")
    label_instructions.setStyleSheet("color: gray;")
    label_instructions.setWordWrap(True)

    conteneur_saisie = QWidget()
    zone_tableau_saisie = QVBoxLayout()
    conteneur_saisie.setLayout(zone_tableau_saisie)

    layout_boutons_action = QHBoxLayout()
    bouton_remplir = QPushButton("Remplir depuis mes données importées")
    bouton_calculer = QPushButton("Calculer")
    layout_boutons_action.addWidget(bouton_remplir)
    layout_boutons_action.addWidget(bouton_calculer)

    fiche_cadre, fiche_titre, fiche_contenu = creer_widget_fiche_resultat()
    fiche_cadre.setVisible(False)

    layout_boutons_vue = QHBoxLayout()
    bouton_vue_tableau = QPushButton("📋 Tableau")
    bouton_vue_graphique = QPushButton("📈 Graphique")
    bouton_vue_formule = QPushButton("Σ Formule")
    bouton_vue_interpretation = QPushButton("💬 Interprétation")
    for b in (bouton_vue_tableau, bouton_vue_graphique, bouton_vue_formule, bouton_vue_interpretation):
        layout_boutons_vue.addWidget(b)

    pile_vues = QStackedWidget()

    tableau_resultat = QTableWidget()
    tableau_resultat.setMinimumHeight(220)
    pile_vues.addWidget(tableau_resultat)  # index 0

    figure = Figure(figsize=(5, 3))
    canvas = FigureCanvasQTAgg(figure)
    canvas.setMinimumHeight(280)
    pile_vues.addWidget(canvas)  # index 1

    label_formule = QLabel("")
    label_formule.setWordWrap(True)
    label_formule.setStyleSheet("font-size: 13px; padding: 10px;")
    pile_vues.addWidget(label_formule)  # index 2

    label_interpretation = QLabel("")
    label_interpretation.setWordWrap(True)
    label_interpretation.setStyleSheet("font-size: 13px; padding: 10px;")
    pile_vues.addWidget(label_interpretation)  # index 3

    bouton_vue_tableau.clicked.connect(lambda: pile_vues.setCurrentIndex(0))
    bouton_vue_graphique.clicked.connect(lambda: pile_vues.setCurrentIndex(1))
    bouton_vue_formule.clicked.connect(lambda: pile_vues.setCurrentIndex(2))
    bouton_vue_interpretation.clicked.connect(lambda: pile_vues.setCurrentIndex(3))

    layout_droit.addWidget(label_titre)
    layout_droit.addWidget(label_instructions)
    layout_droit.addWidget(conteneur_saisie)
    layout_droit.addLayout(layout_boutons_action)
    layout_droit.addWidget(fiche_cadre)
    layout_droit.addLayout(layout_boutons_vue)
    layout_droit.addWidget(pile_vues)
    panneau_droit.setLayout(layout_droit)

    zone_defilement_droite = QScrollArea()
    zone_defilement_droite.setWidgetResizable(True)
    zone_defilement_droite.setWidget(panneau_droit)

    indicateur_actuel = {"nom": None, "config": None, "tableau_saisie": None}
    etats_indicateurs = {}  # {nom_item: {"tableau_saisie": widget, "resultat": df/None, "fiche_texte", "interpretation_texte"}}

    def retirer_widget_saisie_sans_detruire():
        """Retire le tableau de saisie actuellement affiché du layout, SANS le détruire (il reste en mémoire)."""
        while zone_tableau_saisie.count():
            item = zone_tableau_saisie.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)  # détache proprement le widget, sans le supprimer

    def redessiner_graphique_resultat(nom_item, resultat):
        figure.clear()
        if resultat is not None and resultat.shape[0] > 1 and resultat.shape[1] == 2:
            try:
                ax = figure.add_subplot(111)
                top_10 = resultat.head(10)
                colonne_cat, colonne_val = resultat.columns[0], resultat.columns[1]
                ax.barh(top_10[colonne_cat].astype(str), top_10[colonne_val])
                ax.set_title(nom_item)
                ax.invert_yaxis()
                figure.tight_layout()
            except Exception:
                pass
        canvas.draw()

    def selectionner_indicateur(nom_item):
        if nom_item not in INDICATEURS_CONFIG:
            return
        config = INDICATEURS_CONFIG[nom_item]
        indicateur_actuel["nom"] = nom_item
        indicateur_actuel["config"] = config

        label_titre.setText(nom_item)
        label_instructions.setText(
            "Colle tes données ici avec Ctrl+V (depuis Excel par exemple), ou remplis les cases à la main, "
            "puis clique sur 'Calculer'. Colonnes attendues : " + " | ".join(config["colonnes"])
        )

        retirer_widget_saisie_sans_detruire()

        if nom_item not in etats_indicateurs:
            etats_indicateurs[nom_item] = {
                "tableau_saisie": creer_tableau_saisie(config["colonnes"]),
                "resultat": None, "fiche_texte": None, "interpretation_texte": None,
            }

        etat = etats_indicateurs[nom_item]
        zone_tableau_saisie.addWidget(etat["tableau_saisie"])
        etat["tableau_saisie"].show()
        indicateur_actuel["tableau_saisie"] = etat["tableau_saisie"]

        label_formule.setText(obtenir_formule_texte(config))

        if etat["resultat"] is not None:
            # Cet indicateur a déjà été calculé avant : on réaffiche son résultat tel quel.
            resultat = etat["resultat"]
            fiche_titre.setText(nom_item.upper())
            fiche_contenu.setText(etat["fiche_texte"])
            fiche_cadre.setVisible(True)
            remplir_tableau_resultat(tableau_resultat, resultat)
            redessiner_graphique_resultat(nom_item, resultat)
            label_interpretation.setText(etat["interpretation_texte"])
        else:
            tableau_resultat.setRowCount(0)
            tableau_resultat.setColumnCount(0)
            figure.clear()
            canvas.draw()
            label_interpretation.setText("Calcule d'abord un résultat pour voir son interprétation.")
            fiche_cadre.setVisible(False)

        pile_vues.setCurrentIndex(0)

    def gerer_selection_arbre(item, colonne):
        try:
            selectionner_indicateur(item.text(0))
        except Exception as erreur:
            import traceback
            QMessageBox.critical(
                None, "Erreur inattendue",
                f"Une erreur est survenue en ouvrant cet indicateur :\n\n{erreur}\n\n"
                f"Détail technique :\n{traceback.format_exc()[-800:]}"
            )

    def gerer_remplissage():
        if indicateur_actuel["nom"] is None:
            QMessageBox.information(None, "Info", "Sélectionne d'abord un indicateur dans la liste.")
            return
        config = indicateur_actuel["config"]
        remplir_depuis_donnees_importees(
            indicateur_actuel["tableau_saisie"], config["colonnes"], config["mots_cles"], obtenir_donnees_actuelles()
        )

    def gerer_calcul():
        if indicateur_actuel["nom"] is None:
            QMessageBox.information(None, "Info", "Sélectionne d'abord un indicateur dans la liste.")
            return

        nom_item = indicateur_actuel["nom"]
        config = indicateur_actuel["config"]
        tableau_saisie = indicateur_actuel["tableau_saisie"]

        dataframe_saisi = lire_tableau_en_donnees(tableau_saisie, config["colonnes"])
        if dataframe_saisi is None:
            QMessageBox.warning(None, "Erreur", "Le tableau est vide. Colle ou saisis des données d'abord.")
            return

        resultat, message_erreur = calculer_selon_famille(nom_item, config, dataframe_saisi)

        if resultat is None:
            QMessageBox.warning(None, "Erreur de calcul", message_erreur)
            return

        try:
            enregistrer_dernier_resultat(resultat, figure)

            # --- Fiche professionnelle ---
            fiche_titre.setText(nom_item.upper())
            resume_global = calculer_fiche_globale(config, dataframe_saisi)
            lignes_fiche = []
            for cle, valeur in resume_global.items():
                try:
                    lignes_fiche.append(f"{cle} : {float(valeur):,.2f}".replace(",", " "))
                except (ValueError, TypeError):
                    lignes_fiche.append(f"{cle} : {valeur}")
            if resultat.shape[0] == 1:
                colonne_resultat = resultat.columns[-1]
                valeur_resultat = resultat.iloc[0][colonne_resultat]
                lignes_fiche.append(f"Résultat : {valeur_resultat}")
            else:
                lignes_fiche.append(f"{resultat.shape[0]} résultats calculés — voir l'onglet Tableau.")
            fiche_contenu.setText("\n".join(lignes_fiche))
            fiche_cadre.setVisible(True)

            # --- Tableau ---
            remplir_tableau_resultat(tableau_resultat, resultat)

            # --- Graphique ---
            figure.clear()
            if resultat.shape[0] > 1 and resultat.shape[1] == 2:
                try:
                    ax = figure.add_subplot(111)
                    top_10 = resultat.head(10)
                    colonne_cat, colonne_val = resultat.columns[0], resultat.columns[1]
                    ax.barh(top_10[colonne_cat].astype(str), top_10[colonne_val])
                    ax.set_title(nom_item)
                    ax.invert_yaxis()
                    figure.tight_layout()
                except Exception:
                    pass
            canvas.draw()

            # --- Formule (déjà affichée dès la sélection, on la garde) ---
            label_formule.setText(obtenir_formule_texte(config))

            # --- Interprétation ---
            texte_interpretation = generer_interpretation(nom_item, resultat)
            label_interpretation.setText(texte_interpretation)

            # --- Sauvegarde dans le cache, pour que ce résultat reste visible si on revient sur cet indicateur ---
            etats_indicateurs[nom_item]["resultat"] = resultat
            etats_indicateurs[nom_item]["fiche_texte"] = fiche_contenu.text()
            etats_indicateurs[nom_item]["interpretation_texte"] = texte_interpretation

        except Exception as erreur:
            import traceback
            QMessageBox.critical(
                None, "Erreur inattendue",
                f"Une erreur est survenue lors de l'affichage du résultat pour '{nom_item}' :\n\n{erreur}\n\n"
                f"Détail technique :\n{traceback.format_exc()[-800:]}"
            )

    arbre.itemClicked.connect(gerer_selection_arbre)
    bouton_remplir.clicked.connect(gerer_remplissage)
    bouton_calculer.clicked.connect(gerer_calcul)

    diviseur = QSplitter(Qt.Orientation.Horizontal)
    diviseur.addWidget(arbre)
    diviseur.addWidget(zone_defilement_droite)
    diviseur.setStretchFactor(1, 1)

    layout.addWidget(diviseur)
    onglet.setLayout(layout)

    def ouvrir_categorie_depuis_accueil(nom_categorie):
        """Déplie et sélectionne visuellement la catégorie demandée dans l'arbre (appelé depuis Accueil)."""
        item_categorie = elements_categorie.get(nom_categorie)
        if item_categorie:
            item_categorie.setExpanded(True)
            arbre.setCurrentItem(item_categorie)
            arbre.scrollToItem(item_categorie)

    return onglet, ouvrir_categorie_depuis_accueil


# ---------- PAGE COMPLÈTE ----------

def creer_page_demographie(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import, fonction_import_sql):
    """Assemble la page Démographie : Accueil, Données, Analyses, Visualisations, Analyse statistique,
    Graphiques, Tableaux croisés, SIG, Rapports."""
    from Analyse.analyse_avancee import creer_page_analyse_avancee
    from Graphiques.graphiques import creer_page_graphiques
    from Tableaux.tableaux_croises import creer_page_tableaux_croises
    from SIG.sig import creer_page_sig

    page_onglets = QTabWidget()

    dernier_resultat = {"dataframe": None}

    def enregistrer_dernier_resultat(dataframe, figure=None):
        dernier_resultat["dataframe"] = dataframe

    onglet_analyses, ouvrir_categorie = creer_onglet_analyses(obtenir_donnees_actuelles, enregistrer_dernier_resultat)
    onglet_donnees = creer_onglet_donnees(fonction_import, fonction_import_sql)
    onglet_visualisations = creer_onglet_visualisations()
    onglet_rapports = creer_onglet_rapports(lambda: dernier_resultat["dataframe"])

    onglet_analyse_stat = creer_page_analyse_avancee(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import)
    onglet_graphiques = creer_page_graphiques(obtenir_donnees_actuelles)
    onglet_tableaux_croises = creer_page_tableaux_croises(obtenir_donnees_actuelles)
    onglet_sig = creer_page_sig(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import)

    INDEX_ANALYSES = 2

    def gerer_ouverture_categorie(nom_categorie):
        ouvrir_categorie(nom_categorie)
        page_onglets.setCurrentIndex(INDEX_ANALYSES)

    onglet_accueil = creer_onglet_accueil(gerer_ouverture_categorie)

    page_onglets.addTab(onglet_accueil, "Accueil")
    page_onglets.addTab(onglet_donnees, "Données")
    page_onglets.addTab(onglet_analyses, "Analyses")
    page_onglets.addTab(onglet_visualisations, "Visualisations")
    page_onglets.addTab(onglet_analyse_stat, "Analyse statistique")
    page_onglets.addTab(onglet_graphiques, "Graphiques")
    page_onglets.addTab(onglet_tableaux_croises, "Tableaux croisés")
    page_onglets.addTab(onglet_sig, "SIG")
    page_onglets.addTab(onglet_rapports, "Rapports")

    return page_onglets