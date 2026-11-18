"""Module Emploi et Social — utilise le moteur générique partagé."""
from ModuleGenerique.module_generique import creer_page_module

CATEGORIES_ANALYSES = {
    "Emploi": ["Population active", "Emploi", "Chômage", "Sous-emploi", "Secteurs d'activité"],
    "Conditions de travail et revenus": ["Salaires et revenus", "Conditions de travail"],
    "Protection sociale": ["Protection sociale", "Retraites", "Prestations sociales"],
    "Inégalités": ["Pauvreté", "Inégalités sociales", "Personnes en situation de handicap"],
    "Jeunes et femmes": ["Jeunes et emploi", "Emploi des femmes"],
}

INDICATEURS_CONFIG = {
    "Population active": {"colonnes": ["Catégorie", "Population active"], "famille": "classement",
                           "mots_cles": {"Population active": ["population active"]}},
    "Emploi": {"colonnes": ["Catégorie", "Emplois"], "famille": "classement",
               "mots_cles": {"Emplois": ["emploi", "employment"]}},
    "Chômage": {"colonnes": ["Catégorie", "Chômeurs", "Population active"], "famille": "taux",
                "facteur": 100, "nom_taux": "Taux de chômage (%)",
                "mots_cles": {"Chômeurs": ["chomage", "chômage"], "Population active": ["population active"]}},
    "Sous-emploi": {"colonnes": ["Catégorie", "Sous-employés", "Population active"], "famille": "taux",
                     "facteur": 100, "nom_taux": "Taux de sous-emploi (%)",
                     "mots_cles": {"Sous-employés": ["sous-emploi", "sous emploi"],
                                   "Population active": ["population active"]}},
    "Secteurs d'activité": {"colonnes": ["Secteur", "Emplois"], "famille": "classement",
                             "mots_cles": {"Emplois": ["secteur"]}},
    "Salaires et revenus": {"colonnes": ["Catégorie", "Salaire moyen"], "famille": "classement",
                             "mots_cles": {"Salaire moyen": ["salaire", "revenu"]}},
    "Conditions de travail": {"colonnes": ["Catégorie", "Indicateur"], "famille": "classement",
                               "mots_cles": {"Indicateur": ["condition de travail"]}},
    "Protection sociale": {"colonnes": ["Catégorie", "Bénéficiaires"], "famille": "classement",
                            "mots_cles": {"Bénéficiaires": ["protection sociale"]}},
    "Retraites": {"colonnes": ["Catégorie", "Retraités"], "famille": "classement",
                  "mots_cles": {"Retraités": ["retraite"]}},
    "Prestations sociales": {"colonnes": ["Catégorie", "Bénéficiaires"], "famille": "classement",
                              "mots_cles": {"Bénéficiaires": ["prestation"]}},
    "Pauvreté": {"colonnes": ["Catégorie", "Taux de pauvreté (%)"], "famille": "classement",
                 "mots_cles": {"Taux de pauvreté (%)": ["pauvrete", "pauvreté"]}},
    "Inégalités sociales": {"colonnes": ["Catégorie", "Indice d'inégalité"], "famille": "classement",
                             "mots_cles": {"Indice d'inégalité": ["inegalite", "inégalité", "gini"]}},
    "Personnes en situation de handicap": {"colonnes": ["Catégorie", "Population en situation de handicap"],
                                            "famille": "classement",
                                            "mots_cles": {"Population en situation de handicap": ["handicap"]}},
    "Jeunes et emploi": {"colonnes": ["Catégorie", "Jeunes en emploi"], "famille": "classement",
                          "mots_cles": {"Jeunes en emploi": ["jeune"]}},
    "Emploi des femmes": {"colonnes": ["Catégorie", "Femmes en emploi"], "famille": "classement",
                           "mots_cles": {"Femmes en emploi": ["femme"]}},
}

SOURCES_SUPPLEMENTAIRES = ["Services publics", "Entreprises", "API"]

CORRESPONDANCES_FILTRES = {
    "Région": ["region", "région"], "Cercle": ["cercle"], "Commune": ["commune"], "Sexe": ["sexe", "sex"],
    "Âge": ["age", "âge"], "Niveau d'études": ["niveau d'etudes", "niveau d'études"], "Secteur": ["secteur"],
    "Profession": ["profession"], "Année": ["annee", "année"], "Trimestre": ["trimestre"],
    "Période": ["periode", "période"],
}


def creer_page_emploi_social(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import, fonction_import_sql):
    """Assemble la page Emploi et Social, avec la même structure que Démographie."""
    return creer_page_module(
        "Emploi et Social", CATEGORIES_ANALYSES, INDICATEURS_CONFIG, SOURCES_SUPPLEMENTAIRES,
        CORRESPONDANCES_FILTRES, obtenir_donnees_actuelles, obtenir_domaine_actuel,
        fonction_import, fonction_import_sql
    )