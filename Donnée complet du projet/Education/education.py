"""Module Éducation — utilise le moteur générique partagé."""
from ModuleGenerique.module_generique import creer_page_module

CATEGORIES_ANALYSES = {
    "Effectifs et inscriptions": ["Effectifs scolaires", "Inscriptions", "Fréquentation"],
    "Résultats scolaires": ["Réussite aux examens", "Redoublement", "Abandon scolaire",
                             "Transition entre niveaux", "Résultats par matière"],
    "Ressources": ["Ratio élèves / enseignant", "Infrastructures scolaires", "Personnel enseignant"],
    "Alphabétisation": ["Alphabétisation"],
}

INDICATEURS_CONFIG = {
    "Effectifs scolaires": {"colonnes": ["Catégorie", "Élèves"], "famille": "classement",
                             "mots_cles": {"Élèves": ["effectif", "eleve", "élève"]}},
    "Inscriptions": {"colonnes": ["Catégorie", "Inscriptions"], "famille": "classement",
                      "mots_cles": {"Inscriptions": ["inscription"]}},
    "Fréquentation": {"colonnes": ["Catégorie", "Fréquentation"], "famille": "classement",
                       "mots_cles": {"Fréquentation": ["frequentation", "fréquentation"]}},
    "Réussite aux examens": {"colonnes": ["Catégorie", "Admis", "Candidats"], "famille": "taux",
                              "facteur": 100, "nom_taux": "Taux de réussite (%)",
                              "mots_cles": {"Admis": ["reussite", "réussite"], "Candidats": ["candidat"]}},
    "Redoublement": {"colonnes": ["Catégorie", "Redoublants", "Élèves"], "famille": "taux",
                      "facteur": 100, "nom_taux": "Taux de redoublement (%)",
                      "mots_cles": {"Redoublants": ["redoublement", "redouble"], "Élèves": ["effectif", "élève"]}},
    "Abandon scolaire": {"colonnes": ["Catégorie", "Abandons", "Élèves"], "famille": "taux",
                          "facteur": 100, "nom_taux": "Taux d'abandon (%)",
                          "mots_cles": {"Abandons": ["abandon"], "Élèves": ["effectif", "élève"]}},
    "Transition entre niveaux": {"colonnes": ["Catégorie", "Transitions", "Élèves"], "famille": "taux",
                                  "facteur": 100, "nom_taux": "Taux de transition (%)",
                                  "mots_cles": {"Transitions": ["transition"], "Élèves": ["effectif", "élève"]}},
    "Résultats par matière": {"colonnes": ["Matière", "Moyenne"], "famille": "classement",
                               "mots_cles": {"Moyenne": ["matiere", "matière", "note"]}},
    "Ratio élèves / enseignant": {"colonnes": ["Catégorie", "Élèves", "Enseignants"], "famille": "densite",
                                   "mots_cles": {"Élèves": ["effectif", "élève"], "Enseignants": ["enseignant"]}},
    "Infrastructures scolaires": {"colonnes": ["Catégorie", "Infrastructures"], "famille": "classement",
                                   "mots_cles": {"Infrastructures": ["infrastructure", "salle de classe"]}},
    "Personnel enseignant": {"colonnes": ["Catégorie", "Enseignants"], "famille": "classement",
                              "mots_cles": {"Enseignants": ["enseignant", "personnel"]}},
    "Alphabétisation": {"colonnes": ["Catégorie", "Alphabétisés", "Population"], "famille": "taux",
                         "facteur": 100, "nom_taux": "Taux d'alphabétisation (%)",
                         "mots_cles": {"Alphabétisés": ["alphabetisation", "alphabétisation"],
                                       "Population": ["population"]}},
}

SOURCES_SUPPLEMENTAIRES = ["Établissements", "Enquêtes", "API"]

CORRESPONDANCES_FILTRES = {
    "Région": ["region", "région"], "Académie": ["academie", "académie"], "Cercle": ["cercle"],
    "Commune": ["commune"], "École": ["ecole", "école"], "Niveau": ["niveau"], "Classe": ["classe"],
    "Sexe": ["sexe", "sex"], "Âge": ["age", "âge"], "Année scolaire": ["annee scolaire", "année scolaire"],
    "Période": ["periode", "période"],
}


def creer_page_education(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import, fonction_import_sql):
    """Assemble la page Éducation, avec la même structure que Démographie."""
    return creer_page_module(
        "Éducation", CATEGORIES_ANALYSES, INDICATEURS_CONFIG, SOURCES_SUPPLEMENTAIRES,
        CORRESPONDANCES_FILTRES, obtenir_donnees_actuelles, obtenir_domaine_actuel,
        fonction_import, fonction_import_sql
    )